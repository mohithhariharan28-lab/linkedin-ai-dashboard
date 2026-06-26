import asyncio
import os
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
from src.analytics.powerbi_pipeline import PowerBiPipelineService
from src.ai.report_generator import AIReportGenerator
from src.utils.notifications import NotificationGenerator
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger (writes to logs/application.log and console)
logger = setup_logger("main")

async def main() -> None:
    """Main execution flow integrating scraping, analytics calculations, and CSV exports."""
    start_time = time.time()
    execution_time = datetime.utcnow().isoformat()
    logger.info("Initializing LinkedIn AI Analytics Pipeline...")
    
    db_manager = None
    status = "SUCCESS"
    posts_found = 0
    posts_stored = 0
    
    try:
        # Initialize Database Manager (creates views if they don't exist)
        db_manager = DatabaseManager()
        
        # Verify Session
        authenticator = LinkedInAuthenticator()
        session_valid = await authenticator.verify_session()
        
        if not session_valid:
            logger.warning("Session is invalid or expired. Running login prompt...")
            auth_success = await authenticator.authenticate()
            if not auth_success:
                logger.error("Authentication failed. Aborting pipeline.")
                status = "FAILED"
                sys.exit(1)
        
        # 1. Run Profile Scraper Service
        profile_scraper = LinkedInProfileScraperService(headless=True)
        profile_snapshot = await profile_scraper.scrape_profile()
        
        # Save profile snapshot to SQLite (automatically updates follower_history)
        db_manager.repository.save_profile_snapshot(profile_snapshot)
        
        # 2. Run Post Scraper Service (using the discovered profile URL)
        post_scraper = LinkedInPostScraperService(headless=True)
        scraped_posts = await post_scraper.scrape_posts(profile_snapshot.profile_url)
        posts_found = len(scraped_posts)
        
        # 3. Store posts to SQLite (automatically appends metrics snapshots to history)
        for post in scraped_posts:
            db_manager.repository.save_post_snapshot(post)
            posts_stored += 1
            
        logger.info(f"Scraped profile '{profile_snapshot.full_name}' and saved {posts_stored} posts.")
        
        # 3b. Automatically retrieve LinkedIn connections data
        logger.info("Automatically retrieving LinkedIn connections...")
        from src.scraper.connections_service import LinkedInConnectionsService
        connections_service = LinkedInConnectionsService(db_manager.repository)
        inserted, skipped, source = await connections_service.execute_connections_import()
        logger.info(f"LinkedIn Connections: Sync complete ({inserted} imported, {skipped} skipped/updated via {source}).")
        
        # 4. Run Analytics Engine and save calculations
        logger.info("Triggering Analytics Engine calculation...")
        analytics_service = PostAnalyticsService(db_manager.repository)
        metrics = analytics_service.calculate_metrics()
        
        # Save summary, monthly stats, and post rankings
        db_manager.repository.save_analytics_summary(metrics["summary"])
        db_manager.repository.save_monthly_statistics(metrics["monthly_statistics"])
        db_manager.repository.save_post_rankings(metrics["post_rankings"])
        
        # 5. Run Power BI CSV exports
        logger.info("Triggering Power BI data pipeline CSV export...")
        powerbi_service = PowerBiPipelineService(db_manager)
        powerbi_service.run_export()
        
        # 6. Run AI Insights monthly report generation
        logger.info("Triggering AI Insights monthly report generation...")
        report_generator = AIReportGenerator(db_manager.repository)
        report_generator.generate_monthly_report()
        
        # 7. Generate Daily & Monthly summaries
        logger.info("Triggering Daily & Monthly summaries generation...")
        notif_generator = NotificationGenerator(db_manager.repository)
        notif_generator.generate_summaries()
        
        logger.info("Database transaction, CSV exports, AI report, and summaries complete.")
        
    except Exception as e:
        status = "FAILED"
        logger.error(f"Error encountered during main pipeline run: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        # Calculate duration
        duration = time.time() - start_time
        logger.info(f"Pipeline execution finished in {duration:.2f}s with status: {status}")
        
        # Log run stats to execution_log
        if db_manager:
            try:
                log_record = ExecutionLogRecord(
                    execution_time=execution_time,
                    module="analytics_pipeline",
                    status=status,
                    duration=duration
                )
                db_manager.repository.save_execution_log(log_record)
            except Exception as log_error:
                logger.error(f"Failed to save execution log: {log_error}")

        if status == "SUCCESS":
            print(f"Posts Found: {posts_found}")
            print(f"Posts Stored: {posts_stored}")
            print("Database Updated Successfully")
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    asyncio.run(main())
