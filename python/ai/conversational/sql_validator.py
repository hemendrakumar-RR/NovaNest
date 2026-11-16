"""
Phase 5 — SQL Validator
-----------------------
Provides safety checks delegating to NovaNest AST SQL validator so all query paths
share identical read-only, schema-whitelist, and injection protections.
"""

from __future__ import annotations

from python.ai.analyst.sql_ast import validate_sql_ast


def validate_sql(sql_query: str) -> bool:
    """
    Validates that a SQL query is strictly a safe single read-only SELECT/CTE
    against the approved NovaNest schema whitelist.
    """
    is_valid, _, _ = validate_sql_ast(sql_query)
    return is_valid
