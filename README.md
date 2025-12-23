# JUAN365 Telesales Real-Time Dashboard

A real-time telesales performance dashboard built with Streamlit and Google Sheets API.

## Features

- **Real-time data** from Google Sheets with 5-minute auto-refresh
- **6 KPI Cards**: Recharge Count, Answered Calls, Conversion Rate, People Recalled, Answer Rate, Total Deposit
- **Multi-page dashboard**:
  - Overview: Team performance charts and daily trends
  - Team Details: Deep dive into individual team performance
  - Agent Details: Individual agent performance analysis
  - Rankings: Leaderboards and team comparisons
- **Filters**: Date range, Team, Agent
- **Visualizations**: Bar charts, line charts, radar charts
- **CSV Export**: Download filtered data

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Google Sheets Access

The credentials are pre-configured in `.streamlit/secrets.toml`.

Make sure the Google Sheet is shared with the service account email:
```
juan365-reporter@juan365-reporter.iam.gserviceaccount.com
```

### 3. Update Column Mapping

Edit `utils/data_processor.py` to map your actual column names:

```python
COLUMN_MAPPING = {
    "date": "YOUR_DATE_COLUMN",
    "agent_name": "YOUR_AGENT_COLUMN",
    "recharge_count": "YOUR_RECHARGE_COLUMN",
    "answered_calls": "YOUR_ANSWERED_CALLS_COLUMN",
    "total_calls": "YOUR_TOTAL_CALLS_COLUMN",
    "people_recalled": "YOUR_RECALLED_COLUMN",
    "total_deposit": "YOUR_DEPOSIT_COLUMN",
}
```

### 4. Run the Dashboard

```bash
streamlit run app.py
```

Or with custom port:

```bash
streamlit run app.py --server.port 8502
```

## Project Structure

```
telesales-dashboard/
├── .streamlit/
│   ├── config.toml          # Streamlit theme config
│   └── secrets.toml          # Google Sheets credentials
├── utils/
│   ├── __init__.py
│   ├── google_sheets.py      # Google Sheets API integration
│   ├── data_processor.py     # Data standardization
│   └── metrics.py            # KPI calculations
├── pages/
│   ├── 1_Overview.py         # Performance overview
│   ├── 2_Team_Details.py     # Team analysis
│   ├── 3_Agent_Details.py    # Agent analysis
│   └── 4_Rankings.py         # Leaderboards
├── app.py                    # Main dashboard
├── requirements.txt
├── .gitignore
└── README.md
```

## Team Sheets (11 Total)

| Sheet Name | Team | Team Leader | Type |
|------------|------|-------------|------|
| TL MIKE TEAM A | TEAM A | MIKE | RETENTION |
| TL PEARL TEAM B | TEAM B | PEARL | RETENTION |
| TL DEXTER TEAM C | TEAM C | DEXTER | RECALL |
| TL BOB TEAM D | TEAM D | BOB | RECALL |
| TL ONI TEAM E | TEAM E | ONI | RECALL |
| TL TRINA TEAM F | TEAM F | TRINA | RECALL |
| TL MIRRA TEAM G | TEAM G | MIRRA | VIP |
| TL JAYE TEAM H | TEAM H | JAYE | VIP |
| TL WINSON TEAM I | TEAM I | WINSON | VIP |
| TL ANDRE TEAM J | TEAM J | ANDRE | VIP |
| TL NICOLE TEAM K | TEAM K | NICOLE | VIP |

## KPI Definitions

| KPI | Description | Formula |
|-----|-------------|---------|
| Recharge Count | Total successful recharges | SUM(recharge_count) |
| Answered Calls | Total answered calls | SUM(answered_calls) |
| Conversion Rate | Recharges per answered call | recharge_count / answered_calls * 100 |
| People Recalled | Total people recalled | SUM(people_recalled) |
| Answer Rate | Calls answered vs total | answered_calls / total_calls * 100 |
| Total Deposit | Total deposits in PHP | SUM(total_deposit) |

## Currency

All monetary values are displayed in Philippine Peso (₱).

## Support

For issues or feature requests, contact the development team.
