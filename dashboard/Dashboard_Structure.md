# Power BI Dashboard Structure & Layout

This document outlines the visual structure, layout, and user experience guidelines for the 4 LinkedIn Analytics dashboard pages.

---

## Global Design Guidelines
- **Color Palette**: Dark Theme (Premium Aesthetics)
  - Background: Deep Charcoal/Navy (`#121824` / `#1A202C`)
  - Accent / Primary: LinkedIn Blue (`#0A66C2`) or Royal Blue (`#2B6CB0`)
  - Text / Data Labels: Off-White (`#F7FAFC`)
  - Secondary Accents: Emerald Green for growth indicators (`#48BB78`), Red for drop metrics (`#F56565`)
- **Typography**: Modern Sans-Serif (e.g., `Segoe UI`, `Segoe UI Semibold`, or `Inter`)
- **Interactions**: Cross-filtering enabled between visuals. Selecting a specific post or month should slice all other charts on the page.

---

## Page 1 – Executive Overview
Focuses on high-level KPIs and chronological growth and posting volume trends.

### Visual Layout Grid

```
+-----------------------------------------------------------------------------------+
|  [Logo / Title: LinkedIn Exec Overview]              [Slicer: Date Range / Year]  |
+-----------------------------------------------------------------------------------+
|  [KPI Card]        [KPI Card]      [KPI Card]      [KPI Card]      [KPI Card]     |
|  Total Followers   Followers Growth  Total Posts   Total Likes     Avg Eng. Rate  |
+-----------------------------------------------------------------------------------+
|  [Chart 1: Line Chart]                             [Chart 2: Column Chart]        |
|  Follower Growth Trend (Date vs Followers)          Monthly Posting (Month vs Posts)|
+-----------------------------------------------------------------------------------+
|  [Chart 3: Line / Area Chart]                                                     |
|  Engagement Rate Trend Chronological (Post Date vs Engagement Rate)               |
+-----------------------------------------------------------------------------------+
```

### Visual Specifications:
1. **KPI Cards (Multi-Row Card or Single Cards)**:
   - **Total Followers**: Reference `dashboard_overview[total_followers]`.
   - **Followers Growth %**: Reference `dashboard_overview[follower_growth_pct]` (formatted as `%`).
   - **Total Posts**: Reference `dashboard_overview[total_posts]`.
   - **Total Likes**: Reference `dashboard_overview[total_likes]`.
   - **Total Comments**: Reference `dashboard_overview[total_comments]`.
   - **Average Engagement Rate**: Reference `dashboard_overview[avg_engagement_rate]` (formatted as `%`).
2. **Follower Growth Trend (Line Chart)**:
   - Axis: `followers_growth[date]`
   - Values: `followers_growth[followers]`
   - Tooltip: Date, total followers.
3. **Monthly Posting Trend (Column Chart)**:
   - Axis: `monthly_activity[month]` (Sorted chronologically by Month/Year)
   - Values: `monthly_activity[post_count]`
4. **Engagement Trend (Area/Line Chart)**:
   - Axis: `engagement_trend[date]`
   - Values: `engagement_trend[engagement_rate]`
   - Legend / Slicer: `engagement_trend[media_type]`

---

## Page 2 – Post Analytics
Focuses on post breakdown, media type efficiency, and weekday engagement insights.

### Visual Layout Grid

```
+-----------------------------------------------------------------------------------+
|  [Slicer: Media Type Filter]                         [Slicer: Weekday Filter]     |
+-----------------------------------------------------------------------------------+
|  [Chart 1: Bar Chart]            [Chart 2: Bar Chart]          [Chart 3: Column]  |
|  Likes by Month                  Comments by Month             Posts by Weekday   |
+-----------------------------------------------------------------------------------+
|  [Chart 4: Pie/Donut Chart]                           [Chart 5: Matrix Grid]      |
|  Posts by Media Type                                  Posting Frequency Metrics   |
+-----------------------------------------------------------------------------------+
|  [Table View: Top Performing Posts]                                               |
|  Top Posts sorted by Engagement (Text snippet, Date, Media Type, Likes, Eng %)    |
+-----------------------------------------------------------------------------------+
|  [Table View: Worst Performing Posts]                                             |
|  Bottom Posts sorted by Engagement (Text snippet, Date, Likes, Comments, Eng %)   |
+-----------------------------------------------------------------------------------+
```

### Visual Specifications:
1. **Likes & Comments by Month (Clustered Bar Charts)**:
   - Axis: `monthly_activity[month]`
   - Values: `monthly_activity[likes_count]` / `monthly_activity[comments_count]`
2. **Posts by Weekday (Clustered Column Chart)**:
   - Axis: `posting_frequency[weekday]` (Sorted: Mon -> Sun)
   - Values: `posting_frequency[post_count]`
3. **Posting Frequency Matrix**:
   - Rows: `posting_frequency[weekday]`
   - Values: `post_count`, `avg_likes` (formatted as average decimals), `avg_comments`
4. **Top / Worst Performing Posts Tables**:
   - Fields: `post_text` (truncated), `post_date` (Date format), `media_type`, `likes`, `comments`, `reposts`, `engagement_rate` (formatted as `%`)
   - Sorting:
     - Top Posts Table: Sort by `engagement_rate` **Descending**.
     - Worst Posts Table: Sort by `engagement_rate` **Ascending**.

---

## Page 3 – Profile
Exposes personal brand metrics, career experience, and academic timeline.

### Visual Layout Grid

```
+-----------------------------------------------------------------------------------+
|  +---------------------------------------+  +----------------------------------+  |
|  |  Profile Summary Card                 |  |  Timeline / Professional Summary |  |
|  |  Name: [Full Name]                    |  |  About Me:                       |  |
|  |  Headline: [Headline]                 |  |  [About Text Block]              |  |
|  |  Company: [Current Company]           |  |                                  |  |
|  |  Followers: [Count] | Conn: [Count]   |  +----------------------------------+  |
|  +---------------------------------------+                                         |
+-----------------------------------------------------------------------------------+
|  [Timeline Visual: Experience Details]                                            |
|  Gantt Chart or Cards Grid sorted by date (Company, Title, Duration, Location)    |
+-----------------------------------------------------------------------------------+
|  [Timeline Visual: Education Details]                                             |
|  Cards Grid (Institution, Degree, Years, Field of Study)                          |
+-----------------------------------------------------------------------------------+
```

### Visual Specifications:
1. **Profile Summary Card (Text / Multi-row card)**:
   - Fields: `profiles[full_name]`, `profiles[headline]`, `profiles[current_company]`, `profiles[profile_url]`.
2. **Timeline Visuals**:
   - Since Experience and Education are stored as JSON arrays in SQLite, expand them into distinct flat tables during the Power Query import phase (using the **JSON Expand** button on `experience` and `education` fields) to create individual records:
     - **Experience Grid/Timeline**: Show columns `Title`, `Company`, `Date Range`, `Location`, and `Description`.
     - **Education Timeline**: Show columns `School`, `Degree`, `Field of Study`, `Start Year`, `End Year`.

---

## Page 4 – Monthly Report
Dedicated to compiling month-over-month (MoM) calculations and highlight/lowlight tables.

### Visual Layout Grid

```
+-----------------------------------------------------------------------------------+
|  [Slicer: Selected Month/Year]                                                    |
+-----------------------------------------------------------------------------------+
|  [KPI Card]              [KPI Card]              [KPI Card]              [KPI Card]|
|  Monthly Posts Count     Likes Growth MoM %      Comments Growth MoM %   Eng. Rate |
+-----------------------------------------------------------------------------------+
|  [Table View: Month-over-Month Growth Statistics Table]                            |
|  Year/Month | Posts Count | Total Likes | Total Comments | Reaction Growth %      |
+-----------------------------------------------------------------------------------+
|  [Table View: Top 5 Posts of the Selected Month]                                   |
|  Text snippet | Date | Likes | Comments | Engagement %                            |
+-----------------------------------------------------------------------------------+
|  [Table View: Bottom 5 Posts of the Selected Month]                                |
|  Text snippet | Date | Likes | Comments | Engagement %                            |
+-----------------------------------------------------------------------------------+
```

### Visual Specifications:
1. **Selected Month Slicer**:
   - Field: `monthly_activity[month]` and `monthly_activity[year]`.
2. **Monthly KPIs**:
   - **Monthly Posts Count**: Sum of `monthly_activity[post_count]`.
   - **MoM Reaction Growth**: `monthly_activity[monthly_growth_pct]` (displays reaction count growth comparison against last month).
3. **Top / Bottom 5 Posts Table**:
   - Filtered dynamically to the selected Month/Year.
   - Top 5: Filtered to show Top 5 items using Top N filter pane on `engagement_rate` (Descending).
   - Bottom 5: Filtered to show Bottom 5 items using Bottom N filter pane on `engagement_rate` (Ascending).

---

## Page 5 – Network & Connections (New Page)
Exposes personal network metrics, company distribution, industry classification, location distribution, and connection lists.

### Visual Layout Grid

```
+-----------------------------------------------------------------------------------+
|  [Logo / Title: LinkedIn Connections & Network]                   [Search Slicer] |
+-----------------------------------------------------------------------------------+
|  [KPI Card]                                [KPI Card]                             |
|  Total Connections                         New Connections (This Month)           |
+-----------------------------------------------------------------------------------+
|  [Table View: Searchable Connection Members Table]                                |
|  Shows: Name, Headline, Company, Location, Connected Date, Profile URL            |
+-----------------------------------------------------------------------------------+
|  [Chart 1: Horizontal Bar Chart]           [Chart 2: Treemap]                     |
|  Connections by Company                     Connections by Industry (Treemap)     |
+-----------------------------------------------------------------------------------+
|  [Chart 3: Map / Location Bubble Chart]                                           |
|  Connections by Location (City/State vs Connection Count)                         |
+-----------------------------------------------------------------------------------+
```

### Visual Specifications:
1. **KPI Cards**:
   - **Total Connections**: Reference `_Measures[Total Connections]` (derived from `pbi_total_connections.csv`).
   - **New Connections**: Reference `_Measures[New Connections]`. Displays "No data available" (blank indicator) if connection dates are missing.
2. **Searchable Connection Members Table**:
   - Fields: `pbi_connection_directory[full_name]`, `pbi_connection_directory[headline]`, `pbi_connection_directory[company]`, `pbi_connection_directory[location]`, `pbi_connection_directory[connected_date]`, `pbi_connection_directory[profile_url]`.
   - Enable text search on the columns using visual search filters.
3. **Connections by Company (Horizontal Bar Chart)**:
   - Axis: `pbi_company_distribution[company]`
   - Values: `pbi_company_distribution[connection_count]`
   - Sort: Descending (top companies shown at the top).
4. **Connections by Industry (Treemap)**:
   - Grouping: `pbi_industry_distribution[industry]`
   - Values: `pbi_industry_distribution[connection_count]`
   - If industry data is not collected/empty, the visual will display "No connection data available" or show up blank, ready for future data.
5. **Connections by Location (Map)**:
   - Location: `pbi_connection_directory[location]` (Geocoded by city, state, or country).
   - Bubble Size: Count of connections.
   - If no location data is present (e.g. all values are blank), the map will remain clean, ready for future data.

