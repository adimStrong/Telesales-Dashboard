"""
KPI and Metrics Calculation Module
Updated for JUAN365 Telesales Dashboard - Position-Based Extraction
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_active_agents_count(df: pd.DataFrame, days: int = 7) -> int:
    """
    Count unique active agents who are PRESENT and have records in the last N days.
    Uses full agent_name value for counting.
    """
    if df.empty or "agent_name" not in df.columns:
        return 0

    # Filter for present agents only
    if "is_present" in df.columns:
        present_df = df[df["is_present"] == True]
    else:
        present_df = df

    if present_df.empty:
        return 0

    # Check if date column exists and has valid data
    if "date" in present_df.columns and present_df["date"].notna().any():
        # Get the max date in the data as reference point
        max_date = present_df["date"].max()
        cutoff_date = max_date - timedelta(days=days)

        # Filter for records in the last N days
        recent_df = present_df[present_df["date"] >= cutoff_date]
    else:
        # If no date data, use all records
        recent_df = present_df

    if recent_df.empty:
        return 0

    # Count unique agent names
    return recent_df["agent_name"].nunique()


def format_peso(amount: float) -> str:
    """Format number as Philippine Peso"""
    if pd.isna(amount) or amount == 0:
        return "₱0.00"
    return f"₱{amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage"""
    if pd.isna(value):
        return "0.00%"
    return f"{value:.2f}%"


def format_number(value: float) -> str:
    """Format number with comma separators"""
    if pd.isna(value):
        return "0"
    return f"{value:,.0f}"


def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate all main KPIs from the dataframe

    KPIs (based on ACTUAL sheet structure):
    - active_agents: Count of unique agents with data in last 7 days
    - total_calls: SUM of total_calls
    - answered_calls: SUM of answered_calls
    - not_connected: SUM of not_connected
    - connection_rate: CALCULATED (answered_calls / total_calls) * 100
    - people_recalled: SUM of people_recalled (agents only, excluding TL)
    - vip_recalled: SUM of people_recalled from TL rows only
    - friend_added: SUM of friend_added (2026 only, 0 for 2025)
    - conversion_rate_calls: CALCULATED (answered_calls / total_calls) * 100
    - conversion_rate_recalled: CALCULATED (total_recalled / answered_calls) * 100
    """
    if df.empty:
        return {
            "active_agents": 0,
            "recharge_count": 0,
            "total_calls": 0,
            "answered_calls": 0,
            "not_connected": 0,
            "connection_rate": 0.0,
            "people_recalled": 0,
            "vip_recalled": 0,
            "friend_added": 0,
            "ftd_result": 0,
            "conversion_rate_calls": 0.0,
            "conversion_rate_recalled": 0.0,
        }

    # Count unique active agents with records in last 7 days
    active_agents = get_active_agents_count(df, days=7)

    # Sum metrics from columns
    recharge_count = int(df["recharge_count"].sum()) if "recharge_count" in df.columns else 0
    total_calls = int(df["total_calls"].sum()) if "total_calls" in df.columns else 0
    answered_calls = int(df["answered_calls"].sum()) if "answered_calls" in df.columns else 0
    not_connected = int(df["not_connected"].sum()) if "not_connected" in df.columns else 0
    friend_added = int(df["friend_added"].sum()) if "friend_added" in df.columns else 0

    # Separate TL and agent recalled metrics
    # VIP Recalled = TL rows only (agent_name contains "- TL " but NOT "- ATL ")
    if "agent_name" in df.columns and "people_recalled" in df.columns:
        # Match rows where agent_name contains "- TL " (Team Leader) but NOT "- ATL " (Assistant TL)
        is_tl = df["agent_name"].apply(
            lambda x: ("- TL " in str(x).upper() or " TL " in str(x).upper()) and "- ATL " not in str(x).upper()
        )

        # VIP Recalled = TL's people_recalled
        vip_recalled = int(df.loc[is_tl, "people_recalled"].sum())

        # People Recalled = Agents' people_recalled (excluding TL)
        people_recalled = int(df.loc[~is_tl, "people_recalled"].sum())
    else:
        # Fallback: no separation possible
        vip_recalled = 0
        people_recalled = int(df["people_recalled"].sum()) if "people_recalled" in df.columns else 0

    # Calculate FTD Result (ftd_count from FTD TEAM only, before Jan 6 2026)
    # After Jan 6, FTD team uses recharge instead of ftd_count
    ftd_result = 0
    ftd_as_recharge = 0
    if "_team" in df.columns and "ftd_count" in df.columns and "date" in df.columns:
        ftd_team_df = df[df["_team"] == "FTD TEAM"]
        if not ftd_team_df.empty:
            from datetime import datetime as dt
            jan6_2026 = pd.Timestamp(2026, 1, 6)
            # FTD Result = ftd_count before Jan 6
            ftd_before_jan6 = ftd_team_df[ftd_team_df["date"] < jan6_2026]
            ftd_result = int(ftd_before_jan6["ftd_count"].sum()) if not ftd_before_jan6.empty else 0
            # FTD after Jan 6 should be added to recharge
            ftd_after_jan6 = ftd_team_df[ftd_team_df["date"] >= jan6_2026]
            ftd_as_recharge = int(ftd_after_jan6["ftd_count"].sum()) if not ftd_after_jan6.empty else 0

    # Add FTD after Jan 6 to recharge count
    recharge_count = recharge_count + ftd_as_recharge

    # Calculate rates
    connection_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0.0
    conversion_rate_calls = (answered_calls / total_calls * 100) if total_calls > 0 else 0.0
    # Use total recalled (agents + TL) for conversion rate
    total_recalled = people_recalled + vip_recalled
    conversion_rate_recalled = (total_recalled / answered_calls * 100) if answered_calls > 0 else 0.0

    return {
        "active_agents": int(active_agents),
        "recharge_count": recharge_count,
        "total_calls": total_calls,
        "answered_calls": answered_calls,
        "not_connected": not_connected,
        "connection_rate": round(connection_rate, 2),
        "people_recalled": people_recalled,
        "vip_recalled": vip_recalled,
        "friend_added": friend_added,
        "ftd_result": ftd_result,
        "conversion_rate_calls": round(conversion_rate_calls, 2),
        "conversion_rate_recalled": round(conversion_rate_recalled, 2),
    }


def calculate_team_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate metrics grouped by team"""
    if df.empty or "_team" not in df.columns:
        return pd.DataFrame()

    # Build aggregation dict based on available columns
    agg_dict = {}
    col_mapping = {
        "agent_name": "nunique",  # Count unique agents
        "recharge_count": "sum",
        "total_calls": "sum",
        "answered_calls": "sum",
        "not_connected": "sum",
        "people_recalled": "sum",
        "friend_added": "sum",
    }

    for col, agg_func in col_mapping.items():
        if col in df.columns:
            agg_dict[col] = agg_func

    if not agg_dict:
        return pd.DataFrame()

    metrics = df.groupby("_team").agg(agg_dict).reset_index()

    # Rename columns
    rename_map = {
        "agent_name": "active_agents",
    }
    metrics = metrics.rename(columns=rename_map)

    # Calculate rates
    if "answered_calls" in metrics.columns and "total_calls" in metrics.columns:
        metrics["connection_rate"] = np.where(
            metrics["total_calls"] > 0,
            metrics["answered_calls"] / metrics["total_calls"] * 100,
            0
        )

    if "people_recalled" in metrics.columns and "answered_calls" in metrics.columns:
        metrics["conversion_rate_recalled"] = np.where(
            metrics["answered_calls"] > 0,
            metrics["people_recalled"] / metrics["answered_calls"] * 100,
            0
        )

    # Add team leader info
    if "_team_leader" in df.columns:
        tl_map = df.groupby("_team")["_team_leader"].first().to_dict()
        metrics["team_leader"] = metrics["_team"].map(tl_map)

    return metrics.rename(columns={"_team": "team"})


def calculate_agent_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate metrics grouped by agent"""
    if df.empty or "agent_name" not in df.columns:
        return pd.DataFrame()

    group_cols = ["agent_name"]
    if "_team" in df.columns:
        group_cols.append("_team")

    agg_dict = {}
    for col in ["recharge_count", "total_calls", "answered_calls", "not_connected", "people_recalled", "friend_added"]:
        if col in df.columns:
            agg_dict[col] = "sum"

    if not agg_dict:
        return pd.DataFrame()

    metrics = df.groupby(group_cols).agg(agg_dict).reset_index()

    # Calculate rates
    if "answered_calls" in metrics.columns and "total_calls" in metrics.columns:
        metrics["connection_rate"] = np.where(
            metrics["total_calls"] > 0,
            metrics["answered_calls"] / metrics["total_calls"] * 100,
            0
        )

    if "people_recalled" in metrics.columns and "answered_calls" in metrics.columns:
        metrics["conversion_rate_recalled"] = np.where(
            metrics["answered_calls"] > 0,
            metrics["people_recalled"] / metrics["answered_calls"] * 100,
            0
        )

    if "_team" in metrics.columns:
        metrics = metrics.rename(columns={"_team": "team"})

    return metrics


def calculate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate metrics grouped by date"""
    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    agg_dict = {}
    for col in ["recharge_count", "total_calls", "answered_calls", "not_connected", "people_recalled", "friend_added"]:
        if col in df.columns:
            agg_dict[col] = "sum"

    if not agg_dict:
        return pd.DataFrame()

    metrics = df.groupby("date").agg(agg_dict).reset_index()
    metrics = metrics.sort_values("date")

    return metrics


def get_top_performers(df: pd.DataFrame, metric: str = "answered_calls", top_n: int = 10) -> pd.DataFrame:
    """Get top N performers by specified metric"""
    agent_metrics = calculate_agent_metrics(df)

    if agent_metrics.empty or metric not in agent_metrics.columns:
        return pd.DataFrame()

    return agent_metrics.nlargest(top_n, metric)


def calculate_team_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate team vs team comparison metrics"""
    team_metrics = calculate_team_metrics(df)

    if team_metrics.empty:
        return pd.DataFrame()

    # Add rankings
    for metric in ["answered_calls", "connection_rate", "people_recalled"]:
        if metric in team_metrics.columns:
            team_metrics[f"{metric}_rank"] = team_metrics[metric].rank(ascending=False, method="min").astype(int)

    return team_metrics.sort_values("answered_calls", ascending=False)


def calculate_daily_attendance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily attendance summary.
    Returns DataFrame with date, total_agents, present, absent counts.
    """
    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    # Group by date and count attendance
    daily_data = []

    for date in df["date"].dropna().unique():
        date_df = df[df["date"] == date]

        total = date_df["agent_name"].nunique() if "agent_name" in date_df.columns else len(date_df)

        if "is_present" in date_df.columns:
            present = date_df[date_df["is_present"] == True]["agent_name"].nunique() if "agent_name" in date_df.columns else len(date_df[date_df["is_present"] == True])
            absent = total - present
        else:
            present = total
            absent = 0

        daily_data.append({
            "date": date,
            "total_agents": total,
            "present": present,
            "absent": absent,
            "attendance_rate": round((present / total * 100), 1) if total > 0 else 0
        })

    result = pd.DataFrame(daily_data)
    if not result.empty:
        result = result.sort_values("date")

    return result


# =============================================================================
# FTD (First Time Deposit) Team Metrics
# =============================================================================

def calculate_ftd_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate FTD-specific KPIs from the dataframe

    FTD KPIs:
    - active_agents: Count of unique FTD agents (excluding TL)
    - total_recharge: SUM of recharge_count
    - total_ftd: SUM of ftd_count (FTD Result)
    - total_calls: SUM of total_calls
    - answered_calls: SUM of answered_calls
    - not_connected: SUM of not_connected
    - social_media_added: SUM of social_media_added
    - connection_rate: CALCULATED (answered_calls / total_calls) * 100
    - ftd_conversion_rate: CALCULATED (ftd_count / answered_calls) * 100
    """
    from utils.data_processor import FTD_TEAM_LEADER

    if df.empty:
        return {
            "active_agents": 0,
            "total_recharge": 0,
            "total_ftd": 0,
            "total_calls": 0,
            "answered_calls": 0,
            "not_connected": 0,
            "social_media_added": 0,
            "connection_rate": 0.0,
            "ftd_conversion_rate": 0.0,
        }

    # Exclude TL from agent count
    agents_df = df[df["agent_name"] != FTD_TEAM_LEADER] if "agent_name" in df.columns else df

    # Count unique active agents (excluding TL)
    if "agent_name" in agents_df.columns:
        active_agents = agents_df["agent_name"].nunique()
    else:
        active_agents = 0

    # Sum metrics from columns (use full df for totals)
    total_recharge = int(df["recharge_count"].sum()) if "recharge_count" in df.columns else 0
    total_ftd = int(df["ftd_count"].sum()) if "ftd_count" in df.columns else 0
    total_calls = int(df["total_calls"].sum()) if "total_calls" in df.columns else 0
    answered_calls = int(df["answered_calls"].sum()) if "answered_calls" in df.columns else 0
    not_connected = int(df["not_connected"].sum()) if "not_connected" in df.columns else 0
    social_media_added = int(df["social_media_added"].sum()) if "social_media_added" in df.columns else 0

    # Calculate rates
    connection_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0.0
    ftd_conversion_rate = (total_ftd / answered_calls * 100) if answered_calls > 0 else 0.0

    return {
        "active_agents": int(active_agents),
        "total_recharge": total_recharge,
        "total_ftd": total_ftd,
        "total_calls": total_calls,
        "answered_calls": answered_calls,
        "not_connected": not_connected,
        "social_media_added": social_media_added,
        "connection_rate": round(connection_rate, 2),
        "ftd_conversion_rate": round(ftd_conversion_rate, 2),
    }


def calculate_ftd_agent_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate metrics grouped by FTD agent (excluding TL)"""
    from utils.data_processor import FTD_TEAM_LEADER

    if df.empty or "agent_name" not in df.columns:
        return pd.DataFrame()

    # Exclude TL from agent metrics
    df_agents = df[df["agent_name"] != FTD_TEAM_LEADER]

    if df_agents.empty:
        return pd.DataFrame()

    agg_dict = {}
    for col in ["recharge_count", "total_calls",
                "answered_calls", "not_connected", "social_media_added", "ftd_count"]:
        if col in df_agents.columns:
            agg_dict[col] = "sum"

    if not agg_dict:
        return pd.DataFrame()

    metrics = df_agents.groupby("agent_name").agg(agg_dict).reset_index()

    # Calculate rates
    if "answered_calls" in metrics.columns and "total_calls" in metrics.columns:
        metrics["connection_rate"] = np.where(
            metrics["total_calls"] > 0,
            metrics["answered_calls"] / metrics["total_calls"] * 100,
            0
        )

    if "ftd_count" in metrics.columns and "answered_calls" in metrics.columns:
        metrics["ftd_conversion_rate"] = np.where(
            metrics["answered_calls"] > 0,
            metrics["ftd_count"] / metrics["answered_calls"] * 100,
            0
        )

    return metrics


def calculate_ftd_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate FTD metrics grouped by date"""
    from utils.data_processor import FTD_TEAM_LEADER

    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    # Exclude TL from daily agent count
    df_agents = df[df["agent_name"] != FTD_TEAM_LEADER] if "agent_name" in df.columns else df

    agg_dict = {
        "agent_name": "nunique"  # Count unique agents per day (excluding TL)
    }
    for col in ["recharge_count", "total_calls",
                "answered_calls", "not_connected", "social_media_added", "ftd_count"]:
        if col in df.columns:
            agg_dict[col] = "sum"

    metrics = df_agents.groupby("date").agg(agg_dict).reset_index()
    metrics = metrics.rename(columns={"agent_name": "active_agents"})
    metrics = metrics.sort_values("date")

    # Calculate daily rates
    if "answered_calls" in metrics.columns and "total_calls" in metrics.columns:
        metrics["connection_rate"] = np.where(
            metrics["total_calls"] > 0,
            metrics["answered_calls"] / metrics["total_calls"] * 100,
            0
        )

    if "ftd_count" in metrics.columns and "answered_calls" in metrics.columns:
        metrics["ftd_conversion_rate"] = np.where(
            metrics["answered_calls"] > 0,
            metrics["ftd_count"] / metrics["answered_calls"] * 100,
            0
        )

    return metrics


def get_ftd_top_performers(df: pd.DataFrame, metric: str = "recharge_count", top_n: int = 10) -> pd.DataFrame:
    """Get top N FTD performers by specified metric"""
    agent_metrics = calculate_ftd_agent_metrics(df)

    if agent_metrics.empty or metric not in agent_metrics.columns:
        return pd.DataFrame()

    return agent_metrics.nlargest(top_n, metric)
