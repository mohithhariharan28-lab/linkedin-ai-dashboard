import os
import sys
import py_compile
from pathlib import Path

# Add project root to python path to resolve src imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def main() -> None:
    print("=" * 60)
    print("Starting Streamlit Dashboard Verification (Phase 11)...")
    print("=" * 60)

    try:
        # 1. Verify Imports
        print("[+] Verifying module imports...")
        import streamlit as st
        import plotly as py
        import pandas as pd
        import sqlite3
        print("[+] All dependencies successfully resolved (streamlit, plotly, pandas, sqlite3).")

        # 2. Check Database Connection
        db_path = project_root / "data" / "linkedin.db"
        if not db_path.exists():
            print(f"[-] Database file not found at {db_path}.")
            sys.exit(1)
            
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        conn.close()
        print(f"[+] Database connected. Tables found: {', '.join(tables)}")

        # 3. Compile App Script (Syntax validation)
        app_script = project_root / "src" / "dashboard" / "app.py"
        print(f"[+] Running syntax validation on {app_script}...")
        py_compile.compile(str(app_script), doraise=True)
        print("[+] Syntax validation: PASSED.")

        print("\n" + "=" * 60)
        print("Streamlit Dashboard Modules Check: SUCCESS")
        print("Dashboard Ready for Local Server Run")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nStreamlit Dashboard Verification: FAILED - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
