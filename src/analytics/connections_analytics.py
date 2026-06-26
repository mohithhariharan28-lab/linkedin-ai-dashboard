import os
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from src.database.repository import LinkedInRepository
from src.utils.logger import setup_logger

logger = setup_logger("analytics.connections_analytics")

class ConnectionsAnalyticsService:
    """Computes SQL connections summaries and generates dashboard-ready CSV reports."""

    def __init__(self, repository: LinkedInRepository) -> None:
        """Initializes the service with the database repository.

        Args:
            repository: Database repository instance.
        """
        self.repository = repository
        
        project_root = Path(__file__).resolve().parent.parent.parent
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_analytics_and_export(self) -> None:
        """Runs aggregation queries on SQLite and outputs clean CSV sheets."""
        logger.info("Computing LinkedIn Connections Analytics and exporting CSV reports...")
        
        conn = None
        try:
            conn = sqlite3.connect(str(self.repository.db_path))
            
            # 1. Total Connections and Monthly growth calculation
            df_connections = pd.read_sql_query("SELECT * FROM connections", conn)
            total_count = len(df_connections)
            
            if total_count == 0:
                logger.warning("No connections recorded in database. Exporting default empty sheets.")
                # We will write empty dataframes with correct headers
                self._write_empty_reports()
                return

            # Compute New Connections This Month
            # Compare connected_date string against current Month-Year
            now_month = datetime.utcnow().strftime("%Y-%m")
            df_connections["month_val"] = pd.to_datetime(df_connections["connected_date"], errors="coerce").dt.strftime("%Y-%m")
            new_this_month = len(df_connections[df_connections["month_val"] == now_month])

            # 2. Connection Directory (`reports/connections.csv`)
            # Clean directory list
            df_directory = df_connections[[
                "first_name", "last_name", "full_name", "profile_url",
                "headline", "company", "location", "connected_date", "import_source"
            ]].copy()
            df_directory.to_csv(self.reports_dir / "connections.csv", index=False, encoding="utf-8")
            df_directory.to_csv(self.reports_dir / "pbi_connection_directory.csv", index=False, encoding="utf-8")
            logger.info(f"Exported connections directory: {len(df_directory)} rows.")

            # 3. Connection Summary KPIs (`reports/connection_summary.csv` & `reports/pbi_total_connections.csv`)
            df_summary = pd.DataFrame([{
                "total_connections": total_count,
                "new_connections_this_month": new_this_month,
                "scraped_at": datetime.utcnow().isoformat()
            }])
            df_summary.to_csv(self.reports_dir / "connection_summary.csv", index=False, encoding="utf-8")
            df_summary.to_csv(self.reports_dir / "pbi_total_connections.csv", index=False, encoding="utf-8")
            logger.info("Exported connections summary KPI indicators.")

            # 4. Company Distribution (`reports/pbi_company_distribution.csv`)
            # Query vw_connections_by_company view
            df_companies = pd.read_sql_query("SELECT * FROM vw_connections_by_company", conn)
            if not df_companies.empty:
                df_companies["share_pct"] = (df_companies["connection_count"] / total_count) * 100.0
                df_companies.to_csv(self.reports_dir / "pbi_company_distribution.csv", index=False, encoding="utf-8")
                logger.info(f"Exported company distribution metrics: {len(df_companies)} rows.")
            else:
                pd.DataFrame(columns=["company", "connection_count", "share_pct"]).to_csv(
                    self.reports_dir / "pbi_company_distribution.csv", index=False, encoding="utf-8"
                )

            # 5. Monthly Growth Trend (`reports/pbi_monthly_connection_growth.csv`)
            # Query vw_connections_growth view
            df_growth = pd.read_sql_query("SELECT * FROM vw_connections_growth", conn)
            if not df_growth.empty:
                df_growth.to_csv(self.reports_dir / "pbi_monthly_connection_growth.csv", index=False, encoding="utf-8")
                logger.info(f"Exported monthly connection growth trend: {len(df_growth)} rows.")
            else:
                pd.DataFrame(columns=["month", "monthly_count", "cumulative_count"]).to_csv(
                    self.reports_dir / "pbi_monthly_connection_growth.csv", index=False, encoding="utf-8"
                )

            # 6. Industry Distribution (`reports/pbi_industry_distribution.csv`)
            # Query vw_connections_by_industry view
            df_industries = pd.read_sql_query("SELECT * FROM vw_connections_by_industry", conn)
            if not df_industries.empty:
                df_industries["share_pct"] = (df_industries["connection_count"] / total_count) * 100.0
                df_industries.to_csv(self.reports_dir / "pbi_industry_distribution.csv", index=False, encoding="utf-8")
                logger.info(f"Exported industry distribution metrics: {len(df_industries)} rows.")
            else:
                pd.DataFrame(columns=["industry", "connection_count", "share_pct"]).to_csv(
                    self.reports_dir / "pbi_industry_distribution.csv", index=False, encoding="utf-8"
                )

            logger.info("Connections CSV reports export process finished successfully.")
            
        except Exception as e:
            logger.error(f"Connections Analytics Failure: {e}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()

    def _write_empty_reports(self) -> None:
        """Helper to create empty reports files with appropriate columns."""
        # Create empty placeholders to avoid Power BI load errors
        cols_dir = ["first_name", "last_name", "full_name", "profile_url", "headline", "company", "location", "connected_date", "import_source"]
        pd.DataFrame(columns=cols_dir).to_csv(self.reports_dir / "connections.csv", index=False)
        pd.DataFrame(columns=cols_dir).to_csv(self.reports_dir / "pbi_connection_directory.csv", index=False)

        cols_sum = ["total_connections", "new_connections_this_month", "scraped_at"]
        pd.DataFrame(columns=cols_sum).to_csv(self.reports_dir / "connection_summary.csv", index=False)
        pd.DataFrame(columns=cols_sum).to_csv(self.reports_dir / "pbi_total_connections.csv", index=False)

        pd.DataFrame(columns=["company", "connection_count", "share_pct"]).to_csv(self.reports_dir / "pbi_company_distribution.csv", index=False)
        pd.DataFrame(columns=["industry", "connection_count", "share_pct"]).to_csv(self.reports_dir / "pbi_industry_distribution.csv", index=False)
        pd.DataFrame(columns=["month", "monthly_count", "cumulative_count"]).to_csv(self.reports_dir / "pbi_monthly_connection_growth.csv", index=False)
        logger.info("Empty placeholder reports written successfully.")
