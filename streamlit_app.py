import streamlit as st
import requests
import matplotlib.pyplot as plt
import pandas as pd
import time

# ---------------------------------------------------------------------------
# Design Tokens — Minimalist Dark Theme
# ---------------------------------------------------------------------------
BG_PRIMARY = "#0f0f0f"
BG_CARD = "#141414"
BORDER = "#222222"
BORDER_LIGHT = "#333333"
TEXT_PRIMARY = "#e5e5e5"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#666666"
ACCENT = "#a0a0a0"

# Category colors — muted, low-saturation
CATEGORY_COLORS = {
    "Quality": ("rgba(220, 80, 80, 0.08)", "#b05050"),
    "Support": ("rgba(200, 160, 60, 0.08)", "#a08840"),
    "Usability": ("rgba(80, 130, 200, 0.08)", "#5080b0"),
    "Price": ("rgba(80, 170, 100, 0.08)", "#509060"),
    "Features": ("rgba(150, 100, 200, 0.08)", "#906cb0"),
    "Other": ("rgba(140, 140, 140, 0.08)", "#808080"),
}

# Status colors — muted
STATUS_STYLES = {
    "Working well": {
        "bg": "rgba(80, 160, 100, 0.10)",
        "text": "#5a9a6a",
        "border": "rgba(80, 160, 100, 0.20)",
    },
    "Worth watching": {
        "bg": "rgba(200, 170, 60, 0.10)",
        "text": "#a09040",
        "border": "rgba(200, 170, 60, 0.20)",
    },
    "Needs attention": {
        "bg": "rgba(200, 80, 80, 0.10)",
        "text": "#b05555",
        "border": "rgba(200, 80, 80, 0.20)",
    },
}


def get_category_style(category: str):
    cat_cap = category.capitalize()
    return CATEGORY_COLORS.get(cat_cap, CATEGORY_COLORS["Other"])


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="litmus7 | Review Intelligence",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Minimalist CSS — Theme-Aware
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* Theme-aware custom properties using Streamlit's native variables */
    :root {
        --app-bg: var(--background-color, #0f0f0f);
        --app-text: var(--text-color, #e5e5e5);
        --card-bg: color-mix(in srgb, var(--background-color, #0f0f0f), #808080 5%);
        --border-color: color-mix(in srgb, var(--text-color, #e5e5e5), transparent 85%);
        --border-accent: color-mix(in srgb, var(--text-color, #e5e5e5), transparent 75%);
        --text-muted: color-mix(in srgb, var(--text-color, #e5e5e5), transparent 10%);
        --text-secondary: color-mix(in srgb, var(--text-color, #e5e5e5), transparent 40%);
    }

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Remove Streamlit default padding excess */
    .block-container {
        padding-top: 2rem;
    }

    /* Title */
    .main-title {
        font-family: 'Inter', sans-serif;
        color: var(--app-text);
        font-size: 1.8rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* Metric cards — flat, minimal */
    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        text-align: left;
    }

    .metric-label {
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        margin-bottom: 0.3rem;
    }

    .metric-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--app-text);
    }

    /* Insight cards — thin borders, clean */
    .insight-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--border-accent);
        border-radius: 6px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }

    .insight-title {
        color: var(--app-text);
    }

    .insight-meta {
        color: var(--text-muted);
    }

    .insight-quote {
        color: var(--text-secondary);
        border-left-color: var(--border-color);
    }

    /* Section headers */
    .section-title {
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }

    /* Empty state */
    .empty-state {
        color: var(--text-muted);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------
API_BASE = "http://127.0.0.1:8000"

# Title
st.markdown(
    '<div class="main-title">Product Review Intelligence</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Parallel AI analysis for actionable product insights</div>',
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data Fetching
# ---------------------------------------------------------------------------
def fetch_products():
    try:
        response = requests.get(f"{API_BASE}/db/products")
        if response.status_code == 200:
            data = response.json()
            if data:
                return data
    except Exception:
        pass
    return [
        {
            "id": 1,
            "asin": "B018Y229OU",
            "name": "Fire Tablet, 7 Display, Wi-Fi, 8 GB",
            "description": "Amazon Fire Tablet with 7-inch display, Wi-Fi, 8 GB storage.",
        },
        {
            "id": 2,
            "asin": "B00L9EPT8O",
            "name": "Amazon Echo (White)",
            "description": "Amazon Echo smart speaker with Alexa.",
        },
    ]


products_list = fetch_products()
product_names = [p["name"] for p in products_list]

# ---------------------------------------------------------------------------
# Sidebar — Clean, minimal
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("#### Product Selection")
    if not product_names:
        st.warning("No products found. Please initialize the database.")
        st.stop()

    selected_product_name = st.selectbox(
        "Choose a product:", product_names, label_visibility="collapsed"
    )

    selected_prod = next(p for p in products_list if p["name"] == selected_product_name)
    product_id = selected_prod["id"]
    asin = selected_prod.get("asin", "N/A")

    st.markdown("---")
    st.caption(f"ASIN: {asin}")
    st.caption(selected_prod.get("description", ""))
    if "price" in selected_prod and selected_prod["price"]:
        st.caption(f"Price: ${selected_prod['price']}")

    st.markdown("---")
    st.markdown("#### Controls")
    if st.button("Reload Products", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("Clear Cache", use_container_width=True):
        try:
            resp = requests.delete(f"{API_BASE}/analyze/{product_id}/cache")
            if resp.status_code == 200:
                if "insights" in st.session_state:
                    del st.session_state["insights"]
                st.sidebar.success("Cache cleared.")
                st.rerun()
            else:
                st.sidebar.error(f"Failed: {resp.text}")
        except Exception as e:
            st.sidebar.error(f"Connection error: {e}")

# ---------------------------------------------------------------------------
# Main Content Area
# ---------------------------------------------------------------------------

# Fetch reviews
reviews_data = []
try:
    resp = requests.get(f"{API_BASE}/reviews/{product_id}")
    if resp.status_code == 200:
        reviews_data = resp.json().get("reviews", [])
except Exception:
    st.error(
        "Could not connect to FastAPI backend. Please verify uvicorn is running on port 8000."
    )
    st.stop()

# Analysis section
st.markdown('<div class="section-title">Analysis</div>', unsafe_allow_html=True)

analyze_btn = st.button("Analyze Reviews", type="primary", use_container_width=True)

if analyze_btn:
    import json

    progress_bar = st.progress(0, text="Initializing pipeline...")
    time_text = st.empty()

    start_time = time.time()

    try:
        response = requests.get(f"{API_BASE}/analyze/{product_id}/stream", stream=True)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status")

                    elapsed_time = time.time() - start_time
                    time_text.markdown(
                        f"<span style='color: var(--text-muted); font-size: 0.8rem;'>Elapsed: {elapsed_time:.1f}s</span>",
                        unsafe_allow_html=True,
                    )

                    if status == "init":
                        progress_bar.progress(
                            0, text=data.get("message", "Initializing...")
                        )
                    elif status == "processing":
                        processed = data.get("chunks_processed", 0)
                        total = data.get("num_chunks", 1)
                        prog = min(int((processed / total) * 90), 90)
                        progress_bar.progress(
                            prog, text=f"Processing chunks: {processed}/{total}"
                        )
                    elif status == "aggregating":
                        progress_bar.progress(95, text="Aggregating insights...")
                    elif status == "completed":
                        progress_bar.progress(100, text="Complete")

                        insights = data.get("result", [])
                        cached = data.get("cached", False)
                        reviews_analyzed = data.get("reviews_analyzed", 0)
                        execution_time = data.get("execution_time_seconds", 0.0)

                        st.session_state["insights"] = insights
                        st.session_state["cached"] = cached
                        st.session_state["reviews_analyzed"] = reviews_analyzed
                        st.session_state["execution_time"] = execution_time
                        st.session_state["analyzed_prod_id"] = product_id

                        time.sleep(0.3)
                        progress_bar.empty()
                        time_text.empty()
                        st.rerun()
                        break
                    elif status == "error":
                        st.error(f"Error: {data.get('message')}")
                        progress_bar.empty()
                        time_text.empty()
                        break
        else:
            st.error(f"Stream error: {response.text}")
            progress_bar.empty()
            time_text.empty()
    except Exception as e:
        st.error(f"Connection failed: {e}")

# ---------------------------------------------------------------------------
# Results Display
# ---------------------------------------------------------------------------
if (
    "insights" in st.session_state
    and st.session_state.get("analyzed_prod_id") == product_id
):
    insights = st.session_state["insights"]
    cached = st.session_state["cached"]
    reviews_analyzed = st.session_state["reviews_analyzed"]
    execution_time = st.session_state["execution_time"]

    # Metric cards — flat, minimal
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        if cached:
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-label">Source</div>
                <div class="metric-value" style="color: {STATUS_STYLES['Working well']['text']};">Cache Hit</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-label">Source</div>
                <div class="metric-value">Pipeline &middot; {execution_time}s</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    with m_col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Reviews Analyzed</div>
            <div class="metric-value">{reviews_analyzed}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Handle edge cases
    if isinstance(insights, str):
        st.warning("The model returned raw text instead of structured data:")
        st.text(insights)
    elif not insights:
        st.info("No actionable insights extracted from the reviews.")
    else:
        # ---------------------------------------------------------------
        # Chart — Theme-aware HTML/CSS Severity Bars
        # ---------------------------------------------------------------
        st.markdown(
            '<div class="section-title">Severity Overview</div>',
            unsafe_allow_html=True,
        )

        df_insights = pd.DataFrame(insights)

        if "score" in df_insights.columns:
            df_sorted = df_insights.sort_values(by="score", ascending=False)
        else:
            df_sorted = df_insights.copy()
            df_sorted["score"] = 0.0

        for _, row in df_sorted.iterrows():
            insight_text = row.get("insight", "Unknown")
            score = row.get("score", 0.0)
            status = row.get("status", "Needs attention")
            s_style = STATUS_STYLES.get(status, STATUS_STYLES["Needs attention"])

            st.markdown(
                f"""
                <div style="margin-bottom: 1.2rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                        <span style="font-size: 0.88rem; font-weight: 500; color: var(--app-text);">{insight_text}</span>
                        <span style="font-size: 0.85rem; font-weight: 600; color: {s_style['text']};">{score:.1f}</span>
                    </div>
                    <div style="background: var(--border-color); height: 4px; border-radius: 2px; overflow: hidden; width: 100%;">
                        <div style="background: {s_style['text']}; width: {min(score * 10, 100.0)}%; height: 100%; border-radius: 2px;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------------------------------------------------------
        # Insights Cards — Clean, flat
        # ---------------------------------------------------------------
        st.markdown(
            '<div class="section-title">Insights</div>',
            unsafe_allow_html=True,
        )

        # Filter and sort
        col1, col2 = st.columns(2)
        with col1:
            all_cats = ["All"] + sorted(
                list(
                    set(item.get("category", "other").capitalize() for item in insights)
                )
            )
            selected_category = st.selectbox("Category", all_cats)
        with col2:
            sort_options = {
                "Highest severity": ("score", True),
                "Most mentioned": ("frequency", False),
            }
            selected_sort = st.selectbox("Sort", list(sort_options.keys()))

        # Filter
        filtered = []
        for item in insights:
            cat = item.get("category", "other").capitalize()
            if selected_category == "All" or cat == selected_category:
                filtered.append(item)

        # Sort
        sort_field, ascending = sort_options[selected_sort]
        filtered = sorted(
            filtered,
            key=lambda x: float(x.get(sort_field, 0.0)),
            reverse=not ascending,
        )

        # Render cards — 2-column grid
        for i in range(0, len(filtered), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(filtered):
                    item = filtered[i + j]
                    cat = item.get("category", "other").capitalize()
                    status = item.get("status", "Needs attention")
                    score = item.get("score", 0.0)
                    freq = item.get("frequency", 1)
                    quote = item.get("example_quote", "N/A")
                    insight_text = item.get("insight", "")

                    bg_cat, text_cat = get_category_style(cat)
                    s_style = STATUS_STYLES.get(
                        status, STATUS_STYLES["Needs attention"]
                    )

                    with cols[j]:
                        st.markdown(
                            f"""
                        <div class="insight-card" title="Score: {score} | Frequency: {freq}">
                            <div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.7rem;">
                                    <span style="background: {bg_cat}; color: {text_cat}; font-size: 0.65rem; font-weight: 500; padding: 0.15rem 0.5rem; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.05em;">
                                        {cat}
                                    </span>
                                    <span style="background: {s_style['bg']}; color: {s_style['text']}; border: 1px solid {s_style['border']}; font-size: 0.65rem; font-weight: 500; padding: 0.15rem 0.5rem; border-radius: 3px;">
                                        {status}
                                    </span>
                                </div>
                                <div style="font-size: 0.9rem; font-weight: 500; color: var(--app-text); margin-bottom: 0.5rem; line-height: 1.5;">
                                    {insight_text}
                                </div>
                            </div>
                            <div>
                                <div style="color: var(--text-muted); font-size: 0.75rem; margin-bottom: 0.4rem;">
                                    {freq} mentions
                                </div>
                                <div style="font-style: italic; color: var(--text-secondary); padding-left: 0.6rem; border-left: 1px solid var(--border-color); font-size: 0.78rem; line-height: 1.5;">
                                    "{quote}"
                                </div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
else:
    st.markdown(
        """
    <div class="empty-state" style="text-align: center; padding: 3rem 1rem; font-size: 0.9rem;">
        Select a product and click <strong>Analyze Reviews</strong> to begin.
    </div>
    """,
        unsafe_allow_html=True,
    )
