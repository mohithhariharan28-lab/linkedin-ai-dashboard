import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple
from src.database.models import (
    ProfileSnapshot, PostSnapshot, FollowerHistoryRecord, ExecutionLogRecord,
    PostMetricsHistoryRecord, AnalyticsSummary, MonthlyStatistics, PostRanking,
    ConnectionRecord
)
from src.utils.logger import setup_logger

logger = setup_logger("database.repository")

class LinkedInRepository:
    """Manages SQLite database interactions for LinkedIn Analytics."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initializes repository with the path to the SQLite database.

        Args:
            db_path: Path to the SQLite db file. If None, default is data/linkedin.db.
        """
        project_root = Path(__file__).resolve().parent.parent.parent
        self.db_path = Path(db_path or project_root / "data" / "linkedin.db")
        
        # Ensure parent directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize the database schema
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Helper to get a database connection with dictionary/row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Creates the database schema and reporting views if they do not exist."""
        logger.debug(f"Initializing SQLite database at {self.db_path}...")
        
        # Check if industry column exists in connections (run migration if needed)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(connections)")
                cols = [info['name'] for info in cursor.fetchall()]
                if cols and "industry" not in cols:
                    cursor.execute("ALTER TABLE connections ADD COLUMN industry TEXT DEFAULT NULL")
                    conn.commit()
                    logger.info("Database migration: Added industry column to connections table.")
        except sqlite3.Error as migration_err:
            logger.debug(f"Migration check skipped or connections table doesn't exist yet: {migration_err}")

        # Drop existing connection views to force recreation with new schema
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DROP VIEW IF EXISTS vw_connections")
                cursor.execute("DROP VIEW IF EXISTS vw_connections_by_company")
                cursor.execute("DROP VIEW IF EXISTS vw_connections_by_industry")
                cursor.execute("DROP VIEW IF EXISTS vw_connections_growth")
                conn.commit()
        except sqlite3.Error as drop_err:
            logger.debug(f"Failed to drop old views: {drop_err}")
        
        queries = [
            # Profiles snapshot table
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scraped_at TEXT NOT NULL,
                full_name TEXT NOT NULL,
                headline TEXT,
                followers INTEGER,
                connections INTEGER,
                location TEXT,
                about TEXT,
                current_company TEXT,
                profile_url TEXT,
                experience TEXT,   -- JSON array representation
                education TEXT,    -- JSON array representation
                skills TEXT        -- JSON array representation
            );
            """,
            # Posts snapshot table
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linkedin_post_id TEXT UNIQUE NOT NULL,
                scraped_at TEXT NOT NULL,
                post_date TEXT NOT NULL,
                weekday TEXT NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                post_text TEXT,
                media_type TEXT,
                likes INTEGER NOT NULL DEFAULT 0,
                comments INTEGER NOT NULL DEFAULT 0,
                reposts INTEGER NOT NULL DEFAULT 0,
                impressions INTEGER,
                views INTEGER,
                engagement_rate REAL NOT NULL DEFAULT 0.0,
                post_url TEXT
            );
            """,
            # Post metrics tracking table (preserves historical reaction updates)
            """
            CREATE TABLE IF NOT EXISTS post_metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                likes INTEGER NOT NULL,
                comments INTEGER NOT NULL,
                reposts INTEGER NOT NULL,
                views INTEGER,
                impressions INTEGER,
                scraped_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            );
            """,
            # Follower history snapshot table
            """
            CREATE TABLE IF NOT EXISTS follower_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                followers INTEGER NOT NULL
            );
            """,
            # Execution runs tracking table
            """
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time TEXT NOT NULL,
                module TEXT NOT NULL,
                status TEXT NOT NULL,
                duration REAL NOT NULL
            );
            """,
            # Analytics summary calculations table
            """
            CREATE TABLE IF NOT EXISTS analytics_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_followers INTEGER NOT NULL,
                follower_growth_pct REAL NOT NULL,
                total_posts INTEGER NOT NULL,
                total_likes INTEGER NOT NULL,
                total_comments INTEGER NOT NULL,
                total_reposts INTEGER NOT NULL,
                avg_engagement_rate REAL NOT NULL,
                best_post_id TEXT,
                worst_post_id TEXT,
                posting_frequency_per_week REAL NOT NULL,
                avg_days_between_posts REAL NOT NULL,
                weekly_growth_pct REAL NOT NULL,
                monthly_growth_pct REAL NOT NULL,
                computed_at TEXT NOT NULL
            );
            """,
            # Monthly statistics table
            """
            CREATE TABLE IF NOT EXISTS monthly_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month TEXT NOT NULL,
                post_count INTEGER NOT NULL,
                likes_count INTEGER NOT NULL,
                comments_count INTEGER NOT NULL,
                reposts_count INTEGER NOT NULL,
                monthly_growth_pct REAL NOT NULL,
                computed_at TEXT NOT NULL
            );
            """,
            # Post rankings index table
            """
            CREATE TABLE IF NOT EXISTS post_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                linkedin_post_id TEXT NOT NULL,
                rank_by_likes INTEGER NOT NULL,
                rank_by_comments INTEGER NOT NULL,
                rank_by_engagement INTEGER NOT NULL,
                computed_at TEXT NOT NULL
            );
            """,
            # --- SQL Reporting Views for Power BI Data Pipeline ---
            # 1. vw_dashboard_overview
            """
            CREATE VIEW IF NOT EXISTS vw_dashboard_overview AS
            SELECT * FROM analytics_summary ORDER BY computed_at DESC LIMIT 1;
            """,
            # 2. vw_followers_growth
            """
            CREATE VIEW IF NOT EXISTS vw_followers_growth AS
            SELECT date, followers FROM follower_history ORDER BY date ASC;
            """,
            # 3. vw_post_performance
            """
            CREATE VIEW IF NOT EXISTS vw_post_performance AS
            SELECT linkedin_post_id, post_date, weekday, month, year, post_text, media_type, likes, comments, reposts, engagement_rate, post_url 
            FROM posts ORDER BY post_date DESC;
            """,
            # 4. vw_monthly_activity
            """
            CREATE VIEW IF NOT EXISTS vw_monthly_activity AS
            SELECT year, month, post_count, likes_count, comments_count, reposts_count, monthly_growth_pct, computed_at 
            FROM monthly_statistics ORDER BY year ASC, month ASC;
            """,
            # 5. vw_engagement_trend
            """
            CREATE VIEW IF NOT EXISTS vw_engagement_trend AS
            SELECT date(post_date) as date, likes, comments, reposts, engagement_rate, media_type, post_url 
            FROM posts ORDER BY post_date ASC;
            """,
            # 6. vw_top_posts
            """
            CREATE VIEW IF NOT EXISTS vw_top_posts AS
            SELECT linkedin_post_id, post_text, media_type, likes, comments, reposts, engagement_rate, post_url 
            FROM posts ORDER BY engagement_rate DESC LIMIT 10;
            """,
            # 7. vw_posting_frequency
            """
            CREATE VIEW IF NOT EXISTS vw_posting_frequency AS
            SELECT weekday, COUNT(*) as post_count, AVG(likes) as avg_likes, AVG(comments) as avg_comments 
            FROM posts GROUP BY weekday ORDER BY 
            CASE weekday
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END;
            """,
            # 8. connections table
            """
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                full_name TEXT NOT NULL,
                profile_url TEXT UNIQUE NOT NULL,
                headline TEXT,
                company TEXT,
                location TEXT,
                connected_date TEXT,
                industry TEXT,
                import_source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """,
            # 9. vw_connections
            """
            CREATE VIEW IF NOT EXISTS vw_connections AS
            SELECT id, first_name, last_name, full_name, profile_url, headline, company, location, connected_date, industry, import_source, created_at, updated_at
            FROM connections ORDER BY connected_date DESC, created_at DESC;
            """,
            # 10. vw_connections_by_company
            """
            CREATE VIEW IF NOT EXISTS vw_connections_by_company AS
            SELECT company, COUNT(*) as connection_count
            FROM connections
            WHERE company IS NOT NULL AND company != ''
            GROUP BY company
            ORDER BY connection_count DESC;
            """,
            # 11. vw_connections_by_industry
            """
            CREATE VIEW IF NOT EXISTS vw_connections_by_industry AS
            SELECT industry, COUNT(*) as connection_count
            FROM connections
            WHERE industry IS NOT NULL AND industry != ''
            GROUP BY industry
            ORDER BY connection_count DESC;
            """,
            # 12. vw_connections_growth
            """
            CREATE VIEW IF NOT EXISTS vw_connections_growth AS
            WITH MonthlyCounts AS (
                SELECT 
                    strftime('%Y-%m', connected_date) as month_val,
                    COUNT(*) as monthly_count
                FROM connections
                WHERE connected_date IS NOT NULL AND connected_date != ''
                GROUP BY month_val
            )
            SELECT 
                month_val as month,
                monthly_count,
                (SELECT SUM(monthly_count) FROM MonthlyCounts mc2 WHERE mc2.month_val <= mc1.month_val) as cumulative_count
            FROM MonthlyCounts mc1
            ORDER BY month ASC;
            """
        ]
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                conn.commit()
            logger.info("Database tables and reporting views initialized/verified successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error initializing SQLite database: {e}", exc_info=True)
            raise

    def save_profile_snapshot(self, snapshot: ProfileSnapshot) -> int:
        """Inserts a new profile snapshot. Never overwrites historical records.

        Args:
            snapshot: Dataclass instance of ProfileSnapshot.

        Returns:
            int: The primary key of the inserted row.
        """
        logger.info(f"Saving profile snapshot for {snapshot.full_name} to database...")
        
        # Serialize lists to JSON text
        exp_json = json.dumps(snapshot.experience)
        edu_json = json.dumps(snapshot.education)
        skills_json = json.dumps(snapshot.skills)

        query = """
            INSERT INTO profiles (
                scraped_at, full_name, headline, followers, connections,
                location, about, current_company, profile_url,
                experience, education, skills
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    snapshot.scraped_at,
                    snapshot.full_name,
                    snapshot.headline,
                    snapshot.followers,
                    snapshot.connections,
                    snapshot.location,
                    snapshot.about,
                    snapshot.current_company,
                    snapshot.profile_url,
                    exp_json,
                    edu_json,
                    skills_json
                ))
                conn.commit()
                row_id = cursor.lastrowid
                logger.info(f"Database Insert: Successfully inserted profiles row with ID: {row_id}")
                
                # Also automatically insert into follower_history
                if snapshot.followers is not None:
                    # Save date as YYYY-MM-DD
                    date_str = snapshot.scraped_at.split('T')[0]
                    self.save_follower_history(FollowerHistoryRecord(date=date_str, followers=snapshot.followers))
                    
                return row_id
        except sqlite3.Error as e:
            logger.error(f"Database Error inserting profile: {e}", exc_info=True)
            raise

    def save_follower_history(self, record: FollowerHistoryRecord) -> None:
        """Inserts or updates the follower count for a given date.

        Args:
            record: Dataclass instance of FollowerHistoryRecord.
        """
        query = """
            INSERT INTO follower_history (date, followers)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET followers=excluded.followers
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (record.date, record.followers))
                conn.commit()
                logger.info(f"Database Insert: Follower history updated for date {record.date}: {record.followers} followers.")
        except sqlite3.Error as e:
            logger.error(f"Database Error updating follower history: {e}", exc_info=True)
            raise

    def save_post_snapshot(self, snapshot: PostSnapshot) -> int:
        """Inserts or updates static details of a post, updating latest metrics in the posts table.

        Also automatically appends a new metrics record to post_metrics_history.

        Args:
            snapshot: Dataclass instance of PostSnapshot.

        Returns:
            int: The database ID of the posts row.
        """
        query = """
            INSERT INTO posts (
                linkedin_post_id, scraped_at, post_date, weekday, month, year,
                post_text, media_type, likes, comments, reposts, impressions,
                views, engagement_rate, post_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(linkedin_post_id) DO UPDATE SET
                scraped_at=excluded.scraped_at,
                post_date=excluded.post_date,
                weekday=excluded.weekday,
                month=excluded.month,
                year=excluded.year,
                post_text=excluded.post_text,
                media_type=excluded.media_type,
                likes=excluded.likes,
                comments=excluded.comments,
                reposts=excluded.reposts,
                impressions=coalesce(excluded.impressions, posts.impressions),
                views=coalesce(excluded.views, posts.views),
                engagement_rate=excluded.engagement_rate,
                post_url=excluded.post_url
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    snapshot.linkedin_post_id,
                    snapshot.scraped_at,
                    snapshot.post_date,
                    snapshot.weekday,
                    snapshot.month,
                    snapshot.year,
                    snapshot.post_text,
                    snapshot.media_type,
                    snapshot.likes,
                    snapshot.comments,
                    snapshot.reposts,
                    snapshot.impressions,
                    snapshot.views,
                    snapshot.engagement_rate,
                    snapshot.post_url
                ))
                conn.commit()
                
                # Fetch row ID
                cursor.execute("SELECT id FROM posts WHERE linkedin_post_id = ?", (snapshot.linkedin_post_id,))
                row = cursor.fetchone()
                row_id = row['id']
                logger.info(f"Database Insert: Saved/updated post {snapshot.linkedin_post_id} (ID: {row_id}).")
                
                # Save to metrics history table
                metrics_record = PostMetricsHistoryRecord(
                    post_id=row_id,
                    likes=snapshot.likes,
                    comments=snapshot.comments,
                    reposts=snapshot.reposts,
                    views=snapshot.views,
                    impressions=snapshot.impressions,
                    scraped_at=snapshot.scraped_at
                )
                self.save_post_metrics_history(metrics_record)
                
                return row_id
        except sqlite3.Error as e:
            logger.error(f"Database Error inserting/updating post: {e}", exc_info=True)
            raise

    def update_post_engagement_rate(self, linkedin_post_id: str, engagement_rate: float) -> None:
        """Updates the calculated engagement rate for a post.

        Args:
            linkedin_post_id: The unique post identifier.
            engagement_rate: Calculated engagement rate percentage.
        """
        query = "UPDATE posts SET engagement_rate = ? WHERE linkedin_post_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (engagement_rate, linkedin_post_id))
                conn.commit()
                logger.debug(f"Database Update: Set engagement_rate = {engagement_rate:.4f}% for post {linkedin_post_id}")
        except sqlite3.Error as e:
            logger.error(f"Database Error updating engagement rate: {e}")

    def save_post_metrics_history(self, record: PostMetricsHistoryRecord) -> int:
        """Saves a metrics snapshot for historical post reactions tracking.

        Args:
            record: Dataclass instance of PostMetricsHistoryRecord.

        Returns:
            int: The primary key of the inserted row.
        """
        query = """
            INSERT INTO post_metrics_history (post_id, likes, comments, reposts, views, impressions, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    record.post_id,
                    record.likes,
                    record.comments,
                    record.reposts,
                    record.views,
                    record.impressions,
                    record.scraped_at
                ))
                conn.commit()
                row_id = cursor.lastrowid
                logger.debug(f"Database Insert: Logged metrics history row for post ID {record.post_id} (ID: {row_id}).")
                return row_id
        except sqlite3.Error as e:
            logger.error(f"Database Error inserting metrics history: {e}", exc_info=True)
            raise

    def save_execution_log(self, record: ExecutionLogRecord) -> int:
        """Inserts a run execution log record.

        Args:
            record: Dataclass instance of ExecutionLogRecord.

        Returns:
            int: The primary key of the inserted row.
        """
        query = """
            INSERT INTO execution_log (execution_time, module, status, duration)
            VALUES (?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    record.execution_time,
                    record.module,
                    record.status,
                    record.duration
                ))
                conn.commit()
                row_id = cursor.lastrowid
                logger.info(f"Database Insert: Successfully logged run of '{record.module}' with status '{record.status}' (Duration: {record.duration:.2f}s, ID: {row_id})")
                return row_id
        except sqlite3.Error as e:
            logger.error(f"Database Error logging execution: {e}", exc_info=True)
            raise

    def save_analytics_summary(self, summary: AnalyticsSummary) -> int:
        """Inserts a new analytics summary snapshot.

        Args:
            summary: Dataclass instance of AnalyticsSummary.

        Returns:
            int: The primary key of the inserted row.
        """
        query = """
            INSERT INTO analytics_summary (
                total_followers, follower_growth_pct, total_posts, total_likes,
                total_comments, total_reposts, avg_engagement_rate, best_post_id,
                worst_post_id, posting_frequency_per_week, avg_days_between_posts,
                weekly_growth_pct, monthly_growth_pct, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    summary.total_followers,
                    summary.follower_growth_pct,
                    summary.total_posts,
                    summary.total_likes,
                    summary.total_comments,
                    summary.total_reposts,
                    summary.avg_engagement_rate,
                    summary.best_post_id,
                    summary.worst_post_id,
                    summary.posting_frequency_per_week,
                    summary.avg_days_between_posts,
                    summary.weekly_growth_pct,
                    summary.monthly_growth_pct,
                    summary.computed_at
                ))
                conn.commit()
                row_id = cursor.lastrowid
                logger.info(f"Database Insert: Saved analytics summary row with ID: {row_id}")
                return row_id
        except sqlite3.Error as e:
            logger.error(f"Database Error inserting analytics summary: {e}", exc_info=True)
            raise

    def save_monthly_statistics(self, stats_list: List[MonthlyStatistics]) -> None:
        """Inserts monthly statistics records in a transaction.

        Args:
            stats_list: List of MonthlyStatistics dataclass instances.
        """
        query = """
            INSERT INTO monthly_statistics (
                year, month, post_count, likes_count, comments_count, reposts_count,
                monthly_growth_pct, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, [
                    (
                        s.year, s.month, s.post_count, s.likes_count, s.comments_count,
                        s.reposts_count, s.monthly_growth_pct, s.computed_at
                    ) for s in stats_list
                ])
                conn.commit()
                logger.info(f"Database Insert: Saved {len(stats_list)} monthly statistics rows.")
        except sqlite3.Error as e:
            logger.error(f"Database Error inserting monthly statistics: {e}", exc_info=True)
            raise

    def save_post_rankings(self, rankings_list: List[PostRanking]) -> None:
        """Inserts post ranking records in a transaction.

        Args:
            rankings_list: List of PostRanking dataclass instances.
        """
        query = """
            INSERT INTO post_rankings (
                linkedin_post_id, rank_by_likes, rank_by_comments, rank_by_engagement, computed_at
            ) VALUES (?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, [
                    (
                        r.linkedin_post_id, r.rank_by_likes, r.rank_by_comments,
                        r.rank_by_engagement, r.computed_at
                    ) for r in rankings_list
                ])
                conn.commit()
                logger.info(f"Database Insert: Saved {len(rankings_list)} post ranking rows.")
        except sqlite3.Error as e:
            logger.error(f"Database Error inserting post rankings: {e}", exc_info=True)
            raise

    def get_latest_followers(self) -> int:
        """Fetches the follower count from the most recent profile snapshot.

        Returns:
            int: Follower count, or 0 if no snapshots exist.
        """
        query = "SELECT followers FROM profiles ORDER BY scraped_at DESC LIMIT 1"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                row = cursor.fetchone()
                if row and row['followers'] is not None:
                    return row['followers']
                return 0
        except sqlite3.Error as e:
            logger.error(f"Database Error getting latest followers: {e}")
            return 0

    def get_latest_profile(self) -> Optional[ProfileSnapshot]:
        """Fetches the latest profile snapshot.

        Returns:
            Optional[ProfileSnapshot]: Latest profile record or None.
        """
        query = "SELECT * FROM profiles ORDER BY scraped_at DESC LIMIT 1"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                r = cursor.fetchone()
                if not r:
                    return None
                return ProfileSnapshot(
                    full_name=r['full_name'],
                    headline=r['headline'],
                    profile_url=r['profile_url'],
                    followers=r['followers'],
                    connections=r['connections'],
                    location=r['location'],
                    about=r['about'],
                    current_company=r['current_company'],
                    experience=json.loads(r['experience']) if r['experience'] else [],
                    education=json.loads(r['education']) if r['education'] else [],
                    skills=json.loads(r['skills']) if r['skills'] else [],
                    scraped_at=r['scraped_at'],
                    id=r['id']
                )
        except Exception as e:
            logger.error(f"Error getting latest profile: {e}", exc_info=True)
            return None

    def get_latest_analytics_summary(self) -> Optional[AnalyticsSummary]:
        """Fetches the latest entry from analytics_summary.

        Returns:
            Optional[AnalyticsSummary]: Latest summary calculations or None.
        """
        query = "SELECT * FROM analytics_summary ORDER BY computed_at DESC LIMIT 1"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                r = cursor.fetchone()
                if not r:
                    return None
                return AnalyticsSummary(
                    total_followers=r['total_followers'],
                    follower_growth_pct=r['follower_growth_pct'],
                    total_posts=r['total_posts'],
                    total_likes=r['total_likes'],
                    total_comments=r['total_comments'],
                    total_reposts=r['total_reposts'],
                    avg_engagement_rate=r['avg_engagement_rate'],
                    best_post_id=r['best_post_id'],
                    worst_post_id=r['worst_post_id'],
                    posting_frequency_per_week=r['posting_frequency_per_week'],
                    avg_days_between_posts=r['avg_days_between_posts'],
                    weekly_growth_pct=r['weekly_growth_pct'],
                    monthly_growth_pct=r['monthly_growth_pct'],
                    computed_at=r['computed_at'],
                    id=r['id']
                )
        except Exception as e:
            logger.error(f"Error getting latest analytics summary: {e}", exc_info=True)
            return None

    def get_monthly_statistics(self) -> List[MonthlyStatistics]:
        """Fetches all monthly statistics records sorted chronologically.

        Returns:
            List[MonthlyStatistics]: List of MoM statistics.
        """
        query = "SELECT * FROM monthly_statistics ORDER BY year ASC, month ASC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                stats = []
                for r in rows:
                    stats.append(MonthlyStatistics(
                        year=r['year'],
                        month=r['month'],
                        post_count=r['post_count'],
                        likes_count=r['likes_count'],
                        comments_count=r['comments_count'],
                        reposts_count=r['reposts_count'],
                        monthly_growth_pct=r['monthly_growth_pct'],
                        computed_at=r['computed_at'],
                        id=r['id']
                    ))
                return stats
        except Exception as e:
            logger.error(f"Error getting monthly statistics: {e}", exc_info=True)
            return []

    def get_top_posts(self, limit: int = 10) -> List[PostSnapshot]:
        """Fetches top posts ordered by engagement rate descending.

        Args:
            limit: Maximum records to return.

        Returns:
            List[PostSnapshot]: List of top posts.
        """
        query = "SELECT * FROM posts ORDER BY engagement_rate DESC LIMIT ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                posts = []
                for r in rows:
                    posts.append(PostSnapshot(
                        linkedin_post_id=r['linkedin_post_id'],
                        post_date=r['post_date'],
                        weekday=r['weekday'],
                        month=r['month'],
                        year=r['year'],
                        post_text=r['post_text'],
                        media_type=r['media_type'],
                        likes=r['likes'],
                        comments=r['comments'],
                        reposts=r['reposts'],
                        impressions=r['impressions'],
                        views=r['views'],
                        engagement_rate=r['engagement_rate'],
                        post_url=r['post_url'],
                        scraped_at=r['scraped_at'],
                        id=r['id']
                    ))
                return posts
        except Exception as e:
            logger.error(f"Error getting top posts: {e}", exc_info=True)
            return []

    def get_recent_posts(self, limit: int = 10) -> List[PostSnapshot]:
        """Fetches recent posts ordered by date descending.

        Args:
            limit: Maximum records to return.

        Returns:
            List[PostSnapshot]: List of recent posts.
        """
        query = "SELECT * FROM posts ORDER BY post_date DESC LIMIT ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                posts = []
                for r in rows:
                    posts.append(PostSnapshot(
                        linkedin_post_id=r['linkedin_post_id'],
                        post_date=r['post_date'],
                        weekday=r['weekday'],
                        month=r['month'],
                        year=r['year'],
                        post_text=r['post_text'],
                        media_type=r['media_type'],
                        likes=r['likes'],
                        comments=r['comments'],
                        reposts=r['reposts'],
                        impressions=r['impressions'],
                        views=r['views'],
                        engagement_rate=r['engagement_rate'],
                        post_url=r['post_url'],
                        scraped_at=r['scraped_at'],
                        id=r['id']
                    ))
                return posts
        except Exception as e:
            logger.error(f"Error getting recent posts: {e}", exc_info=True)
            return []

    def get_all_posts(self) -> List[PostSnapshot]:
        """Fetches all posts stored in the database.

        Returns:
            List[PostSnapshot]: List of post snapshots.
        """
        query = "SELECT * FROM posts ORDER BY post_date DESC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                posts = []
                for r in rows:
                    posts.append(PostSnapshot(
                        linkedin_post_id=r['linkedin_post_id'],
                        post_date=r['post_date'],
                        weekday=r['weekday'],
                        month=r['month'],
                        year=r['year'],
                        post_text=r['post_text'],
                        media_type=r['media_type'],
                        likes=r['likes'],
                        comments=r['comments'],
                        reposts=r['reposts'],
                        impressions=r['impressions'],
                        views=r['views'],
                        engagement_rate=r['engagement_rate'],
                        post_url=r['post_url'],
                        scraped_at=r['scraped_at'],
                        id=r['id']
                    ))
                return posts
        except sqlite3.Error as e:
            logger.error(f"Database Error getting all posts: {e}")
            return []

    def get_post_metrics_history(self, post_id: int) -> List[PostMetricsHistoryRecord]:
        """Fetches the metrics history for a given post.

        Args:
            post_id: Database key of the post.

        Returns:
            List[PostMetricsHistoryRecord]: Historical metrics records.
        """
        query = "SELECT * FROM post_metrics_history WHERE post_id = ? ORDER BY scraped_at ASC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (post_id,))
                rows = cursor.fetchall()
                history = []
                for r in rows:
                    history.append(PostMetricsHistoryRecord(
                        post_id=r['post_id'],
                        likes=r['likes'],
                        comments=r['comments'],
                        reposts=r['reposts'],
                        views=r['views'],
                        impressions=r['impressions'],
                        scraped_at=r['scraped_at'],
                        id=r['id']
                    ))
                return history
        except sqlite3.Error as e:
            logger.error(f"Database Error getting post metrics: {e}")
            return []

    def get_follower_history(self) -> List[FollowerHistoryRecord]:
        """Fetches the follower tracking history.

        Returns:
            List[FollowerHistoryRecord]: Follower history records.
        """
        query = "SELECT * FROM follower_history ORDER BY date ASC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                records = []
                for r in rows:
                    records.append(FollowerHistoryRecord(
                        date=r['date'],
                        followers=r['followers'],
                        id=r['id']
                    ))
                return records
        except sqlite3.Error as e:
            logger.error(f"Database Error getting follower history: {e}")
            return []

    def save_connection_records(self, records: List[ConnectionRecord]) -> Tuple[int, int]:
        """Saves a batch of connection records, skipping duplicates based on profile_url.

        Args:
            records: List of ConnectionRecord dataclass instances.

        Returns:
            Tuple[int, int]: (inserted_count, skipped_count)
        """
        query_insert = """
            INSERT INTO connections (
                first_name, last_name, full_name, profile_url, headline,
                company, location, connected_date, industry, import_source,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_url) DO UPDATE SET
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                full_name=excluded.full_name,
                headline=coalesce(excluded.headline, headline),
                company=coalesce(excluded.company, company),
                location=coalesce(excluded.location, location),
                connected_date=coalesce(excluded.connected_date, connected_date),
                industry=coalesce(excluded.industry, industry),
                import_source=excluded.import_source,
                updated_at=excluded.updated_at
        """
        
        inserted = 0
        skipped = 0
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for r in records:
                    # Check duplicate if ON CONFLICT DO UPDATE isn't counted as skipped
                    # In SQLITE, ON CONFLICT update updates the row. We will track actual inserts vs updates or count skips.
                    # We can check if URL already exists to count duplicates skipped.
                    cursor.execute("SELECT id FROM connections WHERE profile_url = ?", (r.profile_url,))
                    exists = cursor.fetchone()
                    if exists:
                        skipped += 1
                    else:
                        inserted += 1
                        
                    cursor.execute(query_insert, (
                        r.first_name,
                        r.last_name,
                        r.full_name,
                        r.profile_url,
                        r.headline,
                        r.company,
                        r.location,
                        r.connected_date,
                        r.industry,
                        r.import_source,
                        r.created_at,
                        r.updated_at
                    ))
                conn.commit()
                logger.info(f"Database Connections: Imported {inserted} connections, skipped/updated {skipped} duplicates.")
                return inserted, skipped
        except sqlite3.Error as e:
            logger.error(f"Database Error importing connections: {e}", exc_info=True)
            raise

    def get_all_connections(self) -> List[ConnectionRecord]:
        """Fetches all connections sorted by connected date.

        Returns:
            List[ConnectionRecord]: List of connections.
        """
        query = "SELECT * FROM connections ORDER BY connected_date DESC"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    results.append(ConnectionRecord(
                        first_name=r['first_name'],
                        last_name=r['last_name'],
                        full_name=r['full_name'],
                        profile_url=r['profile_url'],
                        headline=r['headline'],
                        company=r['company'],
                        location=r['location'],
                        connected_date=r['connected_date'],
                        industry=r['industry'] if 'industry' in r.keys() else None,
                        import_source=r['import_source'],
                        created_at=r['created_at'],
                        updated_at=r['updated_at'],
                        id=r['id']
                    ))
                return results
        except sqlite3.Error as e:
            logger.error(f"Database Error getting all connections: {e}")
            return []
