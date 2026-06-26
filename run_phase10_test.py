import os
import sys
from pathlib import Path

# Add project root to python path to resolve src imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.utils.notifications import NotificationGenerator
from src.utils.scheduler import PipelineScheduler

def main() -> None:
    print("=" * 60)
    print("Starting Production Automation Verification (Phase 10)...")
    print("=" * 60)

    try:
        # 1. Initialize Database Manager
        db_manager = DatabaseManager()
        
        # 2. Test Notification Summary Generation
        print("\n[+] Triggering summary notification exports...")
        notif_generator = NotificationGenerator(db_manager.repository)
        daily_path, monthly_path = notif_generator.generate_summaries()
        
        # Verify files
        p_daily = Path(daily_path)
        p_monthly = Path(monthly_path)
        
        if not p_daily.exists() or p_daily.stat().st_size == 0:
            print("[-] Verification Failed: daily_summary.md was not generated or is empty.")
            sys.exit(1)
            
        if not p_monthly.exists() or p_monthly.stat().st_size == 0:
            print("[-] Verification Failed: monthly_summary.md was not generated or is empty.")
            sys.exit(1)
            
        print(f"[+] daily_summary.md: EXISTS ({p_daily.stat().st_size} bytes)")
        print(f"[+] monthly_summary.md: EXISTS ({p_monthly.stat().st_size} bytes)")
        
        # 3. Test Scheduler Instantiation
        print("\n[+] Testing PipelineScheduler initialization...")
        scheduler = PipelineScheduler(interval_seconds=60)
        if scheduler.interval_seconds == 60 and not scheduler.is_running:
            print("[+] PipelineScheduler initialized successfully.")
        else:
            print("[-] Verification Failed: PipelineScheduler failed to initialize properly.")
            sys.exit(1)
            
        # Print daily summary snippet
        print("\nDaily Summary Preview (First 400 characters):")
        print("-" * 50)
        with open(p_daily, "r", encoding="utf-8") as f:
            print(f.read(400) + "\n...")
        print("-" * 50)

        print("\n" + "=" * 60)
        print("Production Automation & Deployment: SUCCESS")
        print("Daily and Monthly Summaries Refreshed Successfully")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\nProduction Automation & Deployment: FAILED - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
