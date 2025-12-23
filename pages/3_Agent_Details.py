"""
JUAN365 Telesales Dashboard - Agent Scorecard Page
Individual agent performance tracking and analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils.google_sheets import load_all_sheets_data, refresh_data
from utils.data_processor import (
    filter_by_date_range, filter_by_agent,
    get_unique_agents, get_unique_dates
)
from utils.metrics import (
    calculate_kpis, calculate_agent_metrics,
    format_percentage, format_number
)

import os

st.set_page_config(
    page_title="Agent Scorecard | JUAN365 Telesales",
    page_icon="👤",
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

# Header
st.markdown('<h1 class="main-header">Agent Scorecard</h1>', unsafe_allow_html=True)

# Load data
with st.spinner("Loading data..."):
    df = load_all_sheets_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# Get all agents for selection
all_agents = get_unique_agents(df)

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

    # Agent selector with search
    st.subheader("Select Agent")
    selected_agent = st.selectbox(
        "Agent",
        options=all_agents,
        index=0 if all_agents else None,
        key="agent_selector",
        placeholder="Search for agent..."
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
    st.caption(f"Total Agents: {len(all_agents)}")

# Check if data exists
if df.empty or not selected_agent:
    st.warning("No data available for selected filters.")
    st.stop()

# Filter for selected agent
agent_df = df[df["agent_name"] == selected_agent]

if agent_df.empty:
    st.warning(f"No data available for {selected_agent}.")
    st.stop()

# Agent Profile
agent_team = agent_df["_team"].iloc[0] if "_team" in agent_df.columns else "N/A"
agent_tl = agent_df["_team_leader"].iloc[0] if "_team_leader" in agent_df.columns else "N/A"
st.markdown(f"### {selected_agent}")
st.markdown(f"**Team:** {agent_team} | **Team Leader:** {agent_tl}")

st.markdown("---")

# Agent KPIs
st.markdown("### Performance Summary")
agent_kpis = calculate_kpis(agent_df)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Calls", format_number(agent_kpis["total_calls"]))
col2.metric("Answered", format_number(agent_kpis["answered_calls"]))
col3.metric("Not Connected", format_number(agent_kpis["not_connected"]))
col4.metric("Recalled", format_number(agent_kpis["people_recalled"]))
col5.metric("Recall Conv", format_percentage(agent_kpis["conversion_rate_recalled"]))

st.markdown("---")

# Agent Daily Performance Chart
st.markdown("### Daily Performance")

# Daily metrics for this agent
agent_daily = agent_df.groupby("date").agg({
    "total_calls": "sum",
    "answered_calls": "sum",
    "not_connected": "sum",
    "people_recalled": "sum"
}).reset_index().sort_values("date")

if not agent_daily.empty:
    # Add rates
    agent_daily["connection_rate"] = agent_daily.apply(
        lambda row: (row["answered_calls"] / row["total_calls"] * 100) if row["total_calls"] > 0 else 0, axis=1
    )
    agent_daily["conversion_rate_recalled"] = agent_daily.apply(
        lambda row: (row["people_recalled"] / row["answered_calls"] * 100) if row["answered_calls"] > 0 else 0, axis=1
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Calls Trend")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=agent_daily["date"],
            y=agent_daily["total_calls"],
            name="Total Calls",
            marker_color="rgba(52, 152, 219, 0.7)"
        ))
        fig.add_trace(go.Bar(
            x=agent_daily["date"],
            y=agent_daily["answered_calls"],
            name="Answered",
            marker_color="rgba(39, 174, 96, 0.7)"
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Calls",
            height=350,
            barmode="overlay",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Conversion Rate Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=agent_daily["date"],
            y=agent_daily["conversion_rate_recalled"],
            mode="lines+markers",
            name="Recall Conv %",
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=10),
            fill="tozeroy",
            fillcolor="rgba(231, 76, 60, 0.2)"
        ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Recall Conv %",
            height=350,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Compare with Team Average
st.markdown("### Comparison with Team")

team_df = df[df["_team"] == agent_team] if "_team" in df.columns else df
team_agent_count = team_df["agent_name"].nunique() if "agent_name" in team_df.columns else 1

# Get team averages
team_total_calls = team_df["total_calls"].sum()
team_answered = team_df["answered_calls"].sum()
team_recalled = team_df["people_recalled"].sum()

team_avg_calls = team_total_calls / team_agent_count if team_agent_count > 0 else 0
team_avg_answered = team_answered / team_agent_count if team_agent_count > 0 else 0
team_avg_recalled = team_recalled / team_agent_count if team_agent_count > 0 else 0
team_conv_rate = (team_recalled / team_answered * 100) if team_answered > 0 else 0

# Agent totals
agent_total_calls = agent_kpis["total_calls"]
agent_answered = agent_kpis["answered_calls"]
agent_recalled = agent_kpis["people_recalled"]
agent_conv_rate = agent_kpis["conversion_rate_recalled"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    diff = agent_total_calls - team_avg_calls
    diff_pct = (diff / team_avg_calls * 100) if team_avg_calls > 0 else 0
    st.metric(
        "Total Calls vs Team Avg",
        format_number(agent_total_calls),
        delta=f"{diff_pct:+.1f}%"
    )

with col2:
    diff = agent_answered - team_avg_answered
    diff_pct = (diff / team_avg_answered * 100) if team_avg_answered > 0 else 0
    st.metric(
        "Answered vs Team Avg",
        format_number(agent_answered),
        delta=f"{diff_pct:+.1f}%"
    )

with col3:
    diff = agent_recalled - team_avg_recalled
    diff_pct = (diff / team_avg_recalled * 100) if team_avg_recalled > 0 else 0
    st.metric(
        "Recalled vs Team Avg",
        format_number(agent_recalled),
        delta=f"{diff_pct:+.1f}%"
    )

with col4:
    diff = agent_conv_rate - team_conv_rate
    st.metric(
        "Recall Conv vs Team Avg",
        format_percentage(agent_conv_rate),
        delta=f"{diff:+.1f}pp"
    )

# Agent vs Team Average Chart
if not agent_daily.empty:
    # Get team daily average
    team_daily = team_df.groupby("date").agg({
        "total_calls": "sum",
        "answered_calls": "sum",
        "people_recalled": "sum"
    }).reset_index()
    team_daily["team_avg_calls"] = team_daily["total_calls"] / team_agent_count
    team_daily["team_avg_recalled"] = team_daily["people_recalled"] / team_agent_count

    # Merge agent and team data
    comparison = agent_daily.merge(
        team_daily[["date", "team_avg_calls", "team_avg_recalled"]],
        on="date",
        how="left"
    )

    st.markdown("##### Agent vs Team Average - Daily Calls")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=comparison["date"],
        y=comparison["total_calls"],
        mode="lines+markers",
        name=f"{selected_agent}",
        line=dict(color="#FF6B35", width=3),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=comparison["date"],
        y=comparison["team_avg_calls"],
        mode="lines",
        name="Team Average",
        line=dict(color="#3498db", width=2, dash="dash")
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Total Calls",
        height=350,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Agent Rankings
st.markdown("### Rankings")

# Calculate all agent metrics for rankings
all_agent_metrics = calculate_agent_metrics(df)

if not all_agent_metrics.empty:
    # Overall rankings
    all_agent_metrics["calls_rank"] = all_agent_metrics["total_calls"].rank(ascending=False, method="min").astype(int)
    all_agent_metrics["answered_rank"] = all_agent_metrics["answered_calls"].rank(ascending=False, method="min").astype(int)
    all_agent_metrics["recalled_rank"] = all_agent_metrics["people_recalled"].rank(ascending=False, method="min").astype(int)
    all_agent_metrics["conv_rank"] = all_agent_metrics["conversion_rate_recalled"].rank(ascending=False, method="min").astype(int)

    # Get agent's ranks
    agent_row = all_agent_metrics[all_agent_metrics["agent_name"] == selected_agent]

    if not agent_row.empty:
        total_agents = len(all_agent_metrics)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            rank = int(agent_row["calls_rank"].iloc[0])
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #3498db, #2980b9); border-radius: 10px; color: white;">
                <h3>#{rank}</h3>
                <p>Total Calls</p>
                <small>of {total_agents} agents</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            rank = int(agent_row["answered_rank"].iloc[0])
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #27ae60, #229954); border-radius: 10px; color: white;">
                <h3>#{rank}</h3>
                <p>Answered Calls</p>
                <small>of {total_agents} agents</small>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            rank = int(agent_row["recalled_rank"].iloc[0])
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #9b59b6, #8e44ad); border-radius: 10px; color: white;">
                <h3>#{rank}</h3>
                <p>People Recalled</p>
                <small>of {total_agents} agents</small>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            rank = int(agent_row["conv_rank"].iloc[0])
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #e74c3c, #c0392b); border-radius: 10px; color: white;">
                <h3>#{rank}</h3>
                <p>Recall Conv %</p>
                <small>of {total_agents} agents</small>
            </div>
            """, unsafe_allow_html=True)

    # Team rankings
    st.markdown("##### Rank within Team")
    team_agents = all_agent_metrics[all_agent_metrics["team"] == agent_team] if "team" in all_agent_metrics.columns else all_agent_metrics

    if not team_agents.empty:
        team_agents = team_agents.copy()
        team_agents["team_calls_rank"] = team_agents["total_calls"].rank(ascending=False, method="min").astype(int)
        team_agents["team_conv_rank"] = team_agents["conversion_rate_recalled"].rank(ascending=False, method="min").astype(int)

        agent_team_row = team_agents[team_agents["agent_name"] == selected_agent]

        if not agent_team_row.empty:
            team_size = len(team_agents)
            col1, col2 = st.columns(2)

            with col1:
                rank = int(agent_team_row["team_calls_rank"].iloc[0])
                st.metric(f"Total Calls Rank in {agent_team}", f"#{rank} of {team_size}")

            with col2:
                rank = int(agent_team_row["team_conv_rank"].iloc[0])
                st.metric(f"Recall Conv Rank in {agent_team}", f"#{rank} of {team_size}")

st.markdown("---")

# Activity Log
with st.expander("View Daily Activity Log"):
    if not agent_daily.empty:
        display_log = agent_daily.copy()
        display_log["date"] = display_log["date"].dt.strftime("%Y-%m-%d")
        display_log["total_calls"] = display_log["total_calls"].apply(lambda x: f"{x:,}")
        display_log["answered_calls"] = display_log["answered_calls"].apply(lambda x: f"{x:,}")
        display_log["not_connected"] = display_log["not_connected"].apply(lambda x: f"{x:,}")
        display_log["people_recalled"] = display_log["people_recalled"].apply(lambda x: f"{x:,}")
        display_log["connection_rate"] = display_log["connection_rate"].apply(lambda x: f"{x:.1f}%")
        display_log["conversion_rate_recalled"] = display_log["conversion_rate_recalled"].apply(lambda x: f"{x:.1f}%")

        display_cols = ["date", "total_calls", "answered_calls", "not_connected", "people_recalled", "connection_rate", "conversion_rate_recalled"]
        display_log = display_log[display_cols].sort_values("date", ascending=False)
        display_log.columns = ["Date", "Total Calls", "Answered", "Not Connected", "Recalled", "Conn Rate", "Recall Conv"]

        st.dataframe(display_log, use_container_width=True, hide_index=True)
