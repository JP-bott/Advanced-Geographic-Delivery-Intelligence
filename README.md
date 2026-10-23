<p align="left"><img src="assets/nexroute_logo.svg" alt="NexRoute Logistics Intelligence" width="380"></p>

# Logistics & Delivery Performance Intelligence

**Python · SQL · pandas · GeoPandas · Plotly · Streamlit**  
**Author:** John Paul Torres  
**Scenario:** NexRoute Logistics, a **fictional** logistics operator in the Philippines, January 1, 2024 through December 31, 2025.

An interactive operations control tower for shipment reliability, courier efficiency, regional delivery patterns, service-level agreements and modeled shipping costs. This project is a data analyst / business intelligence portfolio exercise. **All operational records, couriers, hub identities and shipping costs are synthetic.**

## What the dashboard answers

| Workspace | Management questions |
| --- | --- |
| Operations Overview | How many shipments were processed? How frequently are they delivered on time? How does volume shift each month? |
| Geographic Delivery Analysis | Where are shipments concentrated? Which city centers are served? What are the busiest origin–destination corridors? |
| Courier Performance | Which couriers and vehicle groups have higher success and SLA compliance, once sample size is controlled? |
| SLA & Delay Analytics | Where do late delivered shipments arise? How large are delays? What failure reasons recur? |
| Shipping Cost Analysis | How do service type, distance, region and vehicle relate to fictional shipping expenses? |
| Shipment Explorer | Which records satisfy the filters, and what events belong to each specific shipment? |

## Run locally or in GitHub Codespaces

Requires Python **3.11+**. Open a terminal in the repository root:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. In Codespaces, select **Code → Codespaces → Create codespace on main**, then run the same commands. Streamlit port **8501** is configured for forwarding. Optional full regeneration:

```bash
python scripts/generate_data.py --shipments 26000
python scripts/load_database.py
python scripts/make_assets.py
python -m pytest tests -q
jupyter lab
```

The full downloadable project archive includes raw datasets and a built `database/logistics_analytics.db`. If fetching only source code, run the two data generation commands first. Once installed, shipment analytics and geographic city-point maps run without paid APIs or live data feeds. External fonts are a purely optional browser enhancement.

## Dataset, entity relationships and data engineering

Generated with fixed NumPy seed **20261107**, using 24 representative city locations and twelve fictional hubs spanning NCR, Central Luzon, CALABARZON, Central Visayas, Western Visayas and Davao Region.

| File | Grain / contents |
| --- | --- |
| `data/raw/shipments.csv` | 26,000 unique shipments, dates, status, SLA, destination, weight, simulated costs, geodesic distance |
| `data/raw/couriers.csv` | 60 fictional couriers, assigned regions, vehicle types |
| `data/raw/hubs.csv` | 12 fictional hub sites at representative actual city coordinates |
| `data/raw/delivery_events.csv` | 132,484 shipment events with timestamps and shipment references |
| `data/raw/sla_rules.csv` | 114 region- and service-specific calendar-day SLAs |
| `database/logistics_analytics.db` | Relational SQLite database rebuilt from the raw CSVs |
| `data/geo/city_centers.geojson` | 24 hand-curated representative geographic point features |

<img src="assets/database_schema.png" alt="Relational database schema: shipments linked to couriers, hubs, SLA rules, and delivery events" width="950">

The `shipments` fact table references `couriers`, `hubs`, and `sla_rules`. Tracking events reference shipments and hubs. Foreign keys, unique keys, CHECK constraints and query indexes enforce basic integrity. SQL scripts in `sql/analysis/` answer performance, SLA, cost, regional and courier questions, including CTEs and window functions (`LAG`, `ROW_NUMBER`, `RANK`).

## KPI definitions and exclusions

| Metric | Business rule |
| --- | --- |
| Delivery success % | `Delivered / (Delivered + Failed + Returned) × 100` |
| On-time delivery % | Delivered no later than expected calendar date / all delivered × 100 |
| Failed delivery % | Failed / (Delivered + Failed + Returned) × 100 |
| First-attempt success % | Delivered with exactly one attempt / all delivered × 100 |
| Average delivery days | Mean calendar days from dispatch to actual delivery for delivered shipments |
| Delay days | Positive integer calendar days between actual delivered date and expected date |
| Average days late | Mean delay among *late delivered* parcels only |
| Simulated cost / geographic km | Sum of synthetic shipping costs / sum of straight-line hub-to-city distances |

Cancelled and unresolved/in-transit parcels are **not** put into the resolved success-rate denominator. Returned parcels are resolved but not delivered. A parcel that was not delivered is never marked as on-time delivered. All historical status evaluation uses **December 31, 2025 23:59:59 (Philippine local time)** as the cutoff. SLAs count **calendar days beginning at dispatch**, not business days.

## Example calculated findings from the provided seed

- **26,000** shipments; **24,284** marked delivered (**94.77%** of 25,625 resolved shipments).
- **98.77%** of delivered parcels met the modeled deadline, and **88.30%** succeeded on the first attempt.
- **NCR** accounted for **10,865** shipments, the largest regional share.
- **Davao Region** had the lowest on-time-delivery rate of the covered regions, **97.66%**, and a simulated average shipping cost of **₱265.55**.
- **Recipient unavailable** was the most common failure reason, recorded for **346** failed parcels.
- **Pasig Distribution Center** handled the most modeled origin volume, **4,506** shipments.

These figures are **simulation outputs**, not observations about actual Philippine courier operations. Global dashboard filters recalculate the displayed results and insight text.

## Investigations worth prioritizing

Examine Davao Region route conditions and SLA fit before proposing added capacity. Review the share of attempted deliveries involving unavailable recipients and incorrect addresses. Compare couriers using shipment-count thresholds to reduce small-sample distortions. Assess the highest modeled cost corridors while controlling for route distance, service type and weight. These are possible avenues for investigation, not evidence of an intervention's effectiveness.

## Model design and geographical limitations

- Source locations are manually curated approximate city centers, not official geocoded postal addresses. The point file is original project data; no third-party boundary dataset is redistributed. **No fabricated provincial or regional polygon choropleth is included.**
- Geographic calculations use WGS84 geodesics via `pyproj.Geod`; they are **straight-line distances**, not real driving, marine, air or travel-time measures. Map links connect aggregate origin/destination points and are not routed paths.
- Shipping cost is modeled as `(₱49 + geographic_km × route_factor + weight_kg × ₱18) × service_factor × vehicle_factor × uniform_noise`, with route factor `0.85` for routes involving specified island regions and `0.57` for other routes. Service factors range **0.78–1.85**, vehicle factors **0.88–1.37**, and noise **0.92–1.08**. Cost is floored at ₱35. Delivery fees are a separate simulated markup. These amounts are not market quotations.
- Shipment volumes emphasize NCR; shopping seasons and courier-specific performance generate variability. Dispatch time, due dates and final outcomes obey consistent simulated rules. Failed and returned shipments have terminal event timestamps but **no actual delivery date**. Still-in-transit shipments remain unresolved at cutoff.
- No live vehicle GPS, historical meteorology, traffic congestion, street-routing engine or real commercial SLAs are available. The dataset should not be used for business or public policy decisions.
- The rendered dashboard screenshot is intentionally omitted if the dashboard cannot be launched in the build environment; visual assets are original logo and database schema rather than mock screenshots.

## Project layout

```text
app.py                         Streamlit control tower (six workspaces)
src/                           Reusable processing, KPI, SLA, geospatial, SQL, charts modules
scripts/generate_data.py       Fixed-seed operational simulation
scripts/load_database.py      Deterministic CSV → SQLite loader
scripts/make_assets.py        Original diagram and logo generation
sql/01_create_tables.sql       Constrained relational DDL
sql/02_create_indexes.sql      Analytical indexes
sql/analysis/                  Six multi-query operational analysis files
notebooks/logistics_delivery_analysis.ipynb  Reproducible exploratory notebook
data/raw/                      Five generated source CSVs
data/geo/                      Original city-point GeoJSON
assets/                        Logo, ERD and charts directory
tests/                         Data and KPI validation checks
.devcontainer/                 GitHub Codespaces setup
```

## Reproducibility and testing

Run `python -m pytest tests -q` after regenerating the default shipment count. Tests validate foreign keys, unique IDs, date ordering, SLA joins, dashboard KPI arithmetic, geographic ranges, status transitions, terminal tracking events and filtering. The notebook can be opened with Jupyter Lab or Codespaces. Plotly maps do not need a map-service token; browser/offline renderer behavior may vary by device and Plotly version.

## License

[MIT License](LICENSE) · © 2026 John Paul Torres

---

## Geographic Delivery Intelligence | Control Tower Upgrade

This project preserves the original Streamlit operations analytics at `app.py` and adds a three-panel React/TypeScript map workspace backed by FastAPI. The UX includes a narrow navigation rail, searchable paginated shipment monitor, filtered courier/region status analytics, selectable MapLibre vector layers, hub and corridor selection, an event-based bottom timeline, and a contextual detail panel. All views query the included SQLite dataset; there is no fabricated frontend dataset.

### Startup

```bash
python -m pip install -r requirements.txt
npm --prefix frontend install
python scripts/generate_data.py    # optional if shipped data already exists
python scripts/load_database.py    # optional if shipped SQLite database already exists
./run.sh
```

Open **http://localhost:5173** for the control tower. FastAPI runs on port **8000** and exposes interactive docs at `http://localhost:8000/docs`. You may still run the original app using `streamlit run app.py` on port **8501**. In GitHub Codespaces use the forwarded **5173** port. `./run.sh` starts the backend and frontend together; frontend calls `/api` through Vite's local development proxy.

### Map and analytics

- The default map renders an offline-safe Philippine **national geographic outline** from the bundled `data/geo/philippines_outline.geojson`. It does not depend on external map tiles, keys, or paid services. The source national outline originates in the packaged `countryinfo` world geography collection; its provenance and precision are limited. Destination positions are representative Philippine city centers.
- The switchable **hubs**, **clustered destination centers**, **aggregated origin-to-destination flows**, **geographic risk points**, and **city labels** overlay the map. Route arcs represent conceptual WGS84 point-to-point relationships, not actual vehicle tracks or roadway geometry.
- Administrative regional choropleth is **disabled** until a properly licensed, independently validated `data/geo/philippines_adm1.geojson` is supplied. The API `/api/geo/regions` declares this limitation explicitly rather than fabricating polygons. Regional comparisons and city markers work without it.
- SLA performance is measured only on delivered shipments, and delivery success excludes cancelled and in-transit records. API routes recalculate historical state from terminal tracking events available as of the reporting cutoff; the default cutoff is **December 31, 2025**.
- Risk is classified as **Completed** (on-time delivered), **Delayed** (late delivered or unresolved after SLA), **At Risk** (unresolved with one calendar day or less until SLA), **On Track** (more than one day remains), **Failed** (failed or returned), or **Cancelled** (cancelled). These are historical operational rules, not live predictions.
- Performance: destination records are aggregated at city centers, origin-destination flows are limited to 80 per response, and the shipment list is paginated (24 per page). Detailed events are downloaded only after choosing a shipment.

### API endpoints

`/api/health`, `/api/filters`, `/api/overview`, `/api/shipments`, `/api/shipments/{id}`, `/api/hubs`, `/api/hubs/{id}`, `/api/regions`, `/api/destinations`, `/api/routes`, `/api/sla-performance`, `/api/courier-performance`, `/api/geo/outline`, `/api/geo/regions`.

All reporting endpoints support start/end, destination region, courier, status, service, and reporting cutoff where relevant. API and original notebook reuse the same `src/` KPI feature-engineering modules.

### Verification and known limits

```bash
python -m pytest -q tests/
```

- Backend tests verify endpoint totals, filtration, chronological event histories, cutoff handling, geographic bounds, and original data reconciliation.
- Offline environments without a locally cached npm dependency tree cannot compile or browser-test the React frontend. In Codespaces, npm downloads the listed open-source dependencies on first installation.
- No historical vehicle GPS traces or recorded intermediate hub GPS coordinates are present, so no real-time position or intermediate vehicle route is implied.
- The bundled dataset is intentionally fictional and does not represent actual Philippine logistics providers or rates.

Author: **John Paul Torres** · MIT License · Copyright (c) 2026 John Paul Torres.
