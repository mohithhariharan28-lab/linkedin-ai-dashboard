# Power BI Project (.pbix) Setup Instructions

This document provides quickstart instructions on how to manually construct the `Sample.pbix` file using the exported reports and DAX measures.

---

## Prerequisites
- Install [Power BI Desktop](https://powerbi.microsoft.com/desktop/).
- Run the python scraper and pipeline at least once to generate the CSV datasets inside the `reports/` folder.

---

## Step 1: Import Datasets and Configure Power Query
1. Open **Power BI Desktop**.
2. Go to **Home** -> **Transform Data** to open the **Power Query Editor**.
3. Import all 7 CSV files located in your project's `reports/` folder:
   - File -> New Source -> Text/CSV -> select `dashboard_overview.csv` -> Click OK.
   - Repeat for `followers_growth.csv`, `post_performance.csv`, `monthly_activity.csv`, `engagement_trend.csv`, `top_posts.csv`, and `posting_frequency.csv`.
4. Select `post_performance` and select the `post_date` column. Under **Transform** tab, change the data type to **Date/Time**.
5. Select `engagement_trend` and change the `date` column data type to **Date**.
6. Select `followers_growth` and change the `date` column data type to **Date**.
7. Click **Close & Apply** to load the data.

---

## Step 2: Establish the Date Dimension & Relationships
1. Under the **Model View** (left sidebar), click **New Table** in the modeling ribbon.
2. Create a standard calendar table:
   ```dax
   Calendar = CALENDARAUTO()
   ```
3. Mark it as a date table: Right-click the `Calendar` table -> **Mark as date table** -> Select `Date` column -> Click OK.
4. Set up the following relationships by dragging the fields together:
   - Link `Calendar[Date]` (1) to `followers_growth[date]` (Many) (Active relationship).
   - Link `Calendar[Date]` (1) to `post_performance[post_date]` (Many) (Active relationship - Note: Convert `post_date` to Date type or use Date part).
   - Link `Calendar[Date]` (1) to `engagement_trend[date]` (Many) (Active relationship).

---

## Step 3: Insert DAX Measures
Create a dedicated table to house your DAX measures:
1. Click **Enter Data** on the Home ribbon. Name the table `_Measures` and click **Load**.
2. Open [Measures.sql](file:///C:/Users/aparn/.gemini/antigravity/scratch/linkedin_ai_dashboard/dashboard/Measures.sql).
3. Right-click the `_Measures` table in the Fields pane and select **New Measure**.
4. Copy-paste each DAX formula from `Measures.sql` and hit enter.
5. Hide the dummy column `Column1` in `_Measures` to turn it into a dedicated measures folder (its icon will change to a calculator).

---

## Step 4: Configure Visual Pages & Formatting

### Page 1 – Executive Overview
1. Create a dark theme layout background (`Canvas Background` -> Color: `#121824`, Transparency: `0%`).
2. Add a text box for the title: **LinkedIn Executive Analytics Overview**.
3. Create 5 single-value **Card** visuals across the top:
   - **Total Followers**: `dashboard_overview[total_followers]` (Format: integer).
   - **Followers Growth %**: `_Measures[Followers Growth %]` (Format: percentage, 2 decimal places).
   - **Total Posts**: `dashboard_overview[total_posts]`.
   - **Total Likes**: `dashboard_overview[total_likes]`.
   - **Avg Engagement Rate**: `_Measures[Average Engagement Rate]` (Format: percentage).
4. Add a **Line Chart** for Follower Growth:
   - X-Axis: `Calendar[Date]`
   - Y-Axis: `followers_growth[followers]`
5. Add a **Clustered Column Chart** for Posting Trend:
   - X-Axis: `monthly_activity[month]`
   - Y-Axis: `monthly_activity[post_count]`
6. Add an **Area Chart** for Engagement Trend:
   - X-Axis: `Calendar[Date]`
   - Y-Axis: `post_performance[engagement_rate]`

### Page 2 – Post Analytics
1. Add a **Slicer** visual for `post_performance[media_type]`.
2. Add a **Clustered Bar Chart** for Likes by Month:
   - Y-Axis: `monthly_activity[month]`
   - X-Axis: `monthly_activity[likes_count]`
3. Add a **Clustered Column Chart** for Posts by Weekday:
   - X-Axis: `posting_frequency[weekday]`
   - Y-Axis: `posting_frequency[post_count]`
4. Add a **Matrix Table** for Posting Frequency:
   - Rows: `posting_frequency[weekday]`
   - Values: `post_count`, `avg_likes`, `avg_comments`
5. Add a **Table** visual for **Top 10 Performing Posts**:
   - Columns: `post_text`, `post_date`, `media_type`, `likes`, `engagement_rate`
   - Sort descending by `engagement_rate`. In the Filter Pane, add a filter for `_Measures[Post Engagement Top Rank] <= 10`.
6. Add a **Table** visual for **Bottom 10 Performing Posts**:
   - Columns: `post_text`, `post_date`, `media_type`, `likes`, `comments`, `reposts`, `engagement_rate`
   - Sort ascending by `engagement_rate`. In the Filter Pane, add a filter for `_Measures[Post Engagement Bottom Rank] <= 10`.


### Page 3 – Profile
1. Add a **Multi-row Card** for Profile indicators:
   - Fields: `profiles[full_name]`, `profiles[headline]`, `profiles[current_company]`, `profiles[profile_url]`.
2. Use **Power Query** to parse the JSON arrays in `profiles[experience]` and `profiles[education]`:
   - Duplicate the `profiles` table in Power Query.
   - Right-click the duplicate -> **Rename** -> `experience`.
   - Keep only `id` and `experience` columns.
   - Click the expand icon on the `experience` column -> **Extract Values** or **Expand to New Rows**.
   - Expand the JSON records to get `title`, `company`, `date_range`, `location`, `description`.
   - Do the same for `education` into a new table `education` (expanding `school`, `degree`, `field_of_study`, `start_year`, `end_year`).
3. Add a **Table/Timeline** visual to show career details from the `experience` table.

### Page 4 – Monthly Report
1. Add a dropdown **Slicer** for Month and Year.
2. Add a **KPI Card** displaying MoM growth:
   - Indicator: `monthly_activity[post_count]`
   - Target goal: `_Measures[Monthly Posts Growth %]`
3. Add **Table** visuals for Highlights/Lowlights of the selected month:
   - Columns: `post_text`, `post_date`, `likes`, `comments`, `engagement_rate`.
   - Highlight Table: Sort by `engagement_rate` Descending. In the Filter Pane, add a visual-level filter for `_Measures[Post Engagement Top Rank] <= 5`.
   - Lowlight Table: Sort by `engagement_rate` Ascending. In the Filter Pane, add a visual-level filter for `_Measures[Post Engagement Bottom Rank] <= 5`.


---

## Step 5: Import and Bind Network & Connections Data (Page 5)

### 1. Import Datasets
Import the 5 connection CSV files from your project's `reports/` folder via **Transform Data** -> **New Source** -> **Text/CSV**:
- `pbi_total_connections.csv`
- `pbi_connection_directory.csv`
- `pbi_company_distribution.csv`
- `pbi_industry_distribution.csv`
- `pbi_monthly_connection_growth.csv`

### 2. Configure Power Query transformations
- Select `pbi_connection_directory` and format the `connected_date` column as a **Date** type.
- Select `pbi_monthly_connection_growth` and format the `month` column as **Text** (or date format `YYYY-MM`).

### 3. Establish Relationships (Model View)
In the left sidebar's **Model View**, set up the following relationships:
- Link `Calendar[Date]` (1) to `pbi_connection_directory[connected_date]` (Many) (Active relationship).
- Link `Calendar[Date]` (1) to `pbi_monthly_connection_growth[month]` (Many) (Active relationship - map month string parts to date or use date representation).

---

## Step 6: Configure the New Visualizations

### 1. Page 1 – Executive Overview (Extend Canvas Height to 1080px)
Double-click the canvas background. Under **Visualizations Pane** -> **Format Page** -> **Canvas Settings**, change Type to **Custom** and set Height to **1080px**.
Scroll down to the bottom empty space (Y >= 720px) and add the following:
- **Monthly Posting Trends (Line Chart)**
  - X-Axis: `Calendar[Date]` (or `monthly_activity[month]`)
  - Y-Axis: `monthly_activity[post_count]`
- **Audience Growth Trend (Line Chart)**
  - X-Axis: `Calendar[Date]`
  - Y-Axis: `followers_growth[followers]`
- **Chronological Engagement Rate (Line Chart)**
  - X-Axis: `Calendar[Date]` (or `engagement_trend[date]`)
  - Y-Axis: `_Measures[Average Engagement Rate]`

### 2. Page 2 – Post Analytics (Extend Canvas Height to 1080px)
Change the canvas height settings for Page 2 to **1080px** using the custom height option.
Scroll down to the bottom empty space (Y >= 720px) and add the following:
- **Top 10 Performing Posts (Bar Chart)**
  - Y-Axis: `top_posts[post_text]` (sorted descending by engagement)
  - X-Axis: `top_posts[engagement_rate]`
- **Content Type Distribution (Donut Chart)**
  - Legend: `post_performance[media_type]`
  - Values: `Count of linkedin_post_id` (or similar unique post identifier)

### 3. Page 5 – Network & Connections (Create New Page)
Create a new blank page. Change the background color to `#0F172A` (0% transparency) and name it **Network & Connections**. Set page height to **1080px**.
Add the following visuals:
- **Total Connections KPI Card**
  - Field: `_Measures[Total Connections]`
- **New Connections KPI Card**
  - Field: `_Measures[New Connections]`
- **Searchable Connection Members Table**
  - Columns: `pbi_connection_directory[full_name]`, `pbi_connection_directory[headline]`, `pbi_connection_directory[company]`, `pbi_connection_directory[location]`, `pbi_connection_directory[connected_date]`, `pbi_connection_directory[profile_url]`
  - *Tip*: In the visual options, make the `profile_url` column show up as a clickable link. Add a text search filter box or slicer at the top right of the canvas.
- **Connections by Company (Horizontal Bar Chart)**
  - Y-Axis: `pbi_company_distribution[company]`
  - X-Axis: `pbi_company_distribution[connection_count]`
- **Connections by Industry (Treemap)**
  - Grouping: `pbi_industry_distribution[industry]`
  - Values: `pbi_industry_distribution[connection_count]`
  - *Fallback Note*: If this visual shows blank, it is because industry data is not currently collected by the scraper. It remains ready for future data imports.
- **Connections by Location (Map)**
  - Location: `pbi_connection_directory[location]`
  - Bubble Size: `Count of full_name` (or similar count)
