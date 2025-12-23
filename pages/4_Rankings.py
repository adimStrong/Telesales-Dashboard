"""
JUAN365 Telesales Dashboard - Leaderboard Page
Rankings, top performers, and team comparisons
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.google_sheets import load_all_sheets_data, refresh_data
from utils.data_processor import (
    filter_by_date_range, get_unique_dates, prepare_export_data
)
from utils.metrics import (
    calculate_kpis, calculate_team_metrics, calculate_agent_metrics,
    get_top_performers, calculate_team_comparison,
    format_percentage, format_number
)

import os

st.set_page_config(
    page_title="Leaderboard | JUAN365 Telesales",
    page_icon="🏆",
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
            st.markdown('<h1 class="main-header">Leaderboard & Rankings</h1>', unsafe_allow_html=True)
else:
    st.markdown('<h1 class="main-header">Leaderboard & Rankings</h1>', unsafe_allow_html=True)

# Load data
with st.spinner("Loading data..."):
    df = load_all_sheets_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

# Sidebar
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

    # Ranking metric
    st.subheader("Ranking Options")
    ranking_metric = st.selectbox(
        "Rank By",
        ["total_calls", "answered_calls", "people_recalled", "conversion_rate_recalled"],
        format_func=lambda x: {
            "total_calls": "Total Calls",
            "answered_calls": "Answered Calls",
            "people_recalled": "People Recalled",
            "conversion_rate_recalled": "Recall Conv %"
        }.get(x, x)
    )

    top_n = st.slider("Top N Agents", 5, 30, 10)

    st.markdown("---")
    st.caption(f"Records: {len(df):,}")
    st.caption(f"Agents: {df['agent_name'].nunique() if 'agent_name' in df.columns else 0}")

# Check if data exists
if df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["🏅 Top Performers", "👥 Team Rankings", "⚔️ Team vs Team"])

with tab1:
    st.markdown("### Top Performers Leaderboard")

    top_agents = get_top_performers(df, metric=ranking_metric, top_n=top_n)

    if not top_agents.empty:
        # Leaderboard visualization
        metric_display = {
            "total_calls": "Total Calls",
            "answered_calls": "Answered Calls",
            "people_recalled": "People Recalled",
            "conversion_rate_recalled": "Recall Conv %"
        }.get(ranking_metric, ranking_metric)

        # Create medal colors
        colors = []
        for i in range(len(top_agents)):
            if i == 0:
                colors.append("#FFD700")  # Gold
            elif i == 1:
                colors.append("#C0C0C0")  # Silver
            elif i == 2:
                colors.append("#CD7F32")  # Bronze
            else:
                colors.append("#667eea")  # Regular

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=top_agents[ranking_metric].tolist()[::-1],
            y=top_agents["agent_name"].tolist()[::-1],
            orientation="h",
            marker_color=colors[::-1],
            text=[f"#{i+1}" for i in range(len(top_agents))][::-1],
            textposition="inside",
            textfont=dict(size=14, color="white")
        ))

        # Format x-axis labels based on metric type
        if ranking_metric == "conversion_rate_recalled":
            fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        else:
            fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside")

        fig.update_layout(
            title=f"Top {top_n} Agents by {metric_display}",
            xaxis_title=metric_display,
            yaxis_title="Agent",
            height=max(450, top_n * 35),
            margin=dict(l=0, r=50, t=50, b=0),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Leaderboard table
        st.markdown("### Leaderboard Details")

        display_df = top_agents.copy()
        display_df.insert(0, "Rank", range(1, len(display_df) + 1))

        # Add medals
        medals = ["🥇", "🥈", "🥉"] + [""] * (len(display_df) - 3)
        display_df.insert(0, "", medals[:len(display_df)])

        # Format columns
        if "total_calls" in display_df.columns:
            display_df["total_calls"] = display_df["total_calls"].apply(lambda x: f"{x:,}")
        if "answered_calls" in display_df.columns:
            display_df["answered_calls"] = display_df["answered_calls"].apply(lambda x: f"{x:,}")
        if "not_connected" in display_df.columns:
            display_df["not_connected"] = display_df["not_connected"].apply(lambda x: f"{x:,}")
        if "people_recalled" in display_df.columns:
            display_df["people_recalled"] = display_df["people_recalled"].apply(lambda x: f"{x:,}")
        if "connection_rate" in display_df.columns:
            display_df["connection_rate"] = display_df["connection_rate"].apply(lambda x: f"{x:.1f}%")
        if "conversion_rate_recalled" in display_df.columns:
            display_df["conversion_rate_recalled"] = display_df["conversion_rate_recalled"].apply(lambda x: f"{x:.1f}%")

        # Select display columns
        display_cols = ["", "Rank", "agent_name"]
        if "team" in display_df.columns:
            display_cols.append("team")
        display_cols.extend(["total_calls", "answered_calls", "people_recalled", "conversion_rate_recalled"])
        display_cols = [c for c in display_cols if c in display_df.columns]

        col_names = {
            "agent_name": "Agent",
            "team": "Team",
            "total_calls": "Total Calls",
            "answered_calls": "Answered",
            "people_recalled": "Recalled",
            "conversion_rate_recalled": "Recall Conv"
        }

        st.dataframe(
            display_df[display_cols].rename(columns=col_names),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No agent data available for ranking")

with tab2:
    st.markdown("### Team Rankings")

    team_comparison = calculate_team_comparison(df)

    if not team_comparison.empty:
        # Team ranking charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Teams by Total Calls")
            fig = px.bar(
                team_comparison.sort_values("total_calls", ascending=True),
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
                coloraxis_showscale=False
            )
            fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Teams by Recall Conv %")
            fig = px.bar(
                team_comparison.sort_values("conversion_rate_recalled", ascending=True),
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
                coloraxis_showscale=False
            )
            fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        # Team ranking table
        st.markdown("### Team Ranking Table")

        display_team = team_comparison.copy()

        # Format rank columns
        rank_cols = [col for col in display_team.columns if col.endswith("_rank")]
        for col in rank_cols:
            display_team[col] = display_team[col].apply(lambda x: f"#{int(x)}")

        # Format metrics
        if "total_calls" in display_team.columns:
            display_team["total_calls"] = display_team["total_calls"].apply(lambda x: f"{x:,}")
        if "answered_calls" in display_team.columns:
            display_team["answered_calls"] = display_team["answered_calls"].apply(lambda x: f"{x:,}")
        if "people_recalled" in display_team.columns:
            display_team["people_recalled"] = display_team["people_recalled"].apply(lambda x: f"{x:,}")
        if "connection_rate" in display_team.columns:
            display_team["connection_rate"] = display_team["connection_rate"].apply(lambda x: f"{x:.1f}%")
        if "conversion_rate_recalled" in display_team.columns:
            display_team["conversion_rate_recalled"] = display_team["conversion_rate_recalled"].apply(lambda x: f"{x:.1f}%")

        # Select and rename columns
        display_cols = ["team", "team_leader", "active_agents", "total_calls", "answered_calls", "people_recalled", "conversion_rate_recalled"]
        display_cols.extend([c for c in rank_cols if c in display_team.columns])
        display_cols = [c for c in display_cols if c in display_team.columns]

        col_names = {
            "team": "Team",
            "team_leader": "TL",
            "active_agents": "Agents",
            "total_calls": "Total Calls",
            "answered_calls": "Answered",
            "people_recalled": "Recalled",
            "conversion_rate_recalled": "Recall Conv",
            "answered_calls_rank": "Answered Rank",
            "connection_rate_rank": "Conn Rank",
            "people_recalled_rank": "Recalled Rank"
        }

        st.dataframe(
            display_team[display_cols].rename(columns=col_names),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No team data available")

with tab3:
    st.markdown("### Team vs Team Comparison")

    all_teams = sorted(df["_team"].unique().tolist()) if "_team" in df.columns else []

    if len(all_teams) >= 2:
        col1, col2 = st.columns(2)

        with col1:
            team1 = st.selectbox("Team 1", all_teams, index=0, key="team1_select")
        with col2:
            remaining_teams = [t for t in all_teams if t != team1]
            team2 = st.selectbox("Team 2", remaining_teams, index=0 if remaining_teams else None, key="team2_select")

        if team1 and team2:
            team1_df = df[df["_team"] == team1]
            team2_df = df[df["_team"] == team2]

            team1_kpis = calculate_kpis(team1_df)
            team2_kpis = calculate_kpis(team2_df)

            # Comparison metrics
            metrics = ["total_calls", "answered_calls", "not_connected",
                       "people_recalled", "connection_rate", "conversion_rate_recalled"]
            metric_labels = ["Total Calls", "Answered", "Not Connected",
                             "Recalled", "Connection %", "Recall Conv %"]

            comparison_data = {
                "Metric": metric_labels,
                team1: [team1_kpis[m] for m in metrics],
                team2: [team2_kpis[m] for m in metrics]
            }

            comparison_df = pd.DataFrame(comparison_data)

            # Radar chart - normalize values
            fig = go.Figure()

            max_vals = comparison_df[[team1, team2]].max(axis=1)
            normalized_team1 = (comparison_df[team1] / max_vals * 100).fillna(0)
            normalized_team2 = (comparison_df[team2] / max_vals * 100).fillna(0)

            fig.add_trace(go.Scatterpolar(
                r=normalized_team1.tolist() + [normalized_team1.iloc[0]],
                theta=comparison_df["Metric"].tolist() + [comparison_df["Metric"].iloc[0]],
                fill="toself",
                name=team1,
                line_color="#FF6B35",
                fillcolor="rgba(255, 107, 53, 0.3)"
            ))

            fig.add_trace(go.Scatterpolar(
                r=normalized_team2.tolist() + [normalized_team2.iloc[0]],
                theta=comparison_df["Metric"].tolist() + [comparison_df["Metric"].iloc[0]],
                fill="toself",
                name=team2,
                line_color="#667eea",
                fillcolor="rgba(102, 126, 234, 0.3)"
            ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=450,
                title=f"{team1} vs {team2} - Performance Comparison"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Side by side comparison
            st.markdown("### Head-to-Head Comparison")

            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                st.markdown(f"### {team1}")
                st.metric("Total Calls", format_number(team1_kpis["total_calls"]))
                st.metric("Answered", format_number(team1_kpis["answered_calls"]))
                st.metric("Recalled", format_number(team1_kpis["people_recalled"]))
                st.metric("Recall Conv", format_percentage(team1_kpis["conversion_rate_recalled"]))

            with col2:
                # Winner indicators
                st.markdown("---")

                # Determine winners
                calls_winner = team1 if team1_kpis["total_calls"] > team2_kpis["total_calls"] else team2
                recalled_winner = team1 if team1_kpis["people_recalled"] > team2_kpis["people_recalled"] else team2
                conv_winner = team1 if team1_kpis["conversion_rate_recalled"] > team2_kpis["conversion_rate_recalled"] else team2

                st.markdown(f"<h4 style='text-align:center'>📞 {calls_winner} leads in Total Calls</h4>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='text-align:center'>🔄 {recalled_winner} leads in People Recalled</h4>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='text-align:center'>📈 {conv_winner} has higher Recall Conv %</h4>", unsafe_allow_html=True)

                st.markdown("---")

            with col3:
                st.markdown(f"### {team2}")
                st.metric("Total Calls", format_number(team2_kpis["total_calls"]))
                st.metric("Answered", format_number(team2_kpis["answered_calls"]))
                st.metric("Recalled", format_number(team2_kpis["people_recalled"]))
                st.metric("Recall Conv", format_percentage(team2_kpis["conversion_rate_recalled"]))

            # Detailed comparison table
            st.markdown("### Metrics Comparison")

            comparison_display = comparison_df.copy()
            for col in [team1, team2]:
                comparison_display[col] = comparison_display.apply(
                    lambda row: format_percentage(row[col]) if "%" in row["Metric"] else format_number(row[col]),
                    axis=1
                )

            st.dataframe(comparison_display, use_container_width=True, hide_index=True)
    else:
        st.info("Need at least 2 teams for comparison")

# Export section
st.markdown("---")
st.markdown("### Export Data")

col1, col2 = st.columns(2)

with col1:
    export_df = prepare_export_data(df)
    csv_all = export_df.to_csv(index=False)
    st.download_button(
        label="📥 Download All Data as CSV",
        data=csv_all,
        file_name="juan365_telesales_data.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    if not top_agents.empty:
        csv_rankings = top_agents.to_csv(index=False)
        st.download_button(
            label="📥 Download Rankings as CSV",
            data=csv_rankings,
            file_name="juan365_rankings.csv",
            mime="text/csv",
            use_container_width=True
        )
