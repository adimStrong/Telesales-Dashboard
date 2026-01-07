# Overview Sheet Integration Plan
## JUAN365 Telesales Dashboard - 2025 Data Integration

---

## Current System Analysis

### Architecture
- **Main Spreadsheet ID**: `1ZDRuNCnGKCqmnrq5kYUWF2NUL3DR2RnqBwUsTxPKfL8`
- **Contains**: 12 individual TL team sheets (TEAM A through TEAM L)
- **Data Fields**: date, agent_name, recharge_count, total_calls, not_connected, answered_calls, people_recalled
- **API**: gspread with service account authentication
- **Caching**: 5-minute TTL with Streamlit cache

### Known Issue
- July-October 2025 data not showing (only Nov-Dec appears)
- Individual TL sheets may not have historical data for earlier months

---

## Overview Sheet Details

- **Spreadsheet ID**: `1mVyLUfu2KN3SMltNiiZdw04ZvgUIQYsXyapv0YppsXU`
- **Sheet GID**: `33576148`
- **Purpose**: Consolidated 2025 data (likely contains July-December 2025)

**NOTE**: This is a DIFFERENT spreadsheet from the main TL sheets.

---

## Integration Options

### Option 1: Add Overview as Secondary Source (RECOMMENDED)

**Approach**: Load Overview sheet as additional data source, merge with TL data

**Pros**:
- No disruption to current TL sheet workflow
- Fills gaps for missing months (July-October)
- Maintains team-level granularity from TL sheets
- Easy to implement and test

**Cons**:
- Potential data duplication for Nov-Dec (needs deduplication logic)
- Two API calls (one per spreadsheet)

**Implementation Steps**:
1. Share Overview spreadsheet with service account: `telesales@juan365-reporter.iam.gserviceaccount.com`
2. Add Overview spreadsheet ID to secrets.toml
3. Create `load_overview_data()` function in google_sheets.py
4. Update `load_all_sheets_data()` to merge Overview + TL data
5. Add deduplication logic (prefer TL data for same date/agent)

---

### Option 2: Replace TL Sheets with Overview Only

**Approach**: Switch entirely to Overview spreadsheet

**Pros**:
- Single source of truth
- Simpler maintenance
- One API call

**Cons**:
- May lose team-level sheet organization
- Requires understanding Overview column structure
- Migration risk

---

### Option 3: Hybrid with Priority Logic

**Approach**: Use Overview for historical, TL for recent data

**Pros**:
- Best of both worlds
- Fresh daily data from TL sheets
- Complete historical from Overview

**Cons**:
- More complex logic
- Need date-based priority rules

---

## Recommended Implementation (Option 1)

### Step 1: Grant Access
Share the Overview spreadsheet with the service account email:
```
telesales@juan365-reporter.iam.gserviceaccount.com
```
Grant "Viewer" access.

### Step 2: Update secrets.toml
```toml
[spreadsheet]
spreadsheet_id = "1ZDRuNCnGKCqmnrq5kYUWF2NUL3DR2RnqBwUsTxPKfL8"

[overview_spreadsheet]
spreadsheet_id = "1mVyLUfu2KN3SMltNiiZdw04ZvgUIQYsXyapv0YppsXU"
sheet_name = "Overview"  # Adjust based on actual sheet name
```

### Step 3: Add Overview Loader Function
```python
@st.cache_data(ttl=300)
def load_overview_data() -> pd.DataFrame:
    """Load consolidated data from Overview spreadsheet"""
    try:
        client = get_sheets_client()
        if client is None:
            return pd.DataFrame()

        overview_id = st.secrets["overview_spreadsheet"]["spreadsheet_id"]
        sheet_name = st.secrets["overview_spreadsheet"]["sheet_name"]

        spreadsheet = client.open_by_key(overview_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        raw_values = worksheet.get_all_values()

        # Process with appropriate column mapping
        # (Need to verify Overview column structure first)
        df = standardize_overview_data(raw_values)
        return df

    except Exception as e:
        st.warning(f"Could not load Overview data: {e}")
        return pd.DataFrame()
```

### Step 4: Merge Logic
```python
def load_all_data_combined() -> pd.DataFrame:
    """Load from both sources and merge"""

    # Load TL sheets (current system)
    tl_data = load_all_sheets_data()

    # Load Overview sheet
    overview_data = load_overview_data()

    # Combine (Overview first, TL adds/updates)
    if overview_data.empty:
        return tl_data
    if tl_data.empty:
        return overview_data

    # Concatenate and remove duplicates
    combined = pd.concat([overview_data, tl_data], ignore_index=True)

    # Keep latest entry for same date + agent
    combined = combined.drop_duplicates(
        subset=['date', 'agent_name'],
        keep='last'
    )

    return combined
```

---

## Before Implementation: Required Info

Before implementing, we need to verify:

1. **Overview sheet column structure**: What columns/positions does it use?
2. **Does Overview have team/TL info?**: Or just agent data?
3. **Date format in Overview**: Same as TL sheets or different?
4. **Data completeness**: Does Overview have July-December or partial months?

---

## Quick Test: Verify Access

After sharing with service account, run this test:

```python
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file('path/to/key.json', scopes=[
    'https://www.googleapis.com/auth/spreadsheets.readonly'
])
client = gspread.authorize(creds)

# Test Overview access
spreadsheet = client.open_by_key('1mVyLUfu2KN3SMltNiiZdw04ZvgUIQYsXyapv0YppsXU')
worksheet = spreadsheet.get_worksheet_by_id(33576148)
print(worksheet.get_all_values()[:5])  # First 5 rows
```

---

## Timeline Estimate

| Task | Effort |
|------|--------|
| Share spreadsheet with service account | 2 min |
| Verify Overview structure | 10 min |
| Update secrets.toml | 2 min |
| Implement loader function | 15 min |
| Implement merge logic | 15 min |
| Test locally | 10 min |
| Deploy to Streamlit Cloud | 5 min |
| **Total** | **~1 hour** |

---

## Next Steps

1. **Immediate**: Share Overview spreadsheet with `telesales@juan365-reporter.iam.gserviceaccount.com`
2. **Then**: Examine Overview sheet structure (columns, date format, team info)
3. **Finally**: Implement the integration code

---

*Generated: 2026-01-07*
