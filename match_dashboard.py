import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="🚀 Startup Matchmaking Engine")

# --- Load Data ---
founder_matches = pd.read_csv("founder_top_matches.csv")
provider_matches = pd.read_csv("provider_top_matches.csv")
df = pd.read_csv("Cleaned_User_Matching_Dataset.csv")

# --- Ensure Required Columns Exist ---
for match_df in [founder_matches, provider_matches]:
    if "reason" not in match_df.columns:
        match_df["reason"] = "Explanation not available"
    if "match_score" not in match_df.columns:
        match_df["match_score"] = 0

# --- Helper: Replace user_id with name ---
def get_name(user_id):
    row = df[df["user_id"] == user_id]
    if "name" in df.columns and not row.empty and pd.notna(row["name"].values[0]):
        return row["name"].values[0]
    return user_id

# Replace IDs with names where possible
founder_matches["founder"] = founder_matches["founder_id"].apply(get_name)
founder_matches["provider"] = founder_matches["provider_id"].apply(get_name)  

provider_matches["provider"] = provider_matches["provider_id"].apply(get_name)
provider_matches["founder"] = provider_matches["founder_id"].apply(get_name)  


# --- Sidebar Filters ---
with st.sidebar:
    st.header("🔍 Filter Matches")
    industry_filter = st.multiselect("Filter by Industry", options=df['startup_industry'].dropna().unique())
    skill_filter = st.text_input("Search Reason/Skills")

# --- Main Interface ---
st.title("🤝 Startup Matchmaking Dashboard")
tab1, tab2, tab3 = st.tabs(["🔹 Match Explorer", "📊 Insights", "ℹ️ About"])

# --- TAB 1: Match Explorer ---
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💼 Founders → Top Matches")
        selected_founder = st.selectbox("Choose Founder", founder_matches["founder"].unique())
        f_data = founder_matches[founder_matches["founder"] == selected_founder]

        if industry_filter:
            provider_ids = df[df["startup_industry"].isin(industry_filter)]["user_id"].tolist()
            f_data = f_data[f_data["matched_provider_id"].isin(provider_ids)]

        if skill_filter:
            f_data = f_data[f_data["reason"].str.lower().str.contains(skill_filter.lower())]

        st.dataframe(f_data[["provider", "match_score", "reason"]].sort_values(by="match_score", ascending=False), use_container_width=True)

    with col2:
        st.subheader("🧑‍🏫 Providers → Top Matches")
        selected_provider = st.selectbox("Choose Provider", provider_matches["provider"].unique())
        p_data = provider_matches[provider_matches["provider"] == selected_provider]

        if industry_filter:
            founder_ids = df[df["startup_industry"].isin(industry_filter)]["user_id"].tolist()
            p_data = p_data[p_data["matched_founder_id"].isin(founder_ids)]

        if skill_filter:
            p_data = p_data[p_data["reason"].str.lower().str.contains(skill_filter.lower())]

        st.dataframe(p_data[["founder", "match_score", "reason"]].sort_values(by="match_score", ascending=False), use_container_width=True)

# --- TAB 2: Insights ---
with tab2:
    st.subheader("🎯 Match Score Insights")

    st.markdown("##### 🔹 How strong are our top matches?")
    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.histogram(founder_matches, x="match_score", nbins=20,
                            title="Founder → Provider Match Score Distribution",
                            labels={"match_score": "Match Score"})
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("This chart shows how strong the matches are for founders. A right-skew means better matches.")

    with col2:
        fig2 = px.histogram(provider_matches, x="match_score", nbins=20,
                            title="Provider → Founder Match Score Distribution",
                            labels={"match_score": "Match Score"})
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("This chart shows how strong the matches are for providers. Look for clustering near 100 for high quality.")

    st.markdown("##### 🔹 What industries are most aligned?")
    industry_df = founder_matches.copy()
    industry_df["industry_match"] = industry_df["reason"].apply(lambda r: "Industry aligned" in r)
    top_industries = industry_df.merge(df[["user_id", "startup_industry"]], left_on="founder_id", right_on="user_id")
    industry_counts = top_industries.groupby("startup_industry")["industry_match"].mean().reset_index()
    fig3 = px.bar(industry_counts, x="startup_industry", y="industry_match",
                  labels={"industry_match": "Industry Match Rate"},
                  title="Average Industry Match Rate by Startup Industry")
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Industries with higher bars have more matches where founders and providers share the same domain.")

    st.markdown("##### 🔹 Average Match Score by Startup Stage")
    founder_df = founder_matches.merge(df[["user_id", "startup_stage"]], left_on="founder_id", right_on="user_id")
    avg_stage_scores = founder_df.groupby("startup_stage")["match_score"].mean().reset_index()
    fig4 = px.bar(avg_stage_scores, x="startup_stage", y="match_score", 
                  title="Average Match Score by Startup Stage", 
                  labels={"match_score": "Average Match Score"})
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("##### 🧊 Match Score Heatmap")

    try:
        image = Image.open("match_matrix_heatmap.png")
        st.image(image, caption="Pairwise Match Score Matrix", use_container_width=True)
        st.caption("Each cell represents the score between one founder and one provider. Darker means stronger match.")
    except Exception as e:
        st.error(f"Heatmap image not found or failed to load: {e}")

# --- TAB 3: About ---
with tab3:
    st.markdown("""
    ## 💡 How the Matching Works

    This dashboard uses a scoring algorithm to match Founders with Service Providers/Mentors based on:

    | Matching Criteria            | Weight |
    |-----------------------------|--------|
    | 🏭 Industry Alignment       | 25%    |
    | 🛠 Technical Skill Match     | 25%    |
    | 🎯 Project Type Compatibility | 20%   |
    | ⏰ Timeline Availability     | 20%    |
    | 🔄 Startup Stage Fit        | 10%    |

    ### 🧾 Files Used
    - `Cleaned_User_Matching_Dataset.csv`: Profile information for founders & providers
    - `founder_top_matches.csv`, `provider_top_matches.csv`: Precomputed top match scores
    - `match_matrix_heatmap.png`: Heatmap visualization of match scores

    ### 📘 How to Use
    - Select a **founder** or **provider** to explore their top 5 matches.
    - Use filters in the sidebar to narrow results by **industry** or **skills**.
    - Dive into the **Insights tab** for score distributions and patterns.
    """)
