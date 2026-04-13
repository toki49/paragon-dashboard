"""
Paragon Fellowship — Cohort Comparison Report
Drag in two exit survey files (CSV or XLSX) to compare cohorts side-by-side.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from collections import Counter
import re

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Paragon · Cohort Comparison",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
NAVY   = "#0D1F3C"
BLUE   = "#2563EB"
SILVER = "#A8B8D0"
PALE   = "#C8D6E8"
BG     = "#F4F7FB"
CARD   = "#FFFFFF"
GREEN  = "#16A34A"
RED    = "#DC2626"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

  html, body, [class*="css"] {{
      font-family: 'DM Sans', sans-serif;
      background-color: {BG};
      color: {NAVY};
  }}
  #MainMenu, footer, header {{ visibility: hidden; }}

  .stTabs [data-baseweb="tab-list"] {{
      gap: 0; background: {NAVY}; border-radius: 12px; padding: 4px;
  }}
  .stTabs [data-baseweb="tab"] {{
      color: {SILVER}; font-family: 'DM Sans', sans-serif; font-weight: 500;
      font-size: 0.82rem; letter-spacing: 0.05em; text-transform: uppercase;
      padding: 8px 20px; border-radius: 9px;
  }}
  .stTabs [aria-selected="true"] {{ background: {BLUE} !important; color: white !important; }}
  .stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.5rem; }}

  .masthead {{
      background: {NAVY}; border-radius: 16px; padding: 28px 36px;
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 1.5rem;
  }}
  .masthead-title {{ font-family:'DM Serif Display',serif; font-size:1.9rem; color:white; margin:0; }}
  .masthead-sub {{ font-size:0.82rem; color:{SILVER}; margin:4px 0 0; }}

  .section-header {{
      font-family:'DM Serif Display',serif; font-size:1.3rem;
      color:{NAVY}; margin:2rem 0 .75rem; border-bottom: 1px solid #E2EAF4; padding-bottom: 6px;
  }}

  .kpi-card {{
      background:{CARD}; border-radius:14px; padding:20px 22px;
      border:1px solid #E2EAF4; box-shadow:0 2px 8px rgba(13,31,60,.05);
      height: 100%;
  }}
  .kpi-label {{ font-size:0.68rem; font-weight:600; letter-spacing:.1em;
      text-transform:uppercase; color:{SILVER}; margin-bottom:4px; }}
  .kpi-value {{ font-family:'DM Serif Display',serif; font-size:2.1rem;
      color:{NAVY}; line-height:1; }}
  .kpi-sub {{ font-size:0.75rem; color:{SILVER}; margin-top:4px; }}

  .cohort-badge-su {{
      display:inline-block; background:{NAVY}; color:white;
      border-radius:999px; padding:3px 12px; font-size:.72rem;
      font-weight:700; letter-spacing:.06em;
  }}
  .cohort-badge-fa {{
      display:inline-block; background:{BLUE}; color:white;
      border-radius:999px; padding:3px 12px; font-size:.72rem;
      font-weight:700; letter-spacing:.06em;
  }}

  .delta-up   {{ color:{GREEN}; font-weight:700; font-size:.8rem; }}
  .delta-down {{ color:{RED};   font-weight:700; font-size:.8rem; }}
  .delta-flat {{ color:{SILVER};font-weight:600; font-size:.8rem; }}

  .insight-box {{
      background: linear-gradient(135deg, {NAVY} 0%, #1a3a6b 100%);
      border-radius:14px; padding:22px 26px; color:white; margin-top:1rem;
  }}
  .insight-box h4 {{ font-family:'DM Serif Display',serif; font-size:1.1rem;
      margin:0 0 10px; color:{SILVER}; font-weight:normal; }}
  .insight-box p {{ font-size:.87rem; line-height:1.6; margin:0; color:#dce8f5; }}

  .compare-table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
  .compare-table th {{
      background:{NAVY}; color:white; padding:10px 14px;
      text-align:left; font-weight:600; font-size:.72rem;
      letter-spacing:.08em; text-transform:uppercase;
  }}
  .compare-table td {{ padding:10px 14px; border-bottom:1px solid #E2EAF4; }}
  .compare-table tr:last-child td {{ border-bottom:none; }}
  .compare-table tr:hover td {{ background:#F0F5FD; }}

  .quote-card {{
      background:{CARD}; border-left:3px solid {BLUE}; border-radius:8px;
      padding:12px 16px; margin-bottom:9px; font-size:.85rem;
      font-style:italic; color:{NAVY}; border:1px solid #E2EAF4;
      border-left:3px solid {BLUE}; box-shadow:0 1px 4px rgba(13,31,60,.04);
  }}
  .quote-card-navy {{
      background:{CARD}; border-left:3px solid {NAVY}; border-radius:8px;
      padding:12px 16px; margin-bottom:9px; font-size:.85rem;
      font-style:italic; color:{NAVY}; border:1px solid #E2EAF4;
      border-left:3px solid {NAVY}; box-shadow:0 1px 4px rgba(13,31,60,.04);
  }}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
LIKERT_MAP = {"Strongly Agree":5,"Agree":4,"Neutral":3,"Disagree":2,"Strongly Disagree":1}
HOURS_MAP  = {"1-4 hours":2.5,"5-10 hours":7.5,"11-15 hours":13,"16-20 hours":18,"20+ hours":22}
CAT_ORDER  = ["Strongly Disagree","Disagree","Neutral","Agree","Strongly Agree"]

def base_layout(h=None):
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=NAVY, size=12),
        margin=dict(l=0, r=0, t=30, b=0),
    )
    if h: d["height"] = h
    return d

# ── Data loading ───────────────────────────────────────────────────────────────
def load_file(f):
    if f is None: return None
    name = f.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(f)
    return pd.read_excel(f)

def find_col(df, hints):
    """Find first column matching any hint substring (case-insensitive)."""
    for hint in hints:
        for c in df.columns:
            if hint.lower() in c.lower():
                return c
    return None

def safe_mean(series):
    v = pd.to_numeric(series, errors="coerce").dropna()
    return round(v.mean(), 2) if len(v) else None

def likert_pct(series, threshold=4):
    v = series.map(LIKERT_MAP).dropna()
    return round((v >= threshold).mean() * 100, 0) if len(v) else None

def delta_html(d, unit=""):
    if d is None: return ""
    if d > 0.05:  return f'<span class="delta-up">▲ +{d:.2f}{unit}</span>'
    if d < -0.05: return f'<span class="delta-down">▼ {d:.2f}{unit}</span>'
    return f'<span class="delta-flat">→ {d:+.2f}{unit}</span>'

def avg_bar(val, color, max_val=5):
    pct = (val or 0) / max_val * 100
    return (f'<div style="background:#E2EAF4;border-radius:4px;height:6px;margin-top:8px;">'
            f'<div style="background:{color};width:{pct:.0f}%;height:6px;border-radius:4px;"></div>'
            f'</div>')

def kpi_html(label, v1, v2, name1, name2, unit="", max_val=5):
    d = (v2 - v1) if (v1 is not None and v2 is not None) else None
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div style="display:flex;gap:20px;align-items:flex-end;margin-top:6px;">
        <div>
          <div style="font-size:.67rem;color:{SILVER};font-weight:600;letter-spacing:.07em;">{name1}</div>
          <div class="kpi-value" style="color:{NAVY};">{v1 if v1 else '—'}{unit}</div>
          {avg_bar(v1, NAVY) if v1 and unit=="" else ""}
        </div>
        <div>
          <div style="font-size:.67rem;color:{SILVER};font-weight:600;letter-spacing:.07em;">{name2}</div>
          <div class="kpi-value" style="color:{BLUE};">{v2 if v2 else '—'}{unit}</div>
          {avg_bar(v2, BLUE) if v2 and unit=="" else ""}
        </div>
      </div>
      <div style="margin-top:8px;">{delta_html(d, unit)}</div>
    </div>"""

# ── Top keywords helper ────────────────────────────────────────────────────────
STOPWORDS = {"the","a","an","and","or","to","of","in","is","it","for","on","that","this",
             "i","we","my","was","with","be","have","are","at","but","as","not","would",
             "more","our","also","could","has","been","they","their","from","so","some",
             "if","were","which","by","me","very","really","think","feel","like","get",
             "just","also","even","been","about","much","when","than","well","had"}

def top_words(texts, n=15):
    words = []
    for t in texts:
        words.extend([w for w in re.findall(r"\b[a-zA-Z]{4,}\b", str(t).lower())
                      if w not in STOPWORDS])
    return Counter(words).most_common(n)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="masthead">
  <div>
    <p class="masthead-title">◆ Paragon Fellowship</p>
    <p class="masthead-sub">Cohort Comparison Report · Exit Survey Analytics</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Upload two files ───────────────────────────────────────────────────────────
uc1, uc2 = st.columns(2)
with uc1:
    st.caption("**Cohort A** (e.g. SU25) — CSV or XLSX")
    file_a = st.file_uploader("Cohort A", type=["csv","xlsx"], label_visibility="collapsed", key="fa")
with uc2:
    st.caption("**Cohort B** (e.g. FA25) — CSV or XLSX")
    file_b = st.file_uploader("Cohort B", type=["csv","xlsx"], label_visibility="collapsed", key="fb")

if not file_a or not file_b:
    st.info("Upload both cohort files above to generate the comparison report.", icon="◆")
    st.stop()

df_a = load_file(file_a)
df_b = load_file(file_b)

# ── Cohort name detection ─────────────────────────────────────────────────────
def cohort_name(fname):
    m = re.search(r"(SU\d+|FA\d+|SP\d+|WI\d+)", fname, re.IGNORECASE)
    return m.group(0).upper() if m else fname.split("_")[0].upper()

name_a = cohort_name(file_a.name)
name_b = cohort_name(file_b.name)

Na, Nb = len(df_a), len(df_b)

# ── Column finders ────────────────────────────────────────────────────────────
def C(df, *hints): return find_col(df, hints)

def rating(df, *hints):
    c = C(df, *hints)
    return pd.to_numeric(df[c], errors="coerce") if c else pd.Series(dtype=float)

def likert_ser(df, *hints):
    c = C(df, *hints)
    return df[c] if c else pd.Series(dtype=str)

def text_col(df, *hints):
    c = C(df, *hints)
    return df[c].dropna().tolist() if c else []

# ── Compute core metrics ───────────────────────────────────────────────────────
metrics = {}
for key, hints in {
    "workshops":  ["policy workshops"],
    "speakers":   ["speaker events"],
    "peer":       ["Bridge Buddies","Donut Buddies","engaging were"],
    "experience": ["experience with Paragon"],
    "skills":     ["developed new skills"],
}.items():
    va = rating(df_a, *hints)
    vb = rating(df_b, *hints)
    metrics[key] = (safe_mean(va), safe_mean(vb))

likert_metrics = {}
for key, hints in {
    "understand":  ["understanding of tech policy","improved my understanding"],
    "interest":    ["interest in pursuing","interest in a career"],
    "confidence":  ["ability to procure an internship","confident about my ability"],
}.items():
    sa = likert_ser(df_a, *hints)
    sb = likert_ser(df_b, *hints)
    likert_metrics[key] = (
        likert_pct(sa), likert_pct(sb),
        safe_mean(sa.map(LIKERT_MAP)), safe_mean(sb.map(LIKERT_MAP)),
        sa, sb,
    )

hrs_a = C(df_a, "hours"); hrs_b = C(df_b, "hours")
avg_hrs_a = round(df_a[hrs_a].map(HOURS_MAP).dropna().mean(), 1) if hrs_a else None
avg_hrs_b = round(df_b[hrs_b].map(HOURS_MAP).dropna().mean(), 1) if hrs_b else None

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋  At a Glance",
    "📊  Ratings",
    "🎯  Fellow Outcomes",
    "📈  Trends",
    "💬  Qualitative",
])

# ════════════════════════════════════════════════════════════════════
#  TAB 1 · AT A GLANCE
# ════════════════════════════════════════════════════════════════════
with tab1:
    # cohort badges + N
    b1, b2, _, _ = st.columns(4)
    with b1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Cohort A</div>'
                    f'<div style="margin:6px 0;"><span class="cohort-badge-su">{name_a}</span></div>'
                    f'<div class="kpi-value">{Na}</div><div class="kpi-sub">respondents</div></div>',
                    unsafe_allow_html=True)
    with b2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Cohort B</div>'
                    f'<div style="margin:6px 0;"><span class="cohort-badge-fa">{name_b}</span></div>'
                    f'<div class="kpi-value">{Nb}</div><div class="kpi-sub">respondents</div></div>',
                    unsafe_allow_html=True)

    st.markdown('<p class="section-header">Head-to-Head Summary</p>', unsafe_allow_html=True)

    # big comparison table
    rows = [
        ("Policy Workshops",  *metrics["workshops"]),
        ("Speaker Events",    *metrics["speakers"]),
        ("Peer / Buddy Events",*metrics["peer"]),
        ("Overall Experience",*metrics["experience"]),
        ("Skill Development", *metrics["skills"]),
        ("Avg hrs / week",    avg_hrs_a, avg_hrs_b),
        ("Understood tech policy (≥Agree)", f'{likert_metrics["understand"][0]:.0f}%' if likert_metrics["understand"][0] else "—",
                                             f'{likert_metrics["understand"][1]:.0f}%' if likert_metrics["understand"][1] else "—"),
        ("Career interest (≥Agree)",        f'{likert_metrics["interest"][0]:.0f}%' if likert_metrics["interest"][0] else "—",
                                             f'{likert_metrics["interest"][1]:.0f}%' if likert_metrics["interest"][1] else "—"),
        ("Internship confidence (≥Agree)",  f'{likert_metrics["confidence"][0]:.0f}%' if likert_metrics["confidence"][0] else "—",
                                             f'{likert_metrics["confidence"][1]:.0f}%' if likert_metrics["confidence"][1] else "—"),
    ]

    table_rows = ""
    for label, va, vb in rows:
        try:
            d = float(str(vb).replace('%','')) - float(str(va).replace('%',''))
            is_pct = "%" in str(va)
            dh = delta_html(d, "%" if is_pct else "")
        except:
            dh = ""
        table_rows += f"""
        <tr>
          <td><strong>{label}</strong></td>
          <td>{va}</td>
          <td>{vb}</td>
          <td>{dh}</td>
        </tr>"""

    st.markdown(f"""
    <table class="compare-table">
      <tr>
        <th>Metric</th>
        <th><span class="cohort-badge-su" style="font-size:.7rem;">{name_a}</span></th>
        <th><span class="cohort-badge-fa" style="font-size:.7rem;">{name_b}</span></th>
        <th>Change</th>
      </tr>
      {table_rows}
    </table>
    """, unsafe_allow_html=True)

    # ── Cross-cohort insight box ──────────────────────────────────────
    # Build narrative automatically from data
    improved = [k for k, (a, b) in metrics.items()
                if a is not None and b is not None and b - a > 0.05]
    declined = [k for k, (a, b) in metrics.items()
                if a is not None and b is not None and b - a < -0.05]
    labels_map = {"workshops":"workshop ratings","speakers":"speaker event ratings",
                  "peer":"peer/buddy event ratings","experience":"overall experience",
                  "skills":"skill development scores"}
    imp_str  = ", ".join(labels_map.get(k,k) for k in improved)  or "no metrics"
    dec_str  = ", ".join(labels_map.get(k,k) for k in declined)  or "no metrics"
    conf_d = (likert_metrics["confidence"][1] or 0) - (likert_metrics["confidence"][0] or 0)
    conf_note = (f"Internship confidence rose +{conf_d:.0f}pp to "
                 f"{likert_metrics['confidence'][1]:.0f}% in {name_b}."
                 if conf_d > 0 else
                 f"Internship confidence held steady across cohorts.")

    st.markdown(f"""
    <div class="insight-box">
      <h4>⬡ Cross-Cohort Insight</h4>
      <p>
        Between {name_a} and {name_b}, <strong>{imp_str}</strong> improved
        while <strong>{dec_str}</strong> declined.
        Respondent count grew from {Na} to {Nb} (+{Nb-Na}).
        {conf_note}
        Overall experience ticked {"up" if (metrics["experience"][1] or 0) > (metrics["experience"][0] or 0) else "down"}
        from {metrics["experience"][0]} → {metrics["experience"][1]}/5,
        suggesting {"continued momentum" if (metrics["experience"][1] or 0) >= (metrics["experience"][0] or 0) else "an area to monitor"}.
      </p>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 2 · RATINGS
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-header">Programming Ratings — Side by Side</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    cols3 = [c1, c2, c3]
    prog_keys = [
        ("workshops",  "Policy Workshops"),
        ("speakers",   "Speaker Events"),
        ("peer",       "Peer / Buddy Events"),
    ]
    for i, (key, label) in enumerate(prog_keys):
        va, vb = metrics[key]
        with cols3[i]:
            st.markdown(kpi_html(label, va, vb, name_a, name_b), unsafe_allow_html=True)

    st.markdown("")
    c4, c5 = st.columns(2)
    with c4:
        va, vb = metrics["experience"]
        st.markdown(kpi_html("Overall Experience", va, vb, name_a, name_b), unsafe_allow_html=True)
    with c5:
        va, vb = metrics["skills"]
        st.markdown(kpi_html("Skill Development", va, vb, name_a, name_b), unsafe_allow_html=True)

    # ── Grouped bar: distributions per metric ────────────────────────
    st.markdown('<p class="section-header">Rating Distributions</p>', unsafe_allow_html=True)

    metric_sel = st.selectbox("Select metric", [l for _,l in prog_keys] + ["Overall Experience","Skill Development"],
                               key="dist_sel")
    key_map = {l: k for k, l in prog_keys}
    key_map.update({"Overall Experience":"experience","Skill Development":"skills"})
    sel_key = key_map[metric_sel]

    hints_map = {
        "workshops":["policy workshops"], "speakers":["speaker events"],
        "peer":["Bridge Buddies","Donut Buddies","engaging were"],
        "experience":["experience with Paragon"], "skills":["developed new skills"],
    }
    va_ser = rating(df_a, *hints_map[sel_key])
    vb_ser = rating(df_b, *hints_map[sel_key])

    fig_dist = go.Figure()
    for rating_val in [1, 2, 3, 4, 5]:
        ca = (va_ser == rating_val).sum()
        cb = (vb_ser == rating_val).sum()
        opacity = 0.4 + 0.15 * rating_val
        fig_dist.add_trace(go.Bar(name=str(rating_val), x=[name_a, name_b],
                                   y=[ca, cb], marker_color=BLUE,
                                   marker_opacity=opacity,
                                   text=[ca, cb], textposition="inside"))
    fig_dist.update_layout(**base_layout(300), barmode="stack",
                            legend_title="Rating",
                            xaxis=dict(showgrid=False),
                            yaxis=dict(showgrid=False, title="Respondents"))
    st.plotly_chart(fig_dist, use_container_width=True)

    # ── NPS-style breakdown both cohorts ─────────────────────────────
    st.markdown('<p class="section-header">Experience Satisfaction Breakdown</p>', unsafe_allow_html=True)

    exp_a = rating(df_a, "experience with Paragon")
    exp_b = rating(df_b, "experience with Paragon")

    fig_nps = go.Figure()
    for i, (name, ser) in enumerate([(name_a, exp_a),(name_b, exp_b)]):
        total = ser.dropna().__len__()
        if total == 0: continue
        det = (ser <= 2).sum(); neu = (ser == 3).sum(); pro = (ser >= 4).sum()
        fig_nps.add_trace(go.Bar(name=f"{name} Detractors", y=[name], x=[det/total*100],
                                  orientation="h", marker_color=PALE,
                                  text=[f"Det. {det/total*100:.0f}%"],
                                  textposition="inside", legendgroup=name, showlegend=False))
        fig_nps.add_trace(go.Bar(name=f"{name} Neutral", y=[name], x=[neu/total*100],
                                  orientation="h", marker_color=SILVER,
                                  text=[f"Neutral {neu/total*100:.0f}%"],
                                  textposition="inside", legendgroup=name, showlegend=False))
        fig_nps.add_trace(go.Bar(name=f"{name} Promoters", y=[name], x=[pro/total*100],
                                  orientation="h",
                                  marker_color=NAVY if i==0 else BLUE,
                                  text=[f"Promoters {pro/total*100:.0f}%"],
                                  textposition="inside", legendgroup=name))

    fig_nps.update_layout(**base_layout(140), barmode="stack", showlegend=False,
                           xaxis=dict(showticklabels=False,showgrid=False,range=[0,100]),
                           yaxis=dict(showgrid=False))
    st.plotly_chart(fig_nps, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 3 · FELLOW OUTCOMES
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-header">Outcome Agreement — % Agree or Strongly Agree</p>',
                unsafe_allow_html=True)

    outcome_labels = {
        "understand": "Improved understanding of tech policy",
        "interest":   "Increased career interest",
        "confidence": "More confident about internship prospects",
    }
    fig_out = go.Figure()
    for key, label in outcome_labels.items():
        pa, pb = likert_metrics[key][0], likert_metrics[key][1]
        fig_out.add_trace(go.Bar(name=name_a, y=[label], x=[pa or 0],
                                  orientation="h", marker_color=NAVY,
                                  text=[f"{pa:.0f}%" if pa else ""],
                                  textposition="outside",
                                  showlegend=(key=="understand")))
        fig_out.add_trace(go.Bar(name=name_b, y=[label], x=[pb or 0],
                                  orientation="h", marker_color=BLUE,
                                  text=[f"{pb:.0f}%" if pb else ""],
                                  textposition="outside",
                                  showlegend=(key=="understand")))

    fig_out.update_layout(**base_layout(260), barmode="group",
                           xaxis=dict(range=[0,115],showgrid=False,showticklabels=False),
                           yaxis=dict(showgrid=False),
                           legend=dict(orientation="h",y=1.12),
                           bargap=0.25, bargroupgap=0.08)
    st.plotly_chart(fig_out, use_container_width=True)

    # ── Stacked likert per cohort ─────────────────────────────────────
    st.markdown('<p class="section-header">Full Likert Breakdown</p>', unsafe_allow_html=True)

    lk_sel = st.radio("Outcome", list(outcome_labels.values()), horizontal=True, key="lk_sel")
    lk_key = {v:k for k,v in outcome_labels.items()}[lk_sel]
    sa_ser, sb_ser = likert_metrics[lk_key][4], likert_metrics[lk_key][5]

    fig_lk = go.Figure()
    bar_colors = [RED, "#F87171", SILVER, "#60A5FA", NAVY]
    for i, cat in enumerate(CAT_ORDER):
        ca = (sa_ser == cat).sum()
        cb = (sb_ser == cat).sum()
        fig_lk.add_trace(go.Bar(name=cat, x=[name_a, name_b], y=[ca, cb],
                                 marker_color=bar_colors[i],
                                 text=[ca, cb], textposition="inside"))
    fig_lk.update_layout(**base_layout(280), barmode="stack",
                          legend=dict(orientation="h",y=-0.25,traceorder="normal"),
                          xaxis=dict(showgrid=False),
                          yaxis=dict(showgrid=False,title="Respondents"))
    st.plotly_chart(fig_lk, use_container_width=True)

    # ── Hours + mentorship ────────────────────────────────────────────
    st.markdown('<p class="section-header">Commitment & Engagement</p>', unsafe_allow_html=True)
    h1, h2 = st.columns(2)

    with h1:
        # hours grouped bar
        if hrs_a and hrs_b:
            order = ["1-4 hours","5-10 hours","11-15 hours","16-20 hours","20+ hours"]
            hca = df_a[hrs_a].map(HOURS_MAP).value_counts()
            hcb = df_b[hrs_b].map(HOURS_MAP).value_counts()
            # map back labels
            inv = {v:k for k,v in HOURS_MAP.items()}
            fig_hrs = go.Figure()
            ca_vals = [df_a[hrs_a].str.contains(b, na=False, regex=False).sum() for b in order]
            cb_vals = [df_b[hrs_b].str.contains(b, na=False, regex=False).sum() for b in order]
            fig_hrs.add_trace(go.Bar(name=name_a, x=order, y=ca_vals, marker_color=NAVY))
            fig_hrs.add_trace(go.Bar(name=name_b, x=order, y=cb_vals, marker_color=BLUE))
            fig_hrs.update_layout(**base_layout(260), barmode="group", title="Hours / Week",
                                   xaxis=dict(showgrid=False, tickangle=-20),
                                   yaxis=dict(showgrid=False),
                                   legend=dict(orientation="h",y=1.15))
            st.plotly_chart(fig_hrs, use_container_width=True)

    with h2:
        # mentorship interest donut
        ment_a_c = C(df_a, "alumni mentorship")
        ment_b_c = C(df_b, "alumni mentorship")
        if ment_a_c and ment_b_c:
            ya = (df_a[ment_a_c] == "Yes").sum()
            yb = (df_b[ment_b_c] == "Yes").sum()
            fig_ment = go.Figure()
            fig_ment.add_trace(go.Bar(name=name_a, x=["Yes","No"],
                                       y=[(df_a[ment_a_c]=="Yes").sum(),(df_a[ment_a_c]=="No").sum()],
                                       marker_color=NAVY))
            fig_ment.add_trace(go.Bar(name=name_b, x=["Yes","No"],
                                       y=[(df_b[ment_b_c]=="Yes").sum(),(df_b[ment_b_c]=="No").sum()],
                                       marker_color=BLUE))
            fig_ment.update_layout(**base_layout(260), barmode="group",
                                    title="Mentorship Program Interest",
                                    xaxis=dict(showgrid=False),
                                    yaxis=dict(showgrid=False),
                                    legend=dict(orientation="h",y=1.15))
            st.plotly_chart(fig_ment, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 4 · TRENDS (line charts over time)
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-header">Rating Trends Across Cohorts</p>', unsafe_allow_html=True)

    trend_metrics = [
        ("workshops",  "Policy Workshops",    BLUE),
        ("speakers",   "Speaker Events",      NAVY),
        ("peer",       "Peer / Buddy Events", SILVER),
        ("experience", "Overall Experience",  "#6B8DB8"),
        ("skills",     "Skill Development",   PALE),
    ]

    cohorts = [name_a, name_b]

    # main multi-line chart
    fig_trend = go.Figure()
    for key, label, color in trend_metrics:
        va, vb = metrics[key]
        if va is None and vb is None: continue
        y_vals = [va if va else np.nan, vb if vb else np.nan]
        fig_trend.add_trace(go.Scatter(
            x=cohorts, y=y_vals, name=label,
            mode="lines+markers+text",
            line=dict(color=color, width=2.5),
            marker=dict(size=10, color=color),
            text=[f"{v:.2f}" if v else "" for v in y_vals],
            textposition=["middle left", "middle right"],
            textfont=dict(size=11, color=color),
        ))

    fig_trend.update_layout(
        **base_layout(420),
        yaxis=dict(range=[1, 5.3], showgrid=True, gridcolor="#E2EAF4", title="Avg. Rating (1–5)"),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=-0.18),
        hovermode="x unified",
    )
    # reference lines
    fig_trend.add_hline(y=4.0, line_dash="dot", line_color=SILVER, line_width=1,
                         annotation_text="4.0", annotation_position="right")
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Individual sparkline cards ────────────────────────────────────
    st.markdown('<p class="section-header">Metric Snapshots</p>', unsafe_allow_html=True)
    cols5 = st.columns(5)
    for i, (key, label, color) in enumerate(trend_metrics):
        va, vb = metrics[key]
        with cols5[i]:
            d = (vb - va) if (va and vb) else None
            arrow = "▲" if (d and d > 0) else ("▼" if (d and d < 0) else "→")
            dcolor = GREEN if (d and d > 0) else (RED if (d and d < 0) else SILVER)
            st.markdown(f"""
            <div class="kpi-card" style="text-align:center;">
              <div class="kpi-label">{label}</div>
              <div style="font-family:'DM Serif Display',serif;font-size:1.5rem;color:{NAVY};margin:4px 0">
                {va if va else "—"} → {vb if vb else "—"}
              </div>
              <div style="color:{dcolor};font-weight:700;font-size:.9rem;">
                {arrow} {f"{d:+.2f}" if d is not None else ""}
              </div>
            </div>""", unsafe_allow_html=True)

    # ── Likert trend ──────────────────────────────────────────────────
    st.markdown('<p class="section-header">Outcome Agreement Trend</p>', unsafe_allow_html=True)
    fig_lk_trend = go.Figure()
    lk_colors = [NAVY, BLUE, SILVER]
    for i, (key, label) in enumerate(outcome_labels.items()):
        pa, pb = likert_metrics[key][0], likert_metrics[key][1]
        fig_lk_trend.add_trace(go.Scatter(
            x=cohorts, y=[pa or np.nan, pb or np.nan],
            name=label, mode="lines+markers+text",
            line=dict(color=lk_colors[i], width=2.5),
            marker=dict(size=9),
            text=[f"{v:.0f}%" if v else "" for v in [pa, pb]],
            textposition=["middle left","middle right"],
        ))
    fig_lk_trend.update_layout(
        **base_layout(320),
        yaxis=dict(range=[50,110],showgrid=True,gridcolor="#E2EAF4",title="% Agree/Strongly Agree"),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h",y=-0.22),
    )
    st.plotly_chart(fig_lk_trend, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 5 · QUALITATIVE
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<p class="section-header">Top Keywords by Cohort</p>', unsafe_allow_html=True)

    kw1, kw2 = st.columns(2)
    text_hints = ["suggestions","content of our programming"]

    for col_widget, name, df_coh in [(kw1, name_a, df_a),(kw2, name_b, df_b)]:
        with col_widget:
            badge_class = "cohort-badge-su" if name == name_a else "cohort-badge-fa"
            st.markdown(f'<span class="{badge_class}">{name}</span>', unsafe_allow_html=True)
            texts = text_col(df_coh, *text_hints)
            freq = top_words(texts, 15)
            if freq:
                fw = pd.DataFrame(freq, columns=["word","count"])
                fig_kw = go.Figure(go.Bar(
                    x=fw["count"], y=fw["word"], orientation="h",
                    marker_color=NAVY if name==name_a else BLUE,
                    text=fw["count"], textposition="outside",
                ))
                fig_kw.update_layout(**base_layout(360),
                                      yaxis=dict(autorange="reversed",showgrid=False),
                                      xaxis=dict(showgrid=False,showticklabels=False))
                st.plotly_chart(fig_kw, use_container_width=True)

    # ── Open response browser ─────────────────────────────────────────
    st.markdown('<p class="section-header">Response Explorer</p>', unsafe_allow_html=True)

    resp_options = {
        "Programming Suggestions": ["suggestions","content of our programming"],
        "Experience & Skill Growth": ["elaborate on your rating","skill growth"],
        "Perspective on Tech Policy": ["perspective on tech policy","evolved since"],
    }
    resp_sel = st.selectbox("Question", list(resp_options.keys()), key="resp_sel")
    hints_sel = resp_options[resp_sel]

    rc1, rc2 = st.columns(2)
    for col_widget, name, df_coh in [(rc1, name_a, df_a),(rc2, name_b, df_b)]:
        with col_widget:
            badge_class = "cohort-badge-su" if name == name_a else "cohort-badge-fa"
            st.markdown(f'<span class="{badge_class}">{name} &nbsp;·&nbsp; {len(df_coh)} respondents</span>',
                        unsafe_allow_html=True)
            texts = [t for t in text_col(df_coh, *hints_sel)
                     if str(t).strip().lower() not in ("n/a","na","none","")]
            show_all = st.checkbox(f"Show all ({len(texts)})", key=f"show_{name}_{resp_sel}")
            displayed = texts if show_all else texts[:5]
            card_class = "quote-card-navy" if name == name_a else "quote-card"
            for t in displayed:
                st.markdown(f'<div class="{card_class}">{str(t)[:400]}{"…" if len(str(t))>400 else ""}</div>',
                            unsafe_allow_html=True)