import os
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger
from src.analytics.connections_analytics import ConnectionsAnalyticsService

logger = setup_logger("analytics.powerbi_pipeline")

class PowerBiPipelineService:
    """Handles view executions and CSV exports for Power BI integration."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initializes the pipeline service.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
        
        project_root = Path(__file__).resolve().parent.parent.parent
        self.reports_dir = project_root / "reports"
        
        # Ensure the reports output directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_export(self) -> None:
        """Executes SQL Views and refreshes the CSV files in the reports folder."""
        export_time = datetime.utcnow().isoformat()
        logger.info(f"Starting Power BI CSV export process at {export_time}...")
        
        # Map views to their output CSV filenames
        view_map = {
            "vw_dashboard_overview": "dashboard_overview.csv",
            "vw_followers_growth": "followers_growth.csv",
            "vw_post_performance": "post_performance.csv",
            "vw_monthly_activity": "monthly_activity.csv",
            "vw_engagement_trend": "engagement_trend.csv",
            "vw_top_posts": "top_posts.csv",
            "vw_posting_frequency": "posting_frequency.csv"
        }
        
        # Open sqlite connection to execute queries using pandas
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_manager.db_path))
            
            for view_name, csv_filename in view_map.items():
                csv_path = self.reports_dir / csv_filename
                logger.info(f"Exporting view '{view_name}' to '{csv_path}'...")
                
                try:
                    # Query view using Pandas
                    df = pd.read_sql_query(f"SELECT * FROM {view_name}", conn)
                    rows_count = len(df)
                    
                    # Write to CSV
                    df.to_csv(csv_path, index=False, encoding="utf-8")
                    
                    logger.info(f"CSV Export: Refreshed '{csv_filename}' successfully. ({rows_count} rows exported)")
                    
                except Exception as view_err:
                    logger.error(f"Export Error: Failed to export view '{view_name}' to CSV: {view_err}", exc_info=True)
                    raise
                    
            # Run connections analytics CSV exports automatically
            logger.info("Triggering Connections Analytics CSV export process...")
            conn_analytics = ConnectionsAnalyticsService(self.db_manager.repository)
            conn_analytics.run_analytics_and_export()

            logger.info("Power BI CSV export process finished successfully.")
            
        except Exception as conn_err:
            logger.error(f"Export Error: Database connection failure during export: {conn_err}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()
