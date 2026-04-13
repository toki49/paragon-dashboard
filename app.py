import re
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Paragon Fellowship · Cohort Dashboard",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal palette to reduce visual noise.
NAVY = "#142A4D"
BLUE = "#2E5BFF"
MUTED = "#6E7E96"
BG = "#F7F9FC"
CARD = "#FFFFFF"
BORDER = "#E7ECF3"
SUCCESS = "#0E9F6E"
WARNING = "#D97706"

st.markdown(
    f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] {{
      font-family: 'Inter', sans-serif;
      background-color: {BG};
      color: {NAVY};
  }}
  #MainMenu, footer, header {{ visibility: hidden; }}

  .masthead {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-radius: 14px;
      padding: 18px 22px;
      margin-bottom: 1rem;
  }}
  .masthead h1 {{ margin: 0; font-size: 1.4rem; color: {NAVY}; }}
  .masthead p {{ margin: .35rem 0 0; color: {MUTED}; font-size: .92rem; }}
  .pill {{
      display: inline-block;
      margin-top: .6rem;
      background: #EDF2FF;
      color: {BLUE};
      border: 1px solid #C9D8FF;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: .72rem;
      font-weight: 600;
      letter-spacing: .02em;
  }}
  .kpi-card {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-radius: 12px;
      padding: 14px 16px;
      height: 100%;
  }}
  .kpi-label {{ font-size: .72rem; text-transform: uppercase; color: {MUTED}; letter-spacing: .08em; }}
  .kpi-value {{ font-size: 1.55rem; font-weight: 700; color: {NAVY}; line-height: 1.2; margin-top: .25rem; }}
  .kpi-sub {{ font-size: .8rem; color: {MUTED}; margin-top: .2rem; }}
  .insight {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-left: 4px solid {BLUE};
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: .8rem;
  }}
  .insight h4 {{ margin: 0 0 .35rem; font-size: .95rem; color: {NAVY}; }}
  .insight p {{ margin: 0; color: {MUTED}; font-size: .9rem; }}
  .quote-card {{
      background: {CARD};
      border: 1px solid {BORDER};
      border-radius: 10px;
      padding: 11px 13px;
      font-size: .9rem;
      margin-bottom: .55rem;
      color: {NAVY};
  }}
  .quote-muted {{ color: {MUTED}; font-size: .83rem; margin-bottom: .2rem; }}
</style>
""",
    unsafe_allow_html=True,
)

COL_HINTS = {
    "workshops": ["policy workshops"],
    "speakers": ["speaker events"],
    "peer": ["donut buddies", "bridge buddies", "engaging were the"],
    "experience": ["experience with paragon"],
    "skills": ["developed new skills"],
    "understand": ["understanding of tech policy", "improved my understanding"],
    "interest": ["interest in pursuing a career", "career in tech policy"],
    "confidence": ["ability to procure an internship", "more confident about my ability"],
    "hours": ["hours did you spend", "hours per week"],
    "suggestions": ["suggestions for the content", "suggestions for programming"],
    "elaborate": ["elaborate on your rating", "skill growth"],
    "perspective": ["perspective on tech policy", "shifted your understanding"],
    "team": ["what project team"],
    "edu": ["current educational background"],
}

LIKERT_MAP = {
    "Strongly Agree": 5,
    "Agree": 4,
    "Neutral": 3,
    "Disagree": 2,
    "Strongly Disagree": 1,
}
HOURS_MAP = {"1-4 hours": 2.5, "5-10 hours": 7.5, "11-15 hours": 13, "16-20 hours": 18, "20+ hours": 22}
STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "is", "it", "for", "on", "that", "this", "with", "are",
    "was", "were", "be", "been", "as", "at", "my", "we", "our", "they", "their", "from", "if", "but", "have",
    "has", "had", "will", "would", "could", "should", "more", "very", "just", "about", "into", "than", "also",
}
NEGATIVE_WORDS = {
    "scheduling", "conflict", "overwhelming", "disorganized", "unclear", "confusing", "late", "busy", "workload",
    "limited", "hard", "difficult", "inconsistent", "too", "rushed", "short", "spread", "communication",
}
POSITIVE_WORDS = {
    "helpful", "great", "excellent", "valuable", "insightful", "supportive", "engaging", "strong", "improved",
    "confident", "learned", "clear", "practical", "collaborative", "amazing", "useful", "good",
}


def base_layout(height=300):
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=NAVY, size=12),
        margin=dict(l=0, r=0, t=24, b=0),
        height=height,
    )


def safe_mean(series):
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    return round(cleaned.mean(), 2) if len(cleaned) else None


def pct_agree(series):
    nums = series.map(LIKERT_MAP).dropna()
    return round(float((nums >= 4).mean()) * 100, 1) if len(nums) else None


def find_column(df, hints):
    for hint in hints:
        for c in df.columns:
            if hint.lower() in c.lower():
                return c
    return None


def map_columns(df):
    mapped = {}
    for key, hints in COL_HINTS.items():
        mapped[key] = find_column(df, hints)
    return mapped


def clean_texts(series):
    vals = [str(v).strip() for v in series.dropna().tolist()]
    return [v for v in vals if v and v.lower() not in {"na", "n/a", "none"}]


def top_keywords(texts, n=12):
    words = []
    for t in texts:
        for w in re.findall(r"\b[a-zA-Z]{4,}\b", t.lower()):
            if w not in STOPWORDS:
                words.append(w)
    return Counter(words).most_common(n)


def sentiment_counts(texts):
    pos = 0
    neg = 0
    for text in texts:
        tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))
        if tokens.intersection(POSITIVE_WORDS):
            pos += 1
        if tokens.intersection(NEGATIVE_WORDS):
            neg += 1
    return pos, neg


def cohort_label(filename):
    m = re.search(r"(SU\d+|FA\d+|SP\d+|WI\d+)", filename, re.IGNORECASE)
    return m.group(0).upper() if m else "Uploaded Cohort"


def load_data(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


st.markdown(
    """
<div class="masthead">
  <h1>Paragon Fellowship · Cohort Exit Survey Dashboard</h1>
  <p>Upload one cohort file to get quantitative outcomes and qualitative "what went right / what went wrong" analysis.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Input Data")
    cohort_file = st.file_uploader("Primary cohort survey", type=["csv", "xlsx"], key="primary")
    baseline_file = st.file_uploader("Optional baseline cohort for comparison", type=["csv", "xlsx"], key="baseline")
    st.caption("Tip: export Google Forms responses as CSV, or upload Excel files directly.")

if cohort_file is None:
    st.info("Upload a cohort survey file in the sidebar to generate the dashboard.")
    st.stop()

df = load_data(cohort_file)
df.columns = [str(c).strip() for c in df.columns]
cols = map_columns(df)
cohort_name = cohort_label(cohort_file.name)
responses = len(df)

st.markdown(f'<span class="pill">{cohort_name} · {responses} responses</span>', unsafe_allow_html=True)

metrics = {
    "Policy Workshops": safe_mean(df[cols["workshops"]]) if cols["workshops"] else None,
    "Speaker Events": safe_mean(df[cols["speakers"]]) if cols["speakers"] else None,
    "Peer / Buddy Experience": safe_mean(df[cols["peer"]]) if cols["peer"] else None,
    "Overall Experience": safe_mean(df[cols["experience"]]) if cols["experience"] else None,
    "Skill Growth": safe_mean(df[cols["skills"]]) if cols["skills"] else None,
}
outcomes = {
    "Improved Tech Policy Understanding": pct_agree(df[cols["understand"]]) if cols["understand"] else None,
    "Increased Career Interest": pct_agree(df[cols["interest"]]) if cols["interest"] else None,
    "Internship Confidence": pct_agree(df[cols["confidence"]]) if cols["confidence"] else None,
}
hours_avg = None
if cols["hours"]:
    hours_avg = round(df[cols["hours"]].map(HOURS_MAP).dropna().mean(), 1)

text_columns = [cols["suggestions"], cols["elaborate"], cols["perspective"]]
all_texts = []
for t_col in text_columns:
    if t_col:
        all_texts.extend(clean_texts(df[t_col]))

keyword_pairs = top_keywords(all_texts, n=12)
pos_count, neg_count = sentiment_counts(all_texts)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "What Went Right", "What Went Wrong", "Cohort Comparison"])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Respondents</div><div class="kpi-value">{responses}</div><div class="kpi-sub">submitted exit survey</div></div>',
        unsafe_allow_html=True,
    )
    c2.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Overall Experience</div><div class="kpi-value">{metrics["Overall Experience"] if metrics["Overall Experience"] is not None else "—"}/5</div><div class="kpi-sub">average rating</div></div>',
        unsafe_allow_html=True,
    )
    c3.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Avg Weekly Hours</div><div class="kpi-value">{hours_avg if hours_avg is not None else "—"}</div><div class="kpi-sub">estimated commitment</div></div>',
        unsafe_allow_html=True,
    )
    c4.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Outcome Signals</div><div class="kpi-value">{sum(v is not None for v in outcomes.values())}/3</div><div class="kpi-sub">tracked outcome questions found</div></div>',
        unsafe_allow_html=True,
    )

    ratings_df = pd.DataFrame(
        [{"metric": k, "value": v} for k, v in metrics.items() if v is not None]
    ).sort_values("value", ascending=False)
    if not ratings_df.empty:
        fig = go.Figure(
            go.Bar(
                x=ratings_df["value"],
                y=ratings_df["metric"],
                orientation="h",
                marker_color=BLUE,
                text=ratings_df["value"].map(lambda x: f"{x:.2f}/5"),
                textposition="outside",
            )
        )
        fig.update_layout(
            **base_layout(320),
            xaxis=dict(range=[0, 5.4], showgrid=False, title=None),
            yaxis=dict(showgrid=False, autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

    outcome_df = pd.DataFrame([{"outcome": k, "pct": v} for k, v in outcomes.items() if v is not None])
    if not outcome_df.empty:
        fig2 = go.Figure(
            go.Bar(
                x=outcome_df["pct"],
                y=outcome_df["outcome"],
                orientation="h",
                marker_color=NAVY,
                text=outcome_df["pct"].map(lambda x: f"{x:.1f}%"),
                textposition="outside",
            )
        )
        fig2.update_layout(
            **base_layout(280),
            xaxis=dict(range=[0, 105], showgrid=False, title="% Agree / Strongly Agree"),
            yaxis=dict(showgrid=False, autorange="reversed"),
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    strengths = sorted([(k, v) for k, v in metrics.items() if v is not None], key=lambda x: x[1], reverse=True)[:3]
    for label, value in strengths:
        st.markdown(
            f'<div class="insight"><h4>{label} is a strength</h4><p>Average rating is <strong>{value:.2f}/5</strong>, indicating fellows generally rated this area positively.</p></div>',
            unsafe_allow_html=True,
        )

    if pos_count > 0:
        st.markdown(
            f'<div class="insight"><h4>Positive sentiment in open responses</h4><p>{pos_count} comments included terms like "helpful", "valuable", or "engaging", which reinforces strengths seen in the quantitative scores.</p></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Representative Positive Themes")
    if keyword_pairs:
        top_positive = [w for w, _ in keyword_pairs if w not in NEGATIVE_WORDS][:8]
        if top_positive:
            st.write(", ".join(top_positive))
    sample_texts = [t for t in all_texts if set(re.findall(r"\b[a-zA-Z]{3,}\b", t.lower())).intersection(POSITIVE_WORDS)][:5]
    for quote in sample_texts:
        st.markdown(f'<div class="quote-card"><div class="quote-muted">Open response</div>{quote}</div>', unsafe_allow_html=True)

with tab3:
    risks = sorted([(k, v) for k, v in metrics.items() if v is not None], key=lambda x: x[1])[:3]
    for label, value in risks:
        st.markdown(
            f'<div class="insight"><h4>{label} needs attention</h4><p>Average rating is <strong>{value:.2f}/5</strong>. Consider operational changes, clearer expectations, or format improvements here.</p></div>',
            unsafe_allow_html=True,
        )

    if neg_count > 0:
        st.markdown(
            f'<div class="insight"><h4>Negative sentiment signals</h4><p>{neg_count} comments contain terms tied to friction (for example scheduling, workload, or clarity), suggesting actionable pain points.</p></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Top Pain-Point Keywords")
    neg_keywords = [(w, c) for w, c in keyword_pairs if w in NEGATIVE_WORDS]
    if neg_keywords:
        neg_df = pd.DataFrame(neg_keywords, columns=["word", "count"]).sort_values("count", ascending=False)
        fig3 = go.Figure(
            go.Bar(
                x=neg_df["count"],
                y=neg_df["word"],
                orientation="h",
                marker_color=WARNING,
                text=neg_df["count"],
                textposition="outside",
            )
        )
        fig3.update_layout(
            **base_layout(260),
            xaxis=dict(showgrid=False, title=None),
            yaxis=dict(showgrid=False, autorange="reversed", title=None),
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.caption("No clear negative keyword cluster detected from current open responses.")

    sample_neg = [t for t in all_texts if set(re.findall(r"\b[a-zA-Z]{3,}\b", t.lower())).intersection(NEGATIVE_WORDS)][:6]
    for quote in sample_neg:
        st.markdown(f'<div class="quote-card"><div class="quote-muted">Open response</div>{quote}</div>', unsafe_allow_html=True)

with tab4:
    if baseline_file is None:
        st.info("Upload an optional baseline cohort in the sidebar to compare cohorts side-by-side.")
    else:
        base_df = load_data(baseline_file)
        base_df.columns = [str(c).strip() for c in base_df.columns]
        base_cols = map_columns(base_df)
        base_name = cohort_label(baseline_file.name)

        compare_rows = []
        for metric_label, key in [
            ("Policy Workshops", "workshops"),
            ("Speaker Events", "speakers"),
            ("Peer / Buddy Experience", "peer"),
            ("Overall Experience", "experience"),
            ("Skill Growth", "skills"),
        ]:
            a_val = safe_mean(base_df[base_cols[key]]) if base_cols[key] else None
            b_val = safe_mean(df[cols[key]]) if cols[key] else None
            if a_val is not None and b_val is not None:
                compare_rows.append(
                    {"Metric": metric_label, base_name: a_val, cohort_name: b_val, "Delta": round(b_val - a_val, 2)}
                )

        if compare_rows:
            comp_df = pd.DataFrame(compare_rows)
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

            fig4 = go.Figure()
            fig4.add_trace(
                go.Bar(
                    name=base_name,
                    x=comp_df["Metric"],
                    y=comp_df[base_name],
                    marker_color=NAVY,
                    text=comp_df[base_name].map(lambda x: f"{x:.2f}"),
                    textposition="outside",
                )
            )
            fig4.add_trace(
                go.Bar(
                    name=cohort_name,
                    x=comp_df["Metric"],
                    y=comp_df[cohort_name],
                    marker_color=BLUE,
                    text=comp_df[cohort_name].map(lambda x: f"{x:.2f}"),
                    textposition="outside",
                )
            )
            fig4.update_layout(
                **base_layout(330),
                barmode="group",
                xaxis=dict(showgrid=False),
                yaxis=dict(range=[0, 5.5], showgrid=False, title="Average Rating"),
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig4, use_container_width=True)

            improved = comp_df[comp_df["Delta"] > 0.05]["Metric"].tolist()
            declined = comp_df[comp_df["Delta"] < -0.05]["Metric"].tolist()
            st.markdown(
                f'<div class="insight"><h4>Cross-cohort readout</h4><p><strong>Improved:</strong> {", ".join(improved) if improved else "None flagged"} · <strong>Declined:</strong> {", ".join(declined) if declined else "None flagged"}.</p></div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("Could not find enough matching question columns across both files to compare.")