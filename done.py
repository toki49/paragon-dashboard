import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import io

# ─── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(
    page_title="Paragon Fellowship Dashboard",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── STYLES ──────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

  h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }

  .metric-card {
    background: #181c27;
    border: 1px solid #2a3050;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    border-top: 3px solid;
    text-align: center;
  }

  .metric-card.blue  { border-top-color: #5b8cff; }
  .metric-card.orange{ border-top-color: #ff7c5b; }
  .metric-card.green { border-top-color: #5bffb8; }
  .metric-card.purple{ border-top-color: #b57bff; }

  .metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem;
    line-height: 1;
    margin-bottom: 0.2rem;
  }
  .metric-value.blue  { color: #5b8cff; }
  .metric-value.orange{ color: #ff7c5b; }
  .metric-value.green { color: #5bffb8; }
  .metric-value.purple{ color: #b57bff; }

  .metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #7a85a8;
    margin-bottom: 0.3rem;
  }
  .metric-sub { font-size: 0.8rem; color: #7a85a8; }

  .insight-box {
    background: #ffffff;
    border: 1px solid #e2e6f0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.6rem;
    border-left: 4px solid;
    color: #1a1e2e;
    font-size: 0.88rem;
    line-height: 1.55;
  }
  .insight-box.blue   { border-left-color: #5b8cff; background: #f5f8ff; }
  .insight-box.orange { border-left-color: #ff7c5b; background: #fff8f5; }
  .insight-box.green  { border-left-color: #00c48c; background: #f4fdf9; }

  .section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: #e8ecf7;
    margin-bottom: 0.25rem;
  }
  .section-sub {
    font-size: 0.82rem;
    color: #7a85a8;
    margin-bottom: 1rem;
  }

  .stSelectbox label, .stFileUploader label { font-weight: 600; color: #e8ecf7 !important; }

  div[data-testid="stSidebar"] {
    background: #0f1117;
    border-right: 1px solid #2a3050;
  }

  .report-section {
    background: #181c27;
    border: 1px solid #2a3050;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1rem;
    line-height: 1.7;
    color: #c8cfe8;
  }
  .report-section h3 { color: #5b8cff; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.75rem; }
  .report-section p { margin-bottom: 0.75rem; font-size: 0.9rem; }
  .report-section ul { padding-left: 1.25rem; }
  .report-section li { font-size: 0.9rem; margin-bottom: 0.4rem; }

  .pill {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-right: 0.3rem;
  }
  .pill-blue   { background: rgba(91,140,255,0.15); color: #5b8cff; border: 1px solid rgba(91,140,255,0.3); }
  .pill-orange { background: rgba(255,124,91,0.15); color: #ff7c5b; border: 1px solid rgba(255,124,91,0.3); }
  .pill-green  { background: rgba(91,255,184,0.15); color: #5bffb8; border: 1px solid rgba(91,255,184,0.3); }

  .stTabs [data-baseweb="tab-list"] { gap: 8px; }
  .stTabs [data-baseweb="tab"] {
    background: #181c27;
    border: 1px solid #2a3050;
    border-radius: 20px;
    color: #7a85a8;
    padding: 0.3rem 1rem;
  }
  .stTabs [aria-selected="true"] {
    background: rgba(91,140,255,0.15) !important;
    border-color: #5b8cff !important;
    color: #5b8cff !important;
  }
</style>
""", unsafe_allow_html=True)

# ─── COLORS ──────────────────────────────────────────────────
C_BLUE   = "#5b8cff"
C_ORANGE = "#ff7c5b"
C_GREEN  = "#5bffb8"
C_PURPLE = "#b57bff"
C_BG     = "#0f1117"
C_SURF   = "#181c27"
C_SURF2  = "#1f2435"
C_BORDER = "#2a3050"
C_TEXT   = "#e8ecf7"
C_MUTED  = "#7a85a8"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color=C_TEXT),
    margin=dict(l=10, r=10, t=30, b=10),
)

# ─── COHORT SCHEMA ───────────────────────────────────────────
# Each cohort maps to its column names so we can normalize
COHORT_SCHEMA = {
    "FA25": {
        "team": "What project team were you on?",
        "workshop": "How helpful were the policy workshops? ",
        "speaker": "How insightful were the speaker events?",
        "peer": "How engaging were the Bridge Buddies?",
        "peer_label": "Bridge Buddies",
        "experience": "How was your experience with Paragon?",
        "skills": "I developed new skills during the fellowship program.",
        "understanding": "Paragon improved my understanding of tech policy.",
        "interest": "Paragon has increased my interest in pursuing a career in tech policy/public interest tech.",
        "hours": "How many hours did you spend on Paragon per week? An estimate is fine!",
        "absence": "If you did not attend any speaker series, policy workshops, or Bridge Buddies events, please explain (for each event type) why you did not attend.",
        "suggestions": "Do you have any suggestions for the content of our programming? ",
        "skills_text": "Please elaborate on your rating of your experience and your skill growth!",
        "file_type": "xlsx",
    },
    "SU25": {
        "team": "What project team were you on?",
        "workshop": "How helpful were the policy workshops? ",
        "speaker": "How insightful were the speaker events?",
        "peer": "How engaging were the Donut Buddies?",
        "peer_label": "Donut Buddies",
        "experience": "How was your experience with Paragon?",
        "skills": "I developed new skills during the fellowship program.",
        "understanding": "Paragon improved my understanding of tech policy.",
        "interest": "Paragon has increased my interest in pursuing a career in tech policy/public interest tech.",
        "hours": "How many hours did you spend on Paragon per week? An estimate is fine!",
        "absence": "If you did not attend any speaker series, policy workshops, or Donut Buddies events, please explain (for each event type) why you did not attend.",
        "suggestions": "Do you have any suggestions for the content of our programming? ",
        "skills_text": "Please elaborate on your rating of your experience and your skill growth!",
        "file_type": "csv",
    },
    "SP24": {
        "team": None,
        "workshop": None,
        "speaker": "How insightful were the speaker events?",
        "peer": None,
        "peer_label": "Peer Events",
        "experience": "How was your experience with Paragon?",
        "skills": None,
        "understanding": "How would you rate your understanding of tech policy? ",
        "interest": "How interested are you in pursuing a career in tech policy? ",
        "hours": None,
        "absence": None,
        "suggestions": "If there were topics you wanted to hear about but weren't covered, please share them here, along with any suggestions you may have on how we can improve our lecture series (scheduling, format, etc.)",
        "skills_text": "Please elaborate on your rating of your experience and your skill growth!",
        "file_type": "csv",
    },
}

# ─── DATA LOADING ────────────────────────────────────────────
def load_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    else:
        # Try different encodings
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, encoding=enc)
            except Exception:
                continue
    return None

def detect_cohort(df, filename):
    """Try to auto-detect cohort from filename or columns."""
    fn = filename.lower()
    if "fa25" in fn or "fall_2025" in fn or "fall25" in fn:
        return "FA25"
    if "su25" in fn or "summer25" in fn or "summer_2025" in fn:
        return "SU25"
    if "sp24" in fn or "spring_2024" in fn or "spring24" in fn:
        return "SP24"
    if "sp25" in fn or "spring_2025" in fn or "spring25" in fn:
        return "SP25 (Alumni)"
    # Check columns
    cols = list(df.columns)
    if any("bridge buddies" in c.lower() for c in cols):
        return "FA25"
    if any("donut buddies" in c.lower() for c in cols):
        return "SU25"
    return "Unknown"

def normalize_rating(series):
    """Convert any rating column to numeric 1-5."""
    def parse_val(v):
        if pd.isna(v):
            return np.nan
        if isinstance(v, (int, float)):
            return float(v)
        v = str(v).strip()
        # Likert text
        mapping = {
            "strongly agree": 5, "agree": 4, "neutral": 3,
            "disagree": 2, "strongly disagree": 1,
            "very interested": 5, "somewhat interested": 4,
            "neutral": 3, "somewhat uninterested": 2, "very uninterested": 1,
            "very confident": 5, "confident": 4, "somewhat confident": 3,
            "not very confident": 2, "not confident at all": 1,
            "very high": 5, "high": 4, "moderate": 3, "low": 2, "very low": 1,
        }
        lv = v.lower()
        if lv in mapping:
            return mapping[lv]
        try:
            return float(v)
        except ValueError:
            return np.nan
    return series.apply(parse_val)

def get_avg(series):
    n = normalize_rating(series).dropna()
    return round(n.mean(), 2) if len(n) > 0 else None

def get_dist(series):
    n = normalize_rating(series).dropna()
    counts = {}
    for star in [5, 4, 3, 2, 1]:
        counts[star] = int((n == star).sum())
    return counts

def parse_hours(series):
    """Parse hours-per-week into numeric midpoint."""
    def mid(v):
        if pd.isna(v): return np.nan
        v = str(v).lower()
        if "1-4" in v: return 2.5
        if "5-10" in v: return 7.5
        if "11-15" in v: return 13
        if "16-20" in v: return 18
        if "20+" in v or ">20" in v: return 22
        try: return float(v)
        except: return np.nan
    return series.apply(mid)

# ─── CHART HELPERS ───────────────────────────────────────────
def avg_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"color": color, "size": 36, "family": "DM Serif Display"}, "suffix": "/5"},
        title={"text": title, "font": {"size": 13, "color": C_MUTED}},
        gauge={
            "axis": {"range": [0, 5], "tickcolor": C_MUTED, "tickfont": {"size": 10}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": C_SURF2,
            "bordercolor": C_BORDER,
            "steps": [
                {"range": [0, 2.5], "color": "rgba(255,80,80,0.08)"},
                {"range": [2.5, 3.5], "color": "rgba(255,200,0,0.08)"},
                {"range": [3.5, 5], "color": "rgba(91,255,184,0.08)"},
            ],
        }
    ))
    layout = {**PLOTLY_LAYOUT, "height": 180, "margin": dict(l=20, r=20, t=40, b=0)}
    fig.update_layout(**layout)
    return fig

def dist_bar(dist, color, title):
    stars = [f"{s}★" for s in [5, 4, 3, 2, 1]]
    counts = [dist.get(s, 0) for s in [5, 4, 3, 2, 1]]
    total = sum(counts)
    pcts = [c / total * 100 if total > 0 else 0 for c in counts]

    fig = go.Figure(go.Bar(
        y=stars, x=pcts,
        orientation="h",
        marker_color=color,
        marker_line_width=0,
        text=[f"{c}" for c in counts],
        textposition="outside",
        textfont=dict(color=C_MUTED, size=11),
        hovertemplate="%{y}: %{x:.1f}% (%{text} responses)<extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=title, font=dict(size=13, color=C_MUTED)),
        height=200,
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, max(pcts) * 1.3 + 5]),
        yaxis=dict(gridcolor=C_BORDER, tickfont=dict(color=C_MUTED)),
        bargap=0.25,
    )
    return fig

def team_heatmap(team_data, peer_label):
    if team_data.empty:
        return None
    teams = team_data["team"].tolist()
    metrics = ["workshop", "speaker", "peer"]
    labels  = ["Workshops", "Speakers", peer_label]
    z = [[team_data.iloc[i][m] if pd.notna(team_data.iloc[i][m]) else None for m in metrics] for i in range(len(team_data))]

    fig = go.Figure(go.Heatmap(
        z=z, x=labels, y=teams,
        colorscale=[
            [0.0,  "#ff7c5b"],   # low  → brand orange
            [0.5,  "#ffe8a0"],   # mid  → soft yellow
            [1.0,  "#5bffb8"],   # high → brand green
        ],
        zmin=1, zmax=5,
        text=[[f"{v:.1f}" if v else "—" for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=13, color="#1a1e2e"),
        showscale=True,
        colorbar=dict(
            tickfont=dict(color="#444", size=11),
            outlinecolor="#ddd",
            outlinewidth=1,
            bgcolor="white",
            thickness=14,
            len=0.85,
        ),
        hovertemplate="Team: %{y}<br>%{x}: %{z:.2f}/5<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="DM Sans", color="#1a1e2e"),
        margin=dict(l=10, r=10, t=50, b=10),
        height=max(250, len(teams) * 48 + 100),
        xaxis=dict(side="top", tickfont=dict(color="#1a1e2e", size=13), gridcolor="#eee"),
        yaxis=dict(tickfont=dict(color="#444", size=11), autorange="reversed", gridcolor="#eee"),
    )
    return fig

def comparison_bar(cohorts_avgs):
    """Multi-cohort grouped bar chart."""
    metrics  = ["Workshop", "Speaker", "Peer"]
    cohort_names = list(cohorts_avgs.keys())
    palette  = [C_BLUE, C_ORANGE, C_GREEN, C_PURPLE]

    fig = go.Figure()
    for i, cohort in enumerate(cohort_names):
        vals = cohorts_avgs[cohort]
        fig.add_trace(go.Bar(
            name=cohort,
            x=metrics,
            y=[vals.get("workshop"), vals.get("speaker"), vals.get("peer")],
            marker_color=palette[i % len(palette)],
            marker_line_width=0,
            text=[f"{v:.2f}" if v else "N/A" for v in [vals.get("workshop"), vals.get("speaker"), vals.get("peer")]],
            textposition="outside",
            textfont=dict(size=11),
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        barmode="group",
        bargap=0.2,
        bargroupgap=0.05,
        legend=dict(orientation="h", y=-0.15, font=dict(color=C_MUTED)),
        xaxis=dict(tickfont=dict(color=C_TEXT, size=13), gridcolor=C_BORDER),
        yaxis=dict(range=[0, 5.5], tickfont=dict(color=C_MUTED), gridcolor=C_BORDER),
    )
    return fig

def trend_line(cohorts_avgs, metric, color, label):
    xs, ys = [], []
    for cohort, vals in cohorts_avgs.items():
        v = vals.get(metric)
        if v is not None:
            xs.append(cohort)
            ys.append(v)
    if len(xs) < 2:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines+markers+text",
        line=dict(color=color, width=2.5),
        marker=dict(size=9, color=color),
        text=[f"{v:.2f}" for v in ys],
        textposition="top center",
        textfont=dict(color=color, size=11),
        name=label,
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=220,
        title=dict(text=label, font=dict(color=C_MUTED, size=12)),
        xaxis=dict(tickfont=dict(color=C_MUTED), gridcolor=C_BORDER),
        yaxis=dict(range=[1, 5.5], tickfont=dict(color=C_MUTED), gridcolor=C_BORDER),
        showlegend=False,
    )
    return fig

# ─── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔷 Paragon Dashboard")
    st.markdown('<div style="font-size:0.8rem; color:#7a85a8; margin-bottom:1.5rem;">Fellowship Analytics Platform</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["📊 Programming Feedback", "📈 Cohort Comparison", "📄 Network Analysis Report"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### Upload Cohort Data")
    st.markdown('<div style="font-size:0.78rem; color:#7a85a8; margin-bottom:0.75rem;">Upload one or more exit survey files (CSV or XLSX)</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    st.markdown('<div style="font-size:0.72rem; color:#7a85a8; margin-top:0.5rem;">Supported: FA25, SU25, SP24 formats</div>', unsafe_allow_html=True)

# ─── LOAD & PARSE UPLOADED DATA ──────────────────────────────
all_cohorts = {}   # cohort_name -> {df, schema, avgs, dists, ...}

if uploaded_files:
    for uf in uploaded_files:
        df = load_file(uf)
        if df is None:
            st.sidebar.error(f"Could not read {uf.name}")
            continue

        cohort_name = detect_cohort(df, uf.name)
        schema = COHORT_SCHEMA.get(cohort_name)

        if schema is None:
            # Allow manual fallback for unknown cohorts
            cohort_name = uf.name.split(".")[0].upper()
            # Try to guess columns
            schema = {
                "team": next((c for c in df.columns if "team" in c.lower()), None),
                "workshop": next((c for c in df.columns if "workshop" in c.lower() and "helpful" in c.lower()), None),
                "speaker": next((c for c in df.columns if "speaker" in c.lower() and "insightful" in c.lower()), None),
                "peer": next((c for c in df.columns if "buddies" in c.lower() or "buddy" in c.lower()), None),
                "peer_label": "Peer Events",
                "experience": next((c for c in df.columns if "experience" in c.lower()), None),
                "skills": next((c for c in df.columns if "skills" in c.lower() and "developed" in c.lower()), None),
                "understanding": next((c for c in df.columns if "understanding" in c.lower()), None),
                "interest": next((c for c in df.columns if "interest" in c.lower()), None),
                "hours": next((c for c in df.columns if "hours" in c.lower()), None),
                "absence": next((c for c in df.columns if "absence" in c.lower() or "did not attend" in c.lower()), None),
                "suggestions": next((c for c in df.columns if "suggestion" in c.lower()), None),
                "skills_text": next((c for c in df.columns if "elaborate" in c.lower()), None),
            }

        # Compute stats
        avgs, dists = {}, {}
        for key in ["workshop", "speaker", "peer", "experience", "skills", "understanding", "interest"]:
            col = schema.get(key)
            if col and col in df.columns:
                avgs[key] = get_avg(df[col])
                dists[key] = get_dist(df[col])
            else:
                avgs[key] = None
                dists[key] = {}

        # Team-level breakdown
        team_col = schema.get("team")
        team_data = pd.DataFrame()
        if team_col and team_col in df.columns:
            teams = df[team_col].dropna().unique()
            rows = []
            for team in teams:
                sub = df[df[team_col] == team]
                row = {"team": team}
                for key in ["workshop", "speaker", "peer"]:
                    col = schema.get(key)
                    row[key] = get_avg(sub[col]) if (col and col in sub.columns) else None
                rows.append(row)
            team_data = pd.DataFrame(rows).sort_values("team")

        all_cohorts[cohort_name] = {
            "df": df,
            "schema": schema,
            "avgs": avgs,
            "dists": dists,
            "team_data": team_data,
            "n": len(df),
            "peer_label": schema.get("peer_label", "Peer Events"),
        }

# ─── PAGE: PROGRAMMING FEEDBACK ──────────────────────────────
if page == "📊 Programming Feedback":
    st.markdown("# Programming Feedback")
    st.markdown('<div style="color:#7a85a8; margin-bottom:1.5rem; font-size:0.9rem;">Exit survey data by cohort — upload files in the sidebar to get started.</div>', unsafe_allow_html=True)

    if not all_cohorts:
        st.info("👈 Upload one or more exit survey CSV/XLSX files in the sidebar to view the dashboard.")
    else:
        # Cohort selector
        cohort_names = list(all_cohorts.keys())
        selected = st.selectbox("Select Cohort", cohort_names, key="cohort_select")
        data = all_cohorts[selected]
        df   = data["df"]
        avgs = data["avgs"]
        dists = data["dists"]
        schema = data["schema"]
        peer_label = data["peer_label"]
        n = data["n"]

        st.markdown("---")

        # ── TOP METRICS ──
        st.markdown('<div class="section-header">Overview</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-sub">{selected} · {n} respondents</div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        def metric_card(col, val, label, sub, color):
            with col:
                val_str = f"{val:.2f}" if val else "N/A"
                st.markdown(f"""
                <div class="metric-card {color}">
                  <div class="metric-label">{label}</div>
                  <div class="metric-value {color}">{val_str}</div>
                  <div class="metric-sub">{sub}</div>
                </div>
                """, unsafe_allow_html=True)

        metric_card(c1, avgs.get("workshop"), "Policy Workshops", "avg rating / 5", "blue")
        metric_card(c2, avgs.get("speaker"),  "Speaker Events",   "avg rating / 5", "orange")
        metric_card(c3, avgs.get("peer"),      peer_label,         "avg rating / 5", "green")
        metric_card(c4, avgs.get("experience"),"Overall Experience","avg rating / 5", "purple")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── GAUGES ──
        tab1, tab2 = st.tabs(["📊 Rating Distributions", "🎯 Rating Gauges"])

        with tab1:
            col1, col2, col3 = st.columns(3)
            if dists.get("workshop"):
                with col1:
                    st.plotly_chart(dist_bar(dists["workshop"], C_BLUE, "Policy Workshops"), use_container_width=True)
            if dists.get("speaker"):
                with col2:
                    st.plotly_chart(dist_bar(dists["speaker"], C_ORANGE, "Speaker Events"), use_container_width=True)
            if dists.get("peer"):
                with col3:
                    st.plotly_chart(dist_bar(dists["peer"], C_GREEN, peer_label), use_container_width=True)

        with tab2:
            col1, col2, col3 = st.columns(3)
            if avgs.get("workshop"):
                with col1:
                    st.plotly_chart(avg_gauge(avgs["workshop"], "Policy Workshops", C_BLUE), use_container_width=True)
            if avgs.get("speaker"):
                with col2:
                    st.plotly_chart(avg_gauge(avgs["speaker"], "Speaker Events", C_ORANGE), use_container_width=True)
            if avgs.get("peer"):
                with col3:
                    st.plotly_chart(avg_gauge(avgs["peer"], peer_label, C_GREEN), use_container_width=True)

        st.markdown("---")

        # ── TEAM BREAKDOWN ──
        if not data["team_data"].empty:
            st.markdown('<div class="section-header">By Project Team</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-sub">Average ratings per team across all programming types</div>', unsafe_allow_html=True)
            fig = team_heatmap(data["team_data"], peer_label)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

        # ── FELLOW IMPACT ──
        st.markdown("---")
        st.markdown('<div class="section-header">Fellow Impact</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Self-reported Likert scale outcomes</div>', unsafe_allow_html=True)

        impact_keys = [
            ("understanding", "Improved Understanding", C_BLUE),
            ("interest", "Career Interest", C_ORANGE),
            ("skills", "Developed New Skills", C_GREEN),
        ]
        cols = st.columns(len(impact_keys))
        for col, (key, label, color) in zip(cols, impact_keys):
            if dists.get(key):
                with col:
                    st.plotly_chart(dist_bar(dists[key], color, label), use_container_width=True)

        # Hours per week
        hours_col = schema.get("hours")
        if hours_col and hours_col in df.columns:
            st.markdown("<br>", unsafe_allow_html=True)
            hours_series = df[hours_col].dropna()
            # Normalize to buckets
            bucket_map = {"1-4 hours": 0, "5-10 hours": 0, "11-15 hours": 0, "16-20 hours": 0, "20+ hours": 0}
            for v in hours_series:
                v = str(v).lower()
                if "1-4" in v: bucket_map["1-4 hours"] += 1
                elif "11-15" in v: bucket_map["11-15 hours"] += 1
                elif "16-20" in v: bucket_map["16-20 hours"] += 1
                elif "20+" in v or ">20" in v: bucket_map["20+ hours"] += 1
                elif "5-10" in v or "5 -10" in v: bucket_map["5-10 hours"] += 1
                else: bucket_map["5-10 hours"] += 1  # fallback

            fig_hours = go.Figure(go.Bar(
                x=list(bucket_map.keys()),
                y=list(bucket_map.values()),
                marker_color=C_PURPLE,
                marker_line_width=0,
                text=list(bucket_map.values()),
                textposition="outside",
                textfont=dict(color=C_MUTED),
            ))
            fig_hours.update_layout(
                **PLOTLY_LAYOUT,
                title=dict(text="Hours per Week", font=dict(color=C_MUTED, size=13)),
                height=250,
                xaxis=dict(tickfont=dict(color=C_TEXT), gridcolor=C_BORDER),
                yaxis=dict(tickfont=dict(color=C_MUTED), gridcolor=C_BORDER),
            )
            st.plotly_chart(fig_hours, use_container_width=True)

        # ── QUALITATIVE ──
        st.markdown("---")
        st.markdown('<div class="section-header">Qualitative Responses</div>', unsafe_allow_html=True)

        qtab1, qtab2, qtab3 = st.tabs(["💡 Programming Suggestions", "🚫 Absence Reasons", "📝 Skill Reflections"])

        with qtab1:
            sug_col = schema.get("suggestions")
            if sug_col and sug_col in df.columns:
                responses = df[sug_col].dropna().tolist()
                if responses:
                    for r in responses:
                        if str(r).strip():
                            st.markdown(f'<div class="insight-box blue">💬 {r}</div>', unsafe_allow_html=True)
                else:
                    st.info("No suggestions recorded for this cohort.")
            else:
                st.info("Suggestions column not available for this cohort.")

        with qtab2:
            abs_col = schema.get("absence")
            if abs_col and abs_col in df.columns:
                responses = df[abs_col].dropna().tolist()
                if responses:
                    for r in responses:
                        if str(r).strip():
                            st.markdown(f'<div class="insight-box orange">📌 {r}</div>', unsafe_allow_html=True)
                else:
                    st.info("No absence reasons recorded.")
            else:
                st.info("Absence reason column not available for this cohort.")

        with qtab3:
            sk_col = schema.get("skills_text")
            if sk_col and sk_col in df.columns:
                responses = df[sk_col].dropna().tolist()
                if responses:
                    for r in responses:
                        if str(r).strip():
                            st.markdown(f'<div class="insight-box green">✨ {r}</div>', unsafe_allow_html=True)
                else:
                    st.info("No skill elaborations recorded.")
            else:
                st.info("Skill elaboration column not available for this cohort.")

# ─── PAGE: COHORT COMPARISON ─────────────────────────────────
elif page == "📈 Cohort Comparison":
    st.markdown("# Cohort Comparison")
    st.markdown('<div style="color:#7a85a8; margin-bottom:1.5rem; font-size:0.9rem;">Compare programming ratings and outcomes across multiple cohorts.</div>', unsafe_allow_html=True)

    if len(all_cohorts) < 1:
        st.info("👈 Upload two or more cohort files in the sidebar to compare them.")
    else:
        # Build cohorts_avgs dict for comparison charts
        cohorts_avgs = {name: data["avgs"] for name, data in all_cohorts.items()}
        cohort_ns    = {name: data["n"]    for name, data in all_cohorts.items()}

        # Summary table
        st.markdown('<div class="section-header">At a Glance</div>', unsafe_allow_html=True)

        summary_rows = []
        for name, data in all_cohorts.items():
            a = data["avgs"]
            summary_rows.append({
                "Cohort": name,
                "Respondents": data["n"],
                "Workshops": f"{a['workshop']:.2f}/5" if a.get("workshop") else "N/A",
                "Speakers": f"{a['speaker']:.2f}/5" if a.get("speaker") else "N/A",
                data["peer_label"]: f"{a['peer']:.2f}/5" if a.get("peer") else "N/A",
                "Experience": f"{a['experience']:.2f}/5" if a.get("experience") else "N/A",
            })
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Grouped bar comparison
        st.markdown('<div class="section-header">Programming Ratings by Cohort</div>', unsafe_allow_html=True)
        st.plotly_chart(comparison_bar(cohorts_avgs), use_container_width=True)

        st.markdown("---")

        # Trend lines (only if 2+ cohorts)
        if len(all_cohorts) >= 2:
            st.markdown('<div class="section-header">Trends Over Time</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-sub">How ratings have shifted across cohorts (chronological order)</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                fig = trend_line(cohorts_avgs, "workshop", C_BLUE, "Policy Workshops")
                if fig: st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = trend_line(cohorts_avgs, "speaker", C_ORANGE, "Speaker Events")
                if fig: st.plotly_chart(fig, use_container_width=True)
            with col3:
                fig = trend_line(cohorts_avgs, "peer", C_GREEN, "Peer Events")
                if fig: st.plotly_chart(fig, use_container_width=True)

        # Overall experience trend
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            fig = trend_line(cohorts_avgs, "experience", C_PURPLE, "Overall Experience")
            if fig:
                st.markdown('<div class="section-header">Overall Experience</div>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            # Respondent count over cohorts
            if len(all_cohorts) >= 2:
                names = list(all_cohorts.keys())
                ns = [all_cohorts[n]["n"] for n in names]
                fig_n = go.Figure(go.Bar(
                    x=names, y=ns,
                    marker_color=C_BLUE, marker_line_width=0,
                    text=ns, textposition="outside",
                    textfont=dict(color=C_MUTED),
                ))
                fig_n.update_layout(
                    **PLOTLY_LAYOUT, height=220,
                    title=dict(text="Respondents per Cohort", font=dict(color=C_MUTED, size=12)),
                    xaxis=dict(tickfont=dict(color=C_TEXT)),
                    yaxis=dict(tickfont=dict(color=C_MUTED), gridcolor=C_BORDER),
                )
                st.markdown('<div class="section-header">Participation</div>', unsafe_allow_html=True)
                st.plotly_chart(fig_n, use_container_width=True)

# ─── PAGE: NETWORK ANALYSIS REPORT ───────────────────────────
elif page == "📄 Network Analysis Report":
    st.markdown("# Network Analysis Report")
    st.markdown('<div style="color:#7a85a8; margin-bottom:1.5rem; font-size:0.9rem;">Paragon Network · Spring 2026 · Strategic analysis of speakers, government partners, and mentors.</div>', unsafe_allow_html=True)

    # Quick-nav pills
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
      <span class="pill pill-blue">Overall Network</span>
      <span class="pill pill-blue">Speakers</span>
      <span class="pill pill-blue">Gov Partners</span>
      <span class="pill pill-blue">Mentors</span>
      <span class="pill pill-orange">Strengths</span>
      <span class="pill pill-orange">Weaknesses</span>
      <span class="pill pill-green">Recommendations</span>
    </div>
    """, unsafe_allow_html=True)

    # ── OVERALL NETWORK ──
    with st.expander("🌐 Overall Network", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            <div class="report-section">
              <h3>Overview</h3>
              <p>Paragon's evolving network is a core part of the organization — shaping who fellows learn from, the kinds of projects and partnerships that are possible, and which professional pathways are most visible and accessible.</p>
              <p>This report analyzes Paragon's existing network as of Spring 2026 to identify patterns, strengths, gaps, and opportunities for growth.</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Industry breakdown donut
            industries = ["Gov Partners", "Private", "AI", "Public Policy", "Nonprofit/Advocacy", "Research & Academia", "Other"]
            pcts = [32, 14, 11, 9, 9, 9, 16]
            fig = go.Figure(go.Pie(
                labels=industries, values=pcts, hole=0.55,
                marker_colors=[C_BLUE, C_ORANGE, C_GREEN, C_PURPLE, "#ff5b8c", "#ffb85b", C_BORDER],
                textinfo="percent",
                textfont=dict(size=11, color="white"),
                hovertemplate="%{label}: %{value}%<extra></extra>",
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=260, showlegend=True,
                legend=dict(font=dict(color=C_MUTED, size=10), orientation="v", x=1))
            st.plotly_chart(fig, use_container_width=True)

        # Sector chart
        sectors = ["AI", "Civic/Gov Tech", "Public Policy", "Data & Analytics", "Legal", "Cybersecurity", "National Security", "Other"]
        sector_pcts = [19, 17, 12, 8, 7, 6, 5, 26]
        fig_sec = go.Figure(go.Bar(
            x=sectors, y=sector_pcts,
            marker_color=[C_BLUE, C_GREEN, C_ORANGE, C_PURPLE, "#ff5b8c", "#ffb85b", "#5bffff", C_BORDER],
            marker_line_width=0,
            text=[f"{p}%" for p in sector_pcts],
            textposition="outside",
            textfont=dict(color=C_MUTED, size=11),
        ))
        fig_sec.update_layout(
            **PLOTLY_LAYOUT, height=260,
            title=dict(text="Network by Sector", font=dict(color=C_MUTED, size=13)),
            xaxis=dict(tickfont=dict(color=C_TEXT, size=11)),
            yaxis=dict(tickfont=dict(color=C_MUTED), gridcolor=C_BORDER, ticksuffix="%"),
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    # ── SPEAKERS ──
    with st.expander("🎤 Speakers", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="report-section">
              <h3>Speaker Network</h3>
              <p>By sector, speakers are relatively diversified — strongest in <strong>Research & Academia (28%)</strong>, <strong>Private (22%)</strong>, and <strong>Nonprofit/Advocacy (16%)</strong>. Combined government representation sits at 18%.</p>
              <p>By industry, AI (31%), Public Policy (25%), and Civic/Gov Tech (16%) lead. After that, representation drops off significantly — Legal and Data & Analytics each at 9%, while Cybersecurity, National Security, and Media/Communications are at 3%.</p>
              <p><strong>Experience gap:</strong> 72% of speakers have 10+ years of experience. Only 3% are in the 1–3 year range, and 6% in the 3–5 year range — creating a gap in early-career perspective.</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Speaker industry chart
            sp_industries = ["AI", "Public Policy", "Civic/Gov Tech", "Legal", "Data & Analytics", "Cybersecurity", "Nat. Security", "Media/Comms"]
            sp_pcts = [31, 25, 16, 9, 9, 3, 3, 3]
            fig = go.Figure(go.Bar(
                y=sp_industries, x=sp_pcts, orientation="h",
                marker_color=C_BLUE, marker_line_width=0,
                text=[f"{p}%" for p in sp_pcts], textposition="outside",
                textfont=dict(color=C_MUTED, size=11),
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=280,
                title=dict(text="Speakers by Industry", font=dict(color=C_MUTED, size=12)),
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(tickfont=dict(color=C_MUTED), autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Experience breakdown
        exp_labels = ["10+ years", "5–9 years", "3–5 years", "1–3 years"]
        exp_speaker = [72, 19, 6, 3]
        exp_mentor  = [31, 20, 26, 23]
        exp_govpart = [74, 15, 7, 4]
        fig_exp = go.Figure()
        for label, vals, color in [("Speakers", exp_speaker, C_BLUE), ("Mentors", exp_mentor, C_GREEN), ("Gov Partners", exp_govpart, C_ORANGE)]:
            fig_exp.add_trace(go.Bar(name=label, x=exp_labels, y=vals, marker_color=color, marker_line_width=0))
        fig_exp.update_layout(
            **PLOTLY_LAYOUT, barmode="group", height=260,
            title=dict(text="Experience Distribution by Role", font=dict(color=C_MUTED, size=12)),
            legend=dict(font=dict(color=C_MUTED), orientation="h", y=-0.2),
            xaxis=dict(tickfont=dict(color=C_TEXT)),
            yaxis=dict(tickfont=dict(color=C_MUTED), gridcolor=C_BORDER, ticksuffix="%"),
        )
        st.plotly_chart(fig_exp, use_container_width=True)

    # ── GOVERNMENT PARTNERS ──
    with st.expander("🏛️ Government Partners", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="report-section">
              <h3>Government Partner Network</h3>
              <p>The government partner network is concentrated primarily in <strong>local government (67%)</strong>, followed by state (19%) and federal (4%). A smaller share has transitioned into Nonprofit/Advocacy (7%) and Private (4%).</p>
              <p>This reflects Paragon's strength in working on projects close to implementation and community-level governance. However, the network is less connected to state and federal government institutions.</p>
              <p>By industry, <strong>Civic/Gov Tech (37%)</strong> leads, followed by AI (19%) and Public Policy (15%). 74% of government partners have 10+ years of experience.</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Gov sector pie
            gov_sectors = ["Local Gov", "State Gov", "Federal Gov", "Nonprofit/Advocacy", "Private"]
            gov_pcts = [67, 19, 4, 7, 4]
            fig = go.Figure(go.Pie(
                labels=gov_sectors, values=gov_pcts, hole=0.5,
                marker_colors=[C_BLUE, C_GREEN, C_ORANGE, C_PURPLE, "#ffb85b"],
                textinfo="percent+label",
                textfont=dict(size=10, color="white"),
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=260, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # ── MENTORS ──
    with st.expander("🤝 Mentors", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="report-section">
              <h3>Mentor Network</h3>
              <p>The mentor network is the most balanced across sectors: <strong>Private (34%)</strong>, Research & Academia (23%), Nonprofit/Advocacy (17%), Federal Government (14%).</p>
              <p>By industry, AI (37%), Public Policy (20%), and Civic/Gov Tech (17%) lead, followed by Legal (11%), Cybersecurity (9%), and Energy (6%).</p>
              <p>Unlike speakers and government partners, mentors show the <strong>greatest variety in experience levels</strong>: 10+ years (31%), 3–5 years (26%), 1–3 years (23%), 5–9 years (20%). This makes the mentor network a counterweight to the seniority-heavy speaker pool.</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            mentor_sectors = ["Private", "Research & Academia", "Nonprofit/Advocacy", "Federal Gov", "Other"]
            mentor_pcts = [34, 23, 17, 14, 12]
            fig = go.Figure(go.Pie(
                labels=mentor_sectors, values=mentor_pcts, hole=0.5,
                marker_colors=[C_ORANGE, C_BLUE, C_GREEN, C_PURPLE, C_BORDER],
                textinfo="percent",
                textfont=dict(size=11, color="white"),
            ))
            fig.update_layout(**PLOTLY_LAYOUT, height=260, showlegend=True,
                legend=dict(font=dict(color=C_MUTED, size=10)))
            st.plotly_chart(fig, use_container_width=True)

    # ── KEY FINDINGS ──
    with st.expander("🔍 Key Findings", expanded=True):
        findings = [
            ("blue",   "AI, Civic/Gov Tech & Public Policy are the network's core strengths", "Consistent across speakers, government partners, and mentors — reflecting Paragon's work at the intersection of technology, governance, and policy."),
            ("orange", "Seniority defines the network", "72% of speakers and 74% of gov partners have 10+ years of experience. Strong authority and credibility, but a gap in early-career perspective that the mentor network partially addresses."),
            ("green",  "The mentor network is the most balanced", "Strongest sector, industry, and experience distribution of all three network roles. Provides a counterweight to the seniority concentration elsewhere."),
            ("blue",   "Government partners are locally concentrated", "67% are in local government, creating strong community-level connections but limited state and federal representation."),
            ("orange", "AI is the top industry across all three roles", "31% of speakers, 37% of mentors, and 19% of gov partners work in AI — reflecting Paragon's central identity in the tech policy space."),
        ]
        for color, title, body in findings:
            st.markdown(f"""
            <div class="insight-box {color}">
              <strong>{title}</strong><br>
              <span style="font-size:0.85rem; color:#7a85a8;">{body}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── STRENGTHS & WEAKNESSES ──
    col1, col2 = st.columns(2)
    with col1:
        with st.expander("✅ Network Strengths", expanded=True):
            strengths = [
                "Mentor network is highly diversified across sectors and experience levels — strong mentor-mentee matching potential.",
                "72% of speakers and 74% of gov partners are 10+ year veterans — exceptional credibility and depth of knowledge.",
                "Strong identity: clearly focused in AI, Policy, and Civic/Gov Tech across all roles.",
                "Gov partner network is especially strong in local government — close to implementation and community-level impact.",
                "Each role contributes distinct value: speakers (senior insight), gov partners (local connections), mentors (diverse guidance).",
            ]
            for s in strengths:
                st.markdown(f'<div class="insight-box green" style="font-size:0.85rem;">✓ {s}</div>', unsafe_allow_html=True)

    with col2:
        with st.expander("⚠️ Network Weaknesses", expanded=True):
            weaknesses = [
                "Speaker network is overwhelmingly senior (only 3% are 1–3 years experience) — risks feeling aspirational rather than accessible.",
                "Limited presence in Healthcare/Biotech, Cybersecurity, National Security, Legal, Think Tank, Philanthropic, and Media/Communications.",
                "Gap in mid-career representation across all roles — missing voices that are relatable but grounded.",
                "Early-career perspective exists but is mostly siloed in mentoring — limited reach compared to speaker programming.",
            ]
            for w in weaknesses:
                st.markdown(f'<div class="insight-box orange" style="font-size:0.85rem;">⚠ {w}</div>', unsafe_allow_html=True)

    # ── RECOMMENDATIONS ──
    with st.expander("💡 Recommendations", expanded=True):
        recs = [
            ("1", "Expand early-career speakers", "Increase the number of speakers in the 1–3 and 3–5 year experience range. The mentor network is a natural pipeline — leverage it for future speaker nominations."),
            ("2", "Seek underrepresented sectors intentionally", "Maintain AI/policy strength while broadening into Healthcare/Biotech, Media, National Security, and Think Tanks to widen career pathways."),
            ("3", "Add mid-career professionals", "Bridge the gap between senior experts and early-career mentors. Mid-career voices are relatable and practically grounded."),
            ("4", "Focus on 3–4 sectors per cohort", "Rather than broad expansion, go deep on 3–4 underrepresented areas at a time — enabling stronger representation and more thoughtful programming."),
        ]
        for num, title, body in recs:
            st.markdown(f"""
            <div class="report-section" style="padding:1rem 1.25rem; margin-bottom:0.6rem;">
              <div style="display:flex; align-items:flex-start; gap:1rem;">
                <div style="font-family:'DM Serif Display',serif; font-size:2rem; color:{C_BLUE}; line-height:1; min-width:2rem;">{num}</div>
                <div>
                  <strong style="color:{C_TEXT};">{title}</strong>
                  <p style="font-size:0.85rem; color:{C_MUTED}; margin-top:0.3rem; margin-bottom:0;">{body}</p>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── FUTURE QUESTIONS ──
    with st.expander("🔭 Questions for the Future", expanded=False):
        questions = [
            "Does Paragon want each role to continue serving a distinct function, or aim for more balance across roles?",
            "How can Paragon better engage its alumni network as active connectors, speakers, mentors, and recruiters?",
            "Should Paragon maintain its strong local government focus, or expand state and federal relationships?",
            "Which sectors and industries should Paragon prioritize for future relationship building?",
            "As technology and regulation evolve, which topics and connections will Paragon prioritize?",
            "How should Paragon balance research and practical implementation in network building and programming?",
            "How can Paragon better track and balance technical vs. non-technical roles in the network?",
            "What does network success look like in 2–3 years — larger, more balanced, more specialized, or all three?",
        ]
        for q in questions:
            st.markdown(f'<div class="insight-box blue" style="font-size:0.85rem;">❓ {q}</div>', unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:2rem; padding-top:1rem; border-top:1px solid #2a3050; font-size:0.72rem; color:#7a85a8; text-align:center;">
  Paragon Policy Fellowship · Analytics Dashboard · Data current as of March 2026
</div>
""", unsafe_allow_html=True)
