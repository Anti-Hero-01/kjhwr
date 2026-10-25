# Gridbricks Wind Intelligence

Wind Intelligence is a historical analytical pilot for evaluating UK wind-generation forecasts against observed wind generation. It uses only Elexon's `FUELHH` and `WINDFOR` datasets. It does **not** calculate electricity demand, prices, procurement volumes, savings, or a consumer shortfall.

## Current data status

The default local configuration is **demo mode**. Demo values are deterministic synthetic values and are visibly labelled in the UI; they must not be presented as January 2026 findings.

The Elexon integration has been validated against the public API on October 25, 2026:

- `FUELHH` returned January 2026 records when queried with `settlementDateFrom` and `settlementDateTo`.
- `FUELHH` records include `dataset`, `publishTime`, `startTime`, `settlementDate`, `settlementPeriod`, `fuelType`, and `generation`. The adapter keeps `fuelType == "WIND"` only.
- `WINDFOR` returned historical publication versions when queried with `publishDateTimeFrom` and `publishDateTimeTo`. Records include `dataset`, `publishTime`, `startTime`, and `generation`.
- The observed January response contains half-hourly actuals and hourly forecast targets. The application aggregates the two FUELHH MW observations within each UTC hour using an arithmetic mean, then matches at hourly `startTime`. This produces 24 defensible common-resolution intervals per delivery day.
- A full January retrieval returned 29,760 FUELHH rows, 1,488 WIND half-hour actual rows, and 19,272 WINDFOR publication rows. After hourly aggregation, the expected denominator is 744 hourly intervals. No selected forecast publication exceeded the cutoff.

The previous-day `10:00 Europe/London` cutoff is a configurable analytical assumption, not a claimed market rule. Change it through the API or environment configuration.

## Features

- Existing dark sidebar dashboard with Overview, Accuracy, Forecast History, and Methodology views.
- Delivery-date selector restricted to January 1–31, 2026.
- Configurable decision cutoff and timezone.
- Leakage-safe selection: for each delivery timestamp, choose the latest `publishTime <= previous-day cutoff`.
- Real Elexon mode with explicit upstream errors; it never falls back to synthetic metrics.
- Deterministic demo mode for development and screenshots.
- MAE, RMSE, signed bias, normalized MAE, MAPE excluding zero actuals, sample count, coverage, and missing counts.
- CSV export from the same backend result shown in the dashboard.
- Publication-version history, including selected and later versions where Elexon provides them.
- Real-data accuracy uses hourly common resolution; demo mode retains its half-hourly fixture resolution.

## API

Interactive documentation is available at `http://localhost:8000/docs`.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Mode and supported January range |
| `GET /api/dates` | Valid delivery dates |
| `GET /api/analysis?date=2026-01-15&cutoff=10:00&timezone=Europe/London` | Selected-day series, metadata, and metrics |
| `GET /api/accuracy?start_date=2026-01-01&end_date=2026-01-31&cutoff=10:00` | Aggregate January accuracy |
| `GET /api/forecast-history?date=2026-01-15&cutoff=10:00` | Selected forecasts plus retrieved publication versions |
| `GET /api/export.csv?date=2026-01-15&cutoff=10:00` | CSV generated from the analysis result |

All delivery-date requests outside January 2026 return a validation error. Elexon failures return an explicit 502 response with the upstream error; real mode never labels an empty or synthetic response as successful data.

## Local setup

### Demo mode

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONPATH="."
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Demo status is shown in the sidebar and analysis cards.

### Real Elexon mode

Set these values before starting the backend:

```powershell
$env:DEMO_MODE="false"
$env:ELEXON_BASE_URL="https://data.elexon.co.uk/bmrs/api/v1"
$env:DECISION_CUTOFF="10:00"
$env:TIMEZONE="Europe/London"
```

Then start Uvicorn as above. The first real request can retrieve the January response directly from Elexon and may take several seconds. The adapter uses the official stream endpoints and query parameters documented by Elexon. Check `/api/health`, then call `/api/analysis?date=2026-01-15`.

### Docker Compose

```powershell
docker compose up --build
```

The API is on `http://localhost:8000` and the frontend is on `http://localhost:5173`. Compose defaults to demo mode. Pass an environment file or edit the compose environment for real Elexon mode.

## Metrics and data handling

For valid matched pairs, with `e = forecast - actual`:

- MAE = mean(abs(e))
- RMSE = sqrt(mean(e²))
- Bias = mean(e); positive means overforecasting
- nMAE = MAE / mean(abs(actual)) × 100; unavailable when the denominator is zero
- MAPE = mean(abs(e) / abs(actual)) × 100 over non-zero actuals only

Missing forecasts, missing actuals, invalid numbers, and non-finite values are excluded from accuracy metrics and counted in the response. They are never converted to zero. The dashboard labels MAPE as excluding zero actuals.

## Tests and build

```powershell
cd backend
$env:PYTHONPATH="."
python -m pytest -q

cd ..\frontend
npm run build
```

The backend tests cover metrics, fixed January demo scope, cutoff equality and leakage prevention, API routes, and invalid values. The frontend build is a production Vite build.

## Repository structure

```text
backend/
  app/
    services/
      demo.py
      elexon.py
      forecast.py
      metrics.py
      selection.py
    routes.py
    schemas.py
  tests/
frontend/
  src/main.jsx
  src/styles.css
docker-compose.yml
```

## Deployment and limitations

The frontend can be deployed to Vercel and the backend can be deployed as a Docker/Python service on Render. Set `VITE_API_URL` to the public backend `/api` URL and configure backend CORS for the deployed frontend before publishing. No deployment has been performed or claimed here.

Historical publication access and forecast resolution are properties of the upstream Elexon response. This implementation reports the observed resolution, aggregates FUELHH to the common hourly resolution, and does not interpolate, duplicate, or substitute a later forecast. The cutoff default must be agreed with the customer before operational use.

