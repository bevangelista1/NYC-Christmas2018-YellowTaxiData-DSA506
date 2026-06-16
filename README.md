# NYC Yellow Taxi Holiday Dashboard — DSA506 Project 1

This repository contains a Streamlit Cloud dashboard for DSA506 Project 1 using 2018 NYC Yellow Taxi trip records filtered to Christmas Eve–Christmas Day 2018.

## Project concept
The dashboard uses the QUEST framework: Question, Understand, Explore, Study, Tell.

**Audience:** non-technical transportation planning / taxi operations audience.  
**Decision context:** understand holiday taxi demand, fare patterns, trip characteristics, recorded tipping behavior, and geographic movement patterns.

## Important update: TLC taxi zone lookup
The dashboard now joins the TLC taxi zone lookup table to the trip data. The trip file contains `PULocationID` and `DOLocationID`; the lookup table translates those IDs into readable fields: `Borough`, `Zone`, and `service_zone`.

The app joins the lookup table twice:
- `PULocationID` → pickup borough/zone fields
- `DOLocationID` → dropoff borough/zone fields

This allows the dashboard to show top pickup zones, top dropoff zones, pickup/dropoff borough filters, and a pickup-borough vs. dropoff-borough heatmap.

## Files
- `app.py` — Streamlit dashboard with TLC taxi zone lookup integration
- `taxi_christmas_2018_cleaned.csv.gz` — cleaned/enriched trip dataset derived from the Excel workbook
- `requirements.txt` — packages needed by Streamlit Cloud
- `written_summary_draft.md` — draft 2–3 page written summary updated for taxi zones
- `video_script.md` — short presentation script/story arc updated for taxi zones

## Streamlit Cloud deployment steps
1. Create a new GitHub repository, for example `nyc-taxi-holiday-dashboard`.
2. Upload `app.py`, `requirements.txt`, and `taxi_christmas_2018_cleaned.csv.gz` to the repository root.
3. Go to Streamlit Community Cloud and connect your GitHub account.
4. Select the repository and set the main file path to `app.py`.
5. Deploy and open the public app URL to verify it loads.

## Data notes
Rows in original filtered workbook: 309,751.  
Columns in cleaned trip-data file before Streamlit joins taxi zones: 26.  
Rows retained by the default plausible-trip logic: 306,558.  
Earliest pickup in file: 2018-12-24 00:00:00.  
Latest pickup in file: 2018-12-25 23:58:33.  

Original trip data source: NYC Taxi & Limousine Commission / NYC Open Data, 2018 Yellow Taxi Trip Data.  
Taxi zone lookup source used by the app: TLC taxi zone lookup CSV.
