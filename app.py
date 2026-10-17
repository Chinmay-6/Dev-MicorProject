"""
Global E-Waste Recovery and Circular Economy Analytics
Micro Project - Data Exploration and Visualization (1ADPC302)

Run:  pip install streamlit pandas numpy plotly
      streamlit run app.py
Keep ewaste_data.csv in the same folder as this file.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Global E-Waste Analytics", page_icon="♻️", layout="wide")

# ------------------------------------------------------------------ style
GREEN, RED, ORANGE = "#2ecc9a", "#ff6b81", "#ff9f43"
REGION_COLORS = {"Asia": "#4dabf7", "Americas": "#2ecc9a", "Europe": "#b197fc",
                 "Africa": "#ff9f43", "Oceania": "#ffd43b"}
PLOT = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=50, b=10))

st.markdown("""
<style>
.banner {background: linear-gradient(90deg,#0b6e4f,#14a37f); padding: 1.2rem 1.5rem;
         border-radius: 12px; margin-bottom: 1rem;}
.banner h1 {margin: 0; font-size: 1.9rem; color: white;}
.banner p {margin: .3rem 0 0 0; color: #e6fff6; font-size: .95rem;}
.kpi {background: #1a1f2b; border: 1px solid #2b3140; border-radius: 10px; padding: .8rem 1rem;}
.kpi .l {color: #8b95a5; font-size: .8rem;} .kpi .v {font-size: 1.7rem; font-weight: 700;}
.kpi .s {color: #2ecc9a; font-size: .78rem;}
.note {background: #10263a; border-left: 4px solid #4dabf7; padding: .6rem .9rem;
       border-radius: 6px; font-size: .9rem; margin: .4rem 0 1rem 0;}
</style>
""", unsafe_allow_html=True)


def kpi(col, label, value, sub):
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>'
                 f'<div class="s">{sub}</div></div>', unsafe_allow_html=True)


def note(text):
    st.markdown(f'<div class="note">💡 <b>How to read it:</b> {text}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    needed = {"year", "region", "category", "generated_kt", "recycled_kt", "unrecycled_kt",
              "recoverable_value_musd", "collection_rate_pct", "population_bn"}
    missing = needed - set(df.columns)
    if missing:
        st.error(f"Missing columns in CSV: {sorted(missing)}")
        st.stop()
    return df


csv_path = Path(__file__).with_name("ewaste_data.csv")
if csv_path.exists():
    data = load_data(csv_path)
else:
    up = st.file_uploader("ewaste_data.csv not found next to app.py - upload it here", type="csv")
    if up is None:
        st.stop()
    data = load_data(up)

ALL_REGIONS = sorted(data.region.unique())
ALL_CATS = sorted(data.category.unique())
Y_MIN, Y_MAX = int(data.year.min()), int(data.year.max())

# ------------------------------------------------------------------ sidebar
def reset_filters():
    st.session_state.regions = ALL_REGIONS
    st.session_state.cats = ALL_CATS
    st.session_state.years = (Y_MIN, Y_MAX)
    st.session_state.target = 30


for key, default in [("regions", ALL_REGIONS), ("cats", ALL_CATS),
                     ("years", (Y_MIN, Y_MAX)), ("target", 30)]:
    st.session_state.setdefault(key, default)

with st.sidebar:
    st.header("♻️ Filters & Controls")
    st.caption("Refine the e-waste data in real time.")
    sel_regions = st.multiselect("Region", ALL_REGIONS, key="regions")
    sel_cats = st.multiselect("Product category", ALL_CATS, key="cats")
    y0, y1 = st.slider("Year range", Y_MIN, Y_MAX, key="years")
    target = st.slider("Recycling target for charts (%)", 10, 80, key="target",
                       help="Used for the target line and the 2030 scenario.")
    st.button("Reset All Filters", on_click=reset_filters, width='stretch')

df = data[data.region.isin(sel_regions) & data.category.isin(sel_cats)
          & data.year.between(y0, y1)]
if df.empty:
    st.warning("No records match the current filters. Select at least one region and category.")
    st.stop()

# ------------------------------------------------------------------ summary numbers
yearly = df.groupby("year")[["generated_kt", "recycled_kt", "unrecycled_kt",
                             "recoverable_value_musd"]].sum().reset_index()
yearly["gen_mt"] = yearly.generated_kt / 1000
yearly["rec_mt"] = yearly.recycled_kt / 1000
yearly["gap_mt"] = yearly.unrecycled_kt / 1000
yearly["rate"] = yearly.recycled_kt / yearly.generated_kt * 100

last = yearly.iloc[-1]
first = yearly.iloc[0]
last_year = int(last.year)
# world total of ~82 Mt in 2030 vs the latest data year, applied to the filtered selection
SCALE_2030 = 82.0 / (data[data.year == Y_MAX].generated_kt.sum() / 1000)
growth = (last.gen_mt / first.gen_mt - 1) * 100 if len(yearly) > 1 else 0.0

st.markdown(f"""
<div class="banner"><h1>♻️ Global E-Waste Recovery & Circular Economy Analytics</h1>
<p>Explore e-waste generation, formal recycling and recoverable material value by region and
product category. File: ewaste_data.csv · {len(df):,} of {len(data):,} records active ·
Years {y0}–{y1}</p></div>
""", unsafe_allow_html=True)

c = st.columns(5)
kpi(c[0], f"E-waste generated ({last_year})", f"{last.gen_mt:,.1f} Mt",
    f"{growth:+.0f}% since {int(first.year)}")
kpi(c[1], f"Formally recycled ({last_year})", f"{last.rec_mt:,.1f} Mt", f"{last.rate:.1f}% of generated")
kpi(c[2], f"Recovery gap ({last_year})", f"{last.gap_mt:,.1f} Mt", f"{100 - last.rate:.1f}% not documented")
kpi(c[3], f"Unrecovered value ({last_year})", f"US$ {last.recoverable_value_musd / 1000:,.1f} bn",
    "recoverable materials")
pop = (df[df.year == last_year].drop_duplicates("region").population_bn.sum()) * 1000  # million people
kpi(c[4], "Per-capita e-waste", f"{last.generated_kt / pop:,.1f} kg" if pop else "-", "kg per person per year")
st.write("")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Global Trends", "🌍 Regional Analysis",
                                  "📦 Products & Materials", "♻️ Circular Gap & Scenarios"])

# ------------------------------------------------------------------ tab 1
with tab1:
    st.subheader("Generation vs Formal Recycling")
    col1, col2 = st.columns([3, 2])
    fig = go.Figure()
    fig.add_scatter(x=yearly.year, y=yearly.gen_mt, name="Generated", mode="lines+markers",
                    line=dict(color=ORANGE, width=3))
    fig.add_scatter(x=yearly.year, y=yearly.rec_mt, name="Formally recycled", mode="lines+markers",
                    line=dict(color=GREEN, width=3))
    if last_year == Y_MAX:  # dashed projection to 2030
        gen30 = last.gen_mt * SCALE_2030
        rec30 = gen30 * 0.20
        fig.add_scatter(x=[last_year, 2030], y=[last.gen_mt, gen30], mode="lines", showlegend=False,
                        line=dict(color=ORANGE, dash="dash"))
        fig.add_scatter(x=[last_year, 2030], y=[last.rec_mt, rec30], mode="lines", showlegend=False,
                        line=dict(color=GREEN, dash="dash"))
    fig.update_layout(title="E-waste generated vs formally recycled (dashed = projection to 2030)",
                      yaxis_title="Million tonnes (Mt)", xaxis_title="Year", **PLOT)
    col1.plotly_chart(fig, width='stretch')

    fig = px.area(yearly, x="year", y="rate", title="Formal recycling rate (% of generated)")
    fig.update_traces(line_color=GREEN, fillcolor="rgba(46,204,154,.25)")
    fig.add_hline(y=target, line_dash="dash", line_color=RED,
                  annotation_text=f"Target {target}%", annotation_position="top left")
    fig.update_layout(yaxis_title="%", xaxis_title="Year", yaxis_range=[0, max(40, target + 5)], **PLOT)
    col2.plotly_chart(fig, width='stretch')
    note("The orange line is the e-waste produced and the green line is what is formally recycled. "
         "A widening distance between them means a growing problem. If the rate stays below the "
         "red target line, recycling is not keeping pace with generation.")

# ------------------------------------------------------------------ tab 2
with tab2:
    st.subheader(f"Regional Comparison ({last_year})")
    ry = df[df.year == last_year].groupby("region").agg(
        generated_kt=("generated_kt", "sum"), recycled_kt=("recycled_kt", "sum"),
        pop=("population_bn", "first")).reset_index()
    ry["Generated (Mt)"] = ry.generated_kt / 1000
    ry["Rate (%)"] = ry.recycled_kt / ry.generated_kt * 100
    ry["Per capita (kg)"] = ry.generated_kt / (ry["pop"] * 1000)
    a, b, c3 = st.columns(3)
    f = px.bar(ry.sort_values("Generated (Mt)", ascending=False), x="region", y="Generated (Mt)",
               color="region", color_discrete_map=REGION_COLORS, text_auto=".1f",
               title="E-waste generated (Mt)")
    f.update_layout(showlegend=False, xaxis_title="", **PLOT)
    a.plotly_chart(f, width='stretch')
    f = px.bar(ry, x="region", y="Rate (%)", color="region", color_discrete_map=REGION_COLORS,
               text_auto=".1f", title="Formal recycling rate (%)")
    f.add_hline(y=target, line_dash="dash", line_color=RED)
    f.update_layout(showlegend=False, xaxis_title="", **PLOT)
    b.plotly_chart(f, width='stretch')
    f = px.scatter(ry, x="Per capita (kg)", y="Rate (%)", size="Generated (Mt)", color="region",
                   color_discrete_map=REGION_COLORS, text="region", size_max=55,
                   title="Per-capita e-waste vs recycling rate")
    f.update_traces(textposition="top center")
    f.update_layout(showlegend=False, **PLOT)
    c3.plotly_chart(f, width='stretch')
    note("Taller bars mean larger values. In the bubble chart, further right = more e-waste per "
         "person, higher = better recycling, bigger bubble = more total e-waste. Richer regions "
         "usually create more waste per person but also have better collection systems.")

# ------------------------------------------------------------------ tab 3
with tab3:
    st.subheader(f"Product Categories ({last_year})")
    cy = df[df.year == last_year].groupby("category")[["generated_kt", "recycled_kt",
                                                       "recoverable_value_musd"]].sum().reset_index()
    cy["Rate (%)"] = cy.recycled_kt / cy.generated_kt * 100
    cy["Value (US$ bn)"] = cy.recoverable_value_musd / 1000
    a, b, c3 = st.columns(3)
    f = px.pie(cy, names="category", values="generated_kt", hole=.55, title="Share of e-waste mass")
    f.update_layout(legend=dict(orientation="h", y=-.15), **PLOT)
    a.plotly_chart(f, width='stretch')
    f = px.bar(cy.sort_values("Value (US$ bn)"), x="Value (US$ bn)", y="category", orientation="h",
               text_auto=".1f", title="Unrecovered material value (US$ bn)")
    f.update_traces(marker_color=ORANGE)
    f.update_layout(yaxis_title="", **PLOT)
    b.plotly_chart(f, width='stretch')
    f = px.bar(cy.sort_values("Rate (%)"), x="Rate (%)", y="category", orientation="h",
               text_auto=".1f", title="Recycling rate (%)")
    f.update_traces(marker_color=GREEN)
    f.update_layout(yaxis_title="", **PLOT)
    c3.plotly_chart(f, width='stretch')
    note("The donut shows which products make up the e-waste. The orange bars show the money value "
         "of material that is lost, and the green bars show how well each product group is recycled. "
         "Large lost value with a low recycling rate marks the best opportunity for improvement.")

# ------------------------------------------------------------------ tab 4
with tab4:
    st.subheader("Recovery Gap and 2030 Scenarios")
    a, b = st.columns(2)
    f = go.Figure()
    f.add_scatter(x=yearly.year, y=yearly.rec_mt, stackgroup="one", name="Formally recycled",
                  line=dict(color=GREEN))
    f.add_scatter(x=yearly.year, y=yearly.gap_mt, stackgroup="one", name="Not documented (gap)",
                  line=dict(color=RED))
    f.update_layout(title="Recycled vs not documented (Mt)", yaxis_title="Million tonnes", **PLOT)
    a.plotly_chart(f, width='stretch')

    total30 = last.gen_mt * SCALE_2030
    names = ["Business as usual (20%)", f"Your target ({target}%)", "Strong action (60%)"]
    rates = [20, target, 60]
    rec = [total30 * r / 100 for r in rates]
    gap = [total30 - x for x in rec]
    f = go.Figure()
    f.add_bar(x=names, y=rec, name="Recycled", marker_color=GREEN, text=[f"{x:.1f} Mt" for x in rec])
    f.add_bar(x=names, y=gap, name="Not recycled", marker_color=RED, text=[f"{x:.1f} Mt" for x in gap])
    f.update_layout(barmode="stack", title=f"2030 scenarios for {total30:.1f} Mt of e-waste",
                    yaxis_title="Million tonnes", **PLOT)
    b.plotly_chart(f, width='stretch')
    note("Green is material that returns to the economy and red is material that is lost. The whole "
         "bar is the e-waste expected in 2030; the green part is what each scenario recycles. "
         "Change the target in the sidebar to see how the middle bar moves. The 30% target and 60% "
         "scenario are illustrative.")

# ------------------------------------------------------------------ explorer
st.divider()
st.subheader("📋 Interactive Data Explorer & Export")
st.caption("Inspect, filter and export the e-waste records.")
all_cols = list(data.columns)
default_cols = ["year", "region", "category", "generated_kt", "recycled_kt", "unrecycled_kt",
                "collection_rate_pct", "recoverable_value_musd"]
cc1, cc2 = st.columns([4, 1])
cols = cc1.multiselect("Select columns to display", all_cols, default=default_cols)
limit = cc2.selectbox("Preview rows", [10, 25, 50, 100], index=1)
if not cols:
    st.info("Select at least one column.")
else:
    view = df[cols].sort_values([c for c in ["year", "region", "category"] if c in cols] or cols[:1])
    st.dataframe(view.head(limit), width='stretch', hide_index=True)
    st.download_button(f"⬇ Download Filtered CSV ({len(view):,} Rows)",
                       view.to_csv(index=False).encode("utf-8"),
                       file_name="ewaste_filtered.csv", mime="text/csv", width='stretch')
    st.caption(f"Export will download all {len(view):,} filtered records with the {len(cols)} selected columns.")

st.divider()
st.caption("♻️ Global E-Waste Analytics · Built with Python, Streamlit and Plotly · "
           "Data: modelled dataset calibrated to the Global E-waste Monitor 2024 (ITU/UNITAR).")
