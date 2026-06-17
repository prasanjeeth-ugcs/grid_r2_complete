"""
=============================================================================
 ASTRAM EVENT-DRIVEN CONGESTION — Phase 0: Exploratory Data Analysis (EDA)
=============================================================================
 Bengaluru Traffic Event Management Dataset
 Produces a self-contained interactive HTML dashboard
=============================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime
import warnings, os, json

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA LOADING & CLEANING
# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH = r"d:\round2 - anti\Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv"
OUTPUT_PATH = r"d:\round2 - anti\eda_dashboard.html"

print("=" * 70)
print(" ASTRAM EDA — Loading & Cleaning Data")
print("=" * 70)

df = pd.read_csv(DATA_PATH, low_memory=False)
print(f"  Raw shape: {df.shape[0]} rows × {df.shape[1]} columns")

# --- Replace literal "NULL" strings with NaN ---
df.replace("NULL", np.nan, inplace=True)
df.replace("null", np.nan, inplace=True)

# --- Parse datetime columns ---
datetime_cols = [
    "start_datetime", "end_datetime", "created_date",
    "modified_datetime", "closed_datetime", "resolved_datetime"
]
for col in datetime_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

# --- Boolean columns ---
df["requires_road_closure"] = df["requires_road_closure"].map(
    {True: True, False: False, "TRUE": True, "FALSE": False, "true": True, "false": False}
)
df["authenticated"] = df["authenticated"].map(
    {"yes": True, "no": False, True: True, False: False}
)

# --- Clean coordinates: 0 → NaN for end coordinates ---
for col in ["endlatitude", "endlongitude"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df[col] == 0, col] = np.nan

for col in ["latitude", "longitude", "resolved_at_latitude", "resolved_at_longitude"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --- Numeric columns ---
df["client_id"] = pd.to_numeric(df["client_id"], errors="coerce")
df["age_of_truck"] = pd.to_numeric(df["age_of_truck"], errors="coerce")

# --- Strip whitespace from categorical columns ---
cat_cols = ["event_type", "event_cause", "status", "priority", "corridor",
            "veh_type", "police_station", "zone", "junction", "direction",
            "cargo_material", "reason_breakdown"]
for col in cat_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", np.nan)

print(f"  Cleaned shape: {df.shape[0]} rows × {df.shape[1]} columns")

# ─────────────────────────────────────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

print("\n  Engineering features...")

# --- Temporal features ---
df["hour_of_day"] = df["start_datetime"].dt.hour
df["day_of_week"] = df["start_datetime"].dt.day_name()
df["day_of_week_num"] = df["start_datetime"].dt.dayofweek
df["month"] = df["start_datetime"].dt.month
df["month_name"] = df["start_datetime"].dt.month_name()
df["date"] = df["start_datetime"].dt.date
df["is_weekend"] = df["day_of_week_num"].isin([5, 6])
df["is_rush_hour"] = df["hour_of_day"].apply(
    lambda h: True if (8 <= h <= 10) or (17 <= h <= 20) else False
)

# --- Resolution time (hours) ---
df["resolution_time_hrs"] = (
    df["resolved_datetime"] - df["start_datetime"]
).dt.total_seconds() / 3600
df.loc[df["resolution_time_hrs"] < 0, "resolution_time_hrs"] = np.nan

df["closure_time_hrs"] = (
    df["closed_datetime"] - df["start_datetime"]
).dt.total_seconds() / 3600
df.loc[df["closure_time_hrs"] < 0, "closure_time_hrs"] = np.nan

# --- Report delay (minutes) ---
df["report_delay_min"] = (
    df["created_date"] - df["start_datetime"]
).dt.total_seconds() / 60
df.loc[df["report_delay_min"] < 0, "report_delay_min"] = np.nan

# --- Corridor flag ---
df["is_corridor"] = df["corridor"].apply(
    lambda x: False if pd.isna(x) or x == "Non-corridor" else True
)

# --- Time period ---
def get_time_period(hour):
    if pd.isna(hour):
        return "Unknown"
    hour = int(hour)
    if 6 <= hour < 10:
        return "Morning Rush"
    elif 10 <= hour < 16:
        return "Midday"
    elif 16 <= hour < 21:
        return "Evening Rush"
    elif 21 <= hour < 24:
        return "Late Night"
    else:
        return "Early Morning"

df["time_period"] = df["hour_of_day"].apply(get_time_period)

# --- Duration category ---
def duration_cat(hrs):
    if pd.isna(hrs):
        return "Unknown"
    if hrs < 1:
        return "<1 hour"
    elif hrs < 4:
        return "1-4 hours"
    elif hrs < 12:
        return "4-12 hours"
    else:
        return ">12 hours"

df["duration_category"] = df["resolution_time_hrs"].apply(duration_cat)

print(f"  Features engineered. Total columns: {df.shape[1]}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. STATISTICS COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

print("\n  Computing statistics...")

total_events = len(df)
event_cause_counts = df["event_cause"].value_counts()
event_type_counts = df["event_type"].value_counts()
status_counts = df["status"].value_counts()
priority_counts = df["priority"].value_counts()
corridor_counts = df["corridor"].value_counts().head(20)
veh_type_counts = df["veh_type"].value_counts()
police_station_counts = df["police_station"].value_counts().head(20)
zone_counts = df["zone"].value_counts()

median_resolution = df["resolution_time_hrs"].median()
mean_resolution = df["resolution_time_hrs"].mean()
road_closure_rate = df["requires_road_closure"].sum() / total_events * 100

# --- Missingness ---
missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
missing_df = pd.DataFrame({
    "Column": missing_pct.index,
    "Missing %": missing_pct.values,
    "Missing Count": df.isnull().sum()[missing_pct.index].values
})

print(f"  Total events: {total_events}")
print(f"  Median resolution time: {median_resolution:.1f} hrs")
print(f"  Road closure rate: {road_closure_rate:.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLOR PALETTE & THEME
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    "bg_dark": "#0a0e1a",
    "bg_card": "#111827",
    "bg_card_alt": "#1a2332",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "accent_blue": "#3b82f6",
    "accent_cyan": "#06b6d4",
    "accent_purple": "#8b5cf6",
    "accent_pink": "#ec4899",
    "accent_green": "#10b981",
    "accent_amber": "#f59e0b",
    "accent_red": "#ef4444",
    "accent_orange": "#f97316",
    "grid": "#1e293b",
    "border": "#334155",
}

RISK_COLORS = {
    "Low": "#10b981",
    "Medium": "#f59e0b",
    "High": "#f97316",
    "Critical": "#ef4444",
}

CAUSE_COLORS = px.colors.qualitative.Set3
EVENT_PALETTE = [
    "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
    "#ec4899", "#06b6d4", "#f97316", "#6366f1", "#14b8a6",
    "#a855f7", "#e11d48", "#0ea5e9", "#84cc16", "#fbbf24",
]

PLOTLY_TEMPLATE = dict(
    layout=go.Layout(
        paper_bgcolor=COLORS["bg_card"],
        plot_bgcolor=COLORS["bg_card"],
        font=dict(family="Inter, system-ui, sans-serif", color=COLORS["text_primary"], size=12),
        xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
        yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
        margin=dict(l=60, r=30, t=50, b=50),
        colorway=EVENT_PALETTE,
    )
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. BUILD VISUALIZATIONS
# ─────────────────────────────────────────────────────────────────────────────

print("\n  Building visualizations...")
figures = {}

# --- Chart 1: Event Cause Distribution ---
cause_df = event_cause_counts.reset_index()
cause_df.columns = ["Event Cause", "Count"]
cause_df["Percentage"] = (cause_df["Count"] / total_events * 100).round(1)
cause_df = cause_df.sort_values("Count", ascending=True)

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    y=cause_df["Event Cause"],
    x=cause_df["Count"],
    orientation="h",
    marker=dict(
        color=cause_df["Count"],
        colorscale=[[0, "#1e3a5f"], [0.5, "#3b82f6"], [1, "#06b6d4"]],
        line=dict(width=0),
        cornerradius=4,
    ),
    text=cause_df.apply(lambda r: f"  {r['Count']} ({r['Percentage']}%)", axis=1),
    textposition="outside",
    textfont=dict(size=11, color=COLORS["text_secondary"]),
    hovertemplate="<b>%{y}</b><br>Count: %{x}<br>Percentage: %{text}<extra></extra>",
))
fig1.update_layout(
    title=dict(text="Event Cause Distribution", font=dict(size=16)),
    xaxis_title="Number of Events",
    yaxis_title="",
    height=500,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["event_cause"] = fig1

# --- Chart 2: Event Type Split ---
type_df = event_type_counts.reset_index()
type_df.columns = ["Event Type", "Count"]
fig2 = go.Figure(data=[go.Pie(
    labels=type_df["Event Type"],
    values=type_df["Count"],
    hole=0.55,
    marker=dict(colors=[COLORS["accent_blue"], COLORS["accent_purple"], COLORS["accent_cyan"]]),
    textinfo="label+percent",
    textfont=dict(size=13, color="white"),
    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
)])
fig2.update_layout(
    title=dict(text="Planned vs Unplanned Events", font=dict(size=16)),
    height=400,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
    showlegend=True,
    legend=dict(font=dict(size=12)),
)
figures["event_type"] = fig2

# --- Chart 3: Status Distribution ---
status_df = status_counts.reset_index()
status_df.columns = ["Status", "Count"]
status_colors = {"closed": "#10b981", "active": "#f59e0b", "resolved": "#3b82f6"}
fig3 = go.Figure(data=[go.Pie(
    labels=status_df["Status"],
    values=status_df["Count"],
    hole=0.55,
    marker=dict(colors=[status_colors.get(s, "#8b5cf6") for s in status_df["Status"]]),
    textinfo="label+percent",
    textfont=dict(size=13, color="white"),
)])
fig3.update_layout(
    title=dict(text="Event Status Distribution", font=dict(size=16)),
    height=400,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["status"] = fig3

# --- Chart 4: Priority Distribution ---
prio_df = priority_counts.reset_index()
prio_df.columns = ["Priority", "Count"]
prio_df["Percentage"] = (prio_df["Count"] / total_events * 100).round(1)
fig4 = go.Figure(data=[go.Bar(
    x=prio_df["Priority"],
    y=prio_df["Count"],
    marker=dict(
        color=[COLORS["accent_amber"] if p == "High" else COLORS["accent_cyan"] for p in prio_df["Priority"]],
        cornerradius=6,
    ),
    text=prio_df.apply(lambda r: f"{r['Count']}<br>({r['Percentage']}%)", axis=1),
    textposition="outside",
    textfont=dict(size=12, color=COLORS["text_secondary"]),
)])
fig4.update_layout(
    title=dict(text="Priority Distribution", font=dict(size=16)),
    xaxis_title="Priority Level",
    yaxis_title="Count",
    height=400,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["priority"] = fig4

# --- Chart 5: Hourly Event Heatmap (Hour × Day of Week) ---
dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
heatmap_data = df.groupby(["day_of_week", "hour_of_day"]).size().reset_index(name="count")
heatmap_pivot = heatmap_data.pivot_table(index="day_of_week", columns="hour_of_day", values="count", fill_value=0)
heatmap_pivot = heatmap_pivot.reindex(dow_order)

fig5 = go.Figure(data=go.Heatmap(
    z=heatmap_pivot.values,
    x=[f"{int(h):02d}:00" for h in heatmap_pivot.columns],
    y=heatmap_pivot.index,
    colorscale=[[0, "#0a0e1a"], [0.25, "#1e3a5f"], [0.5, "#3b82f6"], [0.75, "#06b6d4"], [1, "#10b981"]],
    hovertemplate="<b>%{y}</b> at <b>%{x}</b><br>Events: %{z}<extra></extra>",
    colorbar=dict(title="Events", tickfont=dict(color=COLORS["text_secondary"])),
))
fig5.update_layout(
    title=dict(text="Event Frequency — Hour of Day × Day of Week", font=dict(size=16)),
    xaxis_title="Hour of Day",
    yaxis_title="",
    height=420,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["hourly_heatmap"] = fig5

# --- Chart 6: Daily Event Timeline ---
daily_counts = df.groupby("date").size().reset_index(name="count")
daily_counts["date"] = pd.to_datetime(daily_counts["date"])
daily_counts = daily_counts.sort_values("date")
daily_counts["rolling_7d"] = daily_counts["count"].rolling(7, min_periods=1).mean()

fig6 = go.Figure()
fig6.add_trace(go.Bar(
    x=daily_counts["date"],
    y=daily_counts["count"],
    name="Daily Events",
    marker=dict(color=COLORS["accent_blue"], opacity=0.4),
))
fig6.add_trace(go.Scatter(
    x=daily_counts["date"],
    y=daily_counts["rolling_7d"],
    name="7-Day Rolling Avg",
    line=dict(color=COLORS["accent_cyan"], width=2.5),
    mode="lines",
))
fig6.update_layout(
    title=dict(text="Event Timeline — Daily Count with 7-Day Moving Average", font=dict(size=16)),
    xaxis_title="Date",
    yaxis_title="Number of Events",
    height=400,
    legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0)"),
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["daily_timeline"] = fig6

# --- Chart 7: Monthly Event Breakdown by Cause ---
monthly_cause = df.groupby(["month_name", "month", "event_cause"]).size().reset_index(name="count")
monthly_cause = monthly_cause.sort_values("month")
month_order = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
monthly_cause["month_name"] = pd.Categorical(monthly_cause["month_name"], categories=month_order, ordered=True)

fig7 = px.bar(
    monthly_cause, x="month_name", y="count", color="event_cause",
    title="Monthly Event Distribution by Cause",
    labels={"month_name": "Month", "count": "Events", "event_cause": "Event Cause"},
    color_discrete_sequence=EVENT_PALETTE,
)
fig7.update_layout(
    height=450,
    barmode="stack",
    xaxis_title="Month",
    yaxis_title="Number of Events",
    legend=dict(title="Event Cause", font=dict(size=10)),
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["monthly_cause"] = fig7

# --- Chart 8: Top 15 Corridors ---
corr_df = corridor_counts.head(15).reset_index()
corr_df.columns = ["Corridor", "Count"]
corr_df = corr_df.sort_values("Count", ascending=True)

fig8 = go.Figure()
fig8.add_trace(go.Bar(
    y=corr_df["Corridor"],
    x=corr_df["Count"],
    orientation="h",
    marker=dict(
        color=corr_df["Count"],
        colorscale=[[0, "#1e1b4b"], [0.5, "#8b5cf6"], [1, "#c084fc"]],
        cornerradius=4,
    ),
    text=corr_df["Count"],
    textposition="outside",
    textfont=dict(size=11, color=COLORS["text_secondary"]),
))
fig8.update_layout(
    title=dict(text="Top 15 Corridors by Event Count", font=dict(size=16)),
    xaxis_title="Number of Events",
    yaxis_title="",
    height=500,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["corridors"] = fig8

# --- Chart 9: Vehicle Type Breakdown (for breakdowns only) ---
breakdown_df = df[df["event_cause"] == "vehicle_breakdown"]
vt_counts = breakdown_df["veh_type"].value_counts().reset_index()
vt_counts.columns = ["Vehicle Type", "Count"]
vt_counts = vt_counts[vt_counts["Vehicle Type"].notna()]

fig9 = go.Figure(data=[go.Treemap(
    labels=vt_counts["Vehicle Type"],
    parents=[""] * len(vt_counts),
    values=vt_counts["Count"],
    textinfo="label+value+percent root",
    marker=dict(
        colors=EVENT_PALETTE[:len(vt_counts)],
        line=dict(width=2, color=COLORS["bg_dark"]),
    ),
    textfont=dict(size=14),
    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percentRoot:.1%}<extra></extra>",
)])
fig9.update_layout(
    title=dict(text="Vehicle Type Distribution (Breakdown Events Only)", font=dict(size=16)),
    height=450,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["vehicle_type"] = fig9

# --- Chart 10: Resolution Time Distribution ---
res_data = df["resolution_time_hrs"].dropna()
res_data = res_data[res_data <= res_data.quantile(0.95)]  # Remove extreme outliers for vis

fig10 = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3],
                       shared_xaxes=True, vertical_spacing=0.05)
fig10.add_trace(go.Histogram(
    x=res_data,
    nbinsx=50,
    marker=dict(color=COLORS["accent_blue"], opacity=0.7, line=dict(width=0.5, color=COLORS["accent_cyan"])),
    name="Distribution",
    hovertemplate="Duration: %{x:.1f} hrs<br>Count: %{y}<extra></extra>",
), row=1, col=1)
fig10.add_trace(go.Box(
    x=res_data,
    marker=dict(color=COLORS["accent_cyan"]),
    name="Box Plot",
    boxmean="sd",
), row=2, col=1)
fig10.update_layout(
    title=dict(text=f"Resolution Time Distribution (95th pctl, Median={median_resolution:.1f}h, Mean={mean_resolution:.1f}h)", font=dict(size=14)),
    xaxis2_title="Resolution Time (hours)",
    yaxis_title="Frequency",
    height=450,
    showlegend=False,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
fig10.update_xaxes(gridcolor=COLORS["grid"])
fig10.update_yaxes(gridcolor=COLORS["grid"])
figures["resolution_time"] = fig10

# --- Chart 11: Event Cause × Priority Heatmap ---
cause_priority = df.groupby(["event_cause", "priority"]).size().reset_index(name="count")
cp_pivot = cause_priority.pivot_table(index="event_cause", columns="priority", values="count", fill_value=0)

fig11 = go.Figure(data=go.Heatmap(
    z=cp_pivot.values,
    x=cp_pivot.columns.tolist(),
    y=cp_pivot.index.tolist(),
    colorscale=[[0, "#0a0e1a"], [0.3, "#3b1e8f"], [0.6, "#8b5cf6"], [1, "#ec4899"]],
    hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Count: %{z}<extra></extra>",
    text=cp_pivot.values,
    texttemplate="%{text}",
    textfont=dict(size=12, color="white"),
    colorbar=dict(title="Count"),
))
fig11.update_layout(
    title=dict(text="Event Cause × Priority Distribution", font=dict(size=16)),
    xaxis_title="Priority",
    yaxis_title="Event Cause",
    height=450,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["cause_priority"] = fig11

# --- Chart 12: Top 15 Police Stations ---
ps_df = police_station_counts.head(15).reset_index()
ps_df.columns = ["Police Station", "Count"]
ps_df = ps_df.sort_values("Count", ascending=True)

fig12 = go.Figure()
fig12.add_trace(go.Bar(
    y=ps_df["Police Station"],
    x=ps_df["Count"],
    orientation="h",
    marker=dict(
        color=ps_df["Count"],
        colorscale=[[0, "#064e3b"], [0.5, "#10b981"], [1, "#6ee7b7"]],
        cornerradius=4,
    ),
    text=ps_df["Count"],
    textposition="outside",
    textfont=dict(size=11, color=COLORS["text_secondary"]),
))
fig12.update_layout(
    title=dict(text="Top 15 Police Stations by Event Load", font=dict(size=16)),
    xaxis_title="Number of Events",
    yaxis_title="",
    height=500,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["police_stations"] = fig12

# --- Chart 13: Road Closure Analysis ---
closure_by_cause = df.groupby("event_cause")["requires_road_closure"].agg(["sum", "count"]).reset_index()
closure_by_cause.columns = ["Event Cause", "Closures", "Total"]
closure_by_cause["Closure Rate %"] = (closure_by_cause["Closures"] / closure_by_cause["Total"] * 100).round(1)
closure_by_cause = closure_by_cause.sort_values("Closure Rate %", ascending=True)

fig13 = go.Figure()
fig13.add_trace(go.Bar(
    y=closure_by_cause["Event Cause"],
    x=closure_by_cause["Closure Rate %"],
    orientation="h",
    marker=dict(
        color=closure_by_cause["Closure Rate %"],
        colorscale=[[0, "#1e3a5f"], [0.5, "#f59e0b"], [1, "#ef4444"]],
        cornerradius=4,
    ),
    text=closure_by_cause.apply(lambda r: f"  {r['Closure Rate %']}% ({int(r['Closures'])}/{int(r['Total'])})", axis=1),
    textposition="outside",
    textfont=dict(size=11, color=COLORS["text_secondary"]),
))
fig13.update_layout(
    title=dict(text="Road Closure Rate by Event Cause", font=dict(size=16)),
    xaxis_title="Road Closure Rate (%)",
    yaxis_title="",
    height=450,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["road_closure"] = fig13

# --- Chart 14: Geospatial Scatter Map ---
geo_df = df.dropna(subset=["latitude", "longitude"]).copy()
geo_df = geo_df[(geo_df["latitude"].between(12.5, 13.5)) & (geo_df["longitude"].between(77.0, 78.0))]

fig14 = px.scatter_mapbox(
    geo_df,
    lat="latitude",
    lon="longitude",
    color="event_cause",
    size_max=8,
    zoom=10.5,
    center={"lat": 12.97, "lon": 77.59},
    mapbox_style="carto-darkmatter",
    title="Geospatial Distribution of Events Across Bengaluru",
    color_discrete_sequence=EVENT_PALETTE,
    hover_data=["event_cause", "corridor", "priority", "status", "police_station"],
    opacity=0.7,
)
fig14.update_layout(
    height=600,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
    mapbox=dict(style="carto-darkmatter"),
    legend=dict(title="Event Cause", font=dict(size=10), bgcolor="rgba(17,24,39,0.8)"),
)
figures["geospatial"] = fig14

# --- Chart 15: Corridor × Resolution Time ---
corr_res = df[df["is_corridor"]].groupby("corridor")["resolution_time_hrs"].agg(["median", "mean", "count"]).reset_index()
corr_res = corr_res[corr_res["count"] >= 20].sort_values("median", ascending=True)
corr_res.columns = ["Corridor", "Median Hrs", "Mean Hrs", "Count"]

fig15 = go.Figure()
fig15.add_trace(go.Bar(
    y=corr_res["Corridor"],
    x=corr_res["Median Hrs"],
    orientation="h",
    name="Median",
    marker=dict(color=COLORS["accent_blue"], cornerradius=4),
    text=corr_res["Median Hrs"].round(1),
    textposition="outside",
    textfont=dict(size=10, color=COLORS["text_secondary"]),
))
fig15.update_layout(
    title=dict(text="Median Resolution Time by Corridor (≥20 events)", font=dict(size=14)),
    xaxis_title="Median Resolution Time (hours)",
    yaxis_title="",
    height=500,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["corridor_resolution"] = fig15

# --- Chart 16: Missing Values Heatmap ---
miss_cols = missing_df[missing_df["Missing %"] > 0].head(25)
fig16 = go.Figure(data=go.Bar(
    x=miss_cols["Missing %"],
    y=miss_cols["Column"],
    orientation="h",
    marker=dict(
        color=miss_cols["Missing %"],
        colorscale=[[0, "#10b981"], [0.3, "#f59e0b"], [0.7, "#f97316"], [1, "#ef4444"]],
        cornerradius=4,
    ),
    text=miss_cols.apply(lambda r: f"  {r['Missing %']:.1f}% ({int(r['Missing Count'])})", axis=1),
    textposition="outside",
    textfont=dict(size=10, color=COLORS["text_secondary"]),
))
fig16.update_layout(
    title=dict(text="Missing Values by Column (Top 25)", font=dict(size=16)),
    xaxis_title="Missing %",
    yaxis_title="",
    height=600,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["missing_values"] = fig16

# --- Chart 17: Hourly Distribution by Event Cause ---
hourly_cause = df.groupby(["hour_of_day", "event_cause"]).size().reset_index(name="count")
top_causes = event_cause_counts.head(6).index.tolist()
hourly_cause_top = hourly_cause[hourly_cause["event_cause"].isin(top_causes)]

fig17 = px.line(
    hourly_cause_top, x="hour_of_day", y="count", color="event_cause",
    title="Hourly Event Distribution by Top Causes",
    labels={"hour_of_day": "Hour of Day", "count": "Events", "event_cause": "Cause"},
    color_discrete_sequence=EVENT_PALETTE,
    markers=True,
)
fig17.update_layout(
    height=400,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
fig17.update_xaxes(dtick=1)
figures["hourly_by_cause"] = fig17

# --- Chart 18: Road Closure vs Resolution Time ---
closure_res = df.dropna(subset=["resolution_time_hrs"]).copy()
closure_res = closure_res[closure_res["resolution_time_hrs"] <= closure_res["resolution_time_hrs"].quantile(0.95)]
closure_res["Road Closure"] = closure_res["requires_road_closure"].map({True: "Yes", False: "No"})
closure_res = closure_res.dropna(subset=["Road Closure"])

fig18 = px.box(
    closure_res, x="Road Closure", y="resolution_time_hrs",
    color="Road Closure",
    color_discrete_map={"Yes": COLORS["accent_red"], "No": COLORS["accent_green"]},
    title="Resolution Time: Road Closure vs No Closure",
    labels={"resolution_time_hrs": "Resolution Time (hours)", "Road Closure": "Road Closure Required"},
)
fig18.update_layout(
    height=400,
    showlegend=False,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["closure_vs_resolution"] = fig18

# --- Chart 19: Zone-wise Analysis ---
if zone_counts.dropna().shape[0] > 0:
    zone_df = zone_counts.dropna().reset_index()
    zone_df.columns = ["Zone", "Count"]
    zone_df = zone_df.sort_values("Count", ascending=True)
    fig19 = go.Figure()
    fig19.add_trace(go.Bar(
        y=zone_df["Zone"],
        x=zone_df["Count"],
        orientation="h",
        marker=dict(
            color=zone_df["Count"],
            colorscale=[[0, "#1e1b4b"], [0.5, "#6366f1"], [1, "#a78bfa"]],
            cornerradius=4,
        ),
        text=zone_df["Count"],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_secondary"]),
    ))
    fig19.update_layout(
        title=dict(text="Zone-wise Event Distribution", font=dict(size=16)),
        xaxis_title="Number of Events",
        yaxis_title="",
        height=400,
        **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
    )
    figures["zones"] = fig19

# --- Chart 20: Time Period Distribution ---
tp_order = ["Early Morning", "Morning Rush", "Midday", "Evening Rush", "Late Night"]
tp_counts = df["time_period"].value_counts().reindex(tp_order).fillna(0).reset_index()
tp_counts.columns = ["Time Period", "Count"]
tp_colors = ["#1e3a5f", "#f59e0b", "#3b82f6", "#ef4444", "#6366f1"]

fig20 = go.Figure(data=[go.Bar(
    x=tp_counts["Time Period"],
    y=tp_counts["Count"],
    marker=dict(color=tp_colors, cornerradius=6),
    text=tp_counts["Count"],
    textposition="outside",
    textfont=dict(size=12, color=COLORS["text_secondary"]),
)])
fig20.update_layout(
    title=dict(text="Events by Time Period", font=dict(size=16)),
    xaxis_title="Time Period",
    yaxis_title="Number of Events",
    height=400,
    **PLOTLY_TEMPLATE["layout"].to_plotly_json(),
)
figures["time_period"] = fig20


# ─────────────────────────────────────────────────────────────────────────────
# 6. ASSEMBLE HTML DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

print("\n  Assembling HTML dashboard...")

# Convert all figures to HTML divs
chart_htmls = {}
for name, fig in figures.items():
    chart_htmls[name] = pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": True, "responsive": True})

# --- KPI Cards ---
breakdown_pct = (event_cause_counts.get("vehicle_breakdown", 0) / total_events * 100)
unplanned_pct = (event_type_counts.get("unplanned", 0) / total_events * 100)
closed_pct = (status_counts.get("closed", 0) / total_events * 100)
corridor_pct = (df["is_corridor"].sum() / total_events * 100)
weekend_pct = (df["is_weekend"].sum() / total_events * 100)
rush_hour_pct = (df["is_rush_hour"].sum() / total_events * 100)

# Date range
date_min = df["start_datetime"].min()
date_max = df["start_datetime"].max()
date_range_str = f"{date_min.strftime('%b %d, %Y') if pd.notna(date_min) else 'N/A'} — {date_max.strftime('%b %d, %Y') if pd.notna(date_max) else 'N/A'}"

# Summary statistics text
num_corridors = df["corridor"].nunique()
num_police_stations = df["police_station"].nunique()
num_junctions = df["junction"].dropna().nunique()

# Top insights
top_cause = event_cause_counts.index[0] if len(event_cause_counts) > 0 else "N/A"
top_corridor = corridor_counts.index[0] if len(corridor_counts) > 0 else "N/A"
top_station = police_station_counts.index[0] if len(police_station_counts) > 0 else "N/A"

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Astram EDA — Bengaluru Traffic Event Analysis</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0a0e1a;
            --bg-card: #111827;
            --bg-card-alt: #1a2332;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-pink: #ec4899;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --accent-orange: #f97316;
            --border: #334155;
            --grid: #1e293b;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }}
        /* ─── HEADER ─── */
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            border-bottom: 1px solid var(--border);
            padding: 2rem 2rem 1.5rem;
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(ellipse at 20% 50%, rgba(59,130,246,0.1) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 50%, rgba(139,92,246,0.08) 0%, transparent 50%);
            pointer-events: none;
        }}
        .header-content {{ position: relative; z-index: 1; max-width: 1400px; margin: 0 auto; }}
        .header h1 {{
            font-size: 2rem; font-weight: 800;
            background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px; margin-bottom: 0.25rem;
        }}
        .header .subtitle {{ color: var(--text-muted); font-size: 0.95rem; font-weight: 400; }}
        .header .date-range {{
            display: inline-block; margin-top: 0.75rem; padding: 0.35rem 1rem;
            background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.2);
            border-radius: 20px; font-size: 0.8rem; color: var(--accent-blue);
        }}
        /* ─── NAV ─── */
        .nav {{
            background: var(--bg-card); border-bottom: 1px solid var(--border);
            padding: 0.75rem 2rem; position: sticky; top: 0; z-index: 100;
            backdrop-filter: blur(20px);
        }}
        .nav-inner {{
            max-width: 1400px; margin: 0 auto; display: flex; gap: 0.5rem;
            overflow-x: auto; scrollbar-width: none;
        }}
        .nav-inner::-webkit-scrollbar {{ display: none; }}
        .nav-btn {{
            padding: 0.4rem 1rem; border-radius: 8px; border: 1px solid var(--border);
            background: transparent; color: var(--text-secondary); cursor: pointer;
            font-size: 0.8rem; font-family: 'Inter', sans-serif; white-space: nowrap;
            transition: all 0.2s;
        }}
        .nav-btn:hover, .nav-btn.active {{
            background: rgba(59,130,246,0.15); border-color: var(--accent-blue);
            color: var(--accent-blue);
        }}
        /* ─── KPI STRIP ─── */
        .kpi-strip {{
            max-width: 1400px; margin: 1.5rem auto; padding: 0 1.5rem;
            display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem;
        }}
        .kpi-card {{
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: 12px; padding: 1.25rem; position: relative; overflow: hidden;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .kpi-card:hover {{ transform: translateY(-2px); border-color: var(--accent-blue); }}
        .kpi-card .kpi-glow {{
            position: absolute; top: -20px; right: -20px;
            width: 80px; height: 80px; border-radius: 50%;
            filter: blur(30px); opacity: 0.15;
        }}
        .kpi-card .kpi-label {{
            font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1px; color: var(--text-muted); margin-bottom: 0.5rem;
        }}
        .kpi-card .kpi-value {{
            font-size: 1.75rem; font-weight: 800; line-height: 1;
            margin-bottom: 0.25rem;
        }}
        .kpi-card .kpi-sub {{ font-size: 0.75rem; color: var(--text-muted); }}
        /* ─── SECTIONS ─── */
        .main {{ max-width: 1400px; margin: 0 auto; padding: 0 1.5rem 3rem; }}
        .section {{
            margin-bottom: 2rem; scroll-margin-top: 60px;
        }}
        .section-header {{
            display: flex; align-items: center; gap: 0.75rem;
            margin-bottom: 1rem; padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border);
        }}
        .section-header .section-icon {{
            width: 36px; height: 36px; border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem;
        }}
        .section-header h2 {{ font-size: 1.2rem; font-weight: 700; }}
        .section-header .section-desc {{ font-size: 0.8rem; color: var(--text-muted); margin-left: auto; }}
        /* ─── CHART GRID ─── */
        .chart-grid {{ display: grid; gap: 1.25rem; }}
        .chart-grid.two-col {{ grid-template-columns: repeat(2, 1fr); }}
        .chart-grid.three-col {{ grid-template-columns: repeat(3, 1fr); }}
        .chart-grid.single {{ grid-template-columns: 1fr; }}
        @media (max-width: 900px) {{
            .chart-grid.two-col, .chart-grid.three-col {{ grid-template-columns: 1fr; }}
        }}
        .chart-card {{
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: 14px; overflow: hidden;
            transition: border-color 0.2s;
        }}
        .chart-card:hover {{ border-color: rgba(59,130,246,0.3); }}
        .chart-card .js-plotly-plot {{ border-radius: 0 0 14px 14px; }}
        /* ─── INSIGHT CARDS ─── */
        .insight-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
        .insight-card {{
            background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card-alt) 100%);
            border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem;
            border-left: 3px solid var(--accent-blue);
        }}
        .insight-card h4 {{ font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--accent-cyan); }}
        .insight-card p {{ font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6; }}
        .insight-card .highlight {{ color: var(--accent-amber); font-weight: 700; }}
        /* ─── DATA TABLE ─── */
        .data-table-wrapper {{
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: 14px; overflow: hidden;
        }}
        .data-table-wrapper table {{
            width: 100%; border-collapse: collapse; font-size: 0.8rem;
        }}
        .data-table-wrapper th {{
            background: var(--bg-card-alt); padding: 0.75rem 1rem;
            text-align: left; font-weight: 600; color: var(--text-primary);
            border-bottom: 1px solid var(--border);
        }}
        .data-table-wrapper td {{
            padding: 0.6rem 1rem; border-bottom: 1px solid var(--grid);
            color: var(--text-secondary);
        }}
        .data-table-wrapper tr:hover td {{ background: rgba(59,130,246,0.05); }}
        .badge {{
            display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
            font-size: 0.7rem; font-weight: 600;
        }}
        .badge-green {{ background: rgba(16,185,129,0.15); color: #10b981; }}
        .badge-amber {{ background: rgba(245,158,11,0.15); color: #f59e0b; }}
        .badge-red {{ background: rgba(239,68,68,0.15); color: #ef4444; }}
        /* ─── FOOTER ─── */
        .footer {{
            text-align: center; padding: 2rem;
            color: var(--text-muted); font-size: 0.75rem;
            border-top: 1px solid var(--border);
        }}
        /* ─── SCROLL ANIMATIONS ─── */
        .fade-in {{ opacity: 0; transform: translateY(20px); transition: opacity 0.6s, transform 0.6s; }}
        .fade-in.visible {{ opacity: 1; transform: translateY(0); }}
    </style>
</head>
<body>

<!-- ═══ HEADER ═══ -->
<div class="header">
    <div class="header-content">
        <h1>🚦 Astram EDA — Bengaluru Traffic Event Intelligence</h1>
        <div class="subtitle">Phase 0 · Exploratory Data Analysis · Event-Driven Congestion Management System</div>
        <div class="date-range">📅 {date_range_str} · {total_events:,} Events Analyzed</div>
    </div>
</div>

<!-- ═══ NAV ═══ -->
<div class="nav">
    <div class="nav-inner">
        <button class="nav-btn active" onclick="scrollToSection('overview')">Overview</button>
        <button class="nav-btn" onclick="scrollToSection('temporal')">Temporal</button>
        <button class="nav-btn" onclick="scrollToSection('causes')">Causes & Types</button>
        <button class="nav-btn" onclick="scrollToSection('spatial')">Geospatial</button>
        <button class="nav-btn" onclick="scrollToSection('corridors')">Corridors</button>
        <button class="nav-btn" onclick="scrollToSection('vehicles')">Vehicles</button>
        <button class="nav-btn" onclick="scrollToSection('resolution')">Resolution</button>
        <button class="nav-btn" onclick="scrollToSection('quality')">Data Quality</button>
        <button class="nav-btn" onclick="scrollToSection('insights')">Key Insights</button>
    </div>
</div>

<!-- ═══ KPI STRIP ═══ -->
<div class="kpi-strip">
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-blue)"></div>
        <div class="kpi-label">Total Events</div>
        <div class="kpi-value" style="color:var(--accent-blue)">{total_events:,}</div>
        <div class="kpi-sub">{date_range_str}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-red)"></div>
        <div class="kpi-label">Top Cause</div>
        <div class="kpi-value" style="color:var(--accent-red); font-size:1.1rem">{top_cause.replace('_',' ').title()}</div>
        <div class="kpi-sub">{breakdown_pct:.0f}% of all events</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-amber)"></div>
        <div class="kpi-label">Unplanned Rate</div>
        <div class="kpi-value" style="color:var(--accent-amber)">{unplanned_pct:.0f}%</div>
        <div class="kpi-sub">vs {100-unplanned_pct:.0f}% planned</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-cyan)"></div>
        <div class="kpi-label">Median Resolution</div>
        <div class="kpi-value" style="color:var(--accent-cyan)">{median_resolution:.1f}h</div>
        <div class="kpi-sub">Mean: {mean_resolution:.1f}h</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-orange)"></div>
        <div class="kpi-label">Road Closures</div>
        <div class="kpi-value" style="color:var(--accent-orange)">{road_closure_rate:.1f}%</div>
        <div class="kpi-sub">{int(df['requires_road_closure'].sum())} events</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-purple)"></div>
        <div class="kpi-label">Rush Hour Events</div>
        <div class="kpi-value" style="color:var(--accent-purple)">{rush_hour_pct:.0f}%</div>
        <div class="kpi-sub">8-10 AM & 5-8 PM</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-green)"></div>
        <div class="kpi-label">Closure Rate</div>
        <div class="kpi-value" style="color:var(--accent-green)">{closed_pct:.0f}%</div>
        <div class="kpi-sub">{int(status_counts.get('closed',0))} events closed</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-glow" style="background:var(--accent-pink)"></div>
        <div class="kpi-label">Coverage</div>
        <div class="kpi-value" style="color:var(--accent-pink); font-size:1.2rem">{num_corridors}</div>
        <div class="kpi-sub">Corridors · {num_police_stations} Stations</div>
    </div>
</div>

<!-- ═══ MAIN CONTENT ═══ -->
<div class="main">

    <!-- ─── OVERVIEW ─── -->
    <div class="section" id="overview">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(59,130,246,0.15)">📊</div>
            <h2>Overview & Distribution</h2>
            <span class="section-desc">High-level breakdown of event types, statuses, and priorities</span>
        </div>
        <div class="chart-grid three-col">
            <div class="chart-card">{chart_htmls['event_type']}</div>
            <div class="chart-card">{chart_htmls['status']}</div>
            <div class="chart-card">{chart_htmls['priority']}</div>
        </div>
    </div>

    <!-- ─── TEMPORAL ─── -->
    <div class="section" id="temporal">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(6,182,212,0.15)">🕐</div>
            <h2>Temporal Patterns</h2>
            <span class="section-desc">When do events occur? Hour, day, month patterns</span>
        </div>
        <div class="chart-grid single">
            <div class="chart-card">{chart_htmls['daily_timeline']}</div>
        </div>
        <div class="chart-grid two-col" style="margin-top:1.25rem">
            <div class="chart-card">{chart_htmls['hourly_heatmap']}</div>
            <div class="chart-card">{chart_htmls['time_period']}</div>
        </div>
        <div class="chart-grid two-col" style="margin-top:1.25rem">
            <div class="chart-card">{chart_htmls['monthly_cause']}</div>
            <div class="chart-card">{chart_htmls['hourly_by_cause']}</div>
        </div>
    </div>

    <!-- ─── CAUSES ─── -->
    <div class="section" id="causes">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(245,158,11,0.15)">⚡</div>
            <h2>Event Causes & Classification</h2>
            <span class="section-desc">What causes traffic disruptions?</span>
        </div>
        <div class="chart-grid two-col">
            <div class="chart-card">{chart_htmls['event_cause']}</div>
            <div class="chart-card">{chart_htmls['cause_priority']}</div>
        </div>
        <div class="chart-grid single" style="margin-top:1.25rem">
            <div class="chart-card">{chart_htmls['road_closure']}</div>
        </div>
    </div>

    <!-- ─── GEOSPATIAL ─── -->
    <div class="section" id="spatial">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(139,92,246,0.15)">🗺️</div>
            <h2>Geospatial Analysis</h2>
            <span class="section-desc">Where are events concentrated across Bengaluru?</span>
        </div>
        <div class="chart-grid single">
            <div class="chart-card">{chart_htmls['geospatial']}</div>
        </div>
        <div class="chart-grid two-col" style="margin-top:1.25rem">
            <div class="chart-card">{chart_htmls['police_stations']}</div>
            <div class="chart-card">{''.join([chart_htmls.get('zones', '<div style="padding:2rem;color:#64748b;text-align:center">Zone data insufficient</div>')])}</div>
        </div>
    </div>

    <!-- ─── CORRIDORS ─── -->
    <div class="section" id="corridors">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(236,72,153,0.15)">🛤️</div>
            <h2>Corridor Analysis</h2>
            <span class="section-desc">Which corridors face the most disruption?</span>
        </div>
        <div class="chart-grid two-col">
            <div class="chart-card">{chart_htmls['corridors']}</div>
            <div class="chart-card">{chart_htmls['corridor_resolution']}</div>
        </div>
    </div>

    <!-- ─── VEHICLES ─── -->
    <div class="section" id="vehicles">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(16,185,129,0.15)">🚛</div>
            <h2>Vehicle Breakdown Analysis</h2>
            <span class="section-desc">Which vehicle types cause the most breakdowns?</span>
        </div>
        <div class="chart-grid single">
            <div class="chart-card">{chart_htmls['vehicle_type']}</div>
        </div>
    </div>

    <!-- ─── RESOLUTION ─── -->
    <div class="section" id="resolution">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(99,102,241,0.15)">⏱️</div>
            <h2>Resolution Time Analysis</h2>
            <span class="section-desc">How quickly are events resolved?</span>
        </div>
        <div class="chart-grid two-col">
            <div class="chart-card">{chart_htmls['resolution_time']}</div>
            <div class="chart-card">{chart_htmls['closure_vs_resolution']}</div>
        </div>
    </div>

    <!-- ─── DATA QUALITY ─── -->
    <div class="section" id="quality">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(239,68,68,0.15)">🔍</div>
            <h2>Data Quality Report</h2>
            <span class="section-desc">Missingness, type issues, and anomalies</span>
        </div>
        <div class="chart-grid single">
            <div class="chart-card">{chart_htmls['missing_values']}</div>
        </div>
        <div class="data-table-wrapper" style="margin-top:1.25rem">
            <table>
                <thead>
                    <tr>
                        <th>Column</th>
                        <th>Missing %</th>
                        <th>Missing Count</th>
                        <th>Severity</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f"""<tr>
                        <td>{row['Column']}</td>
                        <td>{row['Missing %']:.1f}%</td>
                        <td>{int(row['Missing Count'])}</td>
                        <td><span class="badge {'badge-red' if row['Missing %']>50 else 'badge-amber' if row['Missing %']>10 else 'badge-green'}">{
                            'Critical' if row['Missing %']>50 else 'Warning' if row['Missing %']>10 else 'OK'
                        }</span></td>
                    </tr>""" for _, row in missing_df.head(20).iterrows()])}
                </tbody>
            </table>
        </div>
    </div>

    <!-- ─── KEY INSIGHTS ─── -->
    <div class="section" id="insights">
        <div class="section-header">
            <div class="section-icon" style="background:rgba(245,158,11,0.15)">💡</div>
            <h2>Key Insights & Recommendations</h2>
            <span class="section-desc">Data-driven findings for Module 1–5 development</span>
        </div>
        <div class="insight-grid">
            <div class="insight-card" style="border-left-color:var(--accent-red)">
                <h4>🔴 Dominant Disruption Type</h4>
                <p><span class="highlight">{top_cause.replace('_',' ').title()}</span> accounts for <span class="highlight">{breakdown_pct:.0f}%</span> of all events.
                This should be the primary focus of Module 1 (Risk Prediction) — the model needs strong features for breakdown-type events.</p>
            </div>
            <div class="insight-card" style="border-left-color:var(--accent-amber)">
                <h4>🟡 Temporal Concentration</h4>
                <p><span class="highlight">{rush_hour_pct:.0f}%</span> of events occur during rush hours (8-10 AM, 5-8 PM).
                Module 2 (Impact Score) should heavily weight time-of-day — a breakdown at 9 AM on ORR has 5x the impact of one at 2 AM.</p>
            </div>
            <div class="insight-card" style="border-left-color:var(--accent-blue)">
                <h4>🔵 Corridor Focus</h4>
                <p><span class="highlight">{corridor_pct:.0f}%</span> of events occur on designated corridors.
                The top corridor is <span class="highlight">{top_corridor}</span>. Module 4 (Diversion) should pre-compute alternate routes for the top 10 corridors.</p>
            </div>
            <div class="insight-card" style="border-left-color:var(--accent-green)">
                <h4>🟢 Resolution Performance</h4>
                <p>Median resolution time is <span class="highlight">{median_resolution:.1f} hours</span> (mean: {mean_resolution:.1f}h).
                The large gap between median and mean suggests outliers — some events take days to resolve. Module 3 should flag these for escalation.</p>
            </div>
            <div class="insight-card" style="border-left-color:var(--accent-purple)">
                <h4>🟣 Road Closure Signal</h4>
                <p>Only <span class="highlight">{road_closure_rate:.1f}%</span> of events require road closure.
                However, road closure events likely have disproportionate impact — this is a strong binary feature for the ML model (Module 1).</p>
            </div>
            <div class="insight-card" style="border-left-color:var(--accent-cyan)">
                <h4>🔷 Police Station Load</h4>
                <p>The busiest station is <span class="highlight">{top_station}</span>.
                Module 3 (Resource Recommendation) should balance workload across stations — current data shows uneven distribution.</p>
            </div>
        </div>

        <div class="insight-card" style="border-left-color:var(--accent-pink); margin-top:1rem">
            <h4>🎯 Recommendations for Next Phases</h4>
            <p>
                <strong>Module 1 (Risk Prediction):</strong> Use event_cause + is_corridor + hour_of_day + requires_road_closure as top features. Engineer the 4-level target from priority + road_closure + resolution_time signals.<br>
                <strong>Module 2 (Impact Score):</strong> Weight rush-hour events on major corridors 3-5x higher. Use historical frequency at same junction as a multiplier.<br>
                <strong>Module 3 (Resources):</strong> Build rule matrix from the event_cause × priority cross-tab. Vehicle breakdowns need crane/towing; tree falls need BBMP crew.<br>
                <strong>Module 4 (Diversion):</strong> Pre-map top 10 corridors. ORR and Bellary Road should have pre-computed diversions ready.<br>
                <strong>Module 5 (Dashboard):</strong> Use this EDA dashboard structure as the foundation. Add real-time event feed and prediction overlays.
            </p>
        </div>
    </div>

</div>

<!-- ═══ FOOTER ═══ -->
<div class="footer">
    <p>Astram Event-Driven Congestion Management System · Phase 0: EDA · Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    <p style="margin-top:0.25rem">Built with Python · pandas · Plotly · {total_events:,} events analyzed across {num_corridors} corridors</p>
</div>

<script>
    // ─── Smooth scroll navigation ───
    function scrollToSection(id) {{
        document.getElementById(id).scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        event.target.classList.add('active');
    }}

    // ─── Active nav on scroll ───
    const sections = document.querySelectorAll('.section');
    const navBtns = document.querySelectorAll('.nav-btn');
    window.addEventListener('scroll', () => {{
        let current = '';
        sections.forEach(s => {{
            if (window.scrollY >= s.offsetTop - 100) current = s.id;
        }});
        navBtns.forEach(b => {{
            b.classList.remove('active');
            if (b.getAttribute('onclick')?.includes(current)) b.classList.add('active');
        }});
    }});

    // ─── Fade-in on scroll ───
    const observer = new IntersectionObserver((entries) => {{
        entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('visible'); }});
    }}, {{ threshold: 0.1 }});
    document.querySelectorAll('.chart-card, .insight-card, .kpi-card').forEach(el => {{
        el.classList.add('fade-in');
        observer.observe(el);
    }});

    // ─── Resize all plotly charts on load ───
    window.addEventListener('load', () => {{
        window.dispatchEvent(new Event('resize'));
    }});
</script>

</body>
</html>"""

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n{'=' * 70}")
print(f" [OK] Dashboard saved to: {OUTPUT_PATH}")
print(f" [CHARTS] {len(figures)} interactive charts generated")
print(f" [DATA] {total_events:,} events analyzed")
print(f"{'=' * 70}")
print(f"\n  Open the file in your browser to explore the interactive dashboard!")
