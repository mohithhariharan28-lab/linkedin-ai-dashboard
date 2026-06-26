import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from src.database.repository import LinkedInRepository
from src.database.models import PostSnapshot, FollowerHistoryRecord
from src.utils.logger import setup_logger

logger = setup_logger("ai.insights_service")

class AIInsightsService:
    """Computes advanced predictions and historical insights from SQLite analytics tables."""

    def __init__(self, repository: LinkedInRepository) -> None:
        """Initializes the AI Insights Service.

        Args:
            repository: Database repository instance.
        """
        self.repository = repository

    def get_insights(self) -> Dict[str, Any]:
        """Calculates historical performance metrics and predictions.

        Returns:
            Dict[str, Any]: Calculated insights metrics.
        """
        logger.info("Computing AI Insights from SQLite database...")
        posts: List[PostSnapshot] = self.repository.get_all_posts()
        follower_history: List[FollowerHistoryRecord] = self.repository.get_follower_history()
        latest_followers = self.repository.get_latest_followers()

        # Fallbacks
        best_post = None
        worst_post = None
        best_day = "N/A"
        best_month = "N/A"
        avg_engagement = 0.0
        follower_pred_30d = latest_followers
        eng_pred_next = 0.0
        growth_trend_text = "Stable"
        best_freq_text = "N/A"

        if not posts:
            logger.warning("No posts found in database. Insights will be returned with default/empty values.")
            return {
                "best_post": best_post,
                "worst_post": worst_post,
                "best_day": best_day,
                "best_month": best_month,
                "best_frequency": best_freq_text,
                "avg_engagement": avg_engagement,
                "growth_trend": growth_trend_text,
                "follower_prediction_30d": int(follower_pred_30d),
                "engagement_prediction_next": eng_pred_next
            }

        # 1. Best and Worst Performing Posts by Likes & Engagement
        # We calculate engagement rate as reactions / followers (fallback to 1 if followers is 0)
        followers_denom = latest_followers if latest_followers > 0 else 1
        
        post_ers = []
        for post in posts:
            reactions = post.likes + post.comments + post.reposts
            er = (reactions / followers_denom) * 100.0
            post_ers.append((post, er))
        
        # Sort by engagement rate
        post_ers_sorted = sorted(post_ers, key=lambda x: x[1], reverse=True)
        best_post = post_ers_sorted[0][0]
        worst_post = post_ers_sorted[-1][0]
        
        # 2. Average Engagement
        avg_engagement = sum(x[1] for x in post_ers) / len(posts)

        # 3. Best Posting Day (by Average Engagement)
        day_metrics: Dict[str, List[float]] = {}
        for post, er in post_ers:
            day_metrics.setdefault(post.weekday, []).append(er)
        
        day_averages = {day: sum(ers)/len(ers) for day, ers in day_metrics.items()}
        if day_averages:
            best_day = max(day_averages, key=day_averages.get)

        # 4. Best Posting Month (by Average Engagement)
        month_metrics: Dict[str, List[float]] = {}
        for post, er in post_ers:
            month_metrics.setdefault(post.month, []).append(er)
        
        month_averages = {m: sum(ers)/len(ers) for m, ers in month_metrics.items()}
        if month_averages:
            best_month = max(month_averages, key=month_averages.get)

        # 5. Best Posting Frequency Heuristics
        # Group posts by calendar week and analyze if weeks with higher counts had better average engagement
        week_posts: Dict[str, List[float]] = {}
        for post, er in post_ers:
            try:
                dt = datetime.fromisoformat(post.post_date)
                week_key = dt.strftime("%Y-W%W")
            except ValueError:
                week_key = f"{post.year}-W01"
            week_posts.setdefault(week_key, []).append(er)
            
        freq_bins: Dict[int, List[float]] = {}
        for week, ers in week_posts.items():
            cnt = len(ers)
            freq_bins.setdefault(cnt, []).extend(ers)
            
        freq_averages = {f: sum(ers)/len(ers) for f, ers in freq_bins.items()}
        if freq_averages:
            best_freq = max(freq_averages, key=freq_averages.get)
            best_freq_text = f"{best_freq} posts per week (Avg Engagement: {freq_averages[best_freq]:.2f}%)"
        else:
            best_freq_text = "1-2 posts per week"

        # 6. Growth Trend & Follower Growth Prediction (Linear Regression)
        if len(follower_history) >= 2:
            # Sort follower history chronologically
            history_sorted = sorted(follower_history, key=lambda h: h.date)
            d0 = datetime.strptime(history_sorted[0].date, "%Y-%m-%d")
            
            x = []
            y = []
            for h in history_sorted:
                dt = datetime.strptime(h.date, "%Y-%m-%d")
                days_diff = (dt - d0).days
                x.append(days_diff)
                y.append(h.followers)

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xx = sum(xi**2 for xi in x)
            sum_xy = sum(xi*yi for xi, yi in zip(x, y))

            denom = (n * sum_xx - sum_x**2)
            if denom == 0:
                slope = 0.0
                intercept = float(y[-1])
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denom
                intercept = (sum_y - slope * sum_x) / n

            # Forecast for 30 days after the last recorded date
            last_days_diff = x[-1]
            target_days_diff = last_days_diff + 30
            follower_pred_30d = max(0.0, slope * target_days_diff + intercept)
            
            growth_per_day = slope
            if growth_per_day > 0.5:
                growth_trend_text = f"Strong upward trend (+{growth_per_day:.2f} followers/day)"
            elif growth_per_day < -0.5:
                growth_trend_text = f"Downward trend ({growth_per_day:.2f} followers/day)"
            else:
                growth_trend_text = "Stable growth"
        else:
            growth_trend_text = "Insufficient history for growth analysis"
            follower_pred_30d = latest_followers

        # 7. Engagement Prediction (Exponential moving average of the last 5 posts)
        # Sort posts chronologically
        post_ers_chrono = sorted(post_ers, key=lambda x: x[0].post_date)
        recent_ers = [x[1] for x in post_ers_chrono[-5:]]
        if recent_ers:
            # Simple weighted average prioritizing recency
            weights = list(range(1, len(recent_ers) + 1))
            weighted_sum = sum(val * w for val, w in zip(recent_ers, weights))
            eng_pred_next = weighted_sum / sum(weights)
        else:
            eng_pred_next = avg_engagement

        return {
            "best_post": best_post,
            "worst_post": worst_post,
            "best_day": best_day,
            "best_month": best_month,
            "best_frequency": best_freq_text,
            "avg_engagement": avg_engagement,
            "growth_trend": growth_trend_text,
            "follower_prediction_30d": int(round(follower_pred_30d)),
            "engagement_prediction_next": eng_pred_next
        }
