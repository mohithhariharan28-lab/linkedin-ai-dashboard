import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from src.database.repository import LinkedInRepository
from src.database.models import PostSnapshot, FollowerHistoryRecord
from src.ai.insights_service import AIInsightsService
from src.ai.recommendations import AIRecommendationsService
from src.utils.logger import setup_logger

logger = setup_logger("utils.notifications")

class NotificationGenerator:
    """Calculates daily and monthly changes and outputs summary notification files."""

    def __init__(self, repository: LinkedInRepository) -> None:
        """Initializes the notification generator.

        Args:
            repository: Database repository instance.
        """
        self.repository = repository
        self.insights_service = AIInsightsService(repository)
        self.recommendations_service = AIRecommendationsService(repository)
        
        project_root = Path(__file__).resolve().parent.parent.parent
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_summaries(self) -> Tuple[str, str]:
        """Generates both daily and monthly Markdown summary notifications.

        Returns:
            Tuple[str, str]: Paths to daily_summary.md and monthly_summary.md.
        """
        logger.info("Generating daily and monthly summaries...")
        
        # Load all history
        posts = self.repository.get_all_posts()
        follower_history = sorted(self.repository.get_follower_history(), key=lambda h: h.date)
        latest_followers = self.repository.get_latest_followers()
        
        insights = self.insights_service.get_insights()
        recs = self.recommendations_service.generate_recommendations()

        now = datetime.utcnow()

        # ----------------------------------------------------
        # 1. DAILY SUMMARY
        # ----------------------------------------------------
        daily_followers_delta = 0
        if len(follower_history) >= 2:
            # Compare latest with yesterday or previous entry
            daily_followers_delta = follower_history[-1].followers - follower_history[-2].followers

        # Find posts in the last 24 hours
        daily_posts: List[PostSnapshot] = []
        for p in posts:
            try:
                p_dt = datetime.fromisoformat(p.post_date)
                if now - p_dt <= timedelta(hours=24):
                    daily_posts.append(p)
            except ValueError:
                pass

        daily_new_posts_count = len(daily_posts)
        daily_top_post = None
        if daily_posts:
            # Sort by likes
            daily_top_post = sorted(daily_posts, key=lambda x: x.likes, reverse=True)[0]
        else:
            daily_top_post = insights["best_post"]

        daily_path = self.reports_dir / "daily_summary.md"
        daily_content = f"""# LinkedIn Daily Execution Summary
*Generated on {now.strftime("%Y-%m-%d %H:%M:%S UTC")}*

---

## Brand Snapshot (Last 24 Hours)

- **Total Followers**: {latest_followers:,} ({'+' if daily_followers_delta >= 0 else ''}{daily_followers_delta} followers today)
- **New Posts Published**: {daily_new_posts_count}
- **Overall Growth Trend**: {insights["growth_trend"]}

---

## Daily Highlight Post
"""
        if daily_top_post:
            snippet = (daily_top_post.post_text or "").replace('\n', ' ')[:100] + "..."
            daily_content += f"""
- **Post text**: *"{snippet}"*
- **Metrics**: {daily_top_post.likes} Likes | {daily_top_post.comments} Comments | {daily_top_post.reposts} Reposts
- **Link**: [View LinkedIn Post]({daily_top_post.post_url})
"""
        else:
            daily_content += "\nNo posts published in the last 24 hours.\n"

        daily_content += f"""
---

## Actionable AI Tips for Today
- **Best time to publish today**: **{recs["best_time_slot"]}**
- **Recommended hashtags to include**: {', '.join([h['tag'] for h in recs['top_hashtags'][:3]]) if recs['top_hashtags'] else '#AI, #Careers'}
- **Focus category**: **{recs["best_category"]}**
"""
        
        with open(daily_path, "w", encoding="utf-8") as f:
            f.write(daily_content)
        logger.info(f"Daily summary saved to {daily_path}")

        # ----------------------------------------------------
        # 2. MONTHLY SUMMARY
        # ----------------------------------------------------
        monthly_followers_delta = 0
        if len(follower_history) >= 2:
            # Find closest date to 30 days ago
            target_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            base_rec = follower_history[0]
            for h in follower_history:
                if h.date <= target_date:
                    base_rec = h
                else:
                    break
            monthly_followers_delta = latest_followers - base_rec.followers

        # Find posts in the last 30 days
        monthly_posts: List[PostSnapshot] = []
        for p in posts:
            try:
                p_dt = datetime.fromisoformat(p.post_date)
                if now - p_dt <= timedelta(days=30):
                    monthly_posts.append(p)
            except ValueError:
                pass

        monthly_new_posts_count = len(monthly_posts)
        monthly_top_post = None
        if monthly_posts:
            monthly_top_post = sorted(monthly_posts, key=lambda x: x.likes, reverse=True)[0]
        else:
            monthly_top_post = insights["best_post"]

        monthly_path = self.reports_dir / "monthly_summary.md"
        monthly_content = f"""# LinkedIn Monthly Executive Summary
*Generated on {now.strftime("%B %Y")}*

---

## Brand Snapshot (Last 30 Days)

- **Total Followers**: {latest_followers:,} ({'+' if monthly_followers_delta >= 0 else ''}{monthly_followers_delta} followers this month)
- **New Posts Published**: {monthly_new_posts_count}
- **Average Engagement Rate**: {insights["avg_engagement"]:.2f}%
- **AI 30-Day Follower Projection**: **{insights["follower_prediction_30d"]:,}** followers

---

## Monthly Top Performing Post
"""
        if monthly_top_post:
            snippet = (monthly_top_post.post_text or "").replace('\n', ' ')[:120] + "..."
            monthly_content += f"""
- **Post text**: *"{snippet}"*
- **Metrics**: {monthly_top_post.likes} Likes | {monthly_top_post.comments} Comments | {monthly_top_post.reposts} Reposts
- **Link**: [View LinkedIn Post]({monthly_top_post.post_url})
"""
        else:
            monthly_content += "\nNo posts published in the last 30 days.\n"

        monthly_content += f"""
---

## Strategic AI Recommendations
1. **Optimize Schedule**: Target your posts on **{insights["best_day"]}** during the **{recs["best_time_slot"]}** slot for highest engagement.
2. **Optimal Length**: Format content to **{recs["best_content_length"]}** length.
3. **Category Theme**: Write updates focusing on **{recs["best_category"]}** themes.
4. **Hashtags Strategy**: Prioritize utilizing these tags: {', '.join([h['tag'] for h in recs['top_hashtags'][:5]]) if recs['top_hashtags'] else '#AI, #Internship'}
"""
        
        with open(monthly_path, "w", encoding="utf-8") as f:
            f.write(monthly_content)
        logger.info(f"Monthly summary saved to {monthly_path}")

        return str(daily_path), str(monthly_path)
