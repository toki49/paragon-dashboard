import os
import re
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from airtable_client import fetch_airtable_table
from mapping import build_mapping
from qualitative import (
    aggregate_dashboard_signals,
    analyze_responses,
    representative_sentences,
    top_keywords,
    top_theme_rows,
)

load_dotenv()

st.set_page_config(
    page_title="Paragon Fellowship · Cohort Dashboard",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
  .mapping-low {{ color: #B45309; font-weight: 600; }}
  .mapping-high {{ color: #047857; font-weight: 600; }}
  .source-tabs {{
      border: 1px solid {BORDER};
      border-radius: 10px;
      padding: 6px 8px 10px;
      margin-bottom: 10px;
      background: {CARD};
  }}
  .source-tabs-title {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: {MUTED};
      margin-bottom: 6px;
      font-weight: 600;
  }}
</style>
""",
    unsafe_allow_html=True,
)

LIKERT_MAP = {
    "Strongly Agree": 5,
    "Agree": 4,
    "Neutral": 3,
    "Disagree": 2,
    "Strongly Disagree": 1,
}
HOURS_MAP = {"1-4 hours": 2.5, "5-10 hours": 7.5, "11-15 hours": 13, "16-20 hours": 18, "20+ hours": 22}


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


def clean_texts(series):
    vals = [str(v).strip() for v in series.dropna().tolist()]
    return [v for v in vals if v and v.lower() not in {"na", "n/a", "none"}]


def cohort_label(filename):
    m = re.search(r"(SU\d+|FA\d+|SP\d+|WI\d+)", filename, re.IGNORECASE)
    return m.group(0).upper() if m else "Uploaded Cohort"


def load_data(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def csv_fallback_mapping(df):
    """Heuristic mapping for exported CSV/XLSX survey files (manual upload)."""
    hints = {
        "workshops": ["policy workshops", "helpful were the policy workshops"],
        "speakers": ["speaker events", "insightful were the speaker events"],
        "peer": ["donut buddies", "bridge buddies", "engaging were the"],
        "experience": ["experience with paragon", "how was your experience"],
        "skills": ["developed new skills", "skill growth"],
        "understand": ["improved my understanding", "understanding of tech policy"],
        "interest": ["increased my interest", "career in tech policy"],
        "confidence": ["confident about my ability", "procure an internship"],
        "hours": ["hours did you spend", "hours per week"],
        "suggestions": ["suggestions for the content", "suggestions for programming"],
        "elaborate": ["elaborate on your rating", "skill growth"],
        "perspective": ["perspective on tech policy", "shifted your understanding"],
        "team": ["what project team were you on", "project team"],
        "edu": ["current educational background", "educational background"],
    }
    mapped = {}
    lower_cols = {c: str(c).strip().lower() for c in df.columns}
    for key, key_hints in hints.items():
        match = None
        for hint in key_hints:
            for col, col_low in lower_cols.items():
                if hint in col_low:
                    match = col
                    break
            if match:
                break
        mapped[key] = match
    return mapped


@st.cache_data(show_spinner=False, ttl=300)
def load_airtable_data(token, base_id, table_name, view_name):
    records = fetch_airtable_table(
        token=token,
        base_id=base_id,
        table_name=table_name,
        view_name=view_name,
    )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def read_source_dataframe(source_mode):
    source_name = ""
    cohort_name_value = "Uploaded Cohort"
    status = ""
    df_value = None

    if source_mode == "Airtable (Live)":
        token = os.getenv("AIRTABLE_TOKEN")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        table_name = os.getenv("AIRTABLE_TABLE")
        default_view = os.getenv("AIRTABLE_VIEW", "")
        dv = default_view.strip() if isinstance(default_view, str) else ""
        view_name = dv if dv else None

        if not token or not base_id or not table_name:
            st.warning(
                "Missing Airtable secrets. Add AIRTABLE_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_TABLE in your .env file "
                "or switch to Manual Upload."
            )
            return None, "", ""

        try:
            df_value = load_airtable_data(token, base_id, table_name, view_name)
            source_name = f"Airtable · {table_name}"
            cohort_name_value = "Airtable Cohort"
            status = f"Connected to Airtable ({len(df_value)} rows) · refreshed {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        except Exception as exc:
            st.error(f"Airtable fetch failed: {exc}")
            return None, "", ""

    else:
        upload = st.session_state.get("manual_file")
        if upload is None:
            return None, "", ""
        df_value = load_data(upload)
        source_name = "Manual Upload"
        cohort_name_value = cohort_label(upload.name)
        status = f"Loaded uploaded file ({len(df_value)} rows)"

    if df_value is not None:
        df_value.columns = [str(c).strip() for c in df_value.columns]
    return df_value, cohort_name_value, f"{source_name} · {status}"


st.markdown(
    """
<div class="masthead">
  <h1>Paragon Fellowship · Cohort Exit Survey Dashboard</h1>
  <p>Connect Airtable or upload a cohort file for quantitative outcomes and qualitative insights.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Input Data")
    st.markdown(
        '<div class="source-tabs"><div class="source-tabs-title">Data source</div></div>',
        unsafe_allow_html=True,
    )
    source_mode = st.radio(
        "Data source",
        ["Airtable (Live)", "Manual Upload"],
        horizontal=True,
        label_visibility="collapsed",
        key="data_source_mode",
    )
    if source_mode == "Manual Upload":
        st.file_uploader("Primary cohort survey", type=["csv", "xlsx"], key="manual_file")

    baseline_file = st.file_uploader("Optional baseline cohort for comparison", type=["csv", "xlsx"], key="baseline")
    st.caption("Tip: use Manual Upload if Airtable secrets are not configured.")

df, cohort_name, source_status = read_source_dataframe(source_mode)
if df is None:
    st.info("Pick a data source in the sidebar and provide data (Airtable secrets or a file upload) to generate the dashboard.")
    st.stop()

responses = len(df)
if source_mode == "Airtable (Live)":
    mapping, mapping_details = build_mapping(df.columns.tolist())
    with st.expander("Field Mapping Review", expanded=False):
        st.caption("Low-confidence matches can be overridden below.")
        for metric_key, detail in mapping_details.items():
            current = mapping.get(metric_key)
            options = ["<None>"] + df.columns.tolist()
            default_idx = options.index(current) if current in options else 0
            selected = st.selectbox(
                f'{detail["label"]} ({metric_key}) · {detail["confidence"]} ({detail["score"]})',
                options=options,
                index=default_idx,
                key=f"override_{metric_key}",
            )
            mapping[metric_key] = None if selected == "<None>" else selected
            cls = "mapping-high" if detail["confidence"] in {"high", "medium"} else "mapping-low"
            st.markdown(
                f'<span class="{cls}">Auto match:</span> {detail["column"] or "None"} · {detail["reason"]}',
                unsafe_allow_html=True,
            )
else:
    mapping = csv_fallback_mapping(df)

st.caption(source_status)
st.markdown(f'<span class="pill">{cohort_name} · {responses} responses</span>', unsafe_allow_html=True)

metrics = {
    "Policy Workshops": safe_mean(df[mapping["workshops"]]) if mapping.get("workshops") else None,
    "Speaker Events": safe_mean(df[mapping["speakers"]]) if mapping.get("speakers") else None,
    "Peer / Buddy Experience": safe_mean(df[mapping["peer"]]) if mapping.get("peer") else None,
    "Overall Experience": safe_mean(df[mapping["experience"]]) if mapping.get("experience") else None,
    "Skill Growth": safe_mean(df[mapping["skills"]]) if mapping.get("skills") else None,
}
outcomes = {
    "Improved Tech Policy Understanding": pct_agree(df[mapping["understand"]]) if mapping.get("understand") else None,
    "Increased Career Interest": pct_agree(df[mapping["interest"]]) if mapping.get("interest") else None,
    "Internship Confidence": pct_agree(df[mapping["confidence"]]) if mapping.get("confidence") else None,
}
hours_avg = None
if mapping.get("hours"):
    hours_avg = round(df[mapping["hours"]].map(HOURS_MAP).dropna().mean(), 1)

text_columns = [mapping.get("suggestions"), mapping.get("elaborate"), mapping.get("perspective")]
all_texts = []
for t_col in text_columns:
    if t_col:
        all_texts.extend(clean_texts(df[t_col]))

analyzed, theme_counts = analyze_responses(all_texts)
qual_summary = aggregate_dashboard_signals(analyzed)
keyword_pairs = top_keywords(all_texts, n=12)

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

    ratings_data = [{"metric": k, "value": v} for k, v in metrics.items() if v is not None]
    ratings_df = pd.DataFrame(ratings_data)
    if not ratings_df.empty and "value" in ratings_df.columns:
        ratings_df = ratings_df.sort_values("value", ascending=False)
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
    else:
        st.warning(
            "No quantitative rating fields were mapped. For Airtable, use Field Mapping Review. For Manual Upload, "
            "ensure column names include recognizable phrases (e.g. policy workshops, speaker events)."
        )

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
    else:
        st.info(
            "No outcome agreement fields were mapped yet. Map understand / interest / confidence in Field Mapping Review (Airtable) "
            "or align column wording for manual files."
        )

    st.subheader("Qualitative Sentiment Composition (weighted)")
    comp = pd.DataFrame(
        [
            {"sentiment": "Positive", "share": round(qual_summary["positive"] * 100, 1)},
            {"sentiment": "Neutral", "share": round(qual_summary["neutral"] * 100, 1)},
            {"sentiment": "Negative", "share": round(qual_summary["negative"] * 100, 1)},
        ]
    )
    fig_comp = go.Figure(
        go.Bar(
            x=comp["share"],
            y=comp["sentiment"],
            orientation="h",
            marker_color=[SUCCESS, MUTED,  "#E53E3E"],
            text=comp["share"].map(lambda x: f"{x:.1f}%"),
            textposition="outside",
        )
    )
    fig_comp.update_layout(
        **base_layout(210),
        xaxis=dict(range=[0, 100], showgrid=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with tab2:
    strengths = sorted([(k, v) for k, v in metrics.items() if v is not None], key=lambda x: x[1], reverse=True)[:3]
    for label, value in strengths:
        st.markdown(
            f'<div class="insight"><h4>{label} is a strength</h4><p>Average rating is <strong>{value:.2f}/5</strong>, indicating fellows generally rated this area positively.</p></div>',
            unsafe_allow_html=True,
        )

    pos_theme_rows = top_theme_rows(theme_counts, "positive", n=4)
    if pos_theme_rows:
        theme_str = ", ".join(f"{theme} ({count})" for theme, count in pos_theme_rows)
        st.markdown(
            f'<div class="insight"><h4>Top positive themes</h4><p>{theme_str}</p></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Representative Positive Signals")
    if keyword_pairs:
        top_positive = [w for w, _ in keyword_pairs][:8]
        if top_positive:
            st.write(", ".join(top_positive))
    sample_texts = representative_sentences(analyzed, "positive", limit=6)
    for quote in sample_texts:
        st.markdown(f'<div class="quote-card"><div class="quote-muted">Open response</div>{quote}</div>', unsafe_allow_html=True)

with tab3:
    risks = sorted([(k, v) for k, v in metrics.items() if v is not None], key=lambda x: x[1])[:3]
    for label, value in risks:
        st.markdown(
            f'<div class="insight"><h4>{label} needs attention</h4><p>Average rating is <strong>{value:.2f}/5</strong>. Consider operational changes, clearer expectations, or format improvements here.</p></div>',
            unsafe_allow_html=True,
        )

    neg_theme_rows = top_theme_rows(theme_counts, "negative", n=4)
    if neg_theme_rows:
        theme_str = ", ".join(f"{theme} ({count})" for theme, count in neg_theme_rows)
        st.markdown(
            f'<div class="insight"><h4>Top friction themes</h4><p>{theme_str}</p></div>',
            unsafe_allow_html=True,
        )

    st.subheader("Top Pain-Point Keywords")
    neg_keywords = [(w, c) for w, c in keyword_pairs if w in {"scheduling", "workload", "conflict", "communication", "rushed"}]
    if neg_keywords:
        neg_df = pd.DataFrame(neg_keywords, columns=["word", "count"])
        if not neg_df.empty and "count" in neg_df.columns:
            neg_df = neg_df.sort_values("count", ascending=False)
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

    sample_neg = representative_sentences(analyzed, "negative", limit=6)
    for quote in sample_neg:
        st.markdown(f'<div class="quote-card"><div class="quote-muted">Open response</div>{quote}</div>', unsafe_allow_html=True)

    mixed = representative_sentences(analyzed, "mixed", limit=4)
    if mixed:
        st.subheader("Mixed but Informative Responses")
        st.caption("These contain both positive and negative content and are tracked as mixed, not duplicated blindly.")
        for quote in mixed:
            st.markdown(f'<div class="quote-card"><div class="quote-muted">Mixed response</div>{quote}</div>', unsafe_allow_html=True)

with tab4:
    if baseline_file is None:
        st.info("Upload an optional baseline cohort in the sidebar to compare cohorts side-by-side.")
    else:
        base_df = load_data(baseline_file)
        base_df.columns = [str(c).strip() for c in base_df.columns]
        base_mapping = csv_fallback_mapping(base_df)
        base_name = cohort_label(baseline_file.name)

        compare_rows = []
        for metric_label, key in [
            ("Policy Workshops", "workshops"),
            ("Speaker Events", "speakers"),
            ("Peer / Buddy Experience", "peer"),
            ("Overall Experience", "experience"),
            ("Skill Growth", "skills"),
        ]:
            a_val = safe_mean(base_df[base_mapping[key]]) if base_mapping.get(key) else None
            b_val = safe_mean(df[mapping[key]]) if mapping.get(key) else None
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