Week 7: HSE Safety Dashboard & Alert
app_safety_dashboard.py

Streamlit dashboard for monitoring HSE incidents across 4 sites (Depot A/B/C, Refinery X) over a simulated 365-day period.

Sidebar filters: site, incident type, date range, and an adjustable critical-incident alert threshold.

KPIs: total incidents, average severity, critical count (turns red when any critical incidents are in view), and a compliance rating computed from the filtered data.

Alerting: compares critical-incident count against the threshold slider — st.error if breached, st.warning if any critical incidents exist but under threshold, st.success otherwise.

Charts: weekly incident trend (line), incidents by site (bar), incident type breakdown (pie), day-of-week × shift heatmap, and a geospatial map of incident hotspots.

Export: downloads the currently filtered data as CSV — matches exactly what's on screen.

Run with:

pip install streamlit plotly pandas numpy
streamlit run app_safety_dashboard.py
Week7_Safety_Alert_BrianNyamu.pdf

1-page safety alert on elevated Slip/Trip incidents at Depot A (55 recorded — the largest site+incident-type pattern in the dataset). Headline, context, dated action items for shift supervisors and site leadership. Contact details removed per your last edit — add them back in before circulating.
