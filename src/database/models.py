from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class ProfileSnapshot:
    """Represents a crawled LinkedIn profile snapshot."""
    full_name: str
    headline: str
    profile_url: str
    followers: Optional[int]
    connections: Optional[int]
    location: str
    about: str
    current_company: str
    experience: List[Dict[str, Any]] = field(default_factory=list)
    education: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: Optional[int] = None


@dataclass
class PostSnapshot:
    """Represents a crawled LinkedIn post snapshot."""
    linkedin_post_id: str
    post_date: str
    weekday: str
    month: str
    year: int
    post_text: str
    media_type: str
    likes: int
    comments: int
    reposts: int
    impressions: Optional[int] = None
    views: Optional[int] = None
    engagement_rate: float = 0.0
    post_url: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: Optional[int] = None


@dataclass
class PostMetricsHistoryRecord:
    """Represents a historical metrics entry for a specific post."""
    post_id: int  # References posts.id
    likes: int
    comments: int
    reposts: int
    views: Optional[int] = None
    impressions: Optional[int] = None
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: Optional[int] = None


@dataclass
class FollowerHistoryRecord:
    """Represents historical follower tracking record."""
    date: str
    followers: int
    id: Optional[int] = None


@dataclass
class ExecutionLogRecord:
    """Represents execution run logs."""
    execution_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    module: str = ""
    status: str = ""
    duration: float = 0.0
    id: Optional[int] = None


@dataclass
class AnalyticsSummary:
    """Represents overall high-level metrics calculation snapshot."""
    total_followers: int
    follower_growth_pct: float
    total_posts: int
    total_likes: int
    total_comments: int
    total_reposts: int
    avg_engagement_rate: float
    best_post_id: str
    worst_post_id: str
    posting_frequency_per_week: float
    avg_days_between_posts: float
    weekly_growth_pct: float
    monthly_growth_pct: float
    computed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: Optional[int] = None


@dataclass
class MonthlyStatistics:
    """Represents monthly posting volume and reaction stats."""
    year: int
    month: str
    post_count: int
    likes_count: int
    comments_count: int
    reposts_count: int
    monthly_growth_pct: float
    computed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: Optional[int] = None


@dataclass
class PostRanking:
    """Represents a post ranking index based on reactions and engagement."""
    linkedin_post_id: str
    rank_by_likes: int
    rank_by_comments: int
    rank_by_engagement: int
    computed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: Optional[int] = None


@dataclass
class ConnectionRecord:
    """Represents a LinkedIn connection record."""
    first_name: str
    last_name: str
    full_name: str
    profile_url: str
    headline: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    connected_date: Optional[str] = None  # Format: YYYY-MM-DD
    industry: Optional[str] = None
    import_source: str = "scrape"  # "scrape" or "csv"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    id: Optional[int] = None
