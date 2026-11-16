"""
NovaNest Safe SQL Tokenizer, Recursive-Descent AST Parser & Validator
---------------------------------------------------------------------
Zero-dependency SQL AST analyzer that enforces strict read-only analytics:
- Single statement only (rejects multi-statement queries with semicolons)
- Only SELECT / non-recursive WITH CTE / compound queries (UNION/INTERSECT/EXCEPT)
- Recursive validation of every table reference across FROM, comma joins, JOINs,
  CTEs, subqueries (FROM/WHERE/SELECT/HAVING/JOIN ON), and set operations
- Explicit blocking of sqlite_master, sqlite_schema, sqlite_temp_*, system schemas,
  schema-qualified tables, table-valued functions, and dangerous SQLite functions
- Function allowlist + dangerous function blocklist
- Enforced bounded LIMIT (default 25, max 100)
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional, Set, Tuple

DEFAULT_ROW_LIMIT = 25
MAX_ROW_LIMIT = 100
MAX_AST_DEPTH = 32

ALLOWED_TABLES: Set[str] = {
    "orders",
    "customers",
    "restaurants",
    "deliveries",
    "riders",
    "promotions",
    "ratings_reviews",
    "menu_items",
    "payments",
}

FORBIDDEN_SYSTEM_TABLES: Set[str] = {
    "sqlite_master",
    "sqlite_temp_master",
    "sqlite_schema",
    "sqlite_temp_schema",
    "sqlite_sequence",
    "sqlite_stat1",
    "sqlite_stat2",
    "sqlite_stat3",
    "sqlite_stat4",
    "sqlite_parameters",
    "information_schema",
    "performance_schema",
    "mysql",
    "sys",
    "pg_catalog",
    "pg_tables",
    "pg_class",
    "all_tables",
    "user_tables",
    "master",
}

FORBIDDEN_KEYWORDS: Set[str] = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
    "EXPLAIN",
    "ANALYZE",
    "INTO",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "RELEASE",
    "TRANSACTION",
    "TRIGGER",
    "INDEX",
    "VIEW",
    "RECURSIVE",
}

DANGEROUS_FUNCTIONS: Set[str] = {
    "load_extension",
    "fts3_tokenizer",
    "fts5",
    "randomblob",
    "zeroblob",
    "sqlite_version",
    "sqlite_source_id",
    "sqlite_compileoption_get",
    "sqlite_compileoption_used",
    "sqlite_offset",
    "sqlite_log",
    "eval",
    "edit",
    "readfile",
    "writefile",
    "sqlar_compress",
    "sqlar_uncompress",
    "changes",
    "total_changes",
    "last_insert_rowid",
    "likelihood",
    "likely",
    "unlikely",
    "printf",
    "char",
}

SAFE_FUNCTIONS: Set[str] = {
    # Aggregates & window helpers
    "count",
    "sum",
    "avg",
    "min",
    "max",
    "total",
    "group_concat",
    "row_number",
    "rank",
    "dense_rank",
    # Math / null / conditional
    "round",
    "abs",
    "coalesce",
    "ifnull",
    "nullif",
    "iif",
    "typeof",
    # String
    "lower",
    "upper",
    "trim",
    "ltrim",
    "rtrim",
    "length",
    "substr",
    "substring",
    "instr",
    "replace",
    "like",
    # Date & time
    "date",
    "time",
    "datetime",
    "julianday",
    "strftime",
    "unixepoch",
}

CLAUSE_STOP_KEYWORDS: Set[str] = {
    "FROM",
    "WHERE",
    "GROUP",
    "HAVING",
    "ORDER",
    "LIMIT",
    "OFFSET",
    "UNION",
    "INTERSECT",
    "EXCEPT",
    "JOIN",
    "INNER",
    "LEFT",
    "RIGHT",
    "FULL",
    "CROSS",
    "NATURAL",
    "OUTER",
    "ON",
    "USING",
    "SET",
    "INTO",
    "VALUES",
}

JOIN_MODIFIERS: Set[str] = {"INNER", "LEFT", "RIGHT", "FULL", "CROSS", "NATURAL", "OUTER"}


class SQLValidationError(Exception):
    """Raised when SQL fails lexical, syntactic, or security validation."""


@dataclass(frozen=True)
class Token:
    kind: str  # WORD, QUOTED_IDENT, STRING, NUMBER, SYMBOL, EOF
    value: str  # Normalized text (unquoted for QUOTED_IDENT)
    raw: str
    pos: int

    @property
    def upper(self) -> str:
        return self.value.upper() if self.kind == "WORD" else ""


def _is_forbidden_system_identifier(name: str) -> bool:
    low = name.lower()
    return (
        low in FORBIDDEN_SYSTEM_TABLES
        or low.startswith("sqlite_")
        or low.startswith("pragma_")
    )


def tokenize_sql(sql: str) -> List[Token]:
    """Tokenizes SQL text safely while handling quotes, escapes, and comments."""
    tokens: List[Token] = []
    n = len(sql)
    i = 0

    while i < n:
        ch = sql[i]

        if ch.isspace():
            i += 1
            continue

        # Single-line comment
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            i += 2
            while i < n and sql[i] != "\n":
                i += 1
            continue

        # Block comment
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":
            end = sql.find("*/", i + 2)
            if end == -1:
                raise SQLValidationError("Malformed SQL: unclosed block comment.")
            i = end + 2
            continue

        # Single-quoted string literal
        if ch == "'":
            start = i
            i += 1
            buf: List[str] = []
            closed = False
            while i < n:
                if sql[i] == "'":
                    if i + 1 < n and sql[i + 1] == "'":
                        buf.append("'")
                        i += 2
                        continue
                    closed = True
                    i += 1
                    break
                buf.append(sql[i])
                i += 1
            if not closed:
                raise SQLValidationError("Malformed SQL: unclosed string literal.")
            tokens.append(Token("STRING", "".join(buf), sql[start:i], start))
            continue

        # Double-quoted or backtick identifier
        if ch in ('"', "`"):
            quote = ch
            start = i
            i += 1
            buf = []
            closed = False
            while i < n:
                if sql[i] == quote:
                    if i + 1 < n and sql[i + 1] == quote:
                        buf.append(quote)
                        i += 2
                        continue
                    closed = True
                    i += 1
                    break
                buf.append(sql[i])
                i += 1
            if not closed:
                raise SQLValidationError("Malformed SQL: unclosed quoted identifier.")
            tokens.append(Token("QUOTED_IDENT", "".join(buf), sql[start:i], start))
            continue

        # Bracketed identifier [name]
        if ch == "[":
            start = i
            end = sql.find("]", i + 1)
            if end == -1:
                raise SQLValidationError("Malformed SQL: unclosed bracketed identifier.")
            ident = sql[i + 1 : end]
            i = end + 1
            tokens.append(Token("QUOTED_IDENT", ident, sql[start:i], start))
            continue

        # Multi-char operators
        if i + 1 < n and sql[i : i + 2] in ("<=", ">=", "<>", "!=", "||"):
            sym = sql[i : i + 2]
            tokens.append(Token("SYMBOL", sym, sym, i))
            i += 2
            continue

        # Single-char symbols
        if ch in "(),;.*+-/%<>=:":
            tokens.append(Token("SYMBOL", ch, ch, i))
            i += 1
            continue

        # Bind parameter characters (? or @ or $) -> reject explicit host parameters
        if ch in ("?", "@", "$"):
            raise SQLValidationError(f"Security Alert: Parameter placeholder '{ch}' is not permitted.")

        # Numbers
        if ch.isdigit():
            start = i
            has_dot = False
            while i < n and (sql[i].isdigit() or (sql[i] == "." and not has_dot)):
                if sql[i] == ".":
                    has_dot = True
                i += 1
            if i < n and sql[i].lower() == "e":
                i += 1
                if i < n and sql[i] in ("+", "-"):
                    i += 1
                while i < n and sql[i].isdigit():
                    i += 1
            num = sql[start:i]
            tokens.append(Token("NUMBER", num, num, start))
            continue

        # Unquoted words / identifiers
        if ch.isalpha() or ch == "_":
            start = i
            while i < n and (sql[i].isalnum() or sql[i] == "_"):
                i += 1
            word = sql[start:i]
            tokens.append(Token("WORD", word, word, start))
            continue

        raise SQLValidationError(f"Unexpected character in SQL at position {i}: {ch!r}")

    tokens.append(Token("EOF", "", "", n))
    return tokens


def starts_like_sql_statement(text: str) -> bool:
    """Returns True if raw text begins like a SQL statement or SQL injection attempt."""
    stripped = (text or "").strip()
    if not stripped:
        return False
    # Distinguish SQLite `ANALYZE [table];` from natural language inquiries like "Analyze our GMV..." or "Analyze customer churn..."
    if re.match(r"^\s*analy[sz]e\b", stripped, re.IGNORECASE):
        tokens = stripped.split()
        if len(tokens) > 3 or any(
            w.lower() in (
                "my", "our", "the", "and", "for", "in", "with", "to", "of", "from",
                "gmv", "revenue", "profit", "customer", "restaurant", "rider",
                "performance", "profile", "trends", "churn", "delivery"
            )
            for w in tokens
        ):
            return False
    return bool(
        re.match(
            r"^\s*(?:/\*.*?\*/\s*|--[^\n]*\n\s*|\(*\s*)*(?:SELECT|WITH|DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|EXPLAIN|ANALYZE)\b",
            stripped,
            re.IGNORECASE | re.DOTALL,
        )
    )


class _SQLASTValidator:
    """Recursive-descent SQL AST parser & validator enforcing read-only schema safety."""

    def __init__(self, tokens: List[Token], allowed_tables: Set[str], max_row_limit: int) -> None:
        self.tokens = tokens
        self.pos = 0
        self.allowed_tables = {t.lower() for t in allowed_tables}
        self.max_row_limit = max_row_limit
        self.cte_scopes: List[Set[str]] = []
        self.depth = 0
        self.top_level_has_limit = False

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def match_word(self, word: str) -> bool:
        tok = self.current()
        return tok.kind == "WORD" and tok.value.upper() == word

    def expect_word(self, word: str) -> Token:
        if not self.match_word(word):
            raise SQLValidationError(f"Syntax Error: Expected '{word}', got '{self.current().raw}'.")
        return self.advance()

    def is_active_cte(self, ident: str) -> bool:
        low = ident.lower()
        return any(low in scope for scope in self.cte_scopes)

    def _enter_depth(self) -> None:
        self.depth += 1
        if self.depth > MAX_AST_DEPTH:
            raise SQLValidationError("Security Alert: Query nesting depth exceeds safe limit.")

    def _exit_depth(self) -> None:
        self.depth -= 1

    def validate(self) -> None:
        if self.current().kind == "EOF":
            raise SQLValidationError("Empty SQL query.")

        # Detect multiple statements anywhere (trailing single semicolon allowed)
        for idx, tok in enumerate(self.tokens[:-1]):
            if tok.kind == "SYMBOL" and tok.value == ";":
                if self.tokens[idx + 1].kind != "EOF":
                    raise SQLValidationError("Multi-statement SQL queries are strictly prohibited.")

        first = self.current()
        if first.kind == "WORD":
            uw = first.upper
            if uw == "REPLACE" and self.peek().kind == "WORD" and self.peek().upper == "INTO":
                raise SQLValidationError("Security Alert: Only read-only SELECT analytical queries are allowed.")
            if uw not in ("SELECT", "WITH"):
                raise SQLValidationError("Security Alert: Only read-only SELECT analytical queries are allowed.")
        elif not (first.kind == "SYMBOL" and first.value == "("):
            raise SQLValidationError("Security Alert: Only read-only SELECT analytical queries are allowed.")

        # Global token check for dangerous keywords outside string literals
        for i, tok in enumerate(self.tokens[:-1]):
            if tok.kind == "WORD":
                uw = tok.upper
                if uw in FORBIDDEN_KEYWORDS:
                    raise SQLValidationError(
                        f"Security Alert: Forbidden operation '{uw}' detected. Only read-only SELECT queries are permitted."
                    )
                if uw == "REPLACE" and (i == 0 or (i + 1 < len(self.tokens) and self.tokens[i + 1].upper == "INTO")):
                    raise SQLValidationError(
                        "Security Alert: Forbidden operation 'REPLACE' detected. Only read-only SELECT queries are permitted."
                    )

        self.parse_query(is_top_level=True)

        # Optional single trailing semicolon
        if self.current().kind == "SYMBOL" and self.current().value == ";":
            self.advance()

        if self.current().kind != "EOF":
            raise SQLValidationError(f"Malformed SQL: unexpected trailing token '{self.current().raw}'.")

    def parse_query(self, is_top_level: bool = False) -> None:
        self._enter_depth()
        cte_pushed = False
        try:
            if self.match_word("WITH"):
                self.advance()
                if self.match_word("RECURSIVE"):
                    raise SQLValidationError("Security Alert: Recursive CTE queries are prohibited.")
                local_ctes: Set[str] = set()
                while True:
                    name_tok = self.current()
                    if name_tok.kind not in ("WORD", "QUOTED_IDENT"):
                        raise SQLValidationError("Malformed CTE: expected CTE name.")
                    self.advance()
                    cte_name = name_tok.value.lower()
                    if _is_forbidden_system_identifier(cte_name):
                        raise SQLValidationError(
                            f"Security Alert: CTE name '{name_tok.value}' conflicts with forbidden system table."
                        )

                    # Optional column list CTE(c1, c2)
                    if self.current().kind == "SYMBOL" and self.current().value == "(":
                        self.advance()
                        while not (self.current().kind == "SYMBOL" and self.current().value == ")"):
                            if self.current().kind == "EOF":
                                raise SQLValidationError("Malformed CTE: unclosed column list.")
                            self.advance()
                        self.advance()

                    self.expect_word("AS")
                    if self.match_word("NOT") and self.peek().upper == "MATERIALIZED":
                        self.advance()
                        self.advance()
                    elif self.match_word("MATERIALIZED"):
                        self.advance()

                    if not (self.current().kind == "SYMBOL" and self.current().value == "("):
                        raise SQLValidationError("Malformed CTE: expected '(' before CTE query.")
                    self.advance()
                    self.parse_query(is_top_level=False)
                    if not (self.current().kind == "SYMBOL" and self.current().value == ")"):
                        raise SQLValidationError("Malformed CTE: expected ')' after CTE query.")
                    self.advance()

                    local_ctes.add(cte_name)
                    if self.current().kind == "SYMBOL" and self.current().value == ",":
                        self.advance()
                        continue
                    break

                self.cte_scopes.append(local_ctes)
                cte_pushed = True

            self._parse_compound_select()

            if self.match_word("ORDER"):
                self.advance()
                self.expect_word("BY")
                self._parse_order_by_list()

            if self.match_word("LIMIT"):
                self.advance()
                limit_val = self._parse_limit_value()
                if is_top_level:
                    self.top_level_has_limit = True
                    if limit_val > self.max_row_limit:
                        raise SQLValidationError(
                            f"Security Alert: Query LIMIT {limit_val} exceeds maximum allowed ({self.max_row_limit})."
                        )
                if self.match_word("OFFSET"):
                    self.advance()
                    self._parse_limit_value()
                elif self.current().kind == "SYMBOL" and self.current().value == ",":
                    self.advance()
                    second_val = self._parse_limit_value()
                    if is_top_level and second_val > self.max_row_limit:
                        raise SQLValidationError(
                            f"Security Alert: Query LIMIT {second_val} exceeds maximum allowed ({self.max_row_limit})."
                        )
        finally:
            if cte_pushed:
                self.cte_scopes.pop()
            self._exit_depth()

    def _parse_limit_value(self) -> int:
        tok = self.current()
        if tok.kind != "NUMBER" or "." in tok.value or "e" in tok.value.lower():
            raise SQLValidationError("Security Alert: LIMIT/OFFSET must be a non-negative integer literal.")
        self.advance()
        return int(tok.value)

    def _parse_compound_select(self) -> None:
        self._parse_select_core_or_paren()
        while self.current().kind == "WORD" and self.current().upper in ("UNION", "INTERSECT", "EXCEPT"):
            op = self.advance().upper
            if op == "UNION" and self.match_word("ALL"):
                self.advance()
            self._parse_select_core_or_paren()

    def _parse_select_core_or_paren(self) -> None:
        if self.current().kind == "SYMBOL" and self.current().value == "(":
            self.advance()
            self.parse_query(is_top_level=False)
            if not (self.current().kind == "SYMBOL" and self.current().value == ")"):
                raise SQLValidationError("Malformed SQL: expected ')'.")
            self.advance()
            return
        self._parse_select_core()

    def _parse_select_core(self) -> None:
        self.expect_word("SELECT")
        if self.match_word("DISTINCT") or self.match_word("ALL"):
            self.advance()

        # Projection expressions
        self._parse_expr_list_until(
            stop_words={"FROM", "WHERE", "GROUP", "HAVING", "ORDER", "LIMIT", "UNION", "INTERSECT", "EXCEPT"},
            allow_empty=False,
        )

        # Optional FROM
        if self.match_word("FROM"):
            self.advance()
            self._parse_from_clause()

        # Optional WHERE
        if self.match_word("WHERE"):
            self.advance()
            self._parse_expr(stop_words={"GROUP", "HAVING", "ORDER", "LIMIT", "UNION", "INTERSECT", "EXCEPT"})

        # Optional GROUP BY + HAVING
        if self.match_word("GROUP"):
            self.advance()
            self.expect_word("BY")
            self._parse_expr_list_until(
                stop_words={"HAVING", "ORDER", "LIMIT", "UNION", "INTERSECT", "EXCEPT"},
                allow_empty=False,
            )
            if self.match_word("HAVING"):
                self.advance()
                self._parse_expr(stop_words={"ORDER", "LIMIT", "UNION", "INTERSECT", "EXCEPT"})

    def _parse_from_clause(self) -> None:
        self._parse_table_factor()
        while True:
            if self.current().kind == "SYMBOL" and self.current().value == ",":
                self.advance()
                self._parse_table_factor()
                continue

            if self.current().kind == "WORD" and (self.current().upper in JOIN_MODIFIERS or self.current().upper == "JOIN"):
                while self.current().kind == "WORD" and self.current().upper in JOIN_MODIFIERS:
                    self.advance()
                self.expect_word("JOIN")
                self._parse_table_factor()
                if self.match_word("ON"):
                    self.advance()
                    self._parse_expr(
                        stop_words=CLAUSE_STOP_KEYWORDS
                    )
                elif self.match_word("USING"):
                    self.advance()
                    self._parse_paren_group()
                continue
            break

    def _parse_table_factor(self) -> None:
        tok = self.current()
        if tok.kind == "SYMBOL" and tok.value == "(":
            self.advance()
            inner = self.current()
            if (inner.kind == "WORD" and inner.upper in ("SELECT", "WITH")) or (inner.kind == "SYMBOL" and inner.value == "("):
                self.parse_query(is_top_level=False)
            else:
                self._parse_from_clause()
            if not (self.current().kind == "SYMBOL" and self.current().value == ")"):
                raise SQLValidationError("Malformed SQL: expected ')' in FROM subquery.")
            self.advance()
            self._consume_optional_alias()
            return

        if tok.kind not in ("WORD", "QUOTED_IDENT"):
            raise SQLValidationError(f"Malformed FROM clause near '{tok.raw}'.")

        first_ident = tok.value
        self.advance()

        # Block schema-qualified table references such as main.sqlite_master or temp.orders
        if self.current().kind == "SYMBOL" and self.current().value == ".":
            self.advance()
            second_tok = self.current()
            second_name = second_tok.value if second_tok.kind in ("WORD", "QUOTED_IDENT") else second_tok.raw
            raise SQLValidationError(
                f"Security Alert: Schema-qualified table '{first_ident}.{second_name}' is not permitted; table is not in the approved database schema whitelist."
            )

        # Block table-valued functions in FROM clause such as pragma_table_info('orders')
        if self.current().kind == "SYMBOL" and self.current().value == "(":
            raise SQLValidationError(
                f"Security Alert: Table-valued function '{first_ident}()' in FROM clause is not in the approved database schema whitelist."
            )

        low = first_ident.lower()
        if _is_forbidden_system_identifier(low):
            raise SQLValidationError(
                f"Security Alert: Table '{first_ident}' is not in the approved database schema whitelist (system metadata access prohibited)."
            )
        if low not in self.allowed_tables and not self.is_active_cte(low):
            raise SQLValidationError(
                f"Security Alert: Table '{first_ident}' is not in the approved database schema whitelist."
            )

        self._consume_optional_alias()

    def _consume_optional_alias(self) -> None:
        if self.match_word("AS"):
            self.advance()
            if self.current().kind not in ("WORD", "QUOTED_IDENT"):
                raise SQLValidationError("Malformed SQL: expected alias identifier after AS.")
            self.advance()
            return

        tok = self.current()
        if tok.kind == "WORD" and tok.upper not in CLAUSE_STOP_KEYWORDS:
            self.advance()
        elif tok.kind == "QUOTED_IDENT":
            self.advance()

    def _parse_order_by_list(self) -> None:
        while True:
            self._parse_expr(stop_words={"ASC", "DESC", "NULLS", "LIMIT", "OFFSET", "UNION", "INTERSECT", "EXCEPT"})
            if self.match_word("ASC") or self.match_word("DESC"):
                self.advance()
            if self.match_word("NULLS"):
                self.advance()
                if self.match_word("FIRST") or self.match_word("LAST"):
                    self.advance()
            if self.current().kind == "SYMBOL" and self.current().value == ",":
                self.advance()
                continue
            break

    def _parse_expr_list_until(self, stop_words: Set[str], allow_empty: bool = True) -> None:
        if not allow_empty and (
            self.current().kind == "EOF"
            or (self.current().kind == "WORD" and self.current().upper in stop_words)
            or (self.current().kind == "SYMBOL" and self.current().value in (")", ";"))
        ):
            raise SQLValidationError("Malformed SQL: unexpected empty expression list.")

        while True:
            self._parse_expr(stop_words=stop_words)
            if self.current().kind == "SYMBOL" and self.current().value == ",":
                self.advance()
                continue
            break

    def _parse_expr(self, stop_words: Set[str]) -> None:
        consumed = 0
        while True:
            tok = self.current()
            if tok.kind == "EOF":
                break
            if tok.kind == "SYMBOL" and tok.value in (",", ")", ";"):
                break
            if tok.kind == "WORD" and tok.upper in stop_words:
                break

            # Subquery or parenthesized expression
            if tok.kind == "SYMBOL" and tok.value == "(":
                self._parse_paren_group()
                consumed += 1
                continue

            # Function call: ident( ... ) or schema.func( ... )
            if tok.kind in ("WORD", "QUOTED_IDENT") and self.peek().kind == "SYMBOL" and self.peek().value == "(":
                fn_name = tok.value.lower()
                # Check if CASE or CAST or EXISTS special forms
                self._validate_function_name(fn_name, tok.value)
                self.advance()  # fn_name
                self._parse_paren_group(allow_type_cast=(fn_name == "cast"))
                consumed += 1
                continue

            # Dotted expression like table.col or table.* or schema.func()
            if tok.kind in ("WORD", "QUOTED_IDENT") and self.peek().kind == "SYMBOL" and self.peek().value == ".":
                prefix = tok.value.lower()
                if _is_forbidden_system_identifier(prefix):
                    raise SQLValidationError(
                        f"Security Alert: Reference to system identifier '{tok.value}' is not in the approved database schema whitelist."
                    )
                self.advance()  # prefix
                self.advance()  # .
                member = self.current()
                if member.kind in ("WORD", "QUOTED_IDENT") and self.peek().kind == "SYMBOL" and self.peek().value == "(":
                    raise SQLValidationError(
                        f"Security Alert: Schema-qualified function '{tok.value}.{member.value}()' is not permitted."
                    )
                if member.kind in ("WORD", "QUOTED_IDENT") and _is_forbidden_system_identifier(member.value):
                    raise SQLValidationError(
                        f"Security Alert: Reference to system identifier '{member.value}' is prohibited."
                    )
                if member.kind == "SYMBOL" and member.value == "*":
                    self.advance()
                elif member.kind in ("WORD", "QUOTED_IDENT"):
                    self.advance()
                else:
                    raise SQLValidationError(f"Malformed identifier reference after '{tok.value}.'.")
                consumed += 1
                continue

            if tok.kind in ("WORD", "QUOTED_IDENT") and _is_forbidden_system_identifier(tok.value):
                raise SQLValidationError(
                    f"Security Alert: Identifier '{tok.value}' references restricted system metadata and is not in the approved database schema whitelist."
                )

            self.advance()
            consumed += 1

        if consumed == 0:
            raise SQLValidationError(f"Malformed SQL: expected expression near '{self.current().raw or 'EOF'}'.")

    def _validate_function_name(self, fn_low: str, fn_raw: str) -> None:
        # 'OVER' can precede '(' for window functions, handled safely since it's not a SQL function call here
        if fn_low in DANGEROUS_FUNCTIONS or _is_forbidden_system_identifier(fn_low):
            raise SQLValidationError(
                f"Security Alert: Dangerous or restricted function '{fn_raw}()' is prohibited."
            )
        if fn_low in ("cast", "exists", "over", "filter"):
            return
        if fn_low not in SAFE_FUNCTIONS:
            raise SQLValidationError(
                f"Security Alert: Function '{fn_raw}()' is not permitted in read-only analytical queries."
            )

    def _parse_paren_group(self, allow_type_cast: bool = False) -> None:
        self._enter_depth()
        try:
            self.advance()  # consume '('
            inner = self.current()
            if (inner.kind == "WORD" and inner.upper in ("SELECT", "WITH")) or (inner.kind == "SYMBOL" and inner.value == "("):
                # Could be subquery or nested expr starting with '('
                # Try subquery when SELECT or WITH directly, or nested paren expression
                if inner.kind == "WORD" and inner.upper in ("SELECT", "WITH"):
                    self.parse_query(is_top_level=False)
                else:
                    self._parse_expr_list_until(stop_words=set(), allow_empty=True)
            else:
                if not (inner.kind == "SYMBOL" and inner.value == ")"):
                    stop = {"AS"} if allow_type_cast else set()
                    while True:
                        self._parse_expr(stop_words=stop)
                        if allow_type_cast and self.match_word("AS"):
                            self.advance()
                            if self.current().kind != "WORD":
                                raise SQLValidationError("Malformed CAST: expected type name.")
                            self.advance()
                            if self.current().kind == "SYMBOL" and self.current().value == "(":
                                self.advance()
                                if self.current().kind != "NUMBER":
                                    raise SQLValidationError("Malformed CAST: expected numeric precision.")
                                self.advance()
                                if self.current().kind == "SYMBOL" and self.current().value == ",":
                                    self.advance()
                                    if self.current().kind != "NUMBER":
                                        raise SQLValidationError("Malformed CAST: expected numeric scale.")
                                    self.advance()
                                if not (self.current().kind == "SYMBOL" and self.current().value == ")"):
                                    raise SQLValidationError("Malformed CAST: expected ')'.")
                                self.advance()
                            break
                        if self.current().kind == "SYMBOL" and self.current().value == ",":
                            self.advance()
                            continue
                        break

            if not (self.current().kind == "SYMBOL" and self.current().value == ")"):
                raise SQLValidationError("Malformed SQL: unclosed '(' in expression.")
            self.advance()  # consume ')'
        finally:
            self._exit_depth()


def _strip_comments_and_trailing_semicolon(sql: str) -> str:
    """Removes SQL comments outside quotes/strings and strips trailing semicolons."""
    out: List[str] = []
    n = len(sql)
    i = 0
    while i < n:
        ch = sql[i]
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            i += 2
            while i < n and sql[i] != "\n":
                i += 1
            out.append(" ")
            continue
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":
            end = sql.find("*/", i + 2)
            if end == -1:
                break
            i = end + 2
            out.append(" ")
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            start = i
            i += 1
            while i < n:
                if sql[i] == quote:
                    if i + 1 < n and sql[i + 1] == quote:
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            out.append(sql[start:i])
            continue
        if ch == "[":
            end = sql.find("]", i + 1)
            if end == -1:
                out.append(sql[i:])
                break
            out.append(sql[i : end + 1])
            i = end + 1
            continue
        out.append(ch)
        i += 1
    collapsed = re.sub(r"\s+", " ", "".join(out)).strip()
    return collapsed.rstrip(";").strip()


def validate_sql_ast(
    sql: str,
    allowed_tables: Optional[Set[str]] = None,
    max_row_limit: int = MAX_ROW_LIMIT,
    default_row_limit: int = DEFAULT_ROW_LIMIT,
) -> Tuple[bool, str, str]:
    """
    Validates SQL via lexer + recursive-descent AST traversal.
    Returns (is_valid, sanitized_sql, message).
    """
    if not sql or not sql.strip():
        return False, "", "Empty SQL query."

    tables = allowed_tables if allowed_tables is not None else ALLOWED_TABLES

    try:
        tokens = tokenize_sql(sql)
        validator = _SQLASTValidator(tokens=tokens, allowed_tables=tables, max_row_limit=max_row_limit)
        validator.validate()
    except SQLValidationError as exc:
        return False, "", str(exc)

    clean_sql = _strip_comments_and_trailing_semicolon(sql)
    if not clean_sql:
        return False, "", "Empty SQL query."

    if validator.top_level_has_limit:
        sanitized_sql = f"{clean_sql};"
    else:
        sanitized_sql = f"{clean_sql} LIMIT {default_row_limit};"

    return True, sanitized_sql, "Safe read-only SELECT validated against schema whitelist."
