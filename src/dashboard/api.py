from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, RedirectResponse
from typing import List, Optional, Dict, Any
from src.database.db_manager import DatabaseManager
from src.database.models import ProfileSnapshot, PostSnapshot, FollowerHistoryRecord, AnalyticsSummary, MonthlyStatistics
from src.utils.logger import setup_logger

# Initialize logger
logger = setup_logger("dashboard.api")

# Initialize FastAPI App
app = FastAPI(
    title="LinkedIn AI Analytics REST API",
    description="Read-only REST service exposing scraped LinkedIn profile details, posts statistics, and calculated analytics summaries.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Dependency to yield database manager
def get_db() -> DatabaseManager:
    """Dependency injection helper to obtain DatabaseManager connection."""
    try:
        db = DatabaseManager()
        return db
    except Exception as e:
        logger.critical(f"Failed to connect to the SQLite database: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failure"
        )

# Exception handlers for clean JSON error responses
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception caught on request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred. Please check logs."}
    )

# --- Endpoints ---

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirects the root URL request to the interactive API documentation page."""
    logger.info("GET / requested, redirecting to /docs")
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
def health_check(db: DatabaseManager = Depends(get_db)):
    """Verifies SQLite connection and checks the health status of the API."""
    logger.info("GET /health requested")
    try:
        # Simple test query to check DB connection
        db.repository.get_latest_followers()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

@app.get("/profile", response_model=ProfileSnapshot, tags=["Profile"])
def get_profile(db: DatabaseManager = Depends(get_db)):
    """Retrieves the most recent LinkedIn profile snapshot."""
    logger.info("GET /profile requested")
    profile = db.repository.get_latest_profile()
    if not profile:
        logger.warning("No profile snapshot found in database.")
        raise HTTPException(status_code=404, detail="No profile snapshot found.")
    return profile

@app.get("/followers", response_model=List[FollowerHistoryRecord], tags=["Followers"])
def get_followers(db: DatabaseManager = Depends(get_db)):
    """Retrieves the historical daily follower count logs."""
    logger.info("GET /followers requested")
    history = db.repository.get_follower_history()
    return history

@app.get("/posts", response_model=List[PostSnapshot], tags=["Posts"])
def get_posts(db: DatabaseManager = Depends(get_db)):
    """Retrieves all scraped LinkedIn posts."""
    logger.info("GET /posts requested")
    posts = db.repository.get_all_posts()
    return posts

@app.get("/posts/top", response_model=List[PostSnapshot], tags=["Posts"])
def get_top_posts(
    limit: int = Query(default=10, ge=1, le=100, description="Max posts to return"),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves top performing posts ordered by Engagement Rate descending."""
    logger.info(f"GET /posts/top requested (limit: {limit})")
    posts = db.repository.get_top_posts(limit)
    return posts

@app.get("/posts/recent", response_model=List[PostSnapshot], tags=["Posts"])
def get_recent_posts(
    limit: int = Query(default=10, ge=1, le=100, description="Max posts to return"),
    db: DatabaseManager = Depends(get_db)
):
    """Retrieves recently scraped posts ordered by date descending."""
    logger.info(f"GET /posts/recent requested (limit: {limit})")
    posts = db.repository.get_recent_posts(limit)
    return posts

@app.get("/analytics/summary", response_model=AnalyticsSummary, tags=["Analytics"])
def get_analytics_summary(db: DatabaseManager = Depends(get_db)):
    """Retrieves the latest overall analytics summary calculation snapshot."""
    logger.info("GET /analytics/summary requested")
    summary = db.repository.get_latest_analytics_summary()
    if not summary:
        logger.warning("No analytics summary found in database.")
        raise HTTPException(status_code=404, detail="No analytics summary has been computed yet.")
    return summary

@app.get("/analytics/monthly", response_model=List[MonthlyStatistics], tags=["Analytics"])
def get_analytics_monthly(db: DatabaseManager = Depends(get_db)):
    """Retrieves monthly posting and reaction statistics sorted chronologically."""
    logger.info("GET /analytics/monthly requested")
    monthly_stats = db.repository.get_monthly_statistics()
    return monthly_stats

@app.get("/analytics/engagement", tags=["Analytics"])
def get_analytics_engagement(db: DatabaseManager = Depends(get_db)):
    """Retrieves posts engagement trend data for dashboard visualizations."""
    logger.info("GET /analytics/engagement requested")
    posts = db.repository.get_all_posts()
    # Sort chronologically
    posts_chrono = sorted(posts, key=lambda p: p.post_date)
    
    trend = []
    for p in posts_chrono:
        trend.append({
            "linkedin_post_id": p.linkedin_post_id,
            "date": p.post_date.split('T')[0],
            "likes": p.likes,
            "comments": p.comments,
            "reposts": p.reposts,
            "reactions": p.likes + p.comments + p.reposts,
            "engagement_rate": p.engagement_rate,
            "media_type": p.media_type
        })
    return trend
