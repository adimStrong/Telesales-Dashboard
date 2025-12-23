# JUAN365 Telesales Dashboard

A real-time telesales performance dashboard built with Streamlit, powered by Google Sheets API.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)

## Live Demo

**[View Dashboard](https://telesales-dashboard-kt6pdumn58ewaqgpxcxpht.streamlit.app/)**

---

## Features

- **Real-time Data** - Live connection to Google Sheets with auto-refresh
- **8 Key Metrics** - Active Agents, Recharge Count, Total Calls, Answered, Not Connected, Connection Rate, People Recalled, Recall Conv %
- **Multi-page Dashboard** - 5 interactive pages for different views
- **Smart Filtering** - Date range, team, and agent filters
- **Interactive Charts** - Plotly visualizations with hover details
- **CSV Export** - Download data for offline analysis
- **Responsive Design** - Works on desktop and mobile

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Main (app.py)** | KPIs, team overview, monthly/daily breakdowns |
| **Overview** | Trend charts, team performance comparison |
| **Team Details** | Individual team analysis, agent breakdown |
| **Agent Scorecard** | Agent performance, rankings, team comparison |
| **Leaderboard** | Top performers, team rankings, team vs team |

---

## Key Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| Active Agents | Unique agents in period | COUNT(DISTINCT agent_name) |
| Recharge Count | Daily recharge count | SUM(recharge_count) |
| Total Calls | All calls made | SUM(total_calls) |
| Answered Calls | Connected calls | SUM(answered_calls) |
| Not Connected | Failed connections | SUM(not_connected) |
| Connection Rate | Answer rate | answered / total * 100 |
| People Recalled | Callbacks received | SUM(people_recalled) |
| Recall Conv % | Callback conversion | recalled / answered * 100 |

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/adimStrong/Telesales-Dashboard.git
cd telesales-dashboard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Secrets
Create `.streamlit/secrets.toml`:
```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

### 4. Run Dashboard
```bash
streamlit run app.py
```

---

## Project Structure

```
telesales-dashboard/
├── app.py                    # Main dashboard
├── pages/
│   ├── 1_Overview.py         # KPI trends & team charts
│   ├── 2_Team_Details.py     # Team deep dive
│   ├── 3_Agent_Details.py    # Agent scorecard
│   └── 4_Rankings.py         # Leaderboard
├── utils/
│   ├── google_sheets.py      # Google Sheets API
│   ├── data_processor.py     # Data processing
│   └── metrics.py            # KPI calculations
├── assets/
│   └── logo.jpg              # Company logo
├── .streamlit/
│   ├── config.toml           # Theme config
│   └── secrets.toml          # Credentials (gitignored)
├── requirements.txt
├── CHANGELOG.md              # Recent changes
├── PROJECT_SUMMARY.md        # Detailed docs
└── README.md                 # This file
```

---

## Data Source

### Google Sheets Structure
Data is extracted by column position:

| Column | Data |
|--------|------|
| A | Date |
| B | Agent Name |
| D | Recharge Count |
| H | Total Calls |
| L | Not Connected |
| T | Answered Calls |
| U | People Recalled |

### Team Sheets (11 Teams)

| Team | Leader |
|------|--------|
| TEAM A | MIKE |
| TEAM B | PEARL |
| TEAM C | DEXTER |
| TEAM D | BOB |
| TEAM E | ONI |
| TEAM F | TRINA |
| TEAM G | MIRRA |
| TEAM H | JAYE |
| TEAM I | WINSON |
| TEAM J | ANDRE |
| TEAM K | NICOLE |

---

## Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect repo on [share.streamlit.io](https://share.streamlit.io)
3. Add secrets in dashboard settings
4. Deploy automatically on push

### Current Stats
- **Records:** 8,383
- **Agents:** 234-251
- **Teams:** 11
- **Date Range:** Nov 2 - Dec 22, 2025

---

## Recent Updates

See [CHANGELOG.md](CHANGELOG.md) for detailed changes.

**Latest (Dec 23, 2025):**
- Centered logo with page title
- Removed redundant metrics
- Smart daily trends (auto-expands for small date ranges)

---

## Tech Stack

- **Frontend:** Streamlit
- **Charts:** Plotly
- **Data:** Google Sheets API
- **Auth:** GCP Service Account
- **Hosting:** Streamlit Cloud

---

## License

JUAN365 Philippines - Internal Use

---

## Support

For issues or feature requests, contact the development team.
