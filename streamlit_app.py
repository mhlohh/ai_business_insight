import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import re
from logger import logger

# Page config
st.set_page_config(
    page_title="AI Product Insights Dashboard", page_icon="📈", layout="wide"
)

# Inline SVG Logos
SVG_GEAR = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'

SVG_SEARCH = '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4a6b82" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 10px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'

SVG_PACKAGE = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4a6b82" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><polygon points="12 22.08 12 12 3 6.92 3 17.08 12 22.08"></polygon><polygon points="12 12 21 6.92 21 17.08 12 22.08"></polygon><polygon points="12 2 21 6.92 12 12 3 6.92 12 2"></polygon><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>'

SVG_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4a6b82" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'

SVG_TRENDING = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#b27a50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'

SVG_LIST = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4a6b82" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>'

SVG_TAG = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>'

SVG_REFRESH = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>'

SVG_TARGET = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4a5568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>'

# Custom CSS for Neumorphism (Soft UI) with Consistent Palette
neumorphic_css = """
<style>
    /* Global Styles */
    .stApp {
        background-color: #e0e5ec !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #e0e5ec !important;
        box-shadow: 4px 0 15px rgba(163, 177, 198, 0.4) !important;
        border-right: none !important;
    }
    
    /* Top Header Bar */
    header[data-testid="stHeader"] {
        background-color: #ffffff !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
    }
    header[data-testid="stHeader"] * {
        color: #4a5568 !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #4a5568 !important;
        font-family: 'Outfit', 'Inter', -apple-system, sans-serif !important;
    }
    
    /* Title Styling */
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        color: #4a6b82 !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8), -1px -1px 2px rgba(163,177,198,0.6);
    }
    
    /* Neumorphic Cards */
    .neumorphic-card {
        background-color: #e0e5ec;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 9px 9px 16px rgba(163, 177, 198, 0.6), 
                    -9px -9px 16px rgba(255, 255, 255, 0.6);
        border: none;
    }
    
    .neumorphic-card-inset {
        background-color: #e0e5ec;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: inset 6px 6px 10px rgba(163, 177, 198, 0.5), 
                    inset -6px -6px 10px rgba(255, 255, 255, 0.6);
        border: none;
    }

    /* KPI metric cards */
    .kpi-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
    }
    .kpi-card {
        flex: 1;
        background-color: #e0e5ec;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 6px 6px 12px rgba(163, 177, 198, 0.5), 
                    -6px -6px 12px rgba(255, 255, 255, 0.6);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #4a6b82 !important;
        margin: 5px 0;
    }
    .kpi-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #718096 !important;
    }
    
    /* Neumorphic Badges */
    .category-badge {
        background-color: #e0e5ec;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #4a5568 !important;
        box-shadow: inset 3px 3px 6px rgba(163, 177, 198, 0.4), 
                    inset -3px -3px 6px rgba(255, 255, 255, 0.6);
        display: inline-block;
    }
    
    .score-badge {
        background-color: #e0e5ec;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        color: #b27a50 !important;
        box-shadow: 3px 3px 6px rgba(163, 177, 198, 0.4), 
                    -3px -3px 6px rgba(255, 255, 255, 0.6);
        display: inline-block;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #e0e5ec !important;
        color: #4a5568 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        box-shadow: 6px 6px 12px rgba(163, 177, 198, 0.6), 
                    -6px -6px 12px rgba(255, 255, 255, 0.6) !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        color: #4a6b82 !important;
        box-shadow: 3px 3px 6px rgba(163, 177, 198, 0.6), 
                    -3px -3px 6px rgba(255, 255, 255, 0.6) !important;
    }
    
    div.stButton > button:active {
        box-shadow: inset 4px 4px 8px rgba(163, 177, 198, 0.7), 
                    inset -4px -4px 8px rgba(255, 255, 255, 0.8) !important;
    }

    /* Selectbox & Inputs */
    div[data-baseweb="select"] {
        background-color: #e0e5ec !important;
        border-radius: 12px !important;
        box-shadow: inset 4px 4px 8px rgba(163, 177, 198, 0.5), 
                    inset -4px -4px 8px rgba(255, 255, 255, 0.6) !important;
        border: none !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: transparent !important;
        border: none !important;
    }
</style>
"""
st.markdown(neumorphic_css, unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown(
    f'<div class="neumorphic-card" style="padding: 15px;">'
    f'<h3 style="margin-top:0; text-align:center; display:flex; align-items:center; justify-content:center;">'
    f"{SVG_GEAR}Configuration</h3>"
    f"</div>",
    unsafe_allow_html=True,
)

backend_url = "http://localhost:8000"


# Fetch products
@st.cache_data(ttl=60)
def fetch_products(api_url):
    logger.info(f"Streamlit - Fetching products from {api_url}/products/")
    try:
        response = requests.get(f"{api_url}/products/")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Streamlit - Successfully fetched {len(data)} products")
            return data
    except Exception as e:
        logger.error(f"Streamlit - Error connecting to backend: {e}")
        st.sidebar.error(f"Error connecting to backend: {e}")
    return []


products = fetch_products(backend_url)

if not products:
    st.markdown(
        f'<div class="neumorphic-card" style="border-left: 5px solid #b85c5c; padding: 20px;">'
        f'<h3 style="color: #b85c5c !important; margin: 0;">Connection Error</h3>'
        f'<p style="color: #718096 !important; margin: 5px 0 0 0;">Could not retrieve products. Please ensure the FastAPI backend is running.</p>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# Product list formatter
product_options = {p["name"]: p["id"] for p in products}
selected_product_name = st.sidebar.selectbox(
    "Select a Product", list(product_options.keys())
)
selected_product_id = product_options[selected_product_name]
logger.info(
    f"Streamlit - User active product: {selected_product_name} (ID: {selected_product_id})"
)

# Refresh Cache button
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("Clear Cache"):
    logger.info(
        f"Streamlit - User triggered Cache Clear for product ID {selected_product_id}"
    )
    try:
        res = requests.delete(f"{backend_url}/insights/products/{selected_product_id}")
        if res.status_code == 200:
            logger.info(
                f"Streamlit - Cache successfully cleared on backend for product ID {selected_product_id}"
            )
            st.sidebar.success("Cache cleared successfully!")
            st.cache_data.clear()
        else:
            logger.error(
                f"Streamlit - Failed to clear cache on backend for product ID {selected_product_id}. Status: {res.status_code}"
            )
            st.sidebar.error("Failed to clear cache.")
    except Exception as e:
        logger.error(
            f"Streamlit - Exception during cache clear for product ID {selected_product_id}: {e}"
        )
        st.sidebar.error(f"Error: {e}")

# Main Layout Header
st.markdown(
    f'<div class="main-title">{SVG_SEARCH}AI Product Review Insights</div>',
    unsafe_allow_html=True,
)

# Product Info Card
st.markdown(
    f'<div class="neumorphic-card">'
    f'<h2 style="margin: 0; color: #4a6b82 !important; display: flex; align-items: center;">'
    f"{SVG_PACKAGE}{selected_product_name}</h2>"
    f'<p style="margin: 5px 0 0 0; color: #718096 !important; font-size: 0.95rem;">Product ID: {selected_product_id}</p>'
    f"</div>",
    unsafe_allow_html=True,
)


# Fetch Insights
def get_insights(api_url, product_id):
    logger.info(f"Streamlit - Requesting insights for product ID {product_id}")
    try:
        res = requests.get(f"{api_url}/insights/products/{product_id}")
        if res.status_code == 200:
            data = res.json()
            # If the backend returned wrapped cache data: {"status": "success", "data": {"analysis": "..."}}
            if isinstance(data, dict) and data.get("status") == "success":
                inner_data = data.get("data", {})
                if "analysis" in inner_data:
                    try:
                        import json

                        logger.info(
                            f"Streamlit - Cache hit for product ID {product_id} (wrapped data)"
                        )
                        return json.loads(inner_data["analysis"]), None
                    except Exception as e:
                        logger.error(
                            f"Streamlit - Failed to parse wrapped insights json for product ID {product_id}: {e}"
                        )
                        pass
                logger.info(f"Streamlit - Cache hit for product ID {product_id}")
                return inner_data, None
            logger.info(
                f"Streamlit - Successfully fetched insights for product ID {product_id}"
            )
            return data, None
        else:
            detail = res.json().get("detail", "Failed to fetch insights")
            logger.warning(
                f"Streamlit - Failed to fetch insights for product ID {product_id}. Status: {res.status_code}, Detail: {detail}"
            )
            return None, detail
    except Exception as e:
        logger.error(
            f"Streamlit - Exception during fetching insights for product ID {product_id}: {e}"
        )
        return None, str(e)


insights_data, error = get_insights(backend_url, selected_product_id)

if error:
    st.markdown(
        f'<div class="neumorphic-card" style="text-align: center; padding: 40px; border-top: 4px solid #b27a50;">'
        f'<h3 style="color: #b27a50 !important; margin: 0 0 10px 0;">No insights cached for this product yet.</h3>'
        f'<p style="color: #718096 !important; margin: 0;">The reviews need to be processed by the AI pipeline.</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    if st.button("Generate AI Insights"):
        logger.info(
            f"Streamlit - User triggered AI Insight generation for product ID {selected_product_id}"
        )
        with st.spinner("Processing reviews with parallel LLM agents... Please wait."):
            # Re-fetch which triggers generation
            insights_data, error = get_insights(backend_url, selected_product_id)
            if error:
                logger.error(
                    f"Streamlit - Generation failed for product ID {selected_product_id}: {error}"
                )
                st.markdown(
                    f'<div class="neumorphic-card" style="border-left: 5px solid #b85c5c; padding: 20px; margin-top: 15px;">'
                    f'<h4 style="color: #b85c5c !important; margin: 0;">Analysis Failed</h4>'
                    f'<p style="color: #718096 !important; margin: 5px 0 0 0;">{error}</p>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                logger.info(
                    f"Streamlit - Generation succeeded and cache loaded for product ID {selected_product_id}"
                )
                st.success("Successfully generated new insights!")
                st.rerun()
else:
    # Render Insights
    insights = (
        insights_data.get("insights", [])
        if isinstance(insights_data, dict)
        else insights_data
    )

    if not insights:
        st.info("No insights found.")
        st.stop()

    # Create initial DataFrame
    df = pd.DataFrame(insights)

    # Category weights for frontend score calculation fallback
    category_weights = {
        "quality": 1.5,
        "support": 1.2,
        "usability": 1.3,
        "price": 1.0,
    }

    # Ensure score is computed on the frontend if missing in the API response
    if "score" not in df.columns or df["score"].isnull().all():
        scores = []
        for idx, row in df.iterrows():
            freq = float(row.get("frequency", 1))
            conf = float(row.get("confidence", 0.8))
            cat = str(row.get("category", "other")).lower().strip()
            weight = category_weights.get(cat, 1.0)
            scores.append(round(freq * conf * weight, 2))
        df["score"] = scores

    # Sidebar Filter Controls
    st.sidebar.markdown(
        f'<div class="neumorphic-card" style="padding: 12px; margin-top: 20px;">'
        f'<h4 style="margin:0; text-align:center; color:#4a6b82 !important;">Filter Insights</h4>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Category Filter
    all_categories = sorted(df["category"].str.title().unique())
    selected_categories = st.sidebar.multiselect(
        "Select Categories", options=all_categories, default=all_categories
    )

    # Frequency Filter
    min_freq_val = float(df["frequency"].min()) if "frequency" in df.columns else 1.0
    max_freq_val = float(df["frequency"].max()) if "frequency" in df.columns else 10.0

    if min_freq_val == max_freq_val:
        min_freq_val = 0.0

    selected_min_freq = st.sidebar.slider(
        "Min Mentions (Frequency)",
        min_value=float(min_freq_val),
        max_value=float(max_freq_val),
        value=float(min_freq_val),
        step=1.0,
    )

    # Apply Filters to DataFrame
    df_filtered = df.copy()
    if selected_categories:
        df_filtered = df_filtered[
            df_filtered["category"].str.title().isin(selected_categories)
        ]
    else:
        df_filtered = df_filtered.iloc[0:0]  # Empty df if no categories selected

    if "frequency" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["frequency"] >= selected_min_freq]

    # Calculate stats based on filtered data
    total_insights = len(df_filtered)

    # Calculate avg confidence
    avg_conf = (
        df_filtered["confidence"].mean() * 100
        if "confidence" in df_filtered.columns and not df_filtered.empty
        else 0
    )
    # Top Category
    top_cat = (
        df_filtered["category"].mode()[0]
        if "category" in df_filtered.columns and not df_filtered["category"].empty
        else "N/A"
    )

    # KPI Grid
    st.markdown(
        f'<div class="kpi-container">'
        f'  <div class="kpi-card">'
        f'    <div class="kpi-label">Total Insights</div>'
        f'    <div class="kpi-value">{total_insights}</div>'
        f"  </div>"
        f'  <div class="kpi-card">'
        f'    <div class="kpi-label">Top Category</div>'
        f'    <div class="kpi-value">{top_cat.title()}</div>'
        f"  </div>"
        f'  <div class="kpi-card">'
        f'    <div class="kpi-label">Avg Confidence</div>'
        f'    <div class="kpi-value">{avg_conf:.1f}%</div>'
        f"  </div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not df_filtered.empty:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown(
                f'<div class="neumorphic-card">'
                f'<h3 style="margin-top:0; display: flex; align-items: center;">'
                f"{SVG_CHART}Insight Categories Distribution</h3>",
                unsafe_allow_html=True,
            )

            category_counts = df_filtered["category"].str.title().value_counts()
            fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
            fig.patch.set_facecolor("#e0e5ec")
            ax.set_facecolor("#e0e5ec")

            bars = ax.bar(
                category_counts.index,
                category_counts.values,
                color="#4a6b82",
                edgecolor="#354e60",
                width=0.6,
                linewidth=1.5,
            )

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#718096")
            ax.spines["bottom"].set_color("#718096")
            ax.tick_params(colors="#4a5568", labelsize=10)
            ax.set_ylabel("Count of Insights", color="#4a5568", fontsize=11)

            plt.xticks(rotation=45, ha="right")
            fig.tight_layout()

            st.pyplot(fig)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(
                f'<div class="neumorphic-card">'
                f'<h3 style="margin-top:0; display: flex; align-items: center;">'
                f"{SVG_TRENDING}Insights ranked by Score</h3>",
                unsafe_allow_html=True,
            )

            if "score" in df_filtered.columns:
                df_sorted = df_filtered.sort_values(by="score", ascending=True).tail(
                    5
                )  # Top 5
                fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
                fig.patch.set_facecolor("#e0e5ec")
                ax.set_facecolor("#e0e5ec")

                short_labels = [
                    label[:25] + "..." if len(label) > 25 else label
                    for label in df_sorted["insight"]
                ]
                ax.barh(
                    short_labels,
                    df_sorted["score"],
                    color="#b27a50",
                    edgecolor="#8c5e3d",
                    height=0.5,
                    linewidth=1.5,
                )

                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_color("#718096")
                ax.spines["bottom"].set_color("#718096")
                ax.tick_params(colors="#4a5568", labelsize=10)
                ax.set_xlabel("Impact Score", color="#4a5568", fontsize=11)
                fig.tight_layout()

                st.pyplot(fig)
            else:
                st.write("Score parameter not computed yet.")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="neumorphic-card" style="text-align: center; padding: 40px; border-top: 4px solid #b85c5c;">'
            f'<h3 style="color: #b85c5c !important; margin: 0 0 10px 0;">No matching insights</h3>'
            f'<p style="color: #718096 !important; margin: 0;">Adjust your sidebar filters to display data and visualizations.</p>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # Full insights list Header
    st.markdown(
        f'<h2 style="margin-top:20px; color:#4a6b82; display: flex; align-items: center;">'
        f"{SVG_LIST}AI Insights List</h2>",
        unsafe_allow_html=True,
    )

    if not df_filtered.empty:
        for idx, row in df_filtered.sort_values(by="score", ascending=False).iterrows():
            score_val = row.get("score", 0)
            category_name = str(row.get("category", "other")).title()

            st.markdown(
                f'<div class="neumorphic-card">'
                f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">'
                f'    <span class="category-badge" style="display: flex; align-items: center;">{SVG_TAG}{category_name}</span>'
                f'    <span class="score-badge">Impact: {score_val}</span>'
                f"  </div>"
                f'  <h3 style="margin: 0 0 10px 0; color: #2d3748; font-size: 1.25rem;">{row.get("insight")}</h3>'
                f'  <div class="neumorphic-card-inset">'
                f'    <p style="font-style: italic; color: #4a5568; margin: 0; font-size: 0.95rem;">'
                f'      “{row.get("example_quote")}”'
                f"    </p>"
                f"  </div>"
                f'  <div style="display: flex; gap: 20px; font-size: 0.85rem; color: #718096; margin-top: 15px; border-top: 1px dashed #cbd5e0; padding-top: 10px;">'
                f'    <span style="display: flex; align-items: center;">{SVG_REFRESH}<strong>Frequency:</strong> &nbsp;{int(row.get("frequency", 1))}</span>'
                f'    <span style="display: flex; align-items: center;">{SVG_TARGET}<strong>Confidence:</strong> &nbsp;{row.get("confidence") * 100:.0f}%</span>'
                f"  </div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f'<div class="neumorphic-card" style="text-align: center; padding: 25px;">'
            f'<p style="color: #718096 !important; margin: 0;">Use the filters in the sidebar to populate insights.</p>'
            f"</div>",
            unsafe_allow_html=True,
        )
