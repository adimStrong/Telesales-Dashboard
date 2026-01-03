"""
Data Processing and Standardization Module
JUAN365 Telesales Dashboard - Position-Based Column Extraction
"""
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# COLUMN POSITIONS (0-indexed) - Based on ACTUAL DATA in November
# Headers don't match data positions - using user's original mapping
# =============================================================================
COLUMN_POSITIONS = {
    "date": 0,              # Column A
    "agent_name": 1,        # Column B
    "recharge_count": 3,    # Column D - Daily Recharge Count
    "total_calls": 7,       # Column H (data shows: 41)
    "not_connected": 11,    # Column L (data shows: 15)
    "answered_calls": 19,   # Column T (data shows: 26)
    "people_recalled": 20,  # Column U (data shows: 19)
}

# No date filter - show all data that exists in sheets




def standardize_data(raw_values: list) -> pd.DataFrame:
    """
    Extract data by column position and standardize types.

    Args:
        raw_values: List of lists from worksheet.get_all_values()
                   First row is headers, subsequent rows are data

    Returns:
        Standardized DataFrame with only the columns we need
    """
    if not raw_values or len(raw_values) < 2:
        return pd.DataFrame()

    # Skip header row, extract data rows only
    data_rows = raw_values[1:]

    # Build records by extracting specific columns by position
    data = []
    for row in data_rows:
        # Pad row if it's shorter than expected (26 columns = A-Z)
        if len(row) < 26:
            row = row + [''] * (26 - len(row))

        # Extract only the columns we need by position
        record = {}
        for field, col_idx in COLUMN_POSITIONS.items():
            record[field] = row[col_idx] if col_idx < len(row) else ''

        data.append(record)

    df = pd.DataFrame(data)

    # Remove completely empty rows
    df = df.replace('', pd.NA)
    df = df.dropna(how='all')

    # =========================================================================
    # Parse date column
    # =========================================================================
    if "date" in df.columns:
        # Use 2025 for short date formats (dates without year like "11/2")
        current_year = 2025

        def parse_date(date_str):
            if pd.isna(date_str) or not date_str:
                return pd.NaT

            date_str = str(date_str).strip()

            # Try full date formats first
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y"]:
                try:
                    return pd.to_datetime(date_str, format=fmt)
                except:
                    pass

            # Try short format (month/day) - assume current year
            try:
                parts = date_str.split("/")
                if len(parts) == 2:
                    month, day = int(parts[0]), int(parts[1])
                    return pd.Timestamp(year=current_year, month=month, day=day)
            except:
                pass

            # Fallback to pandas default
            try:
                return pd.to_datetime(date_str, errors="coerce")
            except:
                return pd.NaT

        df["date"] = df["date"].apply(parse_date)

    # =========================================================================
    # Convert numeric columns
    # =========================================================================
    numeric_cols = [
        "recharge_count", "total_calls", "not_connected", "answered_calls", "people_recalled"
    ]

    for col in numeric_cols:
        if col in df.columns:
            # Remove any currency symbols, commas, and whitespace
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(",", "", regex=False)
                df[col] = df[col].str.replace(" ", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # =========================================================================
    # Clean agent_name (trim whitespace)
    # =========================================================================
    if "agent_name" in df.columns:
        df["agent_name"] = df["agent_name"].astype(str).str.strip()
        # Remove empty agent names
        df = df[df["agent_name"] != ""]
        df = df[df["agent_name"] != "nan"]

    # All agents with data are considered present
    df["is_present"] = True

    return df


def filter_by_date_range(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Filter dataframe by date range"""
    if df.empty or "date" not in df.columns:
        return df

    mask = (df["date"] >= pd.Timestamp(start_date)) & (df["date"] <= pd.Timestamp(end_date))
    return df[mask]


def filter_by_team(df: pd.DataFrame, teams: list) -> pd.DataFrame:
    """Filter dataframe by team(s)"""
    if df.empty or "_team" not in df.columns or not teams:
        return df

    return df[df["_team"].isin(teams)]


def filter_by_agent(df: pd.DataFrame, agents: list) -> pd.DataFrame:
    """Filter dataframe by agent(s)"""
    if df.empty or "agent_name" not in df.columns or not agents:
        return df

    return df[df["agent_name"].isin(agents)]


def get_unique_agents(df: pd.DataFrame) -> list:
    """Get list of unique agents"""
    if df.empty or "agent_name" not in df.columns:
        return []

    return sorted(df["agent_name"].dropna().unique().tolist())


def get_unique_dates(df: pd.DataFrame) -> tuple:
    """Get min and max dates from dataframe"""
    if df.empty or "date" not in df.columns:
        return None, None

    valid_dates = df["date"].dropna()
    if valid_dates.empty:
        return None, None

    return valid_dates.min(), valid_dates.max()


def prepare_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare dataframe for CSV export"""
    if df.empty:
        return df

    export_df = df.copy()

    # Rename internal columns to friendly names
    rename_map = {
        "_team": "Team",
        "_team_leader": "Team Leader",
        "_sheet_name": "Source Sheet",
    }

    export_df = export_df.rename(columns=rename_map)

    # Format date
    if "date" in export_df.columns:
        export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")

    return export_df
