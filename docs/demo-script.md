# Wind Intelligence demo script

## Part 1 — Client presentation (maximum 5 minutes)

1. Explain the procurement problem: wind output is uncertain, so the team needs to understand the forecast available at a historical decision cutoff.
2. Open **Overview** and select a January 2026 delivery day. Point out whether the sidebar says live Elexon or clearly labelled demo mode and inspect the forecast-versus-actual chart. In real mode the chart uses 24 hourly common-resolution intervals; demo mode uses its synthetic half-hour fixture.
3. Explain MAE, RMSE, signed bias, normalized MAE, sample count, and coverage. Emphasize that these describe wind forecast uncertainty rather than procurement cost or demand shortfall.
4. Open **Forecast Accuracy** and show the aggregate metrics and CSV export.
5. Open **Forecast History** and explain that forecasts after the configured cutoff must not be used for the decision-time evaluation.
6. Open **Methodology** and show the source datasets, timestamp rules, missing-data handling, and demo-data limitation.

## Part 2 — Technical review (maximum 5 minutes)

1. Show the repository structure: FastAPI services, React/Vite frontend, tests, Docker files, and configuration.
2. Demonstrate the API documentation at `/docs` and call `/api/health`, `/api/dates`, `/api/analysis`, `/api/accuracy`, `/api/forecast-history`, and `/api/export.csv`.
3. Explain the cutoff-selection flow: normalize timestamps, retain publications at or before the cutoff, and choose the latest eligible publication.
4. Explain metric validation: only finite matched forecast/actual pairs are included; missing records are reported rather than treated as zero; zero actuals do not produce unstable percentage ratios.
5. Run the backend tests and frontend production build.
6. Show Docker Compose and explain the Vercel frontend / Render backend deployment shape.
7. Close with known limitations: demo mode is synthetic, live Elexon historical publication availability must be verified in the deployment environment, and the product does not calculate demand, prices, procurement volumes, or savings.

## Recording checklist

- [ ] Use an unlisted YouTube video under 10 minutes.
- [ ] Do not describe synthetic demo results as real January 2026 findings.
- [ ] Show the selected cutoff and timezone.
- [ ] Show a missing-data or limitation state if available.
- [ ] Capture the final public URL only after deployment is actually complete.
