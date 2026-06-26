import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from src.database.repository import LinkedInRepository
from src.database.models import PostSnapshot
from src.ai.insights_service import AIInsightsService
from src.ai.recommendations import AIRecommendationsService
from src.utils.logger import setup_logger

logger = setup_logger("ai.report_generator")

class AIReportGenerator:
    """Generates monthly LinkedIn Analytics report with insights and recommendations."""

    def __init__(self, repository: LinkedInRepository) -> None:
        """Initializes the report generator.

        Args:
            repository: Database repository instance.
        """
        self.repository = repository
        self.insights_service = AIInsightsService(repository)
        self.recommendations_service = AIRecommendationsService(repository)
        
        project_root = Path(__file__).resolve().parent.parent.parent
        self.report_path = project_root / "reports" / "monthly_ai_report.md"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

    def generate_monthly_report(self) -> str:
        """Executes the AI services, formats the report, and writes it to disk.

        Returns:
            str: Path to the generated report file.
        """
        logger.info(f"Generating monthly AI report at {self.report_path}...")
        
        insights = self.insights_service.get_insights()
        recs = self.recommendations_service.generate_recommendations()
        
        latest_summary = self.repository.get_latest_analytics_summary()
        latest_profile = self.repository.get_latest_profile()
        posts = self.repository.get_all_posts()
        
        # 1. Prepare KPI Summary Data
        followers = latest_profile.followers if latest_profile else 0
        total_posts = len(posts)
        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        total_reposts = sum(p.reposts for p in posts)
        avg_er = insights["avg_engagement"]
        
        # Sort posts for rankings
        followers_denom = followers if followers > 0 else 1
        post_ers = []
        for p in posts:
            reactions = p.likes + p.comments + p.reposts
            er = (reactions / followers_denom) * 100.0
            post_ers.append((p, er))
            
        post_ers_sorted = sorted(post_ers, key=lambda x: x[1], reverse=True)
        top_5 = post_ers_sorted[:5]
        bottom_5 = post_ers_sorted[-5:]
        
        # Format timestamps
        current_date_str = datetime.utcnow().strftime("%B %d, %Y")
        
        report_content = f"""# LinkedIn AI Analytics Monthly Performance Report
*Generated on {current_date_str}*

---

## 1. Executive Summary

This monthly report details the LinkedIn personal brand performance. Over this execution period, the profile has shown a **{insights["growth_trend"]}**. The content strategy is primarily driven by **{recs["best_category"]}** themes, which represent the highest-performing content category. 

By analyzing the engagement characteristics of individual posts, we have formulated concrete recommendations to optimize timing, length, and topic tags to maximize future reach.

---

## 2. KPI Summary

The table below outlines the high-level indicators computed from the scraping snapshot history:

| Metric | Current Value | Monthly Growth % | Status |
| :--- | :--- | :--- | :--- |
| **Total Followers** | {followers:,} | {latest_summary.monthly_growth_pct if latest_summary else 0.0:.2f}% | Active |
| **Total Posts** | {total_posts} | N/A | Active |
| **Total Likes** | {total_likes:,} | N/A | Active |
| **Total Comments** | {total_comments} | N/A | Active |
| **Total Reposts** | {total_reposts} | N/A | Active |
| **Avg. Engagement Rate** | {avg_er:.2f}% | N/A | Optimized |

> [!NOTE]
> The Engagement Rate calculation is computed as: `(Likes + Comments + Reposts) / Followers * 100`.

---

## 3. Content Rankings

### Top 5 Performing Posts (By Engagement Rate)

| Rank | Post Snippet | Date | Likes | Comments | Engagement % | Link |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
"""

        for idx, (post, er) in enumerate(top_5, 1):
            snippet = (post.post_text or "").replace('\n', ' ')[:60] + "..."
            date_only = post.post_date.split('T')[0]
            report_content += f"| {idx} | {snippet} | {date_only} | {post.likes} | {post.comments} | {er:.2f}% | [View Post]({post.post_url}) |\n"

        report_content += """
### Bottom 5 Performing Posts (By Engagement Rate)

| Rank | Post Snippet | Date | Likes | Comments | Engagement % | Link |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
"""

        # Re-reverse bottom 5 so the worst is listed first
        for idx, (post, er) in enumerate(reversed(bottom_5), 1):
            snippet = (post.post_text or "").replace('\n', ' ')[:60] + "..."
            date_only = post.post_date.split('T')[0]
            report_content += f"| {idx} | {snippet} | {date_only} | {post.likes} | {post.comments} | {er:.2f}% | [View Post]({post.post_url}) |\n"

        # Predict future counts
        next_followers_goal = int(insights["follower_prediction_30d"])
        pred_er_next = insights["engagement_prediction_next"]

        report_content += f"""
---

## 4. Growth & Predictive Analysis

- **Follower Growth Trend**: {insights["growth_trend"]}
- **30-Day Follower Prediction**: Based on linear regression extrapolation, followers are projected to reach **{next_followers_goal:,}** in the next 30 days.
- **Next Post Engagement Forecast**: The engine predicts an engagement rate of **{pred_er_next:.2f}%** for the next post, assuming it aligns with recent format trends.

---

## 5. Content Optimization Recommendations

These recommendations are generated dynamically by correlating post texts and publication timestamps with overall reach:

### A. Posting Schedule
- **Best Day to Post**: **{insights["best_day"]}** (highest average engagement per post).
- **Best Time Slot**: **{recs["best_time_slot"]}**.
- **Suggested Frequency**: **{recs["suggested_frequency"]}** to maintain maximum algorithm visibility without saturating the feed.

### B. Content & Formats
- **Optimal Text Length**: **{recs["best_content_length"]}**.
- **Highest Performing Category**: **{recs["best_category"]}**. Focus on sharing prompt layouts, AI virtual internship experiences, and carrier progression milestones.

### C. Top Suggested Hashtags
Use these tags in upcoming posts to tap into historical engagement spikes:
"""

        if recs["top_hashtags"]:
            for item in recs["top_hashtags"]:
                report_content += f"- **{item['tag']}** (Used in {item['count']} posts, Avg. Engagement: {item['avg_engagement']:.2f}%)\n"
        else:
            report_content += "- No hashtags found in post history.\n"

        report_content += f"""
---

## 6. Next Month Actionable Goals

1. **Scheduling**: Schedule your primary weekly post on **{insights["best_day"]}** during the **{recs["best_time_slot"]}** window.
2. **Hashtag Mix**: Include at least 3 of your top-performing hashtags (like `{recs["top_hashtags"][0]["tag"] if recs["top_hashtags"] else "#AI"}`) in every career-related post.
3. **Format**: Format updates with **{recs["best_content_length"]}** length.
4. **Follower Target**: Aim to beat the statistical model's 30-day forecast of **{next_followers_goal:,}** followers.
"""

        # Write file
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        logger.info("Report compiled and written to disk successfully.")
        return str(self.report_path)
