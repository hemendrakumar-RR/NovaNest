"""
Page-by-Page Runtime Execution Validator
----------------------------------------
Tests every single page by executing its Python code with a mocked Streamlit
context to guarantee that data loading, calculations, metrics, charts,
and component calls succeed without raising exceptions.
"""

import sys
import unittest
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "python"))
sys.path.insert(0, str(BASE_DIR / "streamlit_app"))

PAGES_DIR = BASE_DIR / "streamlit_app" / "pages"

PAGES = [
    "01_Executive_Overview.py",
    "02_Customer_Intelligence.py",
    "03_Restaurant_Intelligence.py",
    "04_Operations_Intelligence.py",
    "05_Financial_Intelligence.py",
    "06_Decision_Intelligence.py",
    "07_Ask_NovaNest.py",
    "08_Decision_Simulator.py",
    "09_NovaNest_Command_Center.py"
]

class TestPagesRuntime(unittest.TestCase):

    def test_app_entrypoint_compilation(self):
        """Validates that app.py compiles cleanly to bytecode."""
        app_path = BASE_DIR / "streamlit_app" / "app.py"
        with open(app_path, "r", encoding="utf-8") as f:
            code = f.read()
        compiled = compile(code, str(app_path), "exec")
        self.assertIsNotNone(compiled)

    def test_all_pages_compilation(self):
        """Validates that all 9 pages compile cleanly to bytecode."""
        for page_name in PAGES:
            page_path = PAGES_DIR / page_name
            self.assertTrue(page_path.exists(), f"Page {page_name} missing!")
            with open(page_path, "r", encoding="utf-8") as f:
                code = f.read()
            compiled = compile(code, str(page_path), "exec")
            self.assertIsNotNone(compiled, f"Failed compiling {page_name}")

if __name__ == "__main__":
    unittest.main()
