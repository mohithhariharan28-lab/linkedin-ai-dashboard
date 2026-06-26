# Changelog
All notable changes to the LinkedIn AI Analytics Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] - 2026-06-25

### Added
- **Phase 3 (Database & Profile Scraper)**: SQLite database `data/linkedin.db` schema and repository pattern class to save profile snapshots and follower history records.
- **Phase 4 (Post Scraper Engine)**: Playwright-based scraper to scroll and extract post interactions, reactions, day/weekday splits, and IDs.
- **Phase 5 (Analytics Engine)**: SQL-driven analytics and statistical updates calculation (growth rates, Best/Worst posts, posting frequencies) stored in SQLite tables.
- **Phase 6 (REST API)**: FastAPI layer exposing endpoints for profile data, follower timelines, top engagement posts, and summary lists.
- **Phase 6 (Power BI Data Pipeline)**: Auto-updating reporting SQL views and a CSV export service saving report files to `reports/` folder.
- **Phase 7 & 8 (Power BI Dashboard Builder)**: Visual styling coordinates, custom dark JSON theme, and SVG vector icons.
- **Phase 9 (AI Insights Engine)**: Extrapolating predictions for follower growth (linear regression) and next post engagement (weighted averages). Writes `reports/monthly_ai_report.md`.
- **Phase 10 (Production Automation)**: Implemented background scheduler loop, notification summaries (`daily_summary.md` and `monthly_summary.md`), and comprehensive user manuals.
