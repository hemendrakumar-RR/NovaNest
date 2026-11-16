"""
NovaNest Universal Knowledge, Math & Code Engine
------------------------------------------------
Provides accurate deterministic computations, step-by-step mathematical reasoning,
clean code generation, and conceptual explanations across programming, mathematics,
machine learning, and project architecture.
"""

import re
from typing import Dict, Any, Optional


def compute_calculation(query: str) -> Optional[Dict[str, Any]]:
    """
    Parses and solves numerical, financial, and statistical calculations with exact precision.
    """
    q = query.lower()

    # Case A: Compound Interest
    # e.g., "Calculate compound interest on 2000 at 20% for 2 years"
    ci_match = re.search(r"compound\s+interest\s+(?:on\s+)?(?:₹|\$)?(\d+(?:\.\d+)?)\s+(?:at\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:for\s+)?(\d+(?:\.\d+)?)\s*(?:years|year|yr|yrs)?", q)
    if ci_match:
        principal = float(ci_match.group(1))
        rate_pct = float(ci_match.group(2))
        rate_dec = rate_pct / 100.0
        time_yrs = float(ci_match.group(3))

        amount = principal * ((1.0 + rate_dec) ** time_yrs)
        interest = amount - principal

        explanation = (
            f"### Compound Interest Calculation\n\n"
            f"**Formula:**\n"
            f"$$\\text{{Total Amount }} (A) = P \\left(1 + \\frac{{r}}{{n}}\\right)^{{nt}}$$\n"
            f"Where $A = P(1 + r)^t$ for annual compounding ($n = 1$).\n"
            f"$$\\text{{Compound Interest }} (CI) = A - P$$\n\n"
            f"**Given Parameters:**\n"
            f"- **Principal ($P$):** ₹{principal:,.2f}\n"
            f"- **Annual Interest Rate ($r$):** {rate_pct}% ({rate_dec})\n"
            f"- **Time Period ($t$):** {time_yrs:g} years (compounded annually, $n = 1$)\n\n"
            f"**Step-by-Step Calculation:**\n"
            f"1. Growth factor: $(1 + {rate_dec})^{{{time_yrs:g}}} = {((1 + rate_dec) ** time_yrs):.4f}$\n"
            f"2. Final Amount ($A$): ₹{principal:,.2f} $\\times$ {((1 + rate_dec) ** time_yrs):.4f} = **₹{amount:,.2f}**\n"
            f"3. Compound Interest ($CI$): ₹{amount:,.2f} - ₹{principal:,.2f} = **₹{interest:,.2f}**\n\n"
            f"| Metric | Value |\n"
            f"| :--- | :--- |\n"
            f"| **Principal Invested** | ₹{principal:,.2f} |\n"
            f"| **Interest Earned** | **₹{interest:,.2f}** |\n"
            f"| **Maturity / Total Value** | **₹{amount:,.2f}** |"
        )
        return {
            "result": round(interest, 2),
            "amount": round(amount, 2),
            "principal": principal,
            "explanation": explanation
        }

    # Case B: Simple Interest
    si_match = re.search(r"simple\s+interest\s+(?:on\s+)?(?:₹|\$)?(\d+(?:\.\d+)?)\s+(?:at\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:for\s+)?(\d+(?:\.\d+)?)\s*(?:years|year|yr|yrs)?", q)
    if si_match:
        p = float(si_match.group(1))
        r = float(si_match.group(2))
        t = float(si_match.group(3))
        si = (p * r * t) / 100.0
        tot = p + si
        explanation = (
            f"### Simple Interest Calculation\n\n"
            f"**Formula:** $SI = \\frac{{P \\times R \\times T}}{{100}}$\n\n"
            f"- **Principal ($P$):** ₹{p:,.2f}\n"
            f"- **Rate ($R$):** {r}%\n"
            f"- **Time ($T$):** {t:g} years\n\n"
            f"**Calculation:**\n"
            f"$$SI = \\frac{{{p:,.2f} \\times {r} \\times {t}}}{{100}} = \\mathbf{{₹{si:,.2f}}}$$\n"
            f"**Total Amount:** ₹{p:,.2f} + ₹{si:,.2f} = **₹{tot:,.2f}**"
        )
        return {"result": round(si, 2), "amount": round(tot, 2), "explanation": explanation}

    # Case C: Percentage computation (e.g., "What is 15% of 8500")
    pct_match = re.search(r"(?:what\s+is\s+)?(\d+(?:\.\d+)?)\s*%\s+of\s+(?:₹|\$)?(\d+(?:\.\d+)?)", q)
    if pct_match:
        pct = float(pct_match.group(1))
        val = float(pct_match.group(2))
        res = (pct / 100.0) * val
        explanation = (
            f"### Percentage Calculation\n\n"
            f"$$\\frac{{{pct}}}{{100}} \\times {val:,.2f} = \\mathbf{{{res:,.2f}}}$$\n\n"
            f"**Result:** **{pct}%** of **{val:,.2f}** is **{res:,.2f}**."
        )
        return {"result": round(res, 2), "explanation": explanation}

    return None


def get_offline_knowledge_response(query: str, intent: str) -> Dict[str, Any]:
    """
    Supplies comprehensive, high-quality responses for common technical, conceptual,
    programming, and architectural questions when running offline / unconfigured.
    """
    q_lower = query.lower()

    # 1. GREETING & INTRODUCTION
    if intent == "GREETING":
        return {
            "answer": (
                "👋 **Hello! I am NovaNest AI — your Universal Intelligent Assistant & Senior Business Analyst.**\n\n"
                "I combine deep conversational capabilities across software engineering, mathematics, data science, and general knowledge with enterprise-grade **Food Delivery Decision Intelligence**.\n\n"
                "### What I can help you with:\n"
                "1. **General Knowledge & Concepts:** Machine learning, cosine similarity, statistics, database design, system architecture.\n"
                "2. **Programming & Debugging:** Writing Python, SQL, TypeScript, Java code, debugging errors, and code optimization.\n"
                "3. **Mathematics & Financial Modeling:** Step-by-step interest calculations, percentages, statistical formulas.\n"
                "4. **NovaNest Decision Intelligence:** Real platform KPIs, safe SQL queries, root-cause investigations, and what-if Decision Simulations.\n\n"
                "How can I assist you today?"
            ),
            "suggestions": [
                "Explain machine learning in simple words",
                "What is the difference between SQL and NoSQL?",
                "Write a Python program to calculate the average of a list",
                "What is our total revenue?",
                "Calculate compound interest on 2000 at 20% for 2 years"
            ]
        }

    # 2. PYTHON PROGRAM: AVERAGE OF A LIST
    if "average" in q_lower and ("list" in q_lower or "array" in q_lower or "python" in q_lower):
        return {
            "answer": (
                "### Python Program to Calculate the Average of a List\n\n"
                "Here is an efficient, production-grade Python script that calculates the average of a list using multiple approaches, complete with error handling for empty lists.\n\n"
                "```python\n"
                "# Method 1: Using Built-in sum() and len()\n"
                "def calculate_average(numbers: list[float]) -> float:\n"
                "    \"\"\"\n"
                "    Computes the arithmetic mean of a list of numbers.\n"
                "    Raises ValueError if the input list is empty.\n"
                "    \"\"\"\n"
                "    if not numbers:\n"
                "        raise ValueError(\"Cannot calculate average of an empty list\")\n"
                "    return sum(numbers) / len(numbers)\n\n\n"
                "# Method 2: Using the Python Standard Library 'statistics'\n"
                "import statistics\n\n"
                "def calculate_average_statistics(numbers: list[float]) -> float:\n"
                "    return statistics.mean(numbers)\n\n\n"
                "# --- Demonstration & Test Cases ---\n"
                "if __name__ == '__main__':\n"
                "    sample_data = [12.5, 45.0, 78.2, 90.1, 33.4]\n"
                "    avg = calculate_average(sample_data)\n"
                "    print(f\"Numbers: {sample_data}\")\n"
                "    print(f\"Average: {avg:.2f}\")  # Output: 51.84\n\n"
                "    # Empty list edge case handling\n"
                "    try:\n"
                "        calculate_average([])\n"
                "    except ValueError as e:\n"
                "        print(f\"Handled Edge Case: {e}\")\n"
                "```\n\n"
                "### Complexity Analysis:\n"
                "- **Time Complexity:** $\\mathcal{O}(n)$, where $n$ is the number of elements in the list.\n"
                "- **Space Complexity:** $\\mathcal{O}(1)$ auxiliary memory."
            ),
            "suggestions": [
                "How do I calculate median and mode in Python?",
                "Write Python code to find duplicates in a list",
                "Explain time complexity of sorting algorithms"
            ]
        }

    # 3. SQL vs NoSQL
    if "sql" in q_lower and "nosql" in q_lower:
        return {
            "answer": (
                "### Difference Between SQL and NoSQL Databases\n\n"
                "SQL (Relational) and NoSQL (Non-Relational) databases differ fundamentally in their data modeling, storage architecture, scaling mechanisms, and transaction guarantees.\n\n"
                "| Feature | SQL (Relational) | NoSQL (Non-Relational) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Data Structure** | Tabular (Rows & Columns with strict schema) | Flexible (Document JSON, Key-Value, Columnar, Graph) |\n"
                "| **Schema** | Static, predefined schema (DDL required) | Dynamic / Schema-on-read |\n"
                "| **Scaling** | **Vertical scaling** (Scale-up via CPU/RAM) | **Horizontal scaling** (Scale-out via clustering & sharding) |\n"
                "| **ACID vs BASE** | Strict **ACID** (Atomicity, Consistency, Isolation, Durability) | **BASE** (Basically Available, Soft state, Eventual consistency) |\n"
                "| **Query Language** | Structured Query Language (SQL) | Database-specific APIs, BSON/JSON, Cypher, CQL |\n"
                "| **Join Operations** | Native, highly optimized multi-table `JOIN`s | Denormalized data models; joins avoided or emulated in application |\n"
                "| **Popular Examples** | MySQL, PostgreSQL, Oracle, SQL Server, SQLite | MongoDB, Cassandra, DynamoDB, Redis, Neo4j |\n\n"
                "### When to Choose Which?\n"
                "- **Choose SQL when:** You have structured data requiring transactional integrity (e.g., banking transactions, e-commerce order management, NovaNest analytics).\n"
                "- **Choose NoSQL when:** You deal with unstructured/semi-structured data, high-velocity ingestion (e.g., IoT clickstream events), or massive distributed scale requiring horizontal sharding."
            ),
            "suggestions": [
                "Explain database indexing and B-Trees",
                "What is the CAP theorem in distributed systems?",
                "How does MongoDB handle horizontal sharding?"
            ]
        }

    # 4. COSINE SIMILARITY
    if "cosine" in q_lower and "similarity" in q_lower:
        return {
            "answer": (
                "### Cosine Similarity: Concept, Formula, and Practical Example\n\n"
                "**Cosine Similarity** is a metric that measures the cosine of the angle between two non-zero vectors in an inner product space. It evaluates whether two vectors are pointing in roughly the same direction, regardless of their magnitude.\n\n"
                "### Mathematical Formula\n"
                "$$\\text{Cosine Similarity}(\\mathbf{A}, \\mathbf{B}) = \\cos(\\theta) = \\frac{\\mathbf{A} \\cdot \\mathbf{B}}{\\|\\mathbf{A}\\| \\|\\mathbf{B}\\|} = \\frac{\\sum_{i=1}^{n} A_i B_i}{\\sqrt{\\sum_{i=1}^{n} A_i^2} \\sqrt{\\sum_{i=1}^{n} B_i^2}}$$\n\n"
                "### Range of Values:\n"
                "- **$+1$:** Vectors point in the exact same direction (identical direction/high similarity).\n"
                "- **$0$:** Vectors are orthogonal ($90^\\circ$ angle, completely unrelated).\n"
                "- **$-1$:** Vectors point in diametrically opposite directions.\n\n"
                "### Concrete Example:\n"
                "Suppose we compare two customer preference profiles across two features: `[Burgers, Pizzas]`:\n"
                "- **Customer A:** $\\mathbf{A} = [3, 4]$\n"
                "- **Customer B:** $\\mathbf{B} = [6, 8]$\n\n"
                "**1. Dot Product:** $\\mathbf{A} \\cdot \\mathbf{B} = (3 \\times 6) + (4 \\times 8) = 18 + 32 = 50$\n"
                "**2. Magnitude of A:** $\\|\\mathbf{A}\\| = \\sqrt{3^2 + 4^2} = \\sqrt{9 + 16} = 5$\n"
                "**3. Magnitude of B:** $\\|\\mathbf{B}\\| = \\sqrt{6^2 + 8^2} = \\sqrt{36 + 64} = 10$\n"
                "**4. Cosine Similarity:** $\\frac{50}{5 \\times 10} = \\frac{50}{50} = \\mathbf{1.0}$ (Identical preference orientation!)\n\n"
                "```python\n"
                "import numpy as np\n\n"
                "def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:\n"
                "    dot_product = np.dot(a, b)\n"
                "    norm_a = np.linalg.norm(a)\n"
                "    norm_b = np.linalg.norm(b)\n"
                "    return dot_product / (norm_a * norm_b)\n"
                "```"
            ),
            "suggestions": [
                "What is the difference between Cosine Similarity and Euclidean Distance?",
                "How is cosine similarity used in recommendation systems?",
                "Explain TF-IDF text vectorization"
            ]
        }

    # 5. MACHINE LEARNING IN SIMPLE WORDS
    if "machine learning" in q_lower or "ml" in q_lower:
        return {
            "answer": (
                "### Machine Learning Explained in Simple Words\n\n"
                "Imagine teaching a child to recognize a dog. You don't give them a 10,000-rule instruction manual on fur texture, ear angles, and whisker counts. Instead, you show them **thousands of pictures of dogs** until their brain automatically recognizes the pattern.\n\n"
                "**Machine Learning (ML)** works the exact same way for computers:\n"
                "> Instead of programmers writing strict rules by hand, computers learn rules by studying historical examples and data.\n\n"
                "### The Three Main Types of Machine Learning:\n\n"
                "1. **Supervised Learning (Learning with a Teacher):**\n"
                "   - The computer is given problems along with the correct answers (labeled data).\n"
                "   - *Example:* NovaNest predicting whether a customer will churn based on past customer churn histories.\n\n"
                "2. **Unsupervised Learning (Finding Hidden Patterns):**\n"
                "   - The computer is given raw data with no labels and groups similar items together.\n"
                "   - *Example:* Customer Segmentation (grouping high-spending VIPs vs bargain hunters).\n\n"
                "3. **Reinforcement Learning (Learning by Trial and Error):**\n"
                "   - An agent takes actions in an environment to maximize a reward.\n"
                "   - *Example:* Autonomous delivery drones optimizing flight paths under wind resistance.\n\n"
                "### Traditional Programming vs Machine Learning:\n"
                "- **Traditional:** Data + Rules $\\longrightarrow$ **Answers**\n"
                "- **Machine Learning:** Data + Answers $\\longrightarrow$ **Rules (Model)**"
            ),
            "suggestions": [
                "Explain the difference between Overfitting and Underfitting",
                "What is the difference between classification and regression?",
                "How does NovaNest predict customer churn?"
            ]
        }

    # 6. NOVANEST PROJECT ARCHITECTURE
    if "novanest" in q_lower or "digital twin" in q_lower or "project" in q_lower:
        return {
            "answer": (
                "### NovaNest: System Architecture & Capabilities\n\n"
                "**NovaNest** is an enterprise-grade Decision Intelligence Platform and Digital Twin engineered for multi-sided food delivery ecosystems.\n\n"
                "### Core Platform Pillars:\n"
                "1. **Analytical Digital Twin:** Real-time systemic state monitoring (Financial, Merchant, Customer, Logistics) with cross-domain impact ripple modeling.\n"
                "2. **Decision Simulator (What-If Engine):** Deterministic multi-scenario simulator testing adjustments to take-rate commissions, delivery fees, discount subsidies, and demand elasticity.\n"
                "3. **Customer Intelligence Hub:** RFM behavioral clustering, Customer Lifetime Value (CLV) capital modeling, cohort retention matrices, and churn probability scoring.\n"
                "4. **Merchant Performance Suite:** Restaurant health scores, kitchen preparation risk detection, and peer benchmarking.\n"
                "5. **Data Engineering Layer:** Dual MySQL relational store + preprocessed CSV fallback ensuring 100% localhost availability.\n"
                "6. **Universal AI Analyst:** Data-grounded conversational intelligence with safe read-only SQL, root-cause investigations, and general technical reasoning."
            ),
            "suggestions": [
                "What happens if commission increases by 2%?",
                "What is our customer churn risk and VIP CLV capital?",
                "Why are order cancellations increasing?"
            ]
        }

    # 7. GPS & SATELLITE NAVIGATION
    if "gps" in q_lower or "global positioning" in q_lower:
        return {
            "answer": (
                "### How GPS (Global Positioning System) Works\n\n"
                "The **Global Positioning System (GPS)** is a global satellite-based radio navigation network that calculates precise 3D geographical position (latitude, longitude, altitude) and exact time anywhere on Earth.\n\n"
                "### The 3 Core Segments:\n"
                "1. **Space Segment (Satellites):** A constellation of at least 24 active satellites orbiting Earth at an altitude of approximately 20,200 km. Each satellite continuously broadcasts radio signals containing its precise orbital ephemeris and the exact timestamp from onboard atomic clocks.\n"
                "2. **Control Segment:** Ground tracking and monitor stations around the globe that calibrate satellite orbits and time synchronization.\n"
                "3. **User Segment (Receivers):** Chips in smartphones, cars, and navigation systems equipped with GPS antennas.\n\n"
                "### The Mechanism: 3D Trilateration\n"
                "- The receiver calculates distance to each satellite using: $\\text{Distance} = c \\times \\Delta t$, where $c$ is the speed of light and $\\Delta t$ is signal transit delay.\n"
                "- **3 Satellites** produce three overlapping spheres whose intersection identifies coordinates.\n"
                "- A **4th Satellite** is required to correct for receiver clock timing discrepancy, providing pinpoint accuracy down to meters."
            ),
            "suggestions": [
                "Explain cosine similarity with an example",
                "What is the difference between SQL and NoSQL?",
                "Write a Python program to calculate the average of a list"
            ]
        }

    # 8. DEFAULT GENERAL KNOWLEDGE RESPONSE
    return {
        "answer": (
            f"### Comprehensive Analysis\n\n"
            f"Here is an overview addressing your inquiry: **\"{query}\"**\n\n"
            f"To enable live web-scale generative intelligence and arbitrary open-domain brainstorming for this query, "
            f"you can configure the **Google Gemini API** (`gemini-2.5-flash`) by adding `GEMINI_API_KEY` to the `.env` file.\n\n"
            f"- **System Mode:** Localhost Grounded AI Engine\n"
            f"- **Technical Support:** Python, SQL, REST APIs, Decision Science, Machine Learning\n\n"
            f"Feel free to ask specific coding, mathematical, project architectural, or business intelligence questions!"
        ),
        "suggestions": [
            "Explain machine learning in simple words",
            "Write a Python program to calculate the average of a list",
            "What is our total revenue?",
            "What happens if delivery time decreases by 10%?"
        ]
    }
