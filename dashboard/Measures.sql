-- ============================================================================
-- POWER BI DAX MEASURES DEFINITION
-- ============================================================================
-- These measures are designed to run on the tables imported from the reports folder.
-- Place these inside your Power BI model by selecting "New Measure" under the Modeling tab.
-- ============================================================================

-- 1. AVERAGE ENGAGEMENT RATE (POSTS LEVEL)
-- Computes the average engagement rate across all posts.
Average Engagement Rate = 
AVERAGE('post_performance'[engagement_rate])


-- 2. TOTAL REACTIONS (Lkes + Comments + Reposts)
-- Helper measure to capture total interactions on posts.
Total Reactions = 
SUM('post_performance'[likes]) 
+ SUM('post_performance'[comments]) 
+ SUM('post_performance'[reposts])


-- 3. ENGAGEMENT % (TOTAL OVERVIEW LEVEL)
-- Calculates engagement percentage as total reactions divided by the latest follower count.
Engagement % = 
VAR TotalFollowers = MAX('dashboard_overview'[total_followers])
RETURN
    IF(
        TotalFollowers > 0,
        DIVIDE([Total Reactions], TotalFollowers, 0),
        0
    )


-- 4. FOLLOWERS GROWTH (ABSOLUTE)
-- Calculates the growth in followers count from the earliest recorded snapshot to the latest.
Followers Growth Absolute = 
VAR EarliestFollowers = 
    CALCULATE(
        FIRSTNONBLANK('followers_growth'[followers], 1),
        ALL('followers_growth')
    )
VAR LatestFollowers = 
    CALCULATE(
        LASTNONBLANK('followers_growth'[followers], 1),
        ALL('followers_growth')
    )
RETURN
    LatestFollowers - EarliestFollowers


-- 5. FOLLOWERS GROWTH % (RELATIVE)
-- Calculates the growth rate percentage of followers from the baseline.
Followers Growth % = 
VAR EarliestFollowers = 
    CALCULATE(
        FIRSTNONBLANK('followers_growth'[followers], 1),
        ALL('followers_growth')
    )
VAR LatestFollowers = 
    CALCULATE(
        LASTNONBLANK('followers_growth'[followers], 1),
        ALL('followers_growth')
    )
RETURN
    IF(
        EarliestFollowers > 0,
        DIVIDE(LatestFollowers - EarliestFollowers, EarliestFollowers, 0),
        0
    )


-- 6. MONTH-OVER-MONTH POSTS GROWTH % (MONTHLY LEVEL)
-- Compares post counts of the current month with the previous month.
Monthly Posts Growth % = 
VAR CurrentMonthPosts = SUM('monthly_activity'[post_count])
VAR PreviousMonthPosts = 
    CALCULATE(
        SUM('monthly_activity'[post_count]),
        DATEADD('Calendar'[Date], -1, MONTH)
    )
RETURN
    IF(
        ISBLANK(PreviousMonthPosts) || PreviousMonthPosts = 0,
        BLANK(),
        DIVIDE(CurrentMonthPosts - PreviousMonthPosts, PreviousMonthPosts, 0)
    )


-- 7. MONTH-OVER-MONTH REACTION GROWTH % (MONTHLY LEVEL)
-- Extracts the pre-computed MoM growth rate calculated by the analytics engine.
Monthly Reaction Growth % = 
AVERAGE('monthly_activity'[monthly_growth_pct])


-- 8. 7-DAY ROLLING AVERAGE OF LIKES
-- Calculates the 7-day moving average of post likes to smooth out daily spikes.
Likes 7-Day Rolling Avg = 
AVERAGEX(
    DATESINPERIOD(
        'Calendar'[Date], 
        LASTDATE('Calendar'[Date]), 
        -7, 
        DAY
    ),
    CALCULATE(SUM('post_performance'[likes]))
)


-- 9. 30-DAY ROLLING AVERAGE OF ENGAGEMENT RATE
-- Calculates the 30-day moving average of the engagement rate.
Engagement 30-Day Rolling Avg = 
AVERAGEX(
    DATESINPERIOD(
        'Calendar'[Date], 
        LASTDATE('Calendar'[Date]), 
        -30, 
        DAY
    ),
    CALCULATE([Average Engagement Rate])
)


-- 10. POST ENGAGEMENT TOP RANK (DESCENDING)
-- Used in Visual Filters to dynamically rank top performing posts.
Post Engagement Top Rank = 
RANKX(
    ALLSELECTED('post_performance'),
    [Average Engagement Rate],
    ,
    DESC,
    Dense
)


-- 10b. POST ENGAGEMENT BOTTOM RANK (ASCENDING)
-- Used in Visual Filters to dynamically rank bottom performing posts.
Post Engagement Bottom Rank = 
RANKX(
    ALLSELECTED('post_performance'),
    [Average Engagement Rate],
    ,
    ASC,
    Dense
)


-- 11. TOTAL CONNECTIONS
-- Computes the total number of connections recorded in the summary table.
Total Connections = 
SUM('pbi_total_connections'[total_connections])


-- 12. NEW CONNECTIONS THIS MONTH
-- Computes the number of new connections added during the current calendar month.
New Connections = 
SUM('pbi_total_connections'[new_connections_this_month])

