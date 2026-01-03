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

# Sheet configuration - All 12 TL sheets
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
def load_sheet_data(sheet_name: str, retry_count: int = 0) -> pd.DataFrame:
    """Load data from a single sheet using position-based extraction"""
    from utils.data_processor import standardize_data

    max_retries = 3

    try:
        client = get_sheets_client()
        if client is None:
            return pd.DataFrame()

        spreadsheet_id = st.secrets["spreadsheet"]["spreadsheet_id"]
        spreadsheet = client.open_by_key(spreadsheet_id)

        worksheet = spreadsheet.worksheet(sheet_name)

        # Get all values as raw list of lists
        raw_values = worksheet.get_all_values()

        if not raw_values or len(raw_values) < 2:
            return pd.DataFrame()

        # Pass raw values to standardize_data for position-based extraction
        df = standardize_data(raw_values)

        if df.empty:
            return pd.DataFrame()

        # Add metadata columns
        if sheet_name in SHEET_CONFIG:
            config = SHEET_CONFIG[sheet_name]
            df["_team"] = config["team"]
            df["_team_leader"] = config["tl"]
            df["_sheet_name"] = sheet_name

        return df

    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"Sheet '{sheet_name}' not found")
        return pd.DataFrame()
    except gspread.exceptions.APIError as e:
        if "429" in str(e) and retry_count < max_retries:
            # Rate limit hit - wait and retry with exponential backoff
            wait_time = (2 ** retry_count) * 10  # 10s, 20s, 40s
            time.sleep(wait_time)
            return load_sheet_data(sheet_name, retry_count + 1)
        st.error(f"Error loading sheet '{sheet_name}': {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)  # 5-minute cache
def load_all_sheets_data() -> pd.DataFrame:
    """Load and combine data from all TL sheets (or just test sheet)"""
    all_data = []

    if TEST_MODE:
        # Only load test sheet
        sheet_names = [TEST_SHEET]
        st.info(f"TEST MODE: Loading only {TEST_SHEET}")
    else:
        sheet_names = list(SHEET_CONFIG.keys())

    for i, sheet_name in enumerate(sheet_names):
        df = load_sheet_data(sheet_name)
        if not df.empty:
            all_data.append(df)
        # Add small delay between API calls to avoid rate limiting (1 sec between calls)
        if i < len(sheet_names) - 1:
            time.sleep(1)

    if not all_data:
        return pd.DataFrame()

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df


def get_available_sheets() -> list:
    """Get list of available sheet names"""
    return list(SHEET_CONFIG.keys())


def get_team_list() -> list:
    """Get list of all teams"""
    return [config["team"] for config in SHEET_CONFIG.values()]


def get_team_leaders() -> dict:
    """Get mapping of teams to team leaders"""
    return {config["team"]: config["tl"] for config in SHEET_CONFIG.values()}


def refresh_data():
    """Clear cache to force data refresh"""
    load_sheet_data.clear()
    load_all_sheets_data.clear()
    st.cache_data.clear()
