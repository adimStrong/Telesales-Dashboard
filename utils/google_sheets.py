"""
Google Sheets API Integration with 5-minute caching
Position-based data extraction - testing with ONE sheet first
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import time

# Sheet configuration - 2025 TL sheets (12 teams)
SHEET_CONFIG = {
    "TL MIKE TEAM A": {"team": "TEAM A", "tl": "MIKE"},
    "TL PEARL TEAM B": {"team": "TEAM B", "tl": "PEARL"},
    "TL DEXTER TEAM C": {"team": "TEAM C", "tl": "DEXTER"},
    "TL BOB TEAM D": {"team": "TEAM D", "tl": "BOB"},
    "TL ONI TEAM E": {"team": "TEAM E", "tl": "ONI"},
    "TL TRINA TEAM F": {"team": "TEAM F", "tl": "TRINA"},
    "TL MIRRA TEAM G": {"team": "TEAM G", "tl": "MIRRA"},
    "TL JAYE TEAM H": {"team": "TEAM H", "tl": "JAYE"},
    "TL WINSON TEAM I": {"team": "TEAM I", "tl": "WINSON"},
    "TL ANDRE TEAM J": {"team": "TEAM J", "tl": "ANDRE"},
    "TL NICOLE TEAM K": {"team": "TEAM K", "tl": "NICOLE"},
    "TL RUBY TEAM L": {"team": "TEAM L", "tl": "RUBY"},
}

# Sheet configuration - 2026 TL sheets (different TL assignments)
SHEET_CONFIG_2026 = {
    "TEAM A TL ONI": {"team": "TEAM A", "tl": "ONI"},
    "TEAM B TL ONI": {"team": "TEAM B", "tl": "ONI"},
    "TEAM C TL PEARL": {"team": "TEAM C", "tl": "PEARL"},
    "TEAM D TL PEARL": {"team": "TEAM D", "tl": "PEARL"},
    "TEAM E MIRRA": {"team": "TEAM E", "tl": "MIRRA"},
    "TEAM F MIRRA": {"team": "TEAM F", "tl": "MIRRA"},
    "TEAM G TL JAYE": {"team": "TEAM G", "tl": "JAYE"},
    "TEAM H TL JAYE": {"team": "TEAM H", "tl": "JAYE"},
    "TEAM I TL BOB": {"team": "TEAM I", "tl": "BOB"},
    "TEAM J TL WINSON": {"team": "TEAM J", "tl": "WINSON"},
    "TEAM K TEAM RUBY": {"team": "TEAM K", "tl": "RUBY"},
}

# FTD Team Sheet Configuration (2026 only)
FTD_SHEET_CONFIG = {
    "FTD TEAM ANDREI": {"team": "FTD TEAM", "tl": "ANDREI"},
}

# FOR TESTING: Only load one sheet (set to False to load all 11 sheets)
TEST_MODE = False
TEST_SHEET = "TL MIKE TEAM A"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]


@st.cache_resource
def get_sheets_client():
    """Initialize and cache the gspread client"""
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        return None


@st.cache_data(ttl=300)  # 5-minute cache
def load_sheet_data(sheet_name: str, year: int = 2025, retry_count: int = 0) -> pd.DataFrame:
    """Load data from a single sheet using position-based extraction"""
    from utils.data_processor import standardize_data

    max_retries = 3

    try:
        client = get_sheets_client()
        if client is None:
            return pd.DataFrame()

        # Select spreadsheet based on year
        if year == 2026:
            spreadsheet_id = st.secrets["spreadsheet_2026"]["spreadsheet_id"]
            sheet_config = SHEET_CONFIG_2026
        else:
            spreadsheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
            sheet_config = SHEET_CONFIG

        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)

        # Get all values as raw list of lists
        raw_values = worksheet.get_all_values()

        if not raw_values or len(raw_values) < 2:
            return pd.DataFrame()

        # Pass raw values to standardize_data with year for correct column positions
        df = standardize_data(raw_values, year=year)

        if df.empty:
            return pd.DataFrame()

        # Add metadata columns
        if sheet_name in sheet_config:
            config = sheet_config[sheet_name]
            df["_team"] = config["team"]
            df["_team_leader"] = config["tl"]
            df["_sheet_name"] = sheet_name

        return df

    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Sheet '{sheet_name}' not found in {year}")
        return pd.DataFrame()
    except gspread.exceptions.APIError as e:
        if "429" in str(e) and retry_count < max_retries:
            # Rate limit hit - wait and retry with exponential backoff
            wait_time = (2 ** retry_count) * 10  # 10s, 20s, 40s
            time.sleep(wait_time)
            return load_sheet_data(sheet_name, year, retry_count + 1)
        st.error(f"Error loading sheet '{sheet_name}': {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)  # 5-minute cache
def load_all_sheets_data(years: list = None) -> pd.DataFrame:
    """Load and combine data from all TL sheets for specified years

    Args:
        years: List of years to load (e.g., [2025, 2026]). Default loads both.
    """
    if years is None:
        years = [2025, 2026]  # Load both by default

    all_data = []

    if TEST_MODE:
        # Only load test sheet from 2025
        sheet_names = [TEST_SHEET]
        st.info(f"TEST MODE: Loading only {TEST_SHEET}")
        df = load_sheet_data(TEST_SHEET, year=2025)
        if not df.empty:
            all_data.append(df)
    else:
        # Load 2025 data
        if 2025 in years:
            sheet_names_2025 = list(SHEET_CONFIG.keys())
            for i, sheet_name in enumerate(sheet_names_2025):
                df = load_sheet_data(sheet_name, year=2025)
                if not df.empty:
                    all_data.append(df)
                # Add small delay between API calls to avoid rate limiting
                if i < len(sheet_names_2025) - 1:
                    time.sleep(1)

        # Load 2026 data
        if 2026 in years:
            sheet_names_2026 = list(SHEET_CONFIG_2026.keys())
            for i, sheet_name in enumerate(sheet_names_2026):
                df = load_sheet_data(sheet_name, year=2026)
                if not df.empty:
                    all_data.append(df)
                # Add small delay between API calls to avoid rate limiting
                if i < len(sheet_names_2026) - 1:
                    time.sleep(1)

    if not all_data:
        return pd.DataFrame()

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df


@st.cache_data(ttl=300)  # 5-minute cache
def load_ftd_data(year: int = 2026, retry_count: int = 0) -> pd.DataFrame:
    """Load FTD team data from dedicated sheet

    Args:
        year: Data year (default 2026 - FTD sheet only exists in 2026)
        retry_count: Internal retry counter for rate limiting

    Returns:
        DataFrame with FTD team data
    """
    from utils.data_processor import standardize_ftd_data

    max_retries = 3

    try:
        client = get_sheets_client()
        if client is None:
            return pd.DataFrame()

        # FTD is only in 2026 spreadsheet
        spreadsheet_id = st.secrets["spreadsheet_2026"]["spreadsheet_id"]
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Load FTD TEAM ANDREI sheet
        sheet_name = "FTD TEAM ANDREI"
        worksheet = spreadsheet.worksheet(sheet_name)

        # Get all values as raw list of lists
        raw_values = worksheet.get_all_values()

        if not raw_values or len(raw_values) < 2:
            return pd.DataFrame()

        # Pass raw values to standardize_ftd_data
        df = standardize_ftd_data(raw_values, year=year)

        if df.empty:
            return pd.DataFrame()

        # Add metadata columns
        config = FTD_SHEET_CONFIG[sheet_name]
        df["_team"] = config["team"]
        df["_team_leader"] = config["tl"]
        df["_sheet_name"] = sheet_name

        return df

    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"FTD sheet not found in {year}")
        return pd.DataFrame()
    except gspread.exceptions.APIError as e:
        if "429" in str(e) and retry_count < max_retries:
            # Rate limit hit - wait and retry with exponential backoff
            wait_time = (2 ** retry_count) * 10
            time.sleep(wait_time)
            return load_ftd_data(year, retry_count + 1)
        st.error(f"Error loading FTD sheet: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading FTD sheet: {e}")
        return pd.DataFrame()


def refresh_ftd_data():
    """Clear FTD cache to force data refresh"""
    load_ftd_data.clear()


def get_available_sheets(year: int = None) -> list:
    """Get list of available sheet names"""
    if year == 2026:
        return list(SHEET_CONFIG_2026.keys())
    elif year == 2025:
        return list(SHEET_CONFIG.keys())
    else:
        # Return both
        return list(SHEET_CONFIG.keys()) + list(SHEET_CONFIG_2026.keys())


def get_team_list() -> list:
    """Get list of all teams (consistent across years)"""
    # Teams are same structure, just use 2025 as base
    teams = [config["team"] for config in SHEET_CONFIG.values()]
    return sorted(set(teams))


def get_team_leaders(year: int = None) -> dict:
    """Get mapping of teams to team leaders for specified year"""
    if year == 2026:
        return {config["team"]: config["tl"] for config in SHEET_CONFIG_2026.values()}
    elif year == 2025:
        return {config["team"]: config["tl"] for config in SHEET_CONFIG.values()}
    else:
        # Return combined with year info
        result = {}
        for config in SHEET_CONFIG.values():
            team = config["team"]
            result[f"{team} (2025)"] = config["tl"]
        for config in SHEET_CONFIG_2026.values():
            team = config["team"]
            result[f"{team} (2026)"] = config["tl"]
        return result


def get_all_tl_names() -> list:
    """Get list of all unique TL names across all years"""
    tl_names = set()
    for config in SHEET_CONFIG.values():
        tl_names.add(config["tl"])
    for config in SHEET_CONFIG_2026.values():
        tl_names.add(config["tl"])
    return sorted(tl_names)


def refresh_data():
    """Clear cache to force data refresh"""
    load_sheet_data.clear()
    load_all_sheets_data.clear()
    load_ftd_data.clear()
    st.cache_data.clear()
