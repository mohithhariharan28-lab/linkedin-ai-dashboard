# Dashboard Layout Grid & Visual Coordinate Map

This guide provides pixel-perfect layout coordinates (X, Y, Width, Height) based on the standard Power BI 16:9 canvas size of **1280 x 720 pixels**.

---

## Canvas Settings
- **Page Size**: `16:9` (Width: 1280px, Height: 720px)
- **Margins**: Top/Bottom: 20px, Left/Right: 20px
- **Grid Spacing**: 10px snap-to-grid enabled

---

## Page 1 – Executive Overview
Focuses on general high-level audience metrics, post volumes, and interactions.

### Top Navigation & Header
- **Page Title Box**: `X = 20`, `Y = 20`, `W = 800`, `H = 40`
  - Text: "LinkedIn Executive Analytics Overview"
- **Date/Range Slicer**: `X = 960`, `Y = 20`, `W = 300`, `H = 40`

### KPI Cards Block (Horizontal Layout, Top)
- **KPI Card 1: Total Followers**
  - `X = 20`, `Y = 80`, `W = 190`, `H = 80`
- **KPI Card 2: Followers Growth %**
  - `X = 230`, `Y = 80`, `W = 190`, `H = 80`
- **KPI Card 3: Total Posts**
  - `X = 440`, `Y = 80`, `W = 190`, `H = 80`
- **KPI Card 4: Total Likes**
  - `X = 650`, `Y = 80`, `W = 190`, `H = 80`
- **KPI Card 5: Total Comments**
  - `X = 860`, `Y = 80`, `W = 190`, `H = 80`
- **KPI Card 6: Avg Engagement Rate**
  - `X = 1070`, `Y = 80`, `W = 190`, `H = 80`

### Charts Area (Middle)
- **Chart 1: Followers Growth Trend (Line Chart)**
  - `X = 20`, `Y = 180`, `W = 610`, `H = 240`
  - *Data Source*: `followers_growth.csv` (`date` vs `followers`)
- **Chart 2: Monthly Posting Activity (Column Chart)**
  - `X = 650`, `Y = 180`, `W = 610`, `H = 240`
  - *Data Source*: `monthly_activity.csv` (`month` vs `post_count`)

### Chronological Engagement Area (Bottom)
- **Chart 3: Engagement Rate Trend (Line / Area Chart)**
  - `X = 20`, `Y = 440`, `W = 1240`, `H = 260`
  - *Data Source*: `engagement_trend.csv` (`date` vs `engagement_rate` with legend `media_type`)

---

## Page 2 – Posts
Detailed page breaking down reaction trends, weekday postings, and post rankings.

### Header & Slicers Block
- **Page Title**: `X = 20`, `Y = 20`, `W = 400`, `H = 40` (Text: "LinkedIn Post Analysis")
- **Year Slicer**: `X = 540`, `Y = 20`, `W = 200`, `H = 40`
- **Month Slicer**: `X = 760`, `Y = 20`, `W = 200`, `H = 40`
- **Media Type Slicer**: `X = 980`, `Y = 20`, `W = 280`, `H = 40`

### First Row Charts (Reactions & Volumes)
- **Chart 1: Likes by Month (Clustered Column Chart)**
  - `X = 20`, `Y = 80`, `W = 400`, `H = 200`
  - *Data Source*: `monthly_activity.csv` (`month` vs `likes_count`)
- **Chart 2: Comments by Month (Clustered Column Chart)**
  - `X = 440`, `Y = 80`, `W = 400`, `H = 200`
  - *Data Source*: `monthly_activity.csv` (`month` vs `comments_count`)
- **Chart 3: Posts by Month (Clustered Column Chart)**
  - `X = 860`, `Y = 80`, `W = 400`, `H = 200`
  - *Data Source*: `monthly_activity.csv` (`month` vs `post_count`)

### Second Row Charts (Weekday Splits & Rankings)
- **Chart 4: Posts by Weekday (Clustered Column Chart)**
  - `X = 20`, `Y = 300`, `W = 400`, `H = 180`
  - *Data Source*: `posting_frequency.csv` (`weekday` vs `post_count`)
- **Table 5: Top 10 Performing Posts (Table Visual)**
  - `X = 440`, `Y = 300`, `W = 820`, `H = 180`
  - *Data Source*: `top_posts.csv` (Show: text, date, media_type, likes, engagement_rate; sorted desc by engagement_rate)

### Third Row Charts (Bottom Listings)
- **Table 6: Bottom 10 Performing Posts (Table Visual)**
  - `X = 440`, `Y = 500`, `W = 820`, `H = 200`
  - *Data Source*: `post_performance.csv` (Filtered to bottom 10 using Filter Pane Top-N filter by engagement_rate ascending)
- **Chart 7: Posting Frequency Matrix (Matrix Table)**
  - `X = 20`, `Y = 500`, `W = 400`, `H = 200`
  - *Data Source*: `posting_frequency.csv` (Rows: `weekday`, Columns/Values: `post_count`, `avg_likes`, `avg_comments`)

---

## Page 3 – Profile
Highlights CV credentials and timeline records extracted from the profile snapshot.

### Header Block
- **Page Title**: `X = 20`, `Y = 20`, `W = 800`, `H = 40` (Text: "Scraped Profile Details")

### Profile Metadata Panel (Left Card Block)
- **Profile Card Visual (Multi-row Card)**
  - `X = 20`, `Y = 80`, `W = 380`, `H = 620`
  - Fields:
    - **Name**: `profiles[full_name]`
    - **Headline**: `profiles[headline]`
    - **Current Company**: `profiles[current_company]`
    - **Followers**: `profiles[followers]`
    - **Connections**: `profiles[connections]`
    - **Profile URL**: `profiles[profile_url]`
    - **Location**: `profiles[location]`

### Timeline Panel (Right Block)
- **Experience Timeline Table (Table visual)**
  - `X = 420`, `Y = 80`, `W = 840`, `H = 300`
  - *Data Source*: Expanded `experience` table (Title, Company, Date Range, Location, Description)
- **Education Timeline Table (Table visual)**
  - `X = 420`, `Y = 400`, `W = 840`, `H = 300`
  - *Data Source*: Expanded `education` table (School, Degree, Field of Study, Years)

---

## Page 4 – AI Insights (New Layout Panel)
Dedicated space for computed highlights and predictive analytics based on the scraping history.

### Header Block
- **Page Title**: `X = 20`, `Y = 20`, `W = 800`, `H = 40` (Text: "Predictive Analytics & AI Insights")

### Best Timing Insights (Top Cards)
- **Card 1: Best Posting Time**
  - `X = 20`, `Y = 80`, `W = 380`, `H = 140`
  - *Visual/Placeholder*: Card connected to best hourly metrics (e.g. 9:00 AM, retrieved by evaluating peak reactions hour).
- **Card 2: Best Posting Day**
  - `X = 420`, `Y = 80`, `W = 380`, `H = 140`
  - *Visual/Placeholder*: Card connected to best weekday metrics (e.g. Wednesday, retrieved from `posting_frequency.csv` sorted by `avg_likes` desc).
- **Card 3: Growth Prediction (AI Smart Narrative / KPI)**
  - `X = 820`, `Y = 80`, `W = 440`, `H = 140`
  - *Visual*: Power BI **Key Influencers** or **Smart Narrative** visual tracking follower trajectories to predict next month's follower count.

### Text Summaries & Recommendations (Bottom Panels)
- **Smart Narrative Panel: Monthly Summary (Text Visual)**
  - `X = 20`, `Y = 240`, `W = 590`, `H = 460`
  - *Data Source/Binding*: Drag `dashboard_overview` columns into a text block. E.g.: "You published [total_posts] posts this month with an average engagement of [avg_engagement_rate]. Followers grew by [follower_growth_pct]% to [total_followers]."
- **Actionable AI Recommendations Grid (Table / Card Visual)**
  - `X = 630`, `Y = 240`, `W = 630`, `H = 460`
  - *Visual/Binding*: Table showcasing dynamic recommendations:
    - If average engagement < 2% -> "Consider using Carousel/Document media types; they have 1.5x higher engagement rate in your history."
    - If weekday posts count on Wednesday is 0 -> "Wednesday is your highest engagement day (avg likes: [avg_likes]), consider posting then."

---

## Extended Canvas Visual Layout Sections

### Page 1 – Executive Overview (Expanded Canvas: 1280 x 1080 px)
- **Existing Page Layout (0px to 720px Y-height)**: Remains exactly as documented in original Page 1 sections.
- **Scroll Extension Section (720px to 1080px Y-height)**:
  - **Chart 4: Monthly Posting Trends (Line Chart)**
    - `X = 20`, `Y = 740`, `W = 390`, `H = 300`
    - *Data Source*: `monthly_activity.csv` (`month` vs `post_count`)
  - **Chart 5: Audience Growth Trend (Line Chart)**
    - `X = 430`, `Y = 740`, `W = 390`, `H = 300`
    - *Data Source*: `followers_growth.csv` (`date` vs `followers`)
  - **Chart 6: Chronological Engagement Rate (Line Chart)**
    - `X = 840`, `Y = 740`, `W = 420`, `H = 300`
    - *Data Source*: `engagement_trend.csv` (`date` vs `engagement_rate`)

### Page 2 – Posts (Expanded Canvas: 1280 x 1080 px)
- **Existing Page Layout (0px to 720px Y-height)**: Remains exactly as documented in original Page 2 sections.
- **Scroll Extension Section (720px to 1080px Y-height)**:
  - **Chart 8: Top 10 Performing Posts (Bar Chart)**
    - `X = 20`, `Y = 740`, `W = 780`, `H = 300`
    - *Data Source*: `top_posts.csv` (`post_text` vs `engagement_rate`; sorted descending)
  - **Chart 9: Content Type Distribution (Donut Chart)**
    - `X = 820`, `Y = 740`, `W = 440`, `H = 300`
    - *Data Source*: `post_performance.csv` (Legend: `media_type`, Values: Count of `linkedin_post_id`)

---

## Page 5 – Network & Connections (Canvas: 1280 x 1080 px)
Exposes personal network metrics, company distribution, industry classification, location distribution, and connection lists.

### Top Navigation & Header
- **Page Title Box**: `X = 20`, `Y = 20`, `W = 800`, `H = 40` (Text: "LinkedIn Network & Connections")
- **Search Slicer**: `X = 960`, `Y = 20`, `W = 300`, `H = 40`

### KPI Cards Block (Horizontal Layout, Top)
- **KPI Card 1: Total Connections**
  - `X = 20`, `Y = 80`, `W = 600`, `H = 80`
  - *Data Source*: `_Measures[Total Connections]` (derived from `pbi_total_connections.csv`)
- **KPI Card 2: New Connections (This Month)**
  - `X = 650`, `Y = 80`, `W = 610`, `H = 80`
  - *Data Source*: `_Measures[New Connections]` (derived from `pbi_total_connections.csv`)

### Searchable Connection Directory (Middle Section)
- **Table 1: Connection Members Table (Searchable Table)**
  - `X = 20`, `Y = 180`, `W = 1240`, `H = 320`
  - *Data Source*: `pbi_connection_directory.csv` (Displaying: `full_name`, `headline`, `company`, `location`, `connected_date`, `profile_url`)

### Network Analytics (Bottom Section)
- **Chart 2: Connections by Company (Horizontal Bar Chart)**
  - `X = 20`, `Y = 520`, `W = 400`, `H = 500`
  - *Data Source*: `pbi_company_distribution.csv` (`company` vs `connection_count`)
- **Chart 3: Connections by Industry (Treemap)**
  - `X = 440`, `Y = 520`, `W = 400`, `H = 500`
  - *Data Source*: `pbi_industry_distribution.csv` (`industry` vs `connection_count`)
  - *Note*: If no industry data is available, display "No connection data available" label.
- **Chart 4: Connections by Location (Map)**
  - `X = 860`, `Y = 520`, `W = 400`, `H = 500`
  - *Data Source*: `pbi_connection_directory.csv` (Geocoded bubble map with location names as Bubble Location, Bubble size by Count)

