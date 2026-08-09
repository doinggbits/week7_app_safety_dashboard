# --- RUN THIS SCRIPT INDEPENDENTLY VIA TERMINAL: streamlit run app_safety_dashboard.py ---
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set Web UI Configuration Framework
st.set_page_config(page_title="KPC Safety Command Center", layout="wide")

st.title("Operational Safety Command Center")
st.markdown("Real-time monitoring of HSE incidents, risk profiling scores, and corporate regulatory compliance.")

# Cached Data Ingestion Engine.
# @st.cache_data means this only re-runs when the function body changes, not on every
# sidebar interaction — filtering happens on the cached DataFrame below, not by
# regenerating data on each rerun.
@st.cache_data
def fetch_hse_records():
    np.random.seed(42)
    dates = pd.date_range(start='2026-01-01', periods=365, freq='D')
    sites = ['Depot_A', 'Depot_B', 'Depot_C', 'Refinery_X']
    incident_types = ['Slip/Trip', 'Leak/Spill', 'Equipment Failure', 'Near Miss', 'Fire/Heat']

    raw_records = []
    for _ in range(500):
        date = np.random.choice(dates)
        site = np.random.choice(sites)
        inc_type = np.random.choice(incident_types, p=[0.3, 0.2, 0.25, 0.2, 0.05])
        severity = np.random.choice([4, 5]) if inc_type == 'Fire/Heat' else np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
        hour = np.random.randint(0, 24)
        raw_records.append({'date': date, 'site': site, 'incident_type': inc_type,
                             'severity': severity, 'hour': hour})

    df = pd.DataFrame(raw_records)
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()

    # Derive shift from hour — used by the day/shift heatmap below.
    def derive_shift(hour):
        if 6 <= hour < 14:
            return 'Morning Shift'
        elif 14 <= hour < 22:
            return 'Afternoon Shift'
        else:
            return 'Night Shift'
    df['shift'] = df['hour'].apply(derive_shift)
    return df

df_base = fetch_hse_records()

# Sidebar Filtering Implementation.
# Site, incident type, and date range all live in the sidebar so every chart below
# reads from one filtered DataFrame — this keeps every visualization in sync
# automatically instead of wiring each chart to its own filter logic.
st.sidebar.header("Interactive Scope Filters")

selected_facilities = st.sidebar.multiselect(
    "Target Facility Nodes",
    options=list(df_base['site'].unique()),
    default=list(df_base['site'].unique())
)

selected_classes = st.sidebar.multiselect(
    "Incident Classification",
    options=list(df_base['incident_type'].unique()),
    default=list(df_base['incident_type'].unique())
)

# Date range filter. Defaults to the full span of the dataset so nothing is
# hidden until the user narrows it deliberately.
min_date, max_date = df_base['date'].min().date(), df_base['date'].max().date()
selected_date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
# date_input returns a single date while the user is mid-selection (before they've
# picked the end date) — guard against that instead of crashing the app.
if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
else:
    start_date, end_date = min_date, max_date

# Critical-incident alert threshold. Exposed as a sidebar control rather than a
# hardcoded constant so a safety officer can tighten/loosen it without editing code.
alert_threshold = st.sidebar.slider("Critical Incident Alert Threshold", min_value=1, max_value=50, value=15)

# Apply all filters together to build the single DataFrame every chart reads from.
df_filtered = df_base[
    (df_base['site'].isin(selected_facilities)) &
    (df_base['incident_type'].isin(selected_classes)) &
    (df_base['date'].dt.date >= start_date) &
    (df_base['date'].dt.date <= end_date)
]

# Top-Level Metrics Display Row.
# Conditional coloring: st.metric's delta_color turns the delta text red when
# "inverse" is set and the delta is positive-worded as a bad thing (more critical
# incidents = bad), so the color follows the safety direction, not just the sign.
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.metric("Aggregated Incidents", df_filtered.shape[0])

with kpi_col2:
    avg_sev = df_filtered['severity'].mean() if not df_filtered.empty else 0
    st.metric("Average Severity Index", f"{avg_sev:.2f}")

with kpi_col3:
    critical_events = df_filtered[df_filtered['severity'] >= 4].shape[0]
    # Red delta whenever there are any critical events at all — a safety dashboard
    # should never make critical incidents look neutral or good.
    st.metric("Critical Triggers (Sev 4+)", critical_events,
               delta=f"{critical_events} in view" if critical_events > 0 else "None in view",
               delta_color="inverse" if critical_events > 0 else "off")

with kpi_col4:
    # Compliance framed as % of incidents below the critical threshold — reacts to
    # the actual filtered data instead of being a static demo number.
    compliance_pct = (100 * (1 - critical_events / df_filtered.shape[0])) if df_filtered.shape[0] > 0 else 100
    st.metric("Compliance Rating", f"{compliance_pct:.1f}%")

st.divider()

# Safety Conditional Alert System.
# Placed prominently near the top (right after KPIs) since this is the one thing
# a safety officer should never have to scroll to find.
st.subheader("Live Risk Assessment Exceptions")
df_critical_view = df_filtered[df_filtered['severity'] >= 4].sort_values('date', ascending=False)

if len(df_critical_view) > alert_threshold:
    st.error(f"⚠️ THRESHOLD BREACHED: {len(df_critical_view)} critical incidents exceed the "
             f"configured alert threshold of {alert_threshold}. Immediate review recommended.")
elif not df_critical_view.empty:
    st.warning(f"Flagged Attention: {len(df_critical_view)} high-severity entries match your active filters.")
else:
    st.success("Operational Compliance Checked: No high-severity events found within selected parameters.")

if not df_critical_view.empty:
    st.dataframe(df_critical_view, use_container_width=True)

st.divider()

# Time-Series Trend Chart.
# Incidents are aggregated to weekly counts rather than plotted per-day — daily
# counts on a 365-day range are too noisy to read as a trend at a glance.
st.subheader("Incident Trend Over Time")
if not df_filtered.empty:
    weekly = (df_filtered.set_index('date')
              .resample('W')['incident_type']
              .count()
              .reset_index(name='incident_count'))
    fig_trend = px.line(weekly, x='date', y='incident_count', markers=True,
                         labels={'date': 'Week', 'incident_count': 'Incidents'})
    fig_trend.update_layout(hovermode='x unified')
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No records match the current filters.")

# Categorical + Site Breakdown Row.
layout_col1, layout_col2 = st.columns(2)

with layout_col1:
    st.subheader("Volumetric Incident Distribution by Site Node")
    site_agg = df_filtered.groupby('site').size().reset_index(name='count')
    fig_site = px.bar(site_agg, x='site', y='count', color='count',
                       color_continuous_scale='Reds',
                       labels={'site': 'Asset Node', 'count': 'Incidents'})
    st.plotly_chart(fig_site, use_container_width=True)

with layout_col2:
    st.subheader("Incident Type Breakdown")
    type_agg = df_filtered.groupby('incident_type').size().reset_index(name='count')
    fig_type = px.pie(type_agg, names='incident_type', values='count', hole=0.4)
    st.plotly_chart(fig_type, use_container_width=True)

# Shift/Day Heatmap.
# Required visualization #3 (map OR shift/day heatmap) — using the heatmap since
# it surfaces an operational pattern (which shift+day combo is riskiest) that a
# map of static site coordinates can't show.
st.subheader("Incident Frequency by Day and Shift")
days_ordered = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
if not df_filtered.empty:
    pivot_temporal = pd.crosstab(df_filtered['day_of_week'], df_filtered['shift']).reindex(days_ordered)
    fig_heat = px.imshow(pivot_temporal, text_auto=True, color_continuous_scale='YlOrRd',
                          labels=dict(x="Shift", y="Day of Week", color="Incidents"))
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("No records match the current filters.")

# Geospatial Asset Incident Hotspots (bonus — kept from the original draft since
# real site coordinates are available and it adds a second spatial view alongside
# the shift/day heatmap).
st.divider()
st.subheader("Geospatial Asset Incident Hotspots")

coordinates_map = {
    'Depot_A': (-4.0435, 39.6682),    # Mombasa region
    'Depot_B': (-1.2921, 36.8219),    # Nairobi hub
    'Depot_C': (-0.0917, 34.7680),    # Kisumu terminal
    'Refinery_X': (-4.0500, 39.7000)  # Refinery point
}

spatial_records = []
for _, row in df_filtered.iterrows():
    lat, lon = coordinates_map.get(row['site'], (0.0, 0.0))
    # Jitter prevents markers from stacking exactly on top of each other at one site.
    lat += np.random.uniform(-0.03, 0.03)
    lon += np.random.uniform(-0.03, 0.03)
    spatial_records.append({'latitude': lat, 'longitude': lon, 'scale_radius': row['severity'] * 1500})

df_spatial = pd.DataFrame(spatial_records)
if not df_spatial.empty:
    st.map(df_spatial, latitude='latitude', longitude='longitude', size='scale_radius')
else:
    st.info("No records match the current filters.")

# Secure CSV Reporting Download Function.
# Encoded at render time from df_filtered, so the exported file always matches
# exactly what's on screen — not the full unfiltered dataset.
st.divider()
csv_payload = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Export Filtered Safety Data to CSV Report",
    data=csv_payload,
    file_name='safety_incident_report_export.csv',
    mime='text/csv'
)
