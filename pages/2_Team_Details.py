"""
JUAN365 Telesales Dashboard - Team Performance Page
Deep dive into team metrics and comparisons
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils.google_sheets import load_all_sheets_data, refresh_data
from utils.data_processor import filter_by_date_range, filter_by_team, get_unique_dates
from utils.metrics import (
    calculate_kpis, calculate_team_metrics, calculate_agent_metrics,
    calculate_daily_metrics, format_percentage, format_number
)

import os

st.set_page_config(
    page_title="Team Performance | JUAN365 Telesales",
    page_icon="👥",
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

# Header with Logo
header_col1, header_col2 = st.columns([1, 5])
with header_col1:
    logo_path = "assets/logo.jpg"
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)
with header_col2:
    st.markdown('<h1 class="main-header">Team Performance</h1>', unsafe_allow_html=True)

# Load data
with st.spinner("Loading data..."):
    df = load_all_sheets_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# Get all teams for selection
all_teams = sorted(df["_team"].unique().tolist()) if "_team" in df.columns else []

# Sidebar
with st.sidebar:
    # Logo
    logo_path = "assets/logo.jpg"
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)

    st.markdown("---")
    st.header("Filters")

    if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
        refresh_data()
        st.rerun()

    st.markdown("---")

    # Team selector
    st.subheader("Select Team")
    selected_team = st.selectbox(
        "Team",
        options=all_teams,
        index=0 if all_teams else None,
        key="team_selector"
    )

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
    st.caption(f"Total Records: {len(df):,}")

# Check if data exists
if df.empty or not selected_team:
    st.warning("No data available for selected filters.")
    st.stop()

# Filter for selected team
team_df = df[df["_team"] == selected_team]

if team_df.empty:
    st.warning(f"No data available for {selected_team}.")
    st.stop()

# Team header with summary
team_leader = team_df["_team_leader"].iloc[0] if "_team_leader" in team_df.columns else "N/A"
st.markdown(f"### {selected_team} - TL: {team_leader}")

# Team KPIs
kpis = calculate_kpis(team_df)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Agents", format_number(kpis["active_agents"]))
col2.metric("Total Calls", format_number(kpis["total_calls"]))
col3.metric("Answered", format_number(kpis["answered_calls"]))
col4.metric("Recalled", format_number(kpis["people_recalled"]))
col5.metric("Recall Conv", format_percentage(kpis["conversion_rate_recalled"]))

st.markdown("---")

# Team Performance Charts
st.markdown("### Team Daily Performance")

# Daily metrics for this team
team_daily = team_df.groupby("date").agg({
    "total_calls": "sum",
    "answered_calls": "sum",
    "not_connected": "sum",
    "people_recalled": "sum"
}).reset_index().sort_values("date")

if not team_daily.empty:
    # Add rates
    team_daily["connection_rate"] = team_daily.apply(
        lambda row: (row["answered_calls"] / row["total_calls"] * 100) if row["total_calls"] > 0 else 0, axis=1
    )
    team_daily["conversion_rate_recalled"] = team_daily.apply(
        lambda row: (row["people_recalled"] / row["answered_calls"] * 100) if row["answered_calls"] > 0 else 0, axis=1
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Daily Calls")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=team_daily["date"],
            y=team_daily["total_calls"],
            mode="lines+markers",
            name="Total Calls",
            line=dict(color="#3498db", width=2),
            fill="tozeroy",
            fillcolor="rgba(52, 152, 219, 0.2)"
        ))
        fig.add_trace(go.Scatter(
            x=team_daily["date"],
            y=team_daily["answered_calls"],
            mode="lines+markers",
            name="Answered",
            line=dict(color="#27ae60", width=2)
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
        st.markdown("##### Conversion Rates")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=team_daily["date"],
            y=team_daily["conversion_rate_recalled"],
            mode="lines+markers",
            name="Recall Conv %",
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=8)
        ))
        fig.add_trace(go.Scatter(
            x=team_daily["date"],
            y=team_daily["connection_rate"],
            mode="lines+markers",
            name="Connection %",
            line=dict(color="#9b59b6", width=2, dash="dash")
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Rate (%)",
            height=350,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Agent Breakdown within Team
st.markdown("### Agent Performance in Team")

agent_metrics = calculate_agent_metrics(team_df)

if not agent_metrics.empty:
    # Sort by total calls
    agent_metrics = agent_metrics.sort_values("total_calls", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Calls by Agent")
        top_agents = agent_metrics.head(15)  # Show top 15
        fig = px.bar(
            top_agents.sort_values("total_calls", ascending=True),
            x="total_calls",
            y="agent_name",
            orientation="h",
            color="total_calls",
            color_continuous_scale="Blues",
            labels={"total_calls": "Total Calls", "agent_name": "Agent"}
        )
        fig.update_layout(
            showlegend=False,
            height=450,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False
        )
        fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Recall Conv % by Agent")
        fig = px.bar(
            top_agents.sort_values("conversion_rate_recalled", ascending=True),
            x="conversion_rate_recalled",
            y="agent_name",
            orientation="h",
            color="conversion_rate_recalled",
            color_continuous_scale="Greens",
            labels={"conversion_rate_recalled": "Recall Conv %", "agent_name": "Agent"}
        )
        fig.update_layout(
            showlegend=False,
            height=450,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False
        )
        fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # Agent details table
    st.markdown("##### All Agents in Team")
    display_agents = agent_metrics.copy()
    display_agents["total_calls"] = display_agents["total_calls"].apply(lambda x: f"{x:,}")
    display_agents["answered_calls"] = display_agents["answered_calls"].apply(lambda x: f"{x:,}")
    display_agents["not_connected"] = display_agents["not_connected"].apply(lambda x: f"{x:,}")
    display_agents["people_recalled"] = display_agents["people_recalled"].apply(lambda x: f"{x:,}")
    display_agents["connection_rate"] = display_agents["connection_rate"].apply(lambda x: f"{x:.1f}%")
    display_agents["conversion_rate_recalled"] = display_agents["conversion_rate_recalled"].apply(lambda x: f"{x:.1f}%")

    display_cols = ["agent_name", "total_calls", "answered_calls", "not_connected", "people_recalled", "connection_rate", "conversion_rate_recalled"]
    display_agents = display_agents[display_cols]
    display_agents.columns = ["Agent", "Total Calls", "Answered", "Not Connected", "Recalled", "Conn Rate", "Recall Conv"]

    st.dataframe(display_agents, use_container_width=True, hide_index=True)

st.markdown("---")

# All Teams Comparison
st.markdown("### All Teams Comparison")

team_metrics = calculate_team_metrics(df)

if not team_metrics.empty:
    # Highlight selected team
    team_metrics["is_selected"] = team_metrics["team"] == selected_team

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Total Calls Comparison")
        fig = px.bar(
            team_metrics.sort_values("total_calls", ascending=True),
            x="total_calls",
            y="team",
            orientation="h",
            color="is_selected",
            color_discrete_map={True: "#FF6B35", False: "#3498db"},
            labels={"total_calls": "Total Calls", "team": "Team"}
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Recall Conv % Comparison")
        fig = px.bar(
            team_metrics.sort_values("conversion_rate_recalled", ascending=True),
            x="conversion_rate_recalled",
            y="team",
            orientation="h",
            color="is_selected",
            color_discrete_map={True: "#FF6B35", False: "#27ae60"},
            labels={"conversion_rate_recalled": "Recall Conv %", "team": "Team"}
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    # Team ranking table
    st.markdown("##### Team Rankings")

    # Calculate ranks
    team_metrics["calls_rank"] = team_metrics["total_calls"].rank(ascending=False, method="min").astype(int)
    team_metrics["conv_rank"] = team_metrics["conversion_rate_recalled"].rank(ascending=False, method="min").astype(int)

    display_team = team_metrics.copy()
    display_team["total_calls"] = display_team["total_calls"].apply(lambda x: f"{x:,}")
    display_team["answered_calls"] = display_team["answered_calls"].apply(lambda x: f"{x:,}")
    display_team["people_recalled"] = display_team["people_recalled"].apply(lambda x: f"{x:,}")
    display_team["connection_rate"] = display_team["connection_rate"].apply(lambda x: f"{x:.1f}%")
    display_team["conversion_rate_recalled"] = display_team["conversion_rate_recalled"].apply(lambda x: f"{x:.1f}%")
    display_team["calls_rank"] = display_team["calls_rank"].apply(lambda x: f"#{x}")
    display_team["conv_rank"] = display_team["conv_rank"].apply(lambda x: f"#{x}")

    display_cols = ["team", "team_leader", "active_agents", "total_calls", "calls_rank", "answered_calls", "people_recalled", "conversion_rate_recalled", "conv_rank"]
    display_cols = [c for c in display_cols if c in display_team.columns]
    display_team = display_team[display_cols].sort_values("team")

    col_names = {
        "team": "Team",
        "team_leader": "TL",
        "active_agents": "Agents",
        "total_calls": "Total Calls",
        "calls_rank": "Calls Rank",
        "answered_calls": "Answered",
        "people_recalled": "Recalled",
        "conversion_rate_recalled": "Recall Conv",
        "conv_rank": "Conv Rank"
    }

    st.dataframe(
        display_team.rename(columns=col_names),
        use_container_width=True,
        hide_index=True
    )

# Weekly comparison for selected team
st.markdown("---")
st.markdown(f"### {selected_team} - Week over Week")

if not team_daily.empty and len(team_daily) >= 7:
    # Get last 2 weeks
    max_date = team_daily["date"].max()
    week1_start = max_date - timedelta(days=6)
    week2_start = max_date - timedelta(days=13)
    week2_end = max_date - timedelta(days=7)

    week1_df = team_daily[(team_daily["date"] >= week1_start) & (team_daily["date"] <= max_date)]
    week2_df = team_daily[(team_daily["date"] >= week2_start) & (team_daily["date"] <= week2_end)]

    if not week1_df.empty and not week2_df.empty:
        week1_calls = week1_df["total_calls"].sum()
        week2_calls = week2_df["total_calls"].sum()
        week1_recalled = week1_df["people_recalled"].sum()
        week2_recalled = week2_df["people_recalled"].sum()
        week1_answered = week1_df["answered_calls"].sum()
        week2_answered = week2_df["answered_calls"].sum()

        week1_conv = (week1_recalled / week1_answered * 100) if week1_answered > 0 else 0
        week2_conv = (week2_recalled / week2_answered * 100) if week2_answered > 0 else 0

        calls_delta = ((week1_calls - week2_calls) / week2_calls * 100) if week2_calls > 0 else 0
        recalled_delta = ((week1_recalled - week2_recalled) / week2_recalled * 100) if week2_recalled > 0 else 0
        conv_delta = week1_conv - week2_conv

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Calls (This Week)",
                f"{week1_calls:,}",
                delta=f"{calls_delta:+.1f}% vs last week"
            )

        with col2:
            st.metric(
                "People Recalled (This Week)",
                f"{week1_recalled:,}",
                delta=f"{recalled_delta:+.1f}% vs last week"
            )

        with col3:
            st.metric(
                "Recall Conv % (This Week)",
                f"{week1_conv:.1f}%",
                delta=f"{conv_delta:+.1f}pp vs last week"
            )
    else:
        st.info("Not enough data for week-over-week comparison")
else:
    st.info("Not enough data for week-over-week comparison")
