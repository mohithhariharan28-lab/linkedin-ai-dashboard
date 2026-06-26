import asyncio
import logging
from datetime import datetime, timedelta
import sys
import os
from src.database.db_manager import DatabaseManager
from src.database.models import ExecutionLogRecord
from src.utils.logger import setup_logger

logger = setup_logger("utils.scheduler")

class PipelineScheduler:
    """Manages periodic execution of the LinkedIn Analytics pipeline."""

    def __init__(self, interval_seconds: int = 3600) -> None:
        """Initializes the scheduler.

        Args:
            interval_seconds: Loop sleep interval (default is 1 hour).
        """
        self.interval_seconds = interval_seconds
        self.is_running = False

    async def run_pipeline_task(self) -> None:
        """Executes a single full run of the automated analytics pipeline."""
        start_time = datetime.utcnow()
        logger.info(f"Triggering automated pipeline run at {start_time.isoformat()}...")
        
        # Execute main.py main() task
        # We import here to avoid circular dependencies
        from src.main import main as run_main
        
        try:
            # Run main pipeline logic
            await run_main()
            logger.info("Automated pipeline execution completed successfully.")
        except SystemExit as se:
            if se.code == 0:
                logger.info("Automated pipeline execution completed successfully (Exit Code 0).")
            else:
                logger.error(f"Automated pipeline execution failed with exit code: {se.code}")
        except Exception as e:
            logger.error(f"Automated pipeline execution failed: {e}", exc_info=True)

    async def start_loop(self) -> None:
        """Starts the persistent background scheduler loop."""
        self.is_running = True
        logger.info(f"Background Pipeline Scheduler STARTED (Polling interval: {self.interval_seconds}s).")
        
        # Calculate initial run alignments
        last_daily_run = datetime.utcnow() - timedelta(days=1)
        last_weekly_run = datetime.utcnow() - timedelta(days=7)
        last_monthly_run = datetime.utcnow() - timedelta(days=30)
        
        while self.is_running:
            now = datetime.utcnow()
            
            # Check Daily (once every 24 hours)
            if now - last_daily_run >= timedelta(days=1):
                logger.info("Daily schedule trigger hit.")
                await self.run_pipeline_task()
                last_daily_run = now
                
            # Check Weekly (once every 7 days)
            elif now - last_weekly_run >= timedelta(days=7):
                logger.info("Weekly schedule trigger hit.")
                await self.run_pipeline_task()
                last_weekly_run = now
                
            # Check Monthly (once every 30 days)
            elif now - last_monthly_run >= timedelta(days=30):
                logger.info("Monthly schedule trigger hit.")
                await self.run_pipeline_task()
                last_monthly_run = now
                
            # Sleep for next interval
            await asyncio.sleep(self.interval_seconds)

    def stop(self) -> None:
        """Stops the scheduler loop."""
        logger.info("Background Pipeline Scheduler STOPPED.")
        self.is_running = False
