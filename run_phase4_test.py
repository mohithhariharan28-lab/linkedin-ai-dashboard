import asyncio
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from src.auth.login import LinkedInAuthenticator
from src.database.db_manager import DatabaseManager
from src.database.models import ExecutionLogRecord
from src.scraper.profile_service import LinkedInProfileScraperService
from src.scraper.post_scraper import LinkedInPostScraperService
from src.analytics.post_analytics import PostAnalyticsService
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("run_phase4_test")

async def main() -> None:
    """Executes Phase 4 testing: Scrapes profile, posts, stores in SQLite, computes analytics, and prints results."""
    start_time = time.time()
    execution_time = datetime.utcnow().isoformat()
    
    db_manager = None
    status = "SUCCESS"
    posts_found = 0
    posts_stored = 0
    
    try:
        db_manager = DatabaseManager()
        
        # 1. Verify/perform login
        authenticator = LinkedInAuthenticator()
        session_valid = await authenticator.verify_session()
        if not session_valid:
            logger.warning("Session is invalid or expired. Running headed login prompt...")
            auth_success = await authenticator.authenticate()
            if not auth_success:
                print("Verification Failed: Authentication failed.")
                sys.exit(1)
        
        # 2. Run Profile Scraper Service
        profile_scraper = LinkedInProfileScraperService(headless=True)
        profile_snapshot = await profile_scraper.scrape_profile()
        db_manager.repository.save_profile_snapshot(profile_snapshot)
        
        # 3. Run Post Scraper Service (using the discovered profile URL)
        post_scraper = LinkedInPostScraperService(headless=True)
        scraped_posts = await post_scraper.scrape_posts(profile_snapshot.profile_url)
        posts_found = len(scraped_posts)
        
        # 4. Store posts
        for post in scraped_posts:
            db_manager.repository.save_post_snapshot(post)
            posts_stored += 1
            
        # 5. Run Analytics Service to verify calculations
        analytics_service = PostAnalyticsService(db_manager.repository)
        metrics = analytics_service.calculate_metrics()
        
        logger.info("Test execution completed successfully.")
        
        # Print metrics summary in logs
        logger.info(f"Calculated Metrics: {metrics}")
        
    except Exception as e:
        status = "FAILED"
        logger.error(f"Error during Phase 4 test run: {e}", exc_info=True)
        print(f"Verification Failed: {e}")
        sys.exit(1)
        
    finally:
        # Calculate duration
        duration = time.time() - start_time
        
        # Log run stats to execution_log
        if db_manager:
            try:
                log_record = ExecutionLogRecord(
                    execution_time=execution_time,
                    module="run_phase4_test",
                    status=status,
                    duration=duration
                )
                db_manager.repository.save_execution_log(log_record)
            except Exception as log_error:
                logger.error(f"Failed to save execution log: {log_error}")

        if status == "SUCCESS":
            # Print exact output formatting as requested
            print(f"Posts Found: {posts_found}")
            print(f"Posts Stored: {posts_stored}")
            print("Database Updated Successfully")
            
            # Print metrics block for testing visibility
            print("\n" + "="*50)
            print("POST ANALYTICS SUMMARY")
            print("="*50)
            print(f"Followers: {metrics['followers']}")
            print(f"Follower Growth: {metrics['growth_rate_pct']:.2f}%")
            print(f"Total Posts Scraped: {metrics['total_posts']}")
            print(f"Avg Likes/Day: {metrics['avg_likes_per_day']:.2f}")
            print(f"Avg Comments/Day: {metrics['avg_comments_per_day']:.2f}")
            print(f"Avg Engagement Rate: {metrics['avg_engagement_rate']:.2f}%")
            print(f"Posting Frequency: {metrics['posting_frequency_per_week']:.2f} posts/week")
            print(f"Avg Days Between Posts: {metrics['avg_days_between_posts']:.2f} days")
            print(f"Best Post ID: {metrics['best_post_id']} (ER: {metrics['best_post_engagement']:.2f}%)")
            print(f"Worst Post ID: {metrics['worst_post_id']} (ER: {metrics['worst_post_engagement']:.2f}%)")
            print("="*50 + "\n")
            
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
