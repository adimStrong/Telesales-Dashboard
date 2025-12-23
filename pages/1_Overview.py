"""
JUAN365 Telesales Dashboard - Overview Page
KPI Summary with Trend Charts and Team Performance
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils.google_sheets import load_all_sheets_data, refresh_data
from utils.data_processor import filter_by_date_range, filter_by_team, get_unique_dates
from utils.metrics import (
    calculate_kpis, calculate_team_metrics, calculate_daily_metrics,
    format_percentage, format_number
)

import os

st.set_page_config(
    page_title="Dashboard | JUAN365 Telesales",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for header
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header with Logo - Centered
logo_path = "assets/logo.jpg"
if os.path.exists(logo_path):
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        img_col, text_col = st.columns([1, 4])
        with img_col:
            st.image(logo_path, width=80)
        with text_col:
            st.markdown('<h1 class="main-header">Performance Dashboard</h1>', unsafe_allow_html=True)
else:
    st.markdown('<h1 class="main-header">Performance Dashboard</h1>', unsafe_allow_html=True)

# Load data (already standardized)
with st.spinner("Loading data..."):
    df = load_all_sheets_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
        refresh_data()
        st.rerun()

    st.markdown("---")

    # Date filter
    min_date, max_date = get_unique_dates(df)
    if min_date and max_date:
        date_range = st.date_input(
            "Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        if len(date_range) == 2:
            df = filter_by_date_range(df, date_range[0], date_range[1])

    st.markdown("---")

    # Team filter
    all_teams = sorted(df["_team"].unique().tolist()) if "_team" in df.columns else []
    selected_teams = st.multiselect("Teams", all_teams, default=all_teams)
    if selected_teams:
        df = filter_by_team(df, selected_teams)

    st.markdown("---")
    st.caption(f"Records: {len(df):,}")
    st.caption(f"Teams: {df['_team'].nunique() if '_team' in df.columns else 0}")
    st.caption(f"Agents: {df['agent_name'].nunique() if 'agent_name' in df.columns else 0}")

# Check if filtered data is empty
if df.empty:
    st.warning("No data matches your filter criteria.")
    st.stop()

# KPI Summary
st.markdown("### Key Metrics Summary")
kpis = calculate_kpis(df)

# Row 1: 5 KPIs
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Active Agents", format_number(kpis["active_agents"]))
col2.metric("Total Calls", format_number(kpis["total_calls"]))
col3.metric("Answered Calls", format_number(kpis["answered_calls"]))
col4.metric("Not Connected", format_number(kpis["not_connected"]))
col5.metric("Connection Rate", format_percentage(kpis["connection_rate"]))

# Row 2: 2 KPIs
col1, col2 = st.columns(2)
col1.metric("People Recalled", format_number(kpis["people_recalled"]))
col2.metric("Recall Conv %", format_percentage(kpis["conversion_rate_recalled"]))

st.markdown("---")

# Team Performance Charts
st.markdown("### Team Performance")
team_metrics = calculate_team_metrics(df)

if not team_metrics.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Total Calls by Team")
        fig = px.bar(
            team_metrics.sort_values("total_calls", ascending=True),
            x="total_calls",
            y="team",
            orientation="h",
            color="total_calls",
            color_continuous_scale="Blues",
            labels={"total_calls": "Total Calls", "team": "Team"}
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False
        )
        fig.update_traces(
            texttemplate="%{x:,.0f}",
            textposition="outside"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Recall Conversion Rate by Team")
        fig = px.bar(
            team_metrics.sort_values("conversion_rate_recalled", ascending=True),
            x="conversion_rate_recalled",
            y="team",
            orientation="h",
            color="conversion_rate_recalled",
            color_continuous_scale="Greens",
            labels={"conversion_rate_recalled": "Recall Conv %", "team": "Team"}
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False
        )
        fig.update_traces(
            texttemplate="%{x:.1f}%",
            textposition="outside"
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No team data available")

st.markdown("---")

# Daily Trends
st.markdown("### Daily Trends")
daily_metrics = calculate_daily_metrics(df)

if not daily_metrics.empty:
    # Add calculated rates to daily metrics
    daily_metrics["connection_rate"] = daily_metrics.apply(
        lambda row: (row["answered_calls"] / row["total_calls"] * 100) if row["total_calls"] > 0 else 0, axis=1
    )
    daily_metrics["conversion_rate_recalled"] = daily_metrics.apply(
        lambda row: (row["people_recalled"] / row["answered_calls"] * 100) if row["answered_calls"] > 0 else 0, axis=1
    )

    # Metric selector
    metric_options = {
        "total_calls": "Total Calls",
        "answered_calls": "Answered Calls",
        "not_connected": "Not Connected",
        "people_recalled": "People Recalled",
        "connection_rate": "Connection Rate (%)",
        "conversion_rate_recalled": "Recall Conv Rate (%)"
    }

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Calls Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_metrics["date"],
            y=daily_metrics["total_calls"],
            mode="lines+markers",
            name="Total Calls",
            line=dict(color="#3498db", width=2),
            marker=dict(size=6)
        ))
        fig.add_trace(go.Scatter(
            x=daily_metrics["date"],
            y=daily_metrics["answered_calls"],
            mode="lines+markers",
            name="Answered",
            line=dict(color="#27ae60", width=2),
            marker=dict(size=6)
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Calls",
            height=350,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Conversion Rates Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_metrics["date"],
            y=daily_metrics["connection_rate"],
            mode="lines+markers",
            name="Connection Rate",
            line=dict(color="#9b59b6", width=2),
            marker=dict(size=6)
        ))
        fig.add_trace(go.Scatter(
            x=daily_metrics["date"],
            y=daily_metrics["conversion_rate_recalled"],
            mode="lines+markers",
            name="Recall Conv Rate",
            line=dict(color="#e74c3c", width=2),
            marker=dict(size=6)
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Rate (%)",
            height=350,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Daily data table
    with st.expander("View Daily Data"):
        display_daily = daily_metrics.copy()
        display_daily["date"] = display_daily["date"].dt.strftime("%Y-%m-%d")
        display_daily["total_calls"] = display_daily["total_calls"].apply(lambda x: f"{x:,}")
        display_daily["answered_calls"] = display_daily["answered_calls"].apply(lambda x: f"{x:,}")
        display_daily["not_connected"] = display_daily["not_connected"].apply(lambda x: f"{x:,}")
        display_daily["people_recalled"] = display_daily["people_recalled"].apply(lambda x: f"{x:,}")
        display_daily["connection_rate"] = display_daily["connection_rate"].apply(lambda x: f"{x:.1f}%")
        display_daily["conversion_rate_recalled"] = display_daily["conversion_rate_recalled"].apply(lambda x: f"{x:.1f}%")

        display_cols = ["date", "total_calls", "answered_calls", "not_connected", "people_recalled", "connection_rate", "conversion_rate_recalled"]
        display_daily = display_daily[display_cols].sort_values("date", ascending=False)
        display_daily.columns = ["Date", "Total Calls", "Answered", "Not Connected", "Recalled", "Conn Rate", "Recall Conv"]

        st.dataframe(display_daily, use_container_width=True, hide_index=True)
else:
    st.info("No daily trend data available")

# Team metrics table
st.markdown("---")
st.markdown("### Team Metrics Summary")

if not team_metrics.empty:
    display_metrics = team_metrics.copy()

    # Format columns
    if "total_calls" in display_metrics.columns:
        display_metrics["total_calls"] = display_metrics["total_calls"].apply(lambda x: f"{x:,}")
    if "answered_calls" in display_metrics.columns:
        display_metrics["answered_calls"] = display_metrics["answered_calls"].apply(lambda x: f"{x:,}")
    if "not_connected" in display_metrics.columns:
        display_metrics["not_connected"] = display_metrics["not_connected"].apply(lambda x: f"{x:,}")
    if "people_recalled" in display_metrics.columns:
        display_metrics["people_recalled"] = display_metrics["people_recalled"].apply(lambda x: f"{x:,}")
    if "connection_rate" in display_metrics.columns:
        display_metrics["connection_rate"] = display_metrics["connection_rate"].apply(lambda x: f"{x:.1f}%")
    if "conversion_rate_recalled" in display_metrics.columns:
        display_metrics["conversion_rate_recalled"] = display_metrics["conversion_rate_recalled"].apply(lambda x: f"{x:.1f}%")

    # Select and rename columns for display
    display_cols = ["team", "team_leader", "active_agents", "total_calls", "answered_calls", "not_connected", "people_recalled", "connection_rate", "conversion_rate_recalled"]
    display_cols = [c for c in display_cols if c in display_metrics.columns]
    display_metrics = display_metrics[display_cols]

    col_config = {
        "team": "Team",
        "team_leader": "TL",
        "active_agents": "Agents",
        "total_calls": "Total Calls",
        "answered_calls": "Answered",
        "not_connected": "Not Connected",
        "people_recalled": "Recalled",
        "connection_rate": "Conn Rate",
        "conversion_rate_recalled": "Recall Conv"
    }

    st.dataframe(
        display_metrics,
        use_container_width=True,
        hide_index=True,
        column_config=col_config
    )
else:
    st.info("No team metrics available")
