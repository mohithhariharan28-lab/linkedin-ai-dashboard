import os
import sys
from pathlib import Path

# Add project root to python path to resolve src imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.ai.report_generator import AIReportGenerator

def main() -> None:
    print("=" * 60)
    print("Starting AI Insights Engine Verification...")
    print("=" * 60)

    try:
        # Initialize Database Manager
        db_manager = DatabaseManager()
        
        # Instantiate Report Generator
        generator = AIReportGenerator(db_manager.repository)
        
        # Generate the monthly report
        report_path = generator.generate_monthly_report()
        
        # Verify the report file exists
        file_path = Path(report_path)
        if not file_path.exists():
            print("[-] Verification Failed: monthly_ai_report.md was not generated.")
            sys.exit(1)
            
        # Verify size
        size_bytes = file_path.stat().st_size
        if size_bytes == 0:
            print("[-] Verification Failed: monthly_ai_report.md is empty.")
            sys.exit(1)

        print(f"\n[+] monthly_ai_report.md: EXISTS ({size_bytes} bytes)")
        
        # Read and print a snippet
        print("\nReport Preview (First 500 characters):")
        print("-" * 50)
        with open(file_path, "r", encoding="utf-8") as f:
            print(f.read(500) + "\n...")
        print("-" * 50)

        print("\n" + "=" * 60)
        print("AI Insights Engine Execution: SUCCESS")
        print("AI Monthly Report Generated Successfully")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nAI Insights Engine Execution: FAILED - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
