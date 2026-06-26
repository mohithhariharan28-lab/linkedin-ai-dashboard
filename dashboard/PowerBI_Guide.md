# Power BI Data Connection & Refresh Guide

This guide details how to import the generated CSV reports into Microsoft Power BI Desktop, configure data types, model relationships, and set up automated data refreshes.

---

## 1. Connecting Power BI to the CSV Reports

We export seven reporting files to the `reports/` folder in the project directory. Power BI should connect to these CSVs using either a local folder path or a parameterized project path (recommended for portability).

### Step-by-Step Connection Instructions:
1. Open **Power BI Desktop**.
2. Click **Get Data** on the Home ribbon and select **Text/CSV**.
3. Navigate to your project directory:
   `C:\Users\aparn\.gemini\antigravity\scratch\linkedin_ai_dashboard\reports\`
4. Select one of the CSV files (e.g., `dashboard_overview.csv`) and click **Open**.
5. In the preview dialog box, click **Transform Data** (do not click Load directly). This opens the **Power Query Editor**.
6. Repeat this process to import all 7 CSV files:
   - `dashboard_overview.csv`
   - `followers_growth.csv`
   - `post_performance.csv`
   - `monthly_activity.csv`
   - `engagement_trend.csv`
   - `top_posts.csv`
   - `posting_frequency.csv`

---

## 2. Power Query Data Transformation & Types

For accurate calculations, configure columns with the correct data types inside the Power Query Editor.

| Query / Table Name | Column | Data Type | Notes |
| :--- | :--- | :--- | :--- |
| **dashboard_overview** | `computed_at` | Date/Time | ISO Timestamp |
| | `total_followers` | Whole Number | |
| | `follower_growth_pct` | Percentage | Divide by 100 if decimal formatting is needed |
| | `total_posts` | Whole Number | |
| | `total_likes` | Whole Number | |
| | `total_comments` | Whole Number | |
| | `total_reposts` | Whole Number | |
| | `avg_engagement_rate` | Percentage | Raw float (e.g. 1.57 is 1.57% or 0.0157 depending on format) |
| **followers_growth** | `date` | Date | Format: YYYY-MM-DD |
| | `followers` | Whole Number | |
| **post_performance** | `post_date` | Date/Time | ISO Timestamp |
| | `likes`, `comments`, `reposts` | Whole Number | |
| | `engagement_rate` | Percentage / Decimal | Raw engagement rate |
| **monthly_activity** | `computed_at` | Date/Time | |
| | `year` | Whole Number | |
| | `post_count`, `likes_count` | Whole Number | |
| | `monthly_growth_pct` | Percentage | MoM reaction growth |
| **engagement_trend** | `date` | Date | YYYY-MM-DD |
| | `likes`, `comments` | Whole Number | |
| | `engagement_rate` | Percentage | |

*Tip: For any `engagement_rate` or percentage growth columns (e.g. `follower_growth_pct`), ensure they are formatted as **Percentage** in Power BI (Modeling Ribbon -> Format -> Percentage).*

---

## 3. Data Model Relationships

Since the pipeline outputs pre-calculated, dashboard-ready reporting tables, the model is simple and highly performant. 

We recommend implementing a **Star/Snowflake Schema** where applicable, or utilizing a shared **Date Dimension Table** for time intelligence:

1. **Date Table (Calendar)**:
   Create a standard DAX Calendar table to bind all dates together:
   ```dax
   Calendar = CALENDARAUTO()
   ```
2. **Relationships**:
   - Link `Calendar[Date]` (1) to `followers_growth[date]` (many).
   - Link `Calendar[Date]` (1) to `post_performance[post_date]` (many) (convert `post_date` to Date first in Power Query).
   - Link `Calendar[Date]` (1) to `engagement_trend[date]` (many).

---

## 4. Configuring Automated Refresh

To keep the dashboard updated automatically with the latest scraping runs, configure a refresh pipeline.

### Option A: Power BI Personal Gateway (Local File Refresh)
If your Power BI dashboard will run locally or you want to publish it to the Power BI Service while pulling data from your local computer:
1. Download and install the **Power BI Personal Gateway** on your machine.
2. Sign in with your Power BI Service credentials.
3. Once published to the service, go to the **Dataset Settings** for your report.
4. Expand **Gateway connection**, verify your Personal Gateway is online, and map your local folder credentials (Windows credentials to read directory `C:\Users\aparn\...`).
5. Configure a **Scheduled Refresh** (e.g., daily at 8:00 AM) to run after the scraper has finished executing.

### Option B: Cloud Storage Sync (OneDrive / SharePoint) - Recommended
To avoid setting up a local gateway, export the CSVs directly to a synchronized OneDrive or SharePoint folder:
1. Point the Python export pipeline to write CSV reports into your local OneDrive folder (e.g., `C:\Users\aparn\OneDrive\LinkedInReports`).
2. In Power BI, connect using the **Web URL** of those CSV files stored on OneDrive/SharePoint rather than local file paths.
3. This allows the Power BI Service to refresh the dataset directly from the cloud without requiring an active local gateway.
