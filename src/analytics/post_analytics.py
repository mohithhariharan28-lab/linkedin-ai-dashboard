import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.database.repository import LinkedInRepository
from src.database.models import (
    PostSnapshot, FollowerHistoryRecord, AnalyticsSummary, MonthlyStatistics, PostRanking
)
from src.utils.logger import setup_logger

logger = setup_logger("analytics.post_analytics")

class PostAnalyticsService:
    """Computes advanced analytics and performance metrics from LinkedIn database tables."""

    def __init__(self, repository: LinkedInRepository) -> None:
        """Initializes the analytics service.

        Args:
            repository: Database repository instance.
        """
        self.repository = repository

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculates all requested post, monthly stats, rankings, and growth analytics.

        Returns:
            Dict[str, Any]: Compiled analytics results containing structured models and raw reports.
        """
        logger.info("Computing LinkedIn Analytics Engine metrics...")
        
        posts: List[PostSnapshot] = self.repository.get_all_posts()
        followers: int = self.repository.get_latest_followers()
        follower_history: List[FollowerHistoryRecord] = self.repository.get_follower_history()
        
        computed_at = datetime.utcnow().isoformat()
        
        # 1. Base Summary Init
        summary = {
            "total_followers": followers,
            "follower_growth_pct": 0.0,
            "total_posts": len(posts),
            "total_likes": 0,
            "total_comments": 0,
            "total_reposts": 0,
            "avg_engagement_rate": 0.0,
            "best_post_id": "N/A",
            "worst_post_id": "N/A",
            "posting_frequency_per_week": 0.0,
            "avg_days_between_posts": 0.0,
            "weekly_growth_pct": 0.0,
            "monthly_growth_pct": 0.0
        }

        if not posts:
            logger.warning("No posts found in SQLite. Returning empty analytics metrics.")
            return {
                "summary": AnalyticsSummary(**summary, computed_at=computed_at),
                "monthly_statistics": [],
                "post_rankings": [],
                "posts_per_weekday": {},
                "posts_per_month": {}
            }

        # 2. Compute Follower Growths (Total, Weekly, Monthly)
        if len(follower_history) > 1:
            # Overall Growth
            oldest_f = follower_history[0].followers
            newest_f = follower_history[-1].followers
            if oldest_f > 0:
                summary["follower_growth_pct"] = ((newest_f - oldest_f) / oldest_f) * 100.0
                
            # Weekly Growth (over last 7 days)
            newest_dt = datetime.strptime(follower_history[-1].date, "%Y-%m-%d")
            weekly_target_dt = newest_dt - timedelta(days=7)
            
            weekly_old_rec = None
            weekly_min_diff = None
            for rec in follower_history[:-1]:
                rec_dt = datetime.strptime(rec.date, "%Y-%m-%d")
                diff = abs((rec_dt - weekly_target_dt).days)
                if weekly_min_diff is None or diff < weekly_min_diff:
                    weekly_min_diff = diff
                    weekly_old_rec = rec
            if weekly_old_rec and weekly_old_rec.followers > 0:
                summary["weekly_growth_pct"] = ((newest_f - weekly_old_rec.followers) / weekly_old_rec.followers) * 100.0
                
            # Monthly Growth (over last 30 days)
            monthly_target_dt = newest_dt - timedelta(days=30)
            
            monthly_old_rec = None
            monthly_min_diff = None
            for rec in follower_history[:-1]:
                rec_dt = datetime.strptime(rec.date, "%Y-%m-%d")
                diff = abs((rec_dt - monthly_target_dt).days)
                if monthly_min_diff is None or diff < monthly_min_diff:
                    monthly_min_diff = diff
                    monthly_old_rec = rec
            if monthly_old_rec and monthly_old_rec.followers > 0:
                summary["monthly_growth_pct"] = ((newest_f - monthly_old_rec.followers) / monthly_old_rec.followers) * 100.0

        # 3. Calculate post reactions and engagement rates
        total_likes = 0
        total_comments = 0
        total_reposts = 0
        total_er = 0.0
        
        best_post: Optional[PostSnapshot] = None
        worst_post: Optional[PostSnapshot] = None
        
        posts_per_weekday = {}
        posts_per_month = {}
        
        # Monthly grouping structures
        # Group posts by YYYY-MM
        monthly_groups: Dict[str, Dict[str, Any]] = {}

        for post in posts:
            total_likes += post.likes
            total_comments += post.comments
            total_reposts += post.reposts
            
            # Engagement Rate
            reactions = post.likes + post.comments + post.reposts
            denom = post.impressions if (post.impressions and post.impressions > 0) else followers
            er = (reactions / denom * 100.0) if denom > 0 else 0.0
            post.engagement_rate = er
            self.repository.update_post_engagement_rate(post.linkedin_post_id, er)
            total_er += er
            
            # Best / Worst Post
            if best_post is None or er > best_post.engagement_rate:
                best_post = post
            if worst_post is None or er < worst_post.engagement_rate:
                worst_post = post
                
            # Weekday Counts
            wd = post.weekday
            posts_per_weekday[wd] = posts_per_weekday.get(wd, 0) + 1
            
            # Month Counts
            m_name = post.month
            posts_per_month[m_name] = posts_per_month.get(m_name, 0) + 1
            
            # Monthly grouping details (using YYYY-MM format)
            try:
                dt = datetime.fromisoformat(post.post_date)
                group_key = dt.strftime("%Y-%m")
                month_name = dt.strftime("%B")
                year_val = dt.year
            except ValueError:
                group_key = f"{post.year}-{post.month[:3]}"
                month_name = post.month
                year_val = post.year
                
            if group_key not in monthly_groups:
                monthly_groups[group_key] = {
                    "year": year_val,
                    "month": month_name,
                    "post_count": 0,
                    "likes_count": 0,
                    "comments_count": 0,
                    "reposts_count": 0
                }
            monthly_groups[group_key]["post_count"] += 1
            monthly_groups[group_key]["likes_count"] += post.likes
            monthly_groups[group_key]["comments_count"] += post.comments
            monthly_groups[group_key]["reposts_count"] += post.reposts

        summary["total_likes"] = total_likes
        summary["total_comments"] = total_comments
        summary["total_reposts"] = total_reposts
        summary["avg_engagement_rate"] = total_er / len(posts)
        
        if best_post:
            summary["best_post_id"] = best_post.linkedin_post_id
        if worst_post:
            summary["worst_post_id"] = worst_post.linkedin_post_id

        # 4. Posting Span & Frequency
        posts_chronological = sorted(posts, key=lambda p: p.post_date)
        if len(posts_chronological) > 1:
            try:
                d1 = datetime.fromisoformat(posts_chronological[0].post_date)
                d2 = datetime.fromisoformat(posts_chronological[-1].post_date)
                total_days = (d2 - d1).days
                if total_days > 0:
                    summary["posting_frequency_per_week"] = len(posts) / (total_days / 7.0)
                    
                # Days between consecutive posts
                diffs = [(datetime.fromisoformat(posts_chronological[i].post_date) - 
                          datetime.fromisoformat(posts_chronological[i-1].post_date)).days 
                         for i in range(1, len(posts_chronological))]
                if diffs:
                    summary["avg_days_between_posts"] = sum(diffs) / len(diffs)
            except ValueError:
                pass

        # 5. Build Monthly Statistics list (calculating Month-over-Month reaction growth)
        monthly_stats_list: List[MonthlyStatistics] = []
        sorted_keys = sorted(monthly_groups.keys())
        
        for idx, key in enumerate(sorted_keys):
            g = monthly_groups[key]
            mom_growth_pct = 0.0
            
            # Reactions growth compared to the previous month
            if idx > 0:
                prev_key = sorted_keys[idx - 1]
                prev_g = monthly_groups[prev_key]
                prev_reactions = prev_g["likes_count"] + prev_g["comments_count"] + prev_g["reposts_count"]
                curr_reactions = g["likes_count"] + g["comments_count"] + g["reposts_count"]
                if prev_reactions > 0:
                    mom_growth_pct = ((curr_reactions - prev_reactions) / prev_reactions) * 100.0
            
            monthly_stats_list.append(MonthlyStatistics(
                year=g["year"],
                month=g["month"],
                post_count=g["post_count"],
                likes_count=g["likes_count"],
                comments_count=g["comments_count"],
                reposts_count=g["reposts_count"],
                monthly_growth_pct=mom_growth_pct,
                computed_at=computed_at
            ))

        # 6. Rank Posts (by Likes, Comments, and Engagement rate)
        posts_by_likes = sorted(posts, key=lambda p: p.likes, reverse=True)
        posts_by_comments = sorted(posts, key=lambda p: p.comments, reverse=True)
        posts_by_er = sorted(posts, key=lambda p: p.engagement_rate, reverse=True)
        
        ranks = {p.linkedin_post_id: {"likes": 0, "comments": 0, "engagement": 0} for p in posts}
        
        for r_likes, p in enumerate(posts_by_likes, 1):
            ranks[p.linkedin_post_id]["likes"] = r_likes
        for r_comm, p in enumerate(posts_by_comments, 1):
            ranks[p.linkedin_post_id]["comments"] = r_comm
        for r_er, p in enumerate(posts_by_er, 1):
            ranks[p.linkedin_post_id]["engagement"] = r_er
            
        post_rankings_list: List[PostRanking] = []
        for pid, r in ranks.items():
            post_rankings_list.append(PostRanking(
                linkedin_post_id=pid,
                rank_by_likes=r["likes"],
                rank_by_comments=r["comments"],
                rank_by_engagement=r["engagement"],
                computed_at=computed_at
            ))

        # Assemble summary object
        summary_model = AnalyticsSummary(**summary, computed_at=computed_at)

        return {
            "summary": summary_model,
            "monthly_statistics": monthly_stats_list,
            "post_rankings": post_rankings_list,
            "posts_per_weekday": posts_per_weekday,
            "posts_per_month": posts_per_month
        }
