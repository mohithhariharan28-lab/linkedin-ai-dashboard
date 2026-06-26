import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.database.repository import LinkedInRepository
from src.database.models import PostSnapshot
from src.utils.logger import setup_logger

logger = setup_logger("ai.recommendations")

class AIRecommendationsService:
    """Formulates actionable posting guidelines based on text content and timing analyses."""

    def __init__(self, repository: LinkedInRepository) -> None:
        """Initializes the recommendations service.

        Args:
            repository: Database repository instance.
        """
        self.repository = repository

    def generate_recommendations(self) -> Dict[str, Any]:
        """Analyzes historical database records to produce targeted recommendations.

        Returns:
            Dict[str, Any]: Formulated recommendations data.
        """
        logger.info("Analyzing content and metadata for recommendations...")
        posts: List[PostSnapshot] = self.repository.get_all_posts()
        latest_followers = self.repository.get_latest_followers()
        followers_denom = latest_followers if latest_followers > 0 else 1

        if not posts:
            logger.warning("No posts in SQLite database. Returning default recommendations.")
            return {
                "best_time_slot": "Morning (08:00 AM - 12:00 PM)",
                "best_content_length": "Medium (150 - 600 characters)",
                "suggested_frequency": "2-3 times per week",
                "top_hashtags": [],
                "best_category": "Career & Tech Updates"
            }

        # Calculate engagement rates for all posts locally
        post_ers = []
        for post in posts:
            reactions = post.likes + post.comments + post.reposts
            er = (reactions / followers_denom) * 100.0
            post_ers.append((post, er))

        # 1. Best Time to Post (Hourly groups)
        time_slots = {
            "Morning (06:00 AM - 11:59 AM)": [],
            "Afternoon (12:00 PM - 04:59 PM)": [],
            "Evening (05:00 PM - 09:59 PM)": [],
            "Night (10:00 PM - 05:59 AM)": []
        }

        for post, er in post_ers:
            try:
                # E.g., '2026-06-25T14:24:32.678374'
                dt_str = post.post_date
                hour = int(dt_str.split('T')[1].split(':')[0])
            except (IndexError, ValueError):
                # Fallback to a default hour
                hour = 12

            if 6 <= hour < 12:
                time_slots["Morning (06:00 AM - 11:59 AM)"].append(er)
            elif 12 <= hour < 17:
                time_slots["Afternoon (12:00 PM - 04:59 PM)"].append(er)
            elif 17 <= hour < 22:
                time_slots["Evening (05:00 PM - 09:59 PM)"].append(er)
            else:
                time_slots["Night (10:00 PM - 05:59 AM)"].append(er)

        time_averages = {slot: sum(ers)/len(ers) for slot, ers in time_slots.items() if ers}
        best_time_slot = max(time_averages, key=time_averages.get) if time_averages else "Afternoon (12:00 PM - 04:59 PM)"

        # 2. Best Content Length (Short, Medium, Long)
        length_bins = {
            "Short (< 150 chars)": [],
            "Medium (150 - 600 chars)": [],
            "Long (> 600 chars)": []
        }

        for post, er in post_ers:
            txt_len = len(post.post_text) if post.post_text else 0
            if txt_len < 150:
                length_bins["Short (< 150 chars)"].append(er)
            elif 150 <= txt_len <= 600:
                length_bins["Medium (150 - 600 chars)"].append(er)
            else:
                length_bins["Long (> 600 chars)"].append(er)

        length_averages = {b: sum(ers)/len(ers) for b, ers in length_bins.items() if ers}
        best_content_length = max(length_averages, key=length_averages.get) if length_averages else "Medium (150 - 600 chars)"

        # 3. Suggested Posting Frequency
        # Analyze total active weeks and post counts per week
        post_dates_sorted = sorted([p.post_date for p in posts])
        try:
            d_start = datetime.fromisoformat(post_dates_sorted[0])
            d_end = datetime.fromisoformat(post_dates_sorted[-1])
            weeks_diff = max(1.0, (d_end - d_start).days / 7.0)
            avg_posts_per_week = len(posts) / weeks_diff
            if avg_posts_per_week > 4:
                suggested_frequency = "Daily (4-5 times per week)"
            elif avg_posts_per_week > 1.5:
                suggested_frequency = "Moderate (2-3 times per week)"
            else:
                suggested_frequency = "Weekly (1-2 times per week)"
        except (IndexError, ValueError):
            suggested_frequency = "Moderate (2-3 times per week)"

        # 4. Suggested Hashtags (Top Hashtags ranked by average engagement rate of posts containing them)
        hashtag_metrics: Dict[str, List[float]] = {}
        for post, er in post_ers:
            if not post.post_text:
                continue
            # Extract hashtags
            tags = re.findall(r"#(\w+)", post.post_text.lower())
            for tag in set(tags):  # Deduplicate per post
                hashtag_metrics.setdefault(tag, []).append(er)

        hashtag_reports = []
        for tag, ers in hashtag_metrics.items():
            hashtag_reports.append({
                "tag": f"#{tag}",
                "count": len(ers),
                "avg_engagement": sum(ers) / len(ers)
            })

        # Rank hashtags: minimum occurrence of 1, sort by engagement rate descending, then count descending
        top_hashtags = sorted(hashtag_reports, key=lambda x: (x["avg_engagement"], x["count"]), reverse=True)[:8]

        # 5. Content Categories that perform best
        # Map posts to categories based on keyword profiles
        categories = {
            "Career & Internships": [],
            "AI & Prompt Engineering": [],
            "Academic & Continuous Learning": [],
            "General Professional updates": []
        }

        for post, er in post_ers:
            text = (post.post_text or "").lower()
            if any(k in text for k in ["intern", "career", "job", "opportunity", "hired", "select"]):
                categories["Career & Internships"].append(er)
            elif any(k in text for k in ["ai", "prompt", "artificial", "intelligence", "python", "code", "engineering"]):
                categories["AI & Prompt Engineering"].append(er)
            elif any(k in text for k in ["student", "college", "university", "classroom", "learn", "study", "academic"]):
                categories["Academic & Continuous Learning"].append(er)
            else:
                categories["General Professional updates"].append(er)

        cat_averages = {cat: sum(ers)/len(ers) for cat, ers in categories.items() if ers}
        best_category = max(cat_averages, key=cat_averages.get) if cat_averages else "AI & Prompt Engineering"

        return {
            "best_time_slot": best_time_slot,
            "best_content_length": best_content_length,
            "suggested_frequency": suggested_frequency,
            "top_hashtags": top_hashtags,
            "best_category": best_category
        }
