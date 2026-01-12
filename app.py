"""
JUAN365 Telesales Real-Time Dashboard
Main Application Entry Point - Position-Based Column Extraction
Version: 2026-01-10 v2 - VIP Recalled metrics
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

from utils.google_sheets import load_all_sheets_data, refresh_data, get_team_list, get_all_tl_names
from utils.data_processor import (
    filter_by_date_range, filter_by_team,
    filter_by_agent, get_unique_agents, get_unique_dates
)
from utils.metrics import (
    calculate_kpis, format_peso, format_percentage, format_number,
    get_active_agents_count
)

# Page configuration
st.set_page_config(
    page_title="JUAN365 Telesales Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .kpi-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF6B35;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def render_kpi_cards(kpis: dict, year: int = 2026):
    """Render the main KPI cards"""
    # Row 1: TOTAL CALLS, ANSWERED CALLS, NOT CONNECTED, CONNECTION RATE
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Calls",
            value=format_number(kpis["total_calls"]),
        )

    with col2:
        st.metric(
            label="Answered Calls",
            value=format_number(kpis["answered_calls"]),
        )

    with col3:
        st.metric(
            label="Not Connected",
            value=format_number(kpis["not_connected"]),
        )

    with col4:
        st.metric(
            label="Connection Rate",
            value=format_percentage(kpis["connection_rate"]),
        )

    # Row 2: Active Agent, NO. OF RECALLED, VIP RECALLED, CONVERSION RATE
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Active Agents",
            value=format_number(kpis["active_agents"]),
        )

    with col2:
        st.metric(
            label="No. of Recalled",
            value=format_number(kpis["people_recalled"]),
        )

    with col3:
        st.metric(
            label="VIP Recalled",
            value=format_number(kpis.get("vip_recalled", 0)),
        )

    with col4:
        st.metric(
            label="Recall Conv %",
            value=format_percentage(kpis["conversion_rate_recalled"]),
        )

    # Row 3: Recharge Count, Friend Added, FTD Result (hide if 0)
    if year == 2026:
        ftd_result = kpis.get("ftd_result", 0)
        if ftd_result > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="Recharge Count",
                    value=format_number(kpis["recharge_count"]),
                )
            with col2:
                st.metric(
                    label="Friend Added",
                    value=format_number(kpis["friend_added"]),
                )
            with col3:
                st.metric(
                    label="FTD Result",
                    value=format_number(ftd_result),
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Recharge Count",
                    value=format_number(kpis["recharge_count"]),
                )
            with col2:
                st.metric(
                    label="Friend Added",
                    value=format_number(kpis["friend_added"]),
                )
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Recharge Count",
                value=format_number(kpis["recharge_count"]),
            )


def main():
    # Sidebar
    with st.sidebar:
        st.header("Filters")

        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True, type="primary"):
            refresh_data()
            st.rerun()

        # Auto-refresh toggle
        auto_refresh = st.toggle("Auto-refresh (5 min)", value=False)
        if auto_refresh:
            st.info("Data refreshes automatically every 5 minutes")

        st.markdown("---")

        # Year filter (single select to avoid TL confusion across years)
        st.subheader("Year")
        selected_year = st.radio(
            "Select Year",
            options=["2026", "2025"],
            index=0,  # Default to 2026 (current year)
            key="year_filter",
            horizontal=True
        )

    # Header with Logo - Centered
    logo_path = "assets/logo.jpg"
    if os.path.exists(logo_path):
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            img_col, text_col = st.columns([1, 4])
            with img_col:
                st.image(logo_path, width=80)
            with text_col:
                st.markdown('<h1 class="main-header">JUAN365 Telesales Dashboard</h1>', unsafe_allow_html=True)
    else:
        st.markdown('<h1 class="main-header">JUAN365 Telesales Dashboard</h1>', unsafe_allow_html=True)

    # Load data based on year selection (single year only)
    with st.spinner(f"Loading {selected_year} data from Google Sheets..."):
        year_int = int(selected_year)
        df = load_all_sheets_data(years=[year_int])

    if df.empty:
        st.warning("No data available. Please check your Google Sheets connection and sheet names.")
        st.info("Make sure the service account has access to the spreadsheet.")
        return

    # Get date range
    min_date, max_date = get_unique_dates(df)

    # Sidebar filters continued
    with st.sidebar:
        # Date range filter
        st.subheader("Date Range")
        if min_date and max_date:
            date_range = st.date_input(
                "Select dates",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date(),
                key="date_range"
            )
            if len(date_range) == 2:
                df = filter_by_date_range(df, date_range[0], date_range[1])
        else:
            st.info("No date data available")

        st.markdown("---")

        # Team filter
        st.subheader("Team Filter")
        all_teams = sorted(df["_team"].unique().tolist()) if "_team" in df.columns else []
        selected_teams = st.multiselect(
            "Select Teams",
            options=all_teams,
            default=all_teams,
            key="team_filter"
        )
        if selected_teams:
            df = filter_by_team(df, selected_teams)

        st.markdown("---")

        # TL (Team Leader) filter
        st.subheader("Team Leader Filter")
        all_tls = sorted(df["_team_leader"].unique().tolist()) if "_team_leader" in df.columns else []
        selected_tls = st.multiselect(
            "Select Team Leaders",
            options=all_tls,
            default=[],
            key="tl_filter",
            placeholder="All TLs"
        )
        if selected_tls:
            df = df[df["_team_leader"].isin(selected_tls)]

        st.markdown("---")

        # Agent filter
        st.subheader("Agent Filter")
        all_agents = get_unique_agents(df)
        selected_agents = st.multiselect(
            "Select Agents",
            options=all_agents,
            default=[],
            key="agent_filter",
            placeholder="All agents"
        )
        if selected_agents:
            df = filter_by_agent(df, selected_agents)

        st.markdown("---")

        # Data info
        st.subheader("Data Info")
        # Show data date range instead of system time
        if "date" in df.columns and not df["date"].isna().all():
            data_min = df["date"].min().strftime('%Y-%m-%d')
            data_max = df["date"].max().strftime('%Y-%m-%d')
            st.caption(f"Data range: {data_min} to {data_max}")
        else:
            st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"Total records: {len(df):,}")
        st.caption(f"Teams: {df['_team'].nunique() if '_team' in df.columns else 0}")
        # Count unique agents (by full name)
        total_agents = df["agent_name"].nunique() if "agent_name" in df.columns else 0
        st.caption(f"Agents: {total_agents}")

    # Main content
    if df.empty:
        st.warning("No data matches your filter criteria.")
        return

    # Calculate and display KPIs
    st.markdown("### Key Performance Indicators")
    kpis = calculate_kpis(df)
    render_kpi_cards(kpis, year=year_int)

    st.markdown("---")

    # Quick stats row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Teams Overview")
        if "_team" in df.columns:
            # Get all TL names for VIP Recalled separation
            from utils.google_sheets import SHEET_CONFIG, SHEET_CONFIG_2026
            all_tl_names = set()
            for config in SHEET_CONFIG.values():
                all_tl_names.add(config["tl"].upper())
            for config in SHEET_CONFIG_2026.values():
                all_tl_names.add(config["tl"].upper())

            team_data = []
            for team in sorted(df["_team"].unique()):
                team_df = df[df["_team"] == team]
                # Count unique agents
                agent_count = team_df["agent_name"].nunique() if "agent_name" in team_df.columns else 0
                # Sum metrics
                recharge = int(team_df["recharge_count"].sum()) if "recharge_count" in team_df.columns else 0
                total_calls = int(team_df["total_calls"].sum()) if "total_calls" in team_df.columns else 0
                answered = int(team_df["answered_calls"].sum()) if "answered_calls" in team_df.columns else 0
                not_conn = int(team_df["not_connected"].sum()) if "not_connected" in team_df.columns else 0
                friend_add = int(team_df["friend_added"].sum()) if "friend_added" in team_df.columns else 0

                # Separate TL recalled (VIP) from agent recalled
                if "people_recalled" in team_df.columns and "agent_name" in team_df.columns:
                    is_tl = team_df["agent_name"].apply(
                        lambda x: any(tl in str(x).upper() for tl in all_tl_names)
                    )
                    vip_recalled = int(team_df.loc[is_tl, "people_recalled"].sum())
                    people_recalled = int(team_df.loc[~is_tl, "people_recalled"].sum())
                else:
                    vip_recalled = 0
                    people_recalled = int(team_df["people_recalled"].sum()) if "people_recalled" in team_df.columns else 0

                # Calculate conversion rate using total recalled
                total_recalled = people_recalled + vip_recalled
                conv_rate = round((total_recalled / answered * 100), 1) if answered > 0 else 0

                row_data = {
                    "Team": team,
                    "TL": team_df["_team_leader"].iloc[0] if "_team_leader" in team_df.columns else "-",
                    "Agents": agent_count,
                    "Recharge": f"{recharge:,}",
                    "Total Calls": f"{total_calls:,}",
                    "Answered": f"{answered:,}",
                    "Not Connected": f"{not_conn:,}",
                    "Recalled": f"{people_recalled:,}",
                    "VIP Recalled": f"{vip_recalled:,}",
                }
                # Only add Friend Added for 2026
                if year_int == 2026:
                    row_data["Friend Added"] = f"{friend_add:,}"
                row_data["Recall Conv %"] = f"{conv_rate}%"
                team_data.append(row_data)
            team_summary = pd.DataFrame(team_data)
            st.dataframe(team_summary, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("### Monthly Data (click ➕ to expand)")

        if "date" in df.columns:
            # Group by month
            df_with_month = df.copy()
            df_with_month["month"] = df_with_month["date"].dt.to_period("M")

            # Get unique months sorted descending
            months = sorted(df_with_month["month"].unique(), reverse=True)

            for month in months:
                month_df = df_with_month[df_with_month["month"] == month]

                # Calculate month totals
                m_agents = month_df["agent_name"].nunique()
                m_recharge = month_df["recharge_count"].sum() if "recharge_count" in month_df.columns else 0
                m_calls = month_df["total_calls"].sum()
                m_answered = month_df["answered_calls"].sum()
                m_recalled = month_df["people_recalled"].sum()
                m_friend_add = month_df["friend_added"].sum() if "friend_added" in month_df.columns else 0
                m_conv_call = round(m_answered / m_calls * 100, 1) if m_calls > 0 else 0
                m_conv_recall = round(m_recalled / m_answered * 100, 1) if m_answered > 0 else 0

                # Month header with summary (Friend Added only for 2026)
                if year_int == 2026:
                    month_label = f"📅 {month} | Agents: {m_agents} | Recharge: {m_recharge:,} | Calls: {m_calls:,} | Answered: {m_answered:,} | Recalled: {m_recalled:,} | Friend+: {m_friend_add:,} | Conn: {m_conv_call}%"
                else:
                    month_label = f"📅 {month} | Agents: {m_agents} | Recharge: {m_recharge:,} | Calls: {m_calls:,} | Answered: {m_answered:,} | Recalled: {m_recalled:,} | Conn: {m_conv_call}%"

                with st.expander(month_label):
                    # Daily breakdown for this month
                    agg_dict = {
                        "agent_name": "nunique",
                        "total_calls": "sum",
                        "answered_calls": "sum",
                        "not_connected": "sum",
                        "people_recalled": "sum"
                    }
                    if "recharge_count" in month_df.columns:
                        agg_dict["recharge_count"] = "sum"
                    if "friend_added" in month_df.columns and year_int == 2026:
                        agg_dict["friend_added"] = "sum"
                    daily_df = month_df.groupby("date").agg(agg_dict).reset_index()

                    # Calculate conversion rates
                    daily_df["Connection Rate"] = daily_df.apply(
                        lambda row: f"{round(row['answered_calls'] / row['total_calls'] * 100, 1)}%"
                        if row['total_calls'] > 0 else "0%", axis=1
                    )
                    daily_df["Recall Conv %"] = daily_df.apply(
                        lambda row: f"{round(row['people_recalled'] / row['answered_calls'] * 100, 1)}%"
                        if row['answered_calls'] > 0 else "0%", axis=1
                    )

                    # Format date without time
                    daily_df["Date"] = daily_df["date"].dt.strftime("%Y-%m-%d")

                    # Format numbers with commas
                    daily_df["Agents"] = daily_df["agent_name"]
                    if "recharge_count" in daily_df.columns:
                        daily_df["Recharge"] = daily_df["recharge_count"].apply(lambda x: f"{x:,}")
                    daily_df["Total Calls"] = daily_df["total_calls"].apply(lambda x: f"{x:,}")
                    daily_df["Answered"] = daily_df["answered_calls"].apply(lambda x: f"{x:,}")
                    daily_df["Not Conn"] = daily_df["not_connected"].apply(lambda x: f"{x:,}")
                    daily_df["Recalled"] = daily_df["people_recalled"].apply(lambda x: f"{x:,}")
                    if "friend_added" in daily_df.columns and year_int == 2026:
                        daily_df["Friend Added"] = daily_df["friend_added"].apply(lambda x: f"{x:,}")

                    # Select display columns and sort by date
                    display_cols = ["Date", "Agents", "Total Calls", "Answered", "Not Conn", "Recalled", "Connection Rate", "Recall Conv %"]
                    if "Recharge" in daily_df.columns:
                        display_cols.insert(2, "Recharge")
                    if "Friend Added" in daily_df.columns and year_int == 2026:
                        display_cols.insert(-2, "Friend Added")
                    display_daily = daily_df[display_cols]
                    display_daily = display_daily.sort_values("Date", ascending=False)

                    st.dataframe(display_daily, use_container_width=True, hide_index=True)

    # By Team Section
    st.markdown("---")
    st.markdown("### By Team (click ➕ to expand)")

    if "_team" in df.columns:
        for team in sorted(df["_team"].unique()):
            team_df = df[df["_team"] == team]

            # Calculate team totals
            t_agents = team_df["agent_name"].nunique()
            t_recharge = team_df["recharge_count"].sum() if "recharge_count" in team_df.columns else 0
            t_calls = team_df["total_calls"].sum()
            t_answered = team_df["answered_calls"].sum()
            t_recalled = team_df["people_recalled"].sum()
            t_friend_add = team_df["friend_added"].sum() if "friend_added" in team_df.columns else 0
            t_conv_call = round(t_answered / t_calls * 100, 1) if t_calls > 0 else 0
            t_conv_recall = round(t_recalled / t_answered * 100, 1) if t_answered > 0 else 0
            t_tl = team_df["_team_leader"].iloc[0] if "_team_leader" in team_df.columns else "-"

            # Team label (Friend Added only for 2026)
            if year_int == 2026:
                team_label = f"👥 {team} (TL: {t_tl}) | Agents: {t_agents} | Recharge: {t_recharge:,} | Calls: {t_calls:,} | Answered: {t_answered:,} | Recalled: {t_recalled:,} | Friend+: {t_friend_add:,} | Conn: {t_conv_call}%"
            else:
                team_label = f"👥 {team} (TL: {t_tl}) | Agents: {t_agents} | Recharge: {t_recharge:,} | Calls: {t_calls:,} | Answered: {t_answered:,} | Recalled: {t_recalled:,} | Conn: {t_conv_call}%"

            with st.expander(team_label):
                # Agent breakdown for this team
                agg_dict = {
                    "total_calls": "sum",
                    "answered_calls": "sum",
                    "not_connected": "sum",
                    "people_recalled": "sum"
                }
                if "recharge_count" in team_df.columns:
                    agg_dict["recharge_count"] = "sum"
                if "friend_added" in team_df.columns and year_int == 2026:
                    agg_dict["friend_added"] = "sum"
                agent_df = team_df.groupby("agent_name").agg(agg_dict).reset_index()

                # Calculate conversion rates
                agent_df["Conn Rate"] = agent_df.apply(
                    lambda row: f"{round(row['answered_calls'] / row['total_calls'] * 100, 1)}%"
                    if row['total_calls'] > 0 else "0%", axis=1
                )
                agent_df["Recall Conv %"] = agent_df.apply(
                    lambda row: f"{round(row['people_recalled'] / row['answered_calls'] * 100, 1)}%"
                    if row['answered_calls'] > 0 else "0%", axis=1
                )

                # Format numbers with commas
                agent_df["Agent"] = agent_df["agent_name"]
                if "recharge_count" in agent_df.columns:
                    agent_df["Recharge"] = agent_df["recharge_count"].apply(lambda x: f"{x:,}")
                agent_df["Total Calls"] = agent_df["total_calls"].apply(lambda x: f"{x:,}")
                agent_df["Answered"] = agent_df["answered_calls"].apply(lambda x: f"{x:,}")
                agent_df["Not Conn"] = agent_df["not_connected"].apply(lambda x: f"{x:,}")
                agent_df["Recalled"] = agent_df["people_recalled"].apply(lambda x: f"{x:,}")
                if "friend_added" in agent_df.columns and year_int == 2026:
                    agent_df["Friend Added"] = agent_df["friend_added"].apply(lambda x: f"{x:,}")

                # Sort by total calls descending
                agent_df = agent_df.sort_values("total_calls", ascending=False)

                display_cols = ["Agent", "Total Calls", "Answered", "Not Conn", "Recalled", "Conn Rate", "Recall Conv %"]
                if "Recharge" in agent_df.columns:
                    display_cols.insert(1, "Recharge")
                if "Friend Added" in agent_df.columns and year_int == 2026:
                    display_cols.insert(-2, "Friend Added")
                display_agent = agent_df[display_cols]
                st.dataframe(display_agent, use_container_width=True, hide_index=True)

    # By Agent Section (All agents)
    st.markdown("---")
    st.markdown("### All Agents (click ➕ to expand)")

    with st.expander(f"📋 All {df['agent_name'].nunique()} Agents"):
        # All agents breakdown
        agg_dict = {
            "total_calls": "sum",
            "answered_calls": "sum",
            "not_connected": "sum",
            "people_recalled": "sum"
        }
        if "recharge_count" in df.columns:
            agg_dict["recharge_count"] = "sum"
        if "friend_added" in df.columns and year_int == 2026:
            agg_dict["friend_added"] = "sum"
        all_agents_df = df.groupby(["agent_name", "_team"]).agg(agg_dict).reset_index()

        # Calculate conversion rates
        all_agents_df["Conn Rate"] = all_agents_df.apply(
            lambda row: f"{round(row['answered_calls'] / row['total_calls'] * 100, 1)}%"
            if row['total_calls'] > 0 else "0%", axis=1
        )
        all_agents_df["Recall Conv %"] = all_agents_df.apply(
            lambda row: f"{round(row['people_recalled'] / row['answered_calls'] * 100, 1)}%"
            if row['answered_calls'] > 0 else "0%", axis=1
        )

        # Format numbers with commas
        all_agents_df["Agent"] = all_agents_df["agent_name"]
        all_agents_df["Team"] = all_agents_df["_team"]
        if "recharge_count" in all_agents_df.columns:
            all_agents_df["Recharge"] = all_agents_df["recharge_count"].apply(lambda x: f"{x:,}")
        all_agents_df["Total Calls"] = all_agents_df["total_calls"].apply(lambda x: f"{x:,}")
        all_agents_df["Answered"] = all_agents_df["answered_calls"].apply(lambda x: f"{x:,}")
        all_agents_df["Not Conn"] = all_agents_df["not_connected"].apply(lambda x: f"{x:,}")
        all_agents_df["Recalled"] = all_agents_df["people_recalled"].apply(lambda x: f"{x:,}")
        if "friend_added" in all_agents_df.columns and year_int == 2026:
            all_agents_df["Friend Added"] = all_agents_df["friend_added"].apply(lambda x: f"{x:,}")

        # Sort by total calls descending
        all_agents_df = all_agents_df.sort_values("total_calls", ascending=False)

        display_cols = ["Agent", "Team", "Total Calls", "Answered", "Not Conn", "Recalled", "Conn Rate", "Recall Conv %"]
        if "Recharge" in all_agents_df.columns:
            display_cols.insert(2, "Recharge")
        if "Friend Added" in all_agents_df.columns and year_int == 2026:
            display_cols.insert(-2, "Friend Added")
        display_all = all_agents_df[display_cols]
        st.dataframe(display_all, use_container_width=True, hide_index=True)

    # Footer
    st.markdown("---")
    st.caption("JUAN365 Telesales Dashboard | Real-time data from Google Sheets | Auto-refreshes every 5 minutes")


if __name__ == "__main__":
    main()
