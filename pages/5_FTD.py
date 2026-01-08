"""
JUAN365 Telesales Dashboard - FTD (First Time Deposit) Page
FTD Team Performance Tracking and Analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from utils.google_sheets import load_ftd_data, refresh_data
from utils.data_processor import filter_by_date_range, get_unique_dates, get_unique_agents
from utils.metrics import (
    calculate_ftd_kpis, calculate_ftd_agent_metrics, calculate_ftd_daily_metrics,
    get_ftd_top_performers, format_percentage, format_number, format_peso
)

import os

st.set_page_config(
    page_title="FTD | JUAN365 Telesales",
    page_icon="💰",
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
    .ftd-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
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
            st.markdown('<h1 class="main-header">FTD Performance</h1>', unsafe_allow_html=True)
else:
    st.markdown('<h1 class="main-header">FTD Performance</h1>', unsafe_allow_html=True)

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
        refresh_data()
        st.rerun()

    st.markdown("---")

    # Year info (FTD is 2026 only)
    st.subheader("Year")
    st.info("FTD data is available for 2026 only")
    year_int = 2026

    st.markdown("---")

# Load FTD data
with st.spinner("Loading FTD data..."):
    df = load_ftd_data(year=year_int)

if df.empty:
    st.warning("No FTD data available.")
    st.stop()

# Store original data for trends chart
df_original = df.copy()
selected_date_range = None

# Sidebar filters continued
with st.sidebar:
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
            selected_date_range = date_range
            df = filter_by_date_range(df, date_range[0], date_range[1])

    st.markdown("---")

    # Agent filter
    all_agents = get_unique_agents(df_original)
    selected_agents = st.multiselect("Agents", all_agents, default=all_agents)
    if selected_agents:
        df = df[df["agent_name"].isin(selected_agents)]

    st.markdown("---")
    st.caption(f"Records: {len(df):,}")
    st.caption(f"Agents: {df['agent_name'].nunique() if 'agent_name' in df.columns else 0}")

# Check if filtered data is empty
if df.empty:
    st.warning("No data matches your filter criteria.")
    st.stop()

# =============================================================================
# KPI Summary Section
# =============================================================================
st.markdown("### Key FTD Metrics")
kpis = calculate_ftd_kpis(df)

# Row 1: 4 FTD-specific KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active FTD Agents", format_number(kpis["active_agents"]))
col2.metric("Total Deposit Amount", format_peso(kpis["total_deposit_amount"]))
col3.metric("Total Recharges", format_number(kpis["total_recharge"]))
col4.metric("Target Completion", format_percentage(kpis["target_completion"]))

# Row 2: 4 more KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Calls", format_number(kpis["total_calls"]))
col2.metric("Answered Calls", format_number(kpis["answered_calls"]))
col3.metric("Connection Rate", format_percentage(kpis["connection_rate"]))
col4.metric("Recall Conv %", format_percentage(kpis["conversion_rate_recalled"]))

st.markdown("---")

# =============================================================================
# Agent Performance Charts
# =============================================================================
st.markdown("### Agent Performance")

agent_metrics = calculate_ftd_agent_metrics(df)

if not agent_metrics.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Top Agents by Recharges")
        top_recharge = agent_metrics.nlargest(10, "recharge_count")
        fig = px.bar(
            top_recharge.sort_values("recharge_count", ascending=True),
            x="recharge_count",
            y="agent_name",
            orientation="h",
            color="recharge_count",
            color_continuous_scale="Purples",
            labels={"recharge_count": "Recharges", "agent_name": "Agent"}
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
        st.markdown("##### Top Agents by Deposit Amount")
        top_deposit = agent_metrics.nlargest(10, "deposit_amount")
        fig = px.bar(
            top_deposit.sort_values("deposit_amount", ascending=True),
            x="deposit_amount",
            y="agent_name",
            orientation="h",
            color="deposit_amount",
            color_continuous_scale="Greens",
            labels={"deposit_amount": "Deposit Amount", "agent_name": "Agent"}
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False
        )
        fig.update_traces(
            texttemplate="₱%{x:,.0f}",
            textposition="outside"
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No agent data available")

st.markdown("---")

# =============================================================================
# Daily Trends
# =============================================================================
st.markdown("### Daily Trends")

# Use appropriate data for trends
df_for_trends = df
trend_note = ""
if selected_date_range and len(selected_date_range) == 2:
    days_diff = (selected_date_range[1] - selected_date_range[0]).days
    if days_diff < 7:
        current_month_start = selected_date_range[1].replace(day=1)
        df_for_trends = filter_by_date_range(df_original, current_month_start, selected_date_range[1])
        trend_note = f"Showing current month data ({current_month_start.strftime('%b %d')} - {selected_date_range[1].strftime('%b %d, %Y')}) for better trend visualization"

if trend_note:
    st.info(trend_note)

daily_metrics = calculate_ftd_daily_metrics(df_for_trends)

if not daily_metrics.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Daily Recharges & Deposits")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_metrics["date"],
            y=daily_metrics["recharge_count"],
            mode="lines+markers",
            name="Recharges",
            line=dict(color="#9b59b6", width=2),
            marker=dict(size=6)
        ))
        if "deposit_amount" in daily_metrics.columns:
            fig.add_trace(go.Scatter(
                x=daily_metrics["date"],
                y=daily_metrics["deposit_amount"],
                mode="lines+markers",
                name="Deposit Amount",
                yaxis="y2",
                line=dict(color="#27ae60", width=2),
                marker=dict(size=6)
            ))
            fig.update_layout(
                yaxis2=dict(
                    title="Deposit Amount (₱)",
                    overlaying="y",
                    side="right"
                )
            )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Recharges",
            height=350,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Daily Calls & Connection Rate")
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
            line=dict(color="#2ecc71", width=2),
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

    # Daily data table
    with st.expander("View Daily Data"):
        display_daily = daily_metrics.copy()
        display_daily["date"] = display_daily["date"].dt.strftime("%Y-%m-%d")
        if "deposit_amount" in display_daily.columns:
            display_daily["deposit_amount"] = display_daily["deposit_amount"].apply(lambda x: f"₱{x:,.2f}")
        if "recharge_count" in display_daily.columns:
            display_daily["recharge_count"] = display_daily["recharge_count"].apply(lambda x: f"{x:,}")
        if "total_calls" in display_daily.columns:
            display_daily["total_calls"] = display_daily["total_calls"].apply(lambda x: f"{x:,}")
        if "answered_calls" in display_daily.columns:
            display_daily["answered_calls"] = display_daily["answered_calls"].apply(lambda x: f"{x:,}")
        if "connection_rate" in display_daily.columns:
            display_daily["connection_rate"] = display_daily["connection_rate"].apply(lambda x: f"{x:.1f}%")
        if "target_completion" in display_daily.columns:
            display_daily["target_completion"] = display_daily["target_completion"].apply(lambda x: f"{x:.1f}%")

        display_cols = ["date", "active_agents", "deposit_amount", "recharge_count", "total_calls", "answered_calls", "connection_rate", "target_completion"]
        display_cols = [c for c in display_cols if c in display_daily.columns]
        display_daily = display_daily[display_cols].sort_values("date", ascending=False)
        display_daily.columns = ["Date", "Agents", "Deposit Amt", "Recharges", "Total Calls", "Answered", "Conn Rate", "Target %"][:len(display_cols)]

        st.dataframe(display_daily, use_container_width=True, hide_index=True)
else:
    st.info("No daily trend data available")

st.markdown("---")

# =============================================================================
# Agent Rankings Table
# =============================================================================
st.markdown("### FTD Agent Rankings")

if not agent_metrics.empty:
    # Add rankings
    display_metrics = agent_metrics.copy()
    display_metrics["recharge_rank"] = display_metrics["recharge_count"].rank(ascending=False, method="min").astype(int)
    display_metrics["deposit_rank"] = display_metrics["deposit_amount"].rank(ascending=False, method="min").astype(int)

    # Sort by recharge count
    display_metrics = display_metrics.sort_values("recharge_count", ascending=False)

    # Format columns
    if "deposit_amount" in display_metrics.columns:
        display_metrics["deposit_amount"] = display_metrics["deposit_amount"].apply(lambda x: f"₱{x:,.2f}")
    if "recharge_count" in display_metrics.columns:
        display_metrics["recharge_count"] = display_metrics["recharge_count"].apply(lambda x: f"{int(x):,}")
    if "daily_target" in display_metrics.columns:
        display_metrics["daily_target"] = display_metrics["daily_target"].apply(lambda x: f"{int(x):,}")
    if "total_calls" in display_metrics.columns:
        display_metrics["total_calls"] = display_metrics["total_calls"].apply(lambda x: f"{int(x):,}")
    if "answered_calls" in display_metrics.columns:
        display_metrics["answered_calls"] = display_metrics["answered_calls"].apply(lambda x: f"{int(x):,}")
    if "connection_rate" in display_metrics.columns:
        display_metrics["connection_rate"] = display_metrics["connection_rate"].apply(lambda x: f"{x:.1f}%")
    if "target_completion" in display_metrics.columns:
        display_metrics["target_completion"] = display_metrics["target_completion"].apply(lambda x: f"{x:.1f}%")

    # Select columns for display
    display_cols = ["recharge_rank", "agent_name", "deposit_amount", "recharge_count", "daily_target", "target_completion", "total_calls", "answered_calls", "connection_rate"]
    display_cols = [c for c in display_cols if c in display_metrics.columns]
    display_metrics = display_metrics[display_cols]

    col_config = {
        "recharge_rank": "Rank",
        "agent_name": "Agent",
        "deposit_amount": "Deposit Amt",
        "recharge_count": "Recharges",
        "daily_target": "Target",
        "target_completion": "Target %",
        "total_calls": "Calls",
        "answered_calls": "Answered",
        "connection_rate": "Conn Rate"
    }

    st.dataframe(
        display_metrics,
        use_container_width=True,
        hide_index=True,
        column_config=col_config
    )

    # Export option
    with st.expander("Export Data"):
        csv = agent_metrics.to_csv(index=False)
        st.download_button(
            "Download FTD Data as CSV",
            data=csv,
            file_name=f"ftd_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
else:
    st.info("No agent metrics available")
