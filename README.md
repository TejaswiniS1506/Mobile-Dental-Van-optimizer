# Mobile Dental Van Scheduling Optimizer

> Built for UChicago Medicine's mobile dental program through the UChicago Policy Lab (Dec 2025 – Feb 2026)

**[Live Demo → click here to open the dashboard](https://mobile-dental-van-optimizer-ccnnsebff9kiks3zanxc2i.streamlit.app/)**


**[Interactive Model Architecture →](https://tejaswinis1506.github.io/Mobile-Dental-Van-optimizer/flowchart.html)**  

---

## What It Does

The Center for Health and Social Sciences at UChicago needed to answer a hard operational
question: where, when, and how often should a mobile dental clinic van be deployed across
Chicago to maximize patient reach while staying within cost and staffing constraints?

This model takes every relevant constraint — fuel cost, staff wages, shift hours, van capacity,
parking overhead, travel distance — and produces a ranked list of deployment locations. Rankings
are driven by two adjustable weights: patient volume (reach) and cost per acquisition (efficiency).
Shift the weight slider and every score, rank, and calendar entry recalculates instantly.

Built as a formal deliverable for the Harris Policy Lab, the dashboard is intentionally designed
for non-technical users — clinic leadership and operations staff can upload a CSV, adjust
parameters in the sidebar, and get a full deployment plan with no coding required.

---

## Features

- **Live fuel prices** pulled from the U.S. Energy Information Administration API
- **Haversine distance** calculation from base hospital to each site
- **Location-ranking model** scoring each site by patient volume vs. cost per acquisition
- **Financial sensitivity analysis** — see how CPA changes as wages and costs vary ±50%
- **Hospital traffic analysis** — EPIC appointment data identifies lowest-volume days for van deployment
- **Rolling deployment calendar** — dynamically assigns van to highest-demand site each day
- **Excel export** of full deployment plan and site rankings

---

## How to Run Locally
```bash
git clone https://github.com/TejaswiniS1506/Mobile-Dental-Van-optimizer.git
cd Mobile-Dental-Van-optimizer
pip install -r requirements.txt
streamlit run app.py
```

Upload a CSV with columns: `Name`, `Latitude`, `Longitude`, `Senior_Pop`

---

## Data Note

The original site location data is from UChicago Medicine and is not included in this repo.
Upload your own CSV to run the optimization on any set of locations.

### Expected CSV Schema

| Column | Description |
|--------|-------------|
| `SITE NAME` | Name of the deployment location |
| `ADDRESS` | Street address |
| `CITY`, `STATE`, `ZIP` | Location details |
| `seniors_x_coordinates` | Longitude of the site |
| `seniors_y_coordinates` | Latitude of the site |
| `hospital_name` | Closest UCM facility |
| `distance_from_hospital` | Distance from closest UCM facility (miles) |
| `Parking name` | Parking availability at the site |

Optional columns the model will use if present:
- `Senior_Pop` — estimated senior population at site (defaults to 200 if missing)
- `Parking_Distance_Meters` — walking distance from parking to site entrance

The app handles both the raw column names above and the cleaned versions
(`Latitude`, `Longitude`, `Name`, etc.) automatically.

---

## Tech Stack

`Python` · `Streamlit` · `Plotly` · `pandas` · `EIA API` · `Haversine`

---

## Author

**Tejaswini Shashidhar** — MPP Candidate, University of Chicago Harris School of Public Policy  
[LinkedIn](https://linkedin.com/in/tejaswini-shashidhar) · [GitHub](https://github.com/TejaswiniS1506)
