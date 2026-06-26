import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to python path to resolve src imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.database.models import ConnectionRecord
from src.scraper.connections_service import LinkedInConnectionsService
from src.analytics.connections_analytics import ConnectionsAnalyticsService

def seed_mock_data(db_manager: DatabaseManager) -> None:
    """Seeds the connections table with mock records to verify analytics and views."""
    print("[+] Seeding connections table with mock data...")
    
    # Check if we already have records
    conn = sqlite3.connect(str(db_manager.db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM connections")
    cnt = cursor.fetchone()[0]
    conn.close()
    
    if cnt > 0:
        print(f"[+] Database already has {cnt} connections. Seeding skipped.")
        return

    now = datetime.utcnow()
    mock_records = [
        # Google
        ConnectionRecord(
            first_name="Alice", last_name="Smith", full_name="Alice Smith",
            profile_url="https://www.linkedin.com/in/alicesmith",
            headline="Software Engineer at Google", company="Google",
            location="San Francisco, CA", connected_date=(now - timedelta(days=5)).strftime("%Y-%m-%d"),
            import_source="csv"
        ),
        ConnectionRecord(
            first_name="Bob", last_name="Jones", full_name="Bob Jones",
            profile_url="https://www.linkedin.com/in/bobjones",
            headline="Product Manager at Google", company="Google",
            location="New York, NY", connected_date=(now - timedelta(days=12)).strftime("%Y-%m-%d"),
            import_source="csv"
        ),
        # Meta
        ConnectionRecord(
            first_name="Charlie", last_name="Brown", full_name="Charlie Brown",
            profile_url="https://www.linkedin.com/in/charliebrown",
            headline="UX Designer at Meta", company="Meta",
            location="Seattle, WA", connected_date=(now - timedelta(days=25)).strftime("%Y-%m-%d"),
            import_source="csv"
        ),
        # VaultofCodes
        ConnectionRecord(
            first_name="Mohith", last_name="Hariharan", full_name="Mohith Hariharan",
            profile_url="https://www.linkedin.com/in/mohith-hariharan-514345373",
            headline="AI Intern at VaultofCodes", company="VaultofCodes",
            location="Chennai, IN", connected_date=(now - timedelta(days=40)).strftime("%Y-%m-%d"),
            import_source="scrape"
        ),
        # Microsoft
        ConnectionRecord(
            first_name="David", last_name="Wilson", full_name="David Wilson",
            profile_url="https://www.linkedin.com/in/davidwilson",
            headline="Solutions Architect at Microsoft", company="Microsoft",
            location="Redmond, WA", connected_date=(now - timedelta(days=70)).strftime("%Y-%m-%d"),
            import_source="csv"
        ),
        ConnectionRecord(
            first_name="Emma", last_name="Davis", full_name="Emma Davis",
            profile_url="https://www.linkedin.com/in/emmadavis",
            headline="Data Analyst at Microsoft", company="Microsoft",
            location="Chicago, IL", connected_date=(now - timedelta(days=85)).strftime("%Y-%m-%d"),
            import_source="csv"
        ),
        # Self-employed/No company
        ConnectionRecord(
            first_name="Frank", last_name="Miller", full_name="Frank Miller",
            profile_url="https://www.linkedin.com/in/frankmiller",
            headline="Independent Contractor", company=None,
            location="Austin, TX", connected_date=(now - timedelta(days=110)).strftime("%Y-%m-%d"),
            import_source="csv"
        )
    ]
    
    db_manager.repository.save_connection_records(mock_records)
    print(f"[+] Successfully seeded {len(mock_records)} mock connection records.")

def verify_views(db_manager: DatabaseManager) -> None:
    """Queries SQL reporting views and prints count statistics."""
    print("\n[+] Verifying SQL Connections Views:")
    conn = sqlite3.connect(str(db_manager.db_path))
    cursor = conn.cursor()
    
    try:
        # vw_connections
        cursor.execute("SELECT COUNT(*) FROM vw_connections")
        tot = cursor.fetchone()[0]
        print(f"  - vw_connections: OK ({tot} rows)")
        
        # vw_connections_by_company
        cursor.execute("SELECT * FROM vw_connections_by_company")
        rows_comp = cursor.fetchall()
        print(f"  - vw_connections_by_company: OK ({len(rows_comp)} companies found)")
        for c in rows_comp[:3]:
            print(f"    * {c[0]}: {c[1]} connections")
            
        # vw_connections_growth
        cursor.execute("SELECT * FROM vw_connections_growth")
        rows_growth = cursor.fetchall()
        print(f"  - vw_connections_growth: OK ({len(rows_growth)} monthly segments)")
        for g in rows_growth:
            print(f"    * Month {g[0]}: {g[1]} monthly count | {g[2]} cumulative count")
            
    except Exception as e:
        print(f"[-] View Verification Error: {e}")
        raise
    finally:
        conn.close()

def main() -> None:
    print("=" * 60)
    print("Starting LinkedIn Connections Module Verification...")
    print("=" * 60)
    
    try:
        # 1. Initialize DB Manager
        db_manager = DatabaseManager()
        
        # 2. Seed Mock Data
        seed_mock_data(db_manager)
        
        # 3. Test Service Import Runner (Graceful check)
        print("\n[+] Triggering LinkedInConnectionsService import runner...")
        import_service = LinkedInConnectionsService(db_manager.repository)
        
        # Check if local CSV gets parsed or Playwright falls back
        # Since run-mode is non-interactive/headless, Playwright will gracefully log warnings if blocked
        import_task = import_service.execute_connections_import()
        # Execute coroutine in sync harness
        import asyncio
        inserted, skipped, source = asyncio.run(import_task)
        print(f"[+] Import finished. Source used: {source} (Inserted: {inserted}, Skipped: {skipped})")
        
        # 4. Test Analytics and CSV Export
        print("\n[+] Triggering connections analytics calculations...")
        analytics_service = ConnectionsAnalyticsService(db_manager.repository)
        analytics_service.run_analytics_and_export()
        
        # 5. Verify SQL Views
        verify_views(db_manager)
        
        # 6. Verify Exported CSV Files
        reports_dir = project_root / "reports"
        expected_files = [
            "connections.csv",
            "connection_summary.csv",
            "pbi_total_connections.csv",
            "pbi_connection_directory.csv",
            "pbi_company_distribution.csv",
            "pbi_monthly_connection_growth.csv"
        ]
        
        print("\n[+] Verifying Connections CSV Report Sheets:")
        missing_files = []
        for filename in expected_files:
            file_path = reports_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
                print(f"  [-] {filename}: MISSING")
            else:
                size_bytes = file_path.stat().st_size
                print(f"  [+] {filename}: EXISTS ({size_bytes} bytes)")
                
        if missing_files:
            print("\n[-] Verification Failed: Missing generated report files.")
            sys.exit(1)
            
        print("\n" + "=" * 60)
        print("LinkedIn Connections Module Check: SUCCESS")
        print("Connections Reports Refreshed Successfully")
        print("=" * 60)
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[-] LinkedIn Connections Module Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
