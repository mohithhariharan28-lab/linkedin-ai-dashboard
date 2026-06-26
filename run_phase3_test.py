import asyncio
import sys
from dotenv import load_dotenv
from src.database.db_manager import DatabaseManager
from src.scraper.profile_service import LinkedInProfileScraperService
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("run_phase3_test")

async def run_test() -> None:
    try:
        # 1. Initialize DB manager
        db_manager = DatabaseManager()
        
        # 2. Initialize Scraper Service and scrape profile
        # Run headlessly for testing
        scraper = LinkedInProfileScraperService(headless=True)
        snapshot = await scraper.scrape_profile()
        
        # 3. Store in SQLite database
        db_manager.repository.save_profile_snapshot(snapshot)
        
        # 4. Print exact output formatting as requested
        print("\n" + "="*40)
        print("Profile scraped successfully.")
        print(f"Followers: {snapshot.followers if snapshot.followers is not None else 'N/A'}")
        print(f"Connections: {snapshot.connections if snapshot.connections is not None else 'N/A'}")
        print("Database updated.")
        print("="*40 + "\n")
        
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test run failed: {e}", exc_info=True)
        print(f"\nVerification Failed: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_test())
