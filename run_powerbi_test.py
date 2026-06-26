import os
import sys
from pathlib import Path
import pandas as pd

# Add the project root to python path to resolve src imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.analytics.powerbi_pipeline import PowerBiPipelineService

def main() -> None:
    print("=" * 60)
    print("Starting Power BI Data Pipeline Verification...")
    print("=" * 60)
    
    try:
        # Initialize Database Manager
        db_manager = DatabaseManager()
        
        # Initialize Power BI Pipeline Service
        powerbi_service = PowerBiPipelineService(db_manager)
        
        # Run the CSV export
        powerbi_service.run_export()
        
        # Verify the 7 CSV files in reports/
        reports_dir = project_root / "reports"
        expected_files = [
            "dashboard_overview.csv",
            "followers_growth.csv",
            "post_performance.csv",
            "monthly_activity.csv",
            "engagement_trend.csv",
            "top_posts.csv",
            "posting_frequency.csv"
        ]
        
        missing_files = []
        print("\nVerifying Exported CSV Reports:")
        for filename in expected_files:
            file_path = reports_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
                print(f"[-] {filename}: MISSING")
            else:
                size_bytes = file_path.stat().st_size
                # Load with pandas to verify structure and get row count
                df = pd.read_csv(file_path)
                row_count = len(df)
                print(f"[+] {filename}: EXISTS ({size_bytes} bytes, {row_count} rows)")
        
        if missing_files:
            print("\n[-] Verification Failed: Missing files:")
            for f in missing_files:
                print(f"  - {f}")
            sys.exit(1)
            
        print("\n" + "=" * 60)
        print("Power BI Pipeline Execution: SUCCESS")
        print("CSV Reports Refreshed Successfully")
        print("=" * 60)
        sys.exit(0)
        
    except Exception as e:
        print(f"\nPower BI Pipeline Execution: FAILED - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
