# JUAN365 Telesales Dashboard

## Project Summary

A real-time telesales performance dashboard built with Streamlit, connected to Google Sheets for live data updates. The dashboard provides comprehensive analytics for telesales teams, agents, and overall performance metrics.

---

## Live Demo

**URL:** https://telesales-dashboard-kt6pdumn58ewaqgpxcxpht.streamlit.app/

---

## Features

### Multi-Page Dashboard
1. **Main Dashboard (app.py)** - Overview with KPIs, team summary, monthly/daily breakdowns
2. **Overview Page** - KPI summary with trend charts and team performance
3. **Team Details** - Deep dive into individual team metrics and comparisons
4. **Agent Scorecard** - Individual agent performance tracking and rankings
5. **Leaderboard** - Top performers, team rankings, and team vs team comparisons

### Key Capabilities
- Real-time data from Google Sheets
- Date range filtering
- Team and agent filtering
- Interactive Plotly charts
- CSV export functionality
- Auto-refresh option (5 minutes)
- Mobile-responsive layout

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Charts | Plotly |
| Data Source | Google Sheets API |
| Authentication | GCP Service Account |
| Hosting | Streamlit Cloud |
| Version Control | GitHub |

---

## Project Structure

```
telesales-dashboard/
├── app.py                      # Main dashboard entry point
├── pages/
│   ├── 1_Overview.py           # KPI Summary & Trend Charts
│   ├── 2_Team_Details.py       # Team Performance Analysis
│   ├── 3_Agent_Details.py      # Agent Scorecard & Rankings
│   └── 4_Rankings.py           # Leaderboard & Comparisons
├── utils/
│   ├── google_sheets.py        # Google Sheets data loading
│   ├── data_processor.py       # Data filtering & processing
│   └── metrics.py              # KPI calculations
├── assets/
│   └── logo.jpg                # Company logo
├── requirements.txt            # Python dependencies
├── CHANGELOG.md                # Session changelog
└── PROJECT_SUMMARY.md          # This file
```

---

## Key Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| Active Agents | Unique agents in selected period | COUNT(DISTINCT agent_name) |
| Total Calls | All calls made | SUM(total_calls) |
| Answered Calls | Calls that connected | SUM(answered_calls) |
| Not Connected | Calls that didn't connect | SUM(not_connected) |
| Connection Rate | Call answer rate | answered_calls / total_calls |
| People Recalled | Customers who called back | SUM(people_recalled) |
| Recall Conv % | Recall conversion rate | people_recalled / answered_calls |

---

## Data Source

### Google Sheets Structure
- **Source:** Google Sheets with multiple team tabs
- **Columns Used (Position-Based):**
  - Column A: Date
  - Column B: Agent Name
  - Column H: Total Calls
  - Column L: Not Connected
  - Column T: Answered Calls
  - Column U: People Recalled

### Metadata Added
- `_team` - Team name (from sheet tab)
- `_team_leader` - Team leader name

---

## Pages Overview

### 1. Main Dashboard (app.py)
- 8 KPI cards (2 rows)
- Teams Overview table
- Monthly data expandable sections
- Team breakdown expandable sections
- All agents list

### 2. Overview Page
- 7 KPI cards
- Team Performance bar charts (Total Calls, Recall Conv %)
- Daily Trends line charts (Calls, Conversion Rates)
- Team Metrics Summary table
- Smart date filtering (expands to month for small ranges)

### 3. Team Details
- Team selector dropdown
- Team KPIs with team leader info
- Daily performance charts
- Agent breakdown within team
- All teams comparison
- Week-over-week analysis

### 4. Agent Scorecard
- Searchable agent selector
- Agent profile with team info
- Daily performance charts
- Comparison vs team average
- Rankings (overall and within team)
- Activity log

### 5. Leaderboard
- **Tab 1:** Top Performers with chart and table
- **Tab 2:** Team Rankings comparison
- **Tab 3:** Team vs Team radar chart
- CSV export buttons

---

## Deployment

### Streamlit Cloud Setup
1. Connected to GitHub repository
2. Secrets configured (GCP service account JSON)
3. Auto-deploy on push to main branch

### Environment Variables (Secrets)
```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
# ... other GCP credentials
```

---

## Recent Updates (Dec 23, 2025)

1. **Metrics Cleanup** - Removed redundant "Conv. Rate (Calls)", standardized to "Connection Rate"
2. **Logo Redesign** - Centered logo with title, removed from sidebar
3. **Smart Trends** - Daily trends chart auto-expands to month for small date ranges
4. **Documentation** - Added CHANGELOG.md and PROJECT_SUMMARY.md

---

## Performance Stats (Current Data)

- **Total Records:** 8,383
- **Active Agents:** 234-251
- **Teams:** 11
- **Total Calls:** ~2.9M
- **Answered Calls:** ~603K
- **Connection Rate:** ~20.8%
- **Recall Conv %:** ~24.1%
- **Date Range:** Nov 2 - Dec 22, 2025

---

## Repository

**GitHub:** https://github.com/adimStrong/Telesales-Dashboard

---

## Author

JUAN365 Philippines

---

*Built with Streamlit | Powered by Google Sheets*
