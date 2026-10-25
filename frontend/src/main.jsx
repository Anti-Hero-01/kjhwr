import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const fallbackDates = Array.from({ length: 31 }, (_, index) =>
  `2026-01-${String(index + 1).padStart(2, "0")}`);

async function request(path) {
  const response = await fetch(`${API}${path}`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

function App() {
  const [page, setPage] = useState("Overview");
  const [selectedDate, setSelectedDate] = useState("2026-01-15");
  const [cutoff, setCutoff] = useState("10:00");
  const [dates, setDates] = useState(fallbackDates);
  const [data, setData] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    request("/dates").then((body) => setDates(body.dates)).catch(() => setDates(fallbackDates));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError("");
    const encoded = `date=${selectedDate}&cutoff=${cutoff}&timezone=Europe/London`;
    Promise.all([request(`/analysis?${encoded}`), request(`/accuracy?start_date=2026-01-01&end_date=2026-01-31&cutoff=${cutoff}`)])
      .then(([analysis, summary]) => { setData(analysis); setAccuracy(summary); })
      .catch((reason) => { setData(null); setAccuracy(null); setError(reason.message); })
      .finally(() => setLoading(false));
  }, [selectedDate, cutoff]);

  useEffect(() => {
    if (page !== "Forecast History") return;
    request(`/forecast-history?date=${selectedDate}&cutoff=${cutoff}&timezone=Europe/London`)
      .then(setHistory).catch((reason) => setError(reason.message));
  }, [page, selectedDate, cutoff]);

  const chart = useMemo(() => (data?.points || []).map((point) => ({
    ...point, label: new Intl.DateTimeFormat("en-GB", {
      timeZone: "Europe/London", hour: "2-digit", minute: "2-digit",
    }).format(new Date(point.timestamp)),
  })), [data]);

  return <div className="app">
    <aside>
      <div className="brand"><span>✦</span> gridbricks</div>
      <div className="sub">WIND INTELLIGENCE</div>
      {["Overview", "Accuracy", "Forecast History", "Methodology"].map((item) =>
        <button key={item} className={page === item ? "active" : ""} onClick={() => setPage(item)}>{item}</button>)}
      <div className="side-note">SYSTEM STATUS
        <div className="status"><i /> {data?.metadata?.real_data ? "Live Elexon data" : "Demo mode active"}</div>
        <small>{data?.metadata?.source || "No data loaded"}</small>
      </div>
    </aside>
    <main>
      <header>
        <div><p className="eyebrow">OPERATIONS / {page.toUpperCase()}</p><h1>{page}</h1>
          <p className="muted">Decision-time wind forecast intelligence for January 2026.</p></div>
        <a className="export" href={`${API}/export.csv?date=${selectedDate}&cutoff=${cutoff}&timezone=Europe/London`}>↓ Export CSV</a>
      </header>
      <section className="controls panel">
        <label>Delivery date <select value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)}>
          {dates.map((date) => <option key={date}>{date}</option>)}
        </select></label>
        <label>Decision cutoff <input type="time" value={cutoff} onChange={(event) => setCutoff(event.target.value)} /></label>
        <span className="pill">Europe/London · configurable assumption</span>
      </section>
      {loading && <section className="panel info"><h2>Loading analysis…</h2><p>Retrieving the selected delivery day and applying the publication cutoff.</p></section>}
      {error && <section className="panel info error"><h2>Data unavailable</h2><p>{error}</p><p>Real-data mode never substitutes demo values after an Elexon failure.</p></section>}
      {!loading && !error && page === "Overview" && <Overview data={data} chart={chart} />}
      {!loading && !error && page === "Accuracy" && <Accuracy data={accuracy} />}
      {!loading && !error && page === "Forecast History" && <History data={history} />}
      {page === "Methodology" && <Methodology realData={data?.metadata?.real_data} />}
    </main>
  </div>;
}

function Overview({ data, chart }) {
  const metrics = data?.metrics || {};
  return <><section className="cards">
    <Card label="MAE" value={metrics.mae_mw} unit="MW" detail={`${metrics.sample_count || 0} matched intervals`} />
    <Card label="RMSE" value={metrics.rmse_mw} unit="MW" detail="Penalises larger errors" />
    <Card label="BIAS" value={metrics.bias_mw} unit="MW" detail="Positive = overforecast" />
    <Card label="nMAE" value={metrics.nmae_percent} unit="%" detail="Normalised by mean actual" />
    <Card label="COVERAGE" value={metrics.coverage_percent} unit="%" detail={`${metrics.expected_count || 0} expected intervals`} />
  </section>
  <section className="panel chart"><div className="panel-head"><div><h2>Decision-time forecast vs actual</h2><p className="muted">Only matched finite pairs contribute to metrics.</p></div><span className="pill">{data?.mode} mode</span></div>
    <ResponsiveContainer width="100%" height={330}><LineChart data={chart}><CartesianGrid stroke="#26364a" vertical={false} /><XAxis dataKey="label" stroke="#7890a8" /><YAxis stroke="#7890a8" /><Tooltip contentStyle={{ background: "#142235", border: "1px solid #2c425a" }} /><Line type="monotone" dataKey="actual_mw" stroke="#32d399" dot={false} name="Actual MW" /><Line type="monotone" dataKey="forecast_mw" stroke="#f9b44d" dot={false} name="Forecast MW" /></LineChart></ResponsiveContainer>
  </section></>;
}

function Accuracy({ data }) {
  const metrics = data?.metrics || {};
  return <section className="panel info"><h2>January accuracy summary</h2><p>Aggregated over valid matched intervals. MAPE excludes zero actuals and is not used as the primary metric.</p>
    <div className="method-grid"><Info title="MAE">{metrics.mae_mw ?? "—"} MW · n={metrics.sample_count}</Info><Info title="RMSE">{metrics.rmse_mw ?? "—"} MW · n={metrics.sample_count}</Info><Info title="Bias">{metrics.bias_mw ?? "—"} MW</Info><Info title="MAPE">{metrics.mape_percent ?? "—"}% · zero actuals excluded</Info><Info title="Completeness">{metrics.coverage_percent}% · missing forecasts: {metrics.missing_forecast_count}</Info></div>
  </section>;
}

function History({ data }) {
  if (!data) return <section className="panel info"><h2>No history loaded</h2><p>Select a delivery date to inspect publication versions.</p></section>;
  return <section className="panel info"><h2>Forecast publication history</h2><p>Selected version is the latest publication at or before the cutoff. Later versions are never used.</p>
    <table><thead><tr><th>Delivery</th><th>Publication</th><th>Forecast MW</th><th>Actual MW</th><th>Status</th></tr></thead><tbody>
      {data.publication_versions.map((version, index) => {
        const point = data.points.find((item) => item.timestamp === version.timestamp);
        const selected = version.selected;
        return <tr key={`${version.timestamp}-${version.publish_time}-${index}`}><td>{new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", dateStyle: "short", timeStyle: "short" }).format(new Date(version.timestamp))}</td><td>{new Date(version.publish_time).toISOString()}</td><td>{version.forecast_mw}</td><td>{point?.actual_mw ?? "—"}</td><td>{selected ? "SELECTED at cutoff" : version.eligible_at_cutoff ? "Eligible, not latest" : "Excluded after cutoff"}</td></tr>;
      })}
    </tbody></table>
  </section>;
}

function Card({ label, value, unit, detail }) { return <div className="card"><p>{label}</p><strong>{value == null ? "—" : value}<em>{value != null && unit}</em></strong><small>{detail}</small></div>; }
function Info({ title, children }) { return <div className="panel info"><h2>{title}</h2><p>{children}</p></div>; }
function Methodology({ realData }) { return <><Info title="Data source and status">{realData ? "Live Elexon BMRS data is active." : "Demo mode uses deterministic synthetic values and is not a January 2026 finding."} The permitted sources are FUELHH actual wind generation and WINDFOR forecasts.</Info><div className="method-grid"><Info title="Resolution">FUELHH is half-hourly; WINDFOR observations are hourly. Real-data analysis aggregates the two FUELHH values to an hourly arithmetic mean and compares at hourly UTC startTime. The real-data denominator is 24 intervals per delivery day.</Info><Info title="Cutoff">The default 10:00 Europe/London cutoff is a configurable analytical assumption. For each delivery day, publishTime is compared as an aware timestamp against the previous-day local cutoff.</Info><Info title="Limitations">No interpolation, duplication, or carry-forward is used. This pilot measures wind forecast uncertainty only; it does not calculate demand, prices, procurement volumes, savings, or cost.</Info></div></>; }

createRoot(document.getElementById("root")).render(<App />);
