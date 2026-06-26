import asyncio
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from src.database.db_manager import DatabaseManager
from src.database.models import ExecutionLogRecord
from src.analytics.post_analytics import PostAnalyticsService
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("run_phase5_test")

async def run_test() -> None:
    """Executes Phase 5 testing: Loads SQLite data, computes all metrics, stores in SQLite, and logs progress."""
    start_time = time.time()
    execution_time = datetime.utcnow().isoformat()
    logger.info("Initializing Phase 5 Analytics Test execution...")
    
    db_manager = None
    status = "SUCCESS"
    
    try:
        # 1. Initialize Database Manager
        db_manager = DatabaseManager()
        
        # 2. Initialize Analytics Service
        analytics_service = PostAnalyticsService(db_manager.repository)
        
        # 3. Calculate all metrics
        logger.info("Calculating summary, monthly stats, and rankings...")
        metrics = analytics_service.calculate_metrics()
        
        # 4. Save results to the new tables in SQLite
        logger.info("Writing calculated metrics to SQLite...")
        db_manager.repository.save_analytics_summary(metrics["summary"])
        db_manager.repository.save_monthly_statistics(metrics["monthly_statistics"])
        db_manager.repository.save_post_rankings(metrics["post_rankings"])
        
        logger.info("Database transaction complete for calculated analytics metrics.")
        
    except Exception as e:
        status = "FAILED"
        logger.error(f"Error during Phase 5 test run: {e}", exc_info=True)
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
                    module="run_phase5_test",
                    status=status,
                    duration=duration
                )
                db_manager.repository.save_execution_log(log_record)
            except Exception as log_error:
                logger.error(f"Failed to save execution log: {log_error}")

        if status == "SUCCESS":
            # Print exact output formatting as requested
            print("Analytics Engine Execution: SUCCESS")
            print("Database Updated Successfully")
            
            # Print some computed items for visibility
            sum_obj = metrics["summary"]
            print("\n" + "="*50)
            print("PERSISTED ANALYTICS METRICS")
            print("="*50)
            print(f"Total Followers: {sum_obj.total_followers}")
            print(f"Follower Growth: {sum_obj.follower_growth_pct:.2f}%")
            print(f"Weekly Growth: {sum_obj.weekly_growth_pct:.2f}%")
            print(f"Monthly Growth: {sum_obj.monthly_growth_pct:.2f}%")
            print(f"Total Posts: {sum_obj.total_posts}")
            print(f"Total Likes/Comments/Reposts: {sum_obj.total_likes}L / {sum_obj.total_comments}C / {sum_obj.total_reposts}R")
            print(f"Avg Engagement Rate: {sum_obj.avg_engagement_rate:.2f}%")
            print(f"Posting Frequency: {sum_obj.posting_frequency_per_week:.2f} posts/week")
            print(f"Avg Days Between Posts: {sum_obj.avg_days_between_posts:.2f} days")
            print(f"Monthly statistics records count: {len(metrics['monthly_statistics'])}")
            print(f"Post rankings records count: {len(metrics['post_rankings'])}")
            print("="*50 + "\n")
            
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_test())
