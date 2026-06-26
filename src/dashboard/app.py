import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import re

# Set page config
st.set_page_config(
    page_title="LinkedIn AI Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom dark-theme styling with animated background and glassmorphism
st.markdown("""
<style>
    /* Fixed background container */
    #animated-bg-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #0F172A;
        z-index: -9999;
        overflow: hidden;
        pointer-events: none;
    }
    
    #network-canvas {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
    }
    
    /* Subtle Animated Data Grid */
    .grid-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-size: 60px 60px;
        background-image: 
            linear-gradient(to right, rgba(59, 130, 246, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
        mask-image: radial-gradient(circle, black 40%, transparent 85%);
        -webkit-mask-image: radial-gradient(circle, black 40%, transparent 85%);
    }
    
    .grid-overlay::after {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 200%;
        height: 100%;
        background: linear-gradient(
            to right,
            transparent,
            rgba(59, 130, 246, 0.02) 30%,
            rgba(59, 130, 246, 0.06) 50%,
            rgba(59, 130, 246, 0.02) 70%,
            transparent
        );
        transform: skewX(-25deg);
        animation: grid-scan 12s infinite linear;
    }
    
    @keyframes grid-scan {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    /* Light Streaks */
    .light-streak {
        position: absolute;
        width: 80%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.15), transparent);
        pointer-events: none;
    }
    
    .streak-1 {
        top: 25%;
        left: -30%;
        transform: rotate(-12deg);
        animation: streak-drift-1 15s infinite linear;
    }
    
    .streak-2 {
        bottom: 35%;
        right: -30%;
        transform: rotate(20deg);
        animation: streak-drift-2 20s infinite linear;
    }
    
    @keyframes streak-drift-1 {
        0% { transform: translate(-20vw, -5vh) rotate(-12deg); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { transform: translate(40vw, 10vh) rotate(-12deg); opacity: 0; }
    }
    
    @keyframes streak-drift-2 {
        0% { transform: translate(20vw, 5vh) rotate(20deg); opacity: 0; }
        10% { opacity: 0.8; }
        90% { opacity: 0.8; }
        100% { transform: translate(-40vw, -10vh) rotate(20deg); opacity: 0; }
    }
    
    /* Floating Geometric Shapes */
    .shape {
        position: absolute;
        opacity: 0.03;
        border: 1.2px solid #3B82F6;
        pointer-events: none;
        animation: float-shape 28s infinite alternate ease-in-out;
    }
    
    .shape-circle {
        top: 15%;
        right: 18%;
        width: 90px;
        height: 90px;
        border-radius: 50%;
        animation-duration: 22s;
    }
    
    .shape-triangle {
        bottom: 20%;
        left: 12%;
        width: 0;
        height: 0;
        border-left: 35px solid transparent;
        border-right: 35px solid transparent;
        border-bottom: 60px solid rgba(59, 130, 246, 0.12);
        animation-duration: 32s;
        transform-origin: 50% 66%;
    }
    
    .shape-square {
        top: 55%;
        right: 10%;
        width: 60px;
        height: 60px;
        animation-duration: 26s;
        animation-delay: -4s;
    }
    
    @keyframes float-shape {
        0% { transform: translateY(0) rotate(0deg); }
        100% { transform: translateY(-35px) rotate(360deg); }
    }
    
    /* Glowing gradient waves/blobs */
    .blob {
        position: absolute;
        border-radius: 50%;
        filter: blur(100px);
        opacity: 0.11;
        animation: move-blobs 30s infinite alternate ease-in-out;
        pointer-events: none;
    }
    .blob-1 {
        top: -10%;
        left: -10%;
        width: 55vw;
        height: 55vw;
        background: radial-gradient(circle, #3B82F6 0%, transparent 80%);
        animation-duration: 35s;
    }
    .blob-2 {
        bottom: -10%;
        right: -10%;
        width: 65vw;
        height: 65vw;
        background: radial-gradient(circle, #1D4ED8 0%, transparent 80%);
        animation-duration: 45s;
        animation-delay: -6s;
    }
    .blob-3 {
        top: 35%;
        left: 25%;
        width: 48vw;
        height: 48vw;
        background: radial-gradient(circle, #0284C7 0%, transparent 80%);
        animation-duration: 40s;
        animation-delay: -3s;
    }
    
    @keyframes move-blobs {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(6vw, 4vh) scale(1.1); }
        100% { transform: translate(-3vw, -6vh) scale(0.95); }
    }

    /* Make Streamlit container backgrounds transparent to see custom bg */
    .stApp {
        background: transparent !important;
    }
    
    /* Sidebar glassmorphism styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(51, 65, 85, 0.3) !important;
    }
    
    /* KPI Card glassmorphism styling */
    .metric-card {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(59, 130, 246, 0.25) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 12px !important;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(59, 130, 246, 0.6) !important;
        box-shadow: 0 12px 40px 0 rgba(59, 130, 246, 0.15) !important;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #FFFFFF;
    }
    
    .metric-label {
        font-size: 11px;
        color: #CBD5E1;
        text-transform: uppercase;
        margin-top: 5px;
        letter-spacing: 0.5px;
    }

    /* Style dataframe wrappers to fit glassmorphism theme */
    .stDataFrame, .stTable {
        background-color: rgba(30, 41, 59, 0.3) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(4px) !important;
    }
</style>
""", unsafe_allow_html=True)

# Injects the background DOM elements and starts particle node canvas loop via iframe parent document injection
st.components.v1.html(
    """
    <script>
        (function() {
            const parentDoc = window.parent.document;
            if (parentDoc.getElementById("animated-bg-container")) {
                return;
            }
            
            const bgContainer = parentDoc.createElement("div");
            bgContainer.id = "animated-bg-container";
            bgContainer.innerHTML = `
                <div class="grid-overlay"></div>
                <div class="light-streak streak-1"></div>
                <div class="light-streak streak-2"></div>
                <div class="shape shape-circle"></div>
                <div class="shape shape-triangle"></div>
                <div class="shape shape-square"></div>
                <canvas id="network-canvas"></canvas>
                <div class="blob blob-1"></div>
                <div class="blob blob-2"></div>
                <div class="blob blob-3"></div>
            `;
            parentDoc.body.appendChild(bgContainer);
            
            const canvas = bgContainer.querySelector("#network-canvas");
            const ctx = canvas.getContext("2d");
            
            let width = canvas.width = window.parent.innerWidth;
            let height = canvas.height = window.parent.innerHeight;
            
            window.parent.addEventListener("resize", () => {
                width = canvas.width = window.parent.innerWidth;
                height = canvas.height = window.parent.innerHeight;
            });
            
            const particles = [];
            const particleCount = 45;
            const connectionDistance = 130;
            
            class Particle {
                constructor() {
                    this.x = Math.random() * width;
                    this.y = Math.random() * height;
                    this.vx = (Math.random() - 0.5) * 0.2;
                    this.vy = (Math.random() - 0.5) * 0.2;
                    this.radius = Math.random() * 2 + 1.2;
                }
                
                update() {
                    this.x += this.vx;
                    this.y += this.vy;
                    
                    if (this.x < 0 || this.x > width) this.vx *= -1;
                    if (this.y < 0 || this.y > height) this.vy *= -1;
                }
                
                draw() {
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                    ctx.fillStyle = "rgba(59, 130, 246, 0.4)";
                    ctx.shadowBlur = 8;
                    ctx.shadowColor = "#3B82F6";
                    ctx.fill();
                    ctx.shadowBlur = 0;
                }
            }
            
            for (let i = 0; i < particleCount; i++) {
                particles.push(new Particle());
            }
            
            function animate() {
                if (!parentDoc.getElementById("animated-bg-container")) {
                    return;
                }
                
                ctx.clearRect(0, 0, width, height);
                
                for (let i = 0; i < particles.length; i++) {
                    for (let j = i + 1; j < particles.length; j++) {
                        const dx = particles[i].x - particles[j].x;
                        const dy = particles[i].y - particles[j].y;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        
                        if (dist < connectionDistance) {
                            const alpha = (1 - dist / connectionDistance) * 0.12;
                            ctx.beginPath();
                            ctx.moveTo(particles[i].x, particles[i].y);
                            ctx.lineTo(particles[j].x, particles[j].y);
                            ctx.strokeStyle = "rgba(59, 130, 246, " + alpha + ")";
                            ctx.lineWidth = 0.5;
                            ctx.stroke();
                        }
                    }
                }
                
                particles.forEach(p => {
                    p.update();
                    p.draw();
                });
                
                window.parent.requestAnimationFrame(animate);
            }
            
            animate();
        })();
    </script>
    """,
    height=0,
    width=0
)

# Path to SQLite DB
project_root = Path(__file__).resolve().parent.parent.parent
db_path = project_root / "data" / "linkedin.db"

# 5-minute Auto-refresh JavaScript
st.components.v1.html(
    """
    <script>
        setTimeout(function(){
            window.parent.location.reload();
        }, 300000); // 300,000 ms = 5 minutes
    </script>
    """,
    height=0,
    width=0
)

# Helper to execute query
def load_data(query: str, params=()) -> pd.DataFrame:
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database Query Error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# ----------------------------------------------------
# Sidebar Controls
# ----------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png", width=60)
st.sidebar.title("LinkedIn AI Analytics")

# Refresh Button
if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.success("Cache cleared! Dashboard data refreshed.")
    st.rerun()

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation Menu",
    ["Executive Overview", "Growth & Timelines", "Post Analytics", "AI Insights & Forecasts", "Network & Connections"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"*Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
st.sidebar.markdown("*Auto-refresh is active (every 5 mins)*")

# ----------------------------------------------------
# Main View logic
# ----------------------------------------------------
if not db_path.exists():
    st.error(f"SQLite Database not found at {db_path}. Please execute scraping run first.")
else:
    # Page 1: Executive Overview
    if page == "Executive Overview":
        st.title("📊 Executive Brand Overview")
        st.markdown("High-level audience snapshot, interactions, and content volume trends.")
        
        # Load summary calculations
        df_summary = load_data("SELECT * FROM analytics_summary ORDER BY computed_at DESC LIMIT 1")
        
        if not df_summary.empty:
            summary = df_summary.iloc[0]
            
            # Card Columns
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            with c1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["total_followers"]:,}</div><div class="metric-label">Followers</div></div>', unsafe_allow_html=True)
            with c2:
                growth_text = f"+{summary['follower_growth_pct']:.2f}%" if summary['follower_growth_pct'] >= 0 else f"{summary['follower_growth_pct']:.2f}%"
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: {"#10B981" if summary["follower_growth_pct"] >= 0 else "#F43F5E"};">{growth_text}</div><div class="metric-label">Followers Growth</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["total_posts"]}</div><div class="metric-label">Total Posts</div></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["total_likes"]:,}</div><div class="metric-label">Total Likes</div></div>', unsafe_allow_html=True)
            with c5:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["total_comments"]:,}</div><div class="metric-label">Total Comments</div></div>', unsafe_allow_html=True)
            with c6:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["avg_engagement_rate"]:.2f}%</div><div class="metric-label">Avg. Engagement</div></div>', unsafe_allow_html=True)
        else:
            st.warning("No summary analytics found. Displaying default KPI structures.")
            
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Audience Growth Trend (Area Chart)")
            # Load growth metrics showing both followers and connections
            df_growth = load_data("SELECT date(scraped_at) as date, followers, connections FROM profiles ORDER BY scraped_at ASC")
            if not df_growth.empty:
                df_melted = pd.melt(df_growth, id_vars=["date"], value_vars=["followers", "connections"], var_name="Metric", value_name="Count")
                fig_fol = px.area(
                    df_melted, x="date", y="Count", color="Metric",
                    labels={"date": "Date", "Count": "Count", "Metric": "Metric"},
                    template="plotly_dark",
                    color_discrete_map={"followers": "#0A66C2", "connections": "#06B6D4"}
                )
                fig_fol.update_layout(plot_bgcolor="#1E293B", paper_bgcolor="#0F172A", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_fol, use_container_width=True)
            else:
                st.info("No profile growth data found in SQLite.")
                
        with col2:
            st.markdown("### 📅 Monthly Posting Trends (Line Chart)")
            df_mon = load_data("SELECT * FROM monthly_statistics ORDER BY year ASC, month ASC")
            if not df_mon.empty:
                df_mon["Month-Year"] = df_mon["month"] + " " + df_mon["year"].astype(str)
                fig_mon = px.line(
                    df_mon, x="Month-Year", y="post_count",
                    labels={"Month-Year": "Month", "post_count": "Posts"},
                    markers=True,
                    template="plotly_dark"
                )
                fig_mon.update_layout(plot_bgcolor="#1E293B", paper_bgcolor="#0F172A", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_mon, use_container_width=True)
            else:
                st.info("No monthly statistics available yet.")
                
        st.markdown("### ⚡ Chronological Engagement Rates (Line Chart with Markers)")
        df_posts = load_data("SELECT post_date, engagement_rate, media_type FROM posts ORDER BY post_date ASC")
        if not df_posts.empty:
            df_posts["date"] = pd.to_datetime(df_posts["post_date"]).dt.date
            fig_er = px.line(
                df_posts, x="date", y="engagement_rate", color="media_type",
                labels={"date": "Publication Date", "engagement_rate": "Engagement Rate (%)"},
                markers=True,
                template="plotly_dark"
            )
            fig_er.update_layout(plot_bgcolor="#1E293B", paper_bgcolor="#0F172A")
            st.plotly_chart(fig_er, use_container_width=True)
        else:
            st.info("No posts listed in SQLite to render engagement curves.")

    # Page 2: Growth & Timelines
    elif page == "Growth & Timelines":
        st.title("📈 Growth & Performance Timelines")
        st.markdown("Detailed review of follower growth metrics, MoM indicators, and weekly shifts.")
        
        df_summary = load_data("SELECT * FROM analytics_summary ORDER BY computed_at DESC LIMIT 1")
        if not df_summary.empty:
            summary = df_summary.iloc[0]
            g1, g2, g3 = st.columns(3)
            with g1:
                st.metric("Total Followers Growth (All-Time)", f"{summary['follower_growth_pct']:.2f}%")
            with g2:
                st.metric("Weekly Followers Growth (Last 7d)", f"{summary['weekly_growth_pct']:.2f}%")
            with g3:
                st.metric("Monthly Followers Growth (Last 30d)", f"{summary['monthly_growth_pct']:.2f}%")
                
        st.markdown("---")
        
        st.markdown("### 🗓️ Monthly Activity Growth Ledger")
        df_ledger = load_data("SELECT year, month, post_count, likes_count, comments_count, reposts_count, monthly_growth_pct FROM monthly_statistics ORDER BY year DESC, month DESC")
        if not df_ledger.empty:
            df_ledger["monthly_growth_pct"] = df_ledger["monthly_growth_pct"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(
                df_ledger.rename(columns={
                    "year": "Year", "month": "Month", "post_count": "Posts", 
                    "likes_count": "Likes", "comments_count": "Comments", 
                    "reposts_count": "Reposts", "monthly_growth_pct": "MoM Growth (Reactions)"
                }),
                use_container_width=True
            )
        else:
            st.info("No ledger entries generated.")
            
        st.markdown("### 📋 Chronological Follower Count Ledgers")
        df_fol_ledger = load_data("SELECT date, followers FROM follower_history ORDER BY date DESC")
        if not df_fol_ledger.empty:
            st.dataframe(df_fol_ledger.rename(columns={"date": "Date", "followers": "Follower Count"}), use_container_width=True)

    # Page 3: Post Analytics
    elif page == "Post Analytics":
        st.title("📝 Post Performance & Analytics")
        st.markdown("Correlate formats, keywords, and schedules against reactions.")

        # Slicers at top
        s1, s2, s3 = st.columns(3)
        with s1:
            years = load_data("SELECT DISTINCT year FROM posts ORDER BY year DESC")["year"].tolist()
            years_options = ["All Years"] + [int(y) for y in years]
            selected_year = st.selectbox("Filter Year", years_options)
        with s2:
            months = load_data("SELECT DISTINCT month FROM posts")["month"].tolist()
            months_options = ["All Months"] + months
            selected_month = st.selectbox("Filter Month", months_options)
        with s3:
            media = load_data("SELECT DISTINCT media_type FROM posts")["media_type"].tolist()
            media_options = ["All Media Types"] + media
            selected_media = st.selectbox("Filter Media Type", media_options)
            
        # Keyword Search
        search_query = st.text_input("🔍 Search Post Text (Regex / Keyword Match)", "")

        # Construct Query
        query = "SELECT linkedin_post_id, post_date, post_text, media_type, likes, comments, reposts, engagement_rate, post_url, weekday FROM posts WHERE 1=1"
        params = []
        
        if selected_year != "All Years":
            query += " AND year = ?"
            params.append(selected_year)
        if selected_month != "All Months":
            query += " AND month = ?"
            params.append(selected_month)
        if selected_media != "All Media Types":
            query += " AND media_type = ?"
            params.append(selected_media)
        if search_query:
            query += " AND post_text LIKE ?"
            params.append(f"%{search_query}%")
            
        query += " ORDER BY post_date DESC"
        
        df_filtered = load_data(query, tuple(params))
        
        if not df_filtered.empty:
            st.markdown(f"**Total Posts Matching Filters**: {len(df_filtered)}")
            
            # Displays charts comparing likes and comments trends
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                fig_l = px.line(
                    df_filtered.iloc[::-1], x="post_date", y="likes",
                    title="Likes Trend Over Selection", template="plotly_dark"
                )
                fig_l.update_layout(plot_bgcolor="#1E293B", paper_bgcolor="#0F172A")
                st.plotly_chart(fig_l, use_container_width=True)
            with col_t2:
                fig_c = px.line(
                    df_filtered.iloc[::-1], x="post_date", y="comments",
                    title="Comments Trend Over Selection", template="plotly_dark"
                )
                fig_c.update_layout(plot_bgcolor="#1E293B", paper_bgcolor="#0F172A")
                st.plotly_chart(fig_c, use_container_width=True)

            # Visuals row 2: Donut Pie Chart & Weekday Frequency Matrix
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.markdown("### 🍕 Posts by Media Type")
                df_media = df_filtered.groupby("media_type").size().reset_index(name="count")
                fig_pie = px.pie(
                    df_media, names="media_type", values="count",
                    hole=0.4,
                    template="plotly_dark",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_layout(plot_bgcolor="#1E293B", paper_bgcolor="#0F172A", margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_chart2:
                st.markdown("### 📊 Weekday Posting Frequency Matrix")
                # Group by weekday and calculate averages
                df_matrix = df_filtered.groupby("weekday").agg(
                    post_count=("likes", "count"),
                    avg_likes=("likes", "mean"),
                    avg_comments=("comments", "mean"),
                    avg_engagement=("engagement_rate", "mean")
                ).reset_index()
                
                # Order weekdays Mon-Sun
                weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                df_matrix["weekday"] = pd.Categorical(df_matrix["weekday"], categories=weekday_order, ordered=True)
                df_matrix = df_matrix.sort_values("weekday").reset_index(drop=True)
                
                # Format metrics
                df_matrix["avg_likes"] = df_matrix["avg_likes"].map(lambda x: f"{x:.1f}")
                df_matrix["avg_comments"] = df_matrix["avg_comments"].map(lambda x: f"{x:.1f}")
                df_matrix["avg_engagement"] = df_matrix["avg_engagement"].map(lambda x: f"{x:.2f}%")
                
                st.dataframe(
                    df_matrix.rename(columns={
                        "weekday": "Weekday", "post_count": "Post Count", 
                        "avg_likes": "Avg Likes", "avg_comments": "Avg Comments",
                        "avg_engagement": "Avg Engagement"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

            # Renders Table List
            st.markdown("### Top Performing Posts (Within Selection)")
            df_tops = df_filtered.sort_values(by="engagement_rate", ascending=False).head(10)
            st.dataframe(
                df_tops.rename(columns={
                    "post_date": "Date", "post_text": "Content", "media_type": "Format",
                    "likes": "Likes", "comments": "Comments", "reposts": "Reposts",
                    "engagement_rate": "Engagement %", "post_url": "LinkedIn Link"
                }),
                use_container_width=True
            )
            
            st.markdown("### Worst Performing Posts (Within Selection)")
            df_worsts = df_filtered.sort_values(by="engagement_rate", ascending=True).head(10)
            st.dataframe(
                df_worsts.rename(columns={
                    "post_date": "Date", "post_text": "Content", "media_type": "Format",
                    "likes": "Likes", "comments": "Comments", "reposts": "Reposts",
                    "engagement_rate": "Engagement %", "post_url": "LinkedIn Link"
                }),
                use_container_width=True
            )
        else:
            st.info("No posts match the configured filters.")

    # Page 4: AI Insights & Forecasts
    elif page == "AI Insights & Forecasts":
        st.title("🤖 AI Insights & Extrapolated Forecasts")
        st.markdown("Calculated recommendations, growth predictions, and performance highlights.")

        # Re-run local AI insights calculations on display
        from src.ai.insights_service import AIInsightsService
        from src.ai.recommendations import AIRecommendationsService
        from src.database.repository import LinkedInRepository
        
        repository = LinkedInRepository()
        insights_service = AIInsightsService(repository)
        recs_service = AIRecommendationsService(repository)
        
        insights = insights_service.get_insights()
        recs = recs_service.generate_recommendations()

        i1, i2 = st.columns(2)
        with i1:
            st.markdown("### 🏆 Content Optimization Summary")
            st.markdown(f"- **Best Day to Post**: **{insights['best_day']}**")
            st.markdown(f"- **Best Time Slot**: **{recs['best_time_slot']}**")
            st.markdown(f"- **Optimal Content Length**: **{recs['best_content_length']}**")
            st.markdown(f"- **Best Performing Category**: **{recs['best_category']}**")
            st.markdown(f"- **Suggested Posting Frequency**: **{recs['suggested_frequency']}**")
            
        with i2:
            st.markdown("### 🔮 AI Algorithmic Forecasts")
            latest_followers = repository.get_latest_followers()
            st.metric("Current Followers Count", f"{latest_followers:,}")
            st.metric("30-Day Follower Projection (AI)", f"{insights['follower_prediction_30d']:,}", 
                      delta=int(insights['follower_prediction_30d'] - latest_followers))
            st.metric("Next Post Engagement Forecast", f"{insights['engagement_prediction_next']:.2f}%")

        st.markdown("---")

        st.markdown("### 💡 Actionable Insights & Recommendations")
        # List hashtags
        if recs["top_hashtags"]:
            st.markdown("**Top-Performing Hashtags Index**:")
            for h in recs["top_hashtags"]:
                st.markdown(f"- **{h['tag']}** (Used: {h['count']} times, Avg. Engagement Rate: **{h['avg_engagement']:.2f}%**)")
        else:
            st.markdown("- No hashtags recorded in posts.")

        # Show brief summary
        st.markdown("### 📑 Dynamic Monthly Executive Summary")
        latest_summary = repository.get_latest_analytics_summary()
        if latest_summary:
            st.info(f"""
            **Monthly Performance Review**:
            You published **{latest_summary.total_posts}** posts this period with an average engagement of **{latest_summary.avg_engagement_rate:.2f}%**.
            Followers grew by **{latest_summary.monthly_growth_pct:.2f}%** to **{latest_summary.total_followers:,}**.
            
            *AI Strategic Suggestion*: Focus your schedule around **{insights['best_day']}** mornings, utilizing tags like `{[h['tag'] for h in recs['top_hashtags'][:2]] if recs['top_hashtags'] else '#AI'}` to capitalize on historical algorithm traction.
            """)
        else:
            st.info("No analytics summaries stored to generate text narrative blocks.")

    # Page 5: Network & Connections
    elif page == "Network & Connections":
        st.title("🤝 Network & Connections Directory")
        st.markdown("Detailed breakdown of your LinkedIn connections, company distribution, and connection lists.")

        # Query connections details from profile snapshot (real header count)
        df_profile = load_data("SELECT connections, scraped_at FROM profiles ORDER BY scraped_at DESC LIMIT 1")
        profile_conn_count = 0
        if not df_profile.empty and df_profile.iloc[0]["connections"] is not None:
            profile_conn_count = int(df_profile.iloc[0]["connections"])

        # Query connections details
        df_connections = load_data("SELECT full_name, headline, company, location, connected_date, profile_url FROM connections ORDER BY connected_date DESC")
        
        total_conn = len(df_connections)
        
        # Show KPI metrics
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Connections (Profile Header)", f"{profile_conn_count:,}" if profile_conn_count > 0 else "N/A")
        with c2:
            st.metric("Directory List Members Count", f"{total_conn:,}")
        with c3:
            # Calculate new connections this month (compare YYYY-MM)
            now_month = datetime.now().strftime("%Y-%m")
            if not df_connections.empty:
                df_connections["month_val"] = pd.to_datetime(df_connections["connected_date"], errors="coerce").dt.strftime("%Y-%m")
                new_this_month = len(df_connections[df_connections["month_val"] == now_month])
            else:
                new_this_month = 0
            st.metric("New Directory Connections (This Month)", f"{new_this_month:,}")
            
        st.markdown("---")
        st.markdown("### 📋 Connection Members List")
        
        if not df_connections.empty:
            # Search filter for connection members
            search_query = st.text_input("🔍 Search connections by name, headline, company, or location", "")
            
            if search_query:
                # Case-insensitive substring matching
                df_filtered = df_connections[
                    df_connections["full_name"].str.contains(search_query, case=False, na=False) |
                    df_connections["headline"].str.contains(search_query, case=False, na=False) |
                    df_connections["company"].str.contains(search_query, case=False, na=False) |
                    df_connections["location"].str.contains(search_query, case=False, na=False)
                ]
            else:
                df_filtered = df_connections
                
            st.dataframe(
                df_filtered[["full_name", "headline", "company", "location", "connected_date", "profile_url"]].rename(columns={
                    "full_name": "Name", "headline": "Headline", "company": "Company",
                    "location": "Location", "connected_date": "Connected Date", "profile_url": "Profile URL"
                }),
                use_container_width=True
            )
        else:
            st.info("No connection members directory data available. To populate the directory names compliantly, request your LinkedIn data archive (Connections.csv), place the file in the project folder, and run a data refresh.")
