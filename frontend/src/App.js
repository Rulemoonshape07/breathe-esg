import { useCallback, useEffect, useState } from "react";
import "./index.css";

const API = "https://breathe-esg-vdcu.onrender.com/api";

// ── helpers ──────────────────────────────────────────────────────────────────
const fmt = (n) => n == null ? "—" : Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 });
const scopeColor = { scope1: "#ff9f43", scope2: "#4db8ff", scope3: "#a29bfe" };
const scopeLabel = { scope1: "Scope 1", scope2: "Scope 2", scope3: "Scope 3" };
const statusColor = {
  pending: { bg: "rgba(255,209,102,0.12)", text: "#ffd166", dot: "#ffd166" },
  approved: { bg: "rgba(0,229,160,0.12)", text: "#00e5a0", dot: "#00e5a0" },
  rejected: { bg: "rgba(255,92,92,0.12)", text: "#ff5c5c", dot: "#ff5c5c" },
  suspicious: { bg: "rgba(255,92,92,0.18)", text: "#ff5c5c", dot: "#ff5c5c" },
};
const sourceIcon = { sap: "⬡", utility: "⚡", travel: "✈" };
const sourceLabel = { sap: "SAP", utility: "Utility", travel: "Travel" };

function Badge({ label, color, bg }) {
  return (
    <span style={{
      background: bg, color, fontSize: 11, fontWeight: 600,
      padding: "2px 8px", borderRadius: 99, letterSpacing: "0.04em",
      fontFamily: "DM Mono, monospace", textTransform: "uppercase",
      display: "inline-flex", alignItems: "center", gap: 5,
    }}>
      <span style={{ width: 5, height: 5, borderRadius: "50%", background: color, display: "inline-block" }} />
      {label}
    </span>
  );
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: "var(--surface)", border: "1px solid var(--border)",
      borderRadius: "var(--radius)", padding: "20px 22px",
      borderTop: `2px solid ${accent || "var(--border)"}`,
    }}>
      <div style={{ color: "var(--text2)", fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 8, fontFamily: "DM Mono, monospace" }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 800, color: accent || "var(--text)", lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ color: "var(--text3)", fontSize: 12, marginTop: 5 }}>{sub}</div>}
    </div>
  );
}

// ── Upload Panel ──────────────────────────────────────────────────────────────
function UploadPanel({ companies, onDone }) {
  const [company, setCompany] = useState("");
  const [source, setSource] = useState("sap");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const upload = async () => {
    if (!file || !company) return alert("Select company and file");
    setLoading(true); setResult(null);
    const fd = new FormData();
    fd.append("file", file);
    fd.append("source_type", source);
    fd.append("company_id", company);
    try {
      const r = await fetch(`${API}/ingestion/upload/`, { method: "POST", body: fd });
      const d = await r.json();
      setResult(d);
      onDone();
    } catch (e) { setResult({ error: e.message }); }
    setLoading(false);
  };

  const sampleCSVs = {
    sap: `PLANT,MATERIAL,DESCRIPTION,QUANTITY,UNIT,POSTING_DATE,DOC_NUMBER\nPLANT_HYD,DIESEL001,Diesel for generators,5000,L,01.01.2024,5000100001\nPLANT_HYD,PETROL002,Petrol for vehicles,1200,L,15.01.2024,5000100002\nPLANT_PUN,DIESEL001,Diesel DG set,8500,L,20.01.2024,5000100003`,
    utility: `METER_ID,ACCOUNT_NUMBER,BILLING_PERIOD_START,BILLING_PERIOD_END,CONSUMPTION_KWH,TARIFF_CATEGORY,LOCATION,BILL_NUMBER\nMH-001,ACC-2024-001,18/01/2024,17/02/2024,45000,HT-Commercial,Hyderabad Office,TPDDL/24/001\nMH-002,ACC-2024-002,18/01/2024,17/02/2024,32000,LT-Commercial,Pune Office,TPDDL/24/002`,
    travel: `EMPLOYEE_ID,TRAVEL_DATE,CATEGORY,ORIGIN,DESTINATION,DISTANCE_KM,TRANSPORT_MODE,HOTEL_NAME,NIGHTS\nEMP-001,15/01/2024,flight,HYD,DEL,1253,air,,\nEMP-001,15/01/2024,hotel,,,,,Taj Hotel Delhi,2\nEMP-002,20/01/2024,taxi,DEL,DEL,18,cab,,\nEMP-003,25/01/2024,flight,BOM,LHR,7200,air,,`,
  };

  const downloadSample = () => {
    const blob = new Blob([sampleCSVs[source]], { type: "text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = `sample_${source}.csv`; a.click();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <label style={labelStyle}>Company</label>
          <select value={company} onChange={e => setCompany(e.target.value)} style={inputStyle}>
            <option value="">— select —</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Data Source</label>
          <select value={source} onChange={e => setSource(e.target.value)} style={inputStyle}>
            <option value="sap">⬡ SAP — Fuel & Procurement</option>
            <option value="utility">⚡ Utility — Electricity</option>
            <option value="travel">✈ Travel — Concur/Navan</option>
          </select>
        </div>
      </div>

      <div>
        <label style={labelStyle}>CSV File</label>
        <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} style={{ ...inputStyle, cursor: "pointer" }} />
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <button onClick={upload} disabled={loading} style={btnStyle("#00e5a0", "#0a0e0f")}>
          {loading ? "Processing…" : "↑ Ingest Data"}
        </button>
        <button onClick={downloadSample} style={btnStyle("var(--border2)", "var(--text2)")}>
          ↓ Sample {source.toUpperCase()} CSV
        </button>
      </div>

      {result && (
        <div style={{ background: result.error ? "var(--red-dim)" : "var(--green-dim)", border: `1px solid ${result.error ? "var(--red)" : "var(--green)"}`, borderRadius: "var(--radius)", padding: "14px 16px", fontFamily: "DM Mono, monospace", fontSize: 12 }}>
          {result.error ? (
            <span style={{ color: "var(--red)" }}>✗ {result.error}</span>
          ) : (
            <div style={{ color: "var(--green)", display: "flex", flexDirection: "column", gap: 4 }}>
              <div>✓ Ingested — {result.rows_success} rows success · {result.rows_failed} failed · {result.rows_suspicious} flagged</div>
              {result.errors?.length > 0 && <div style={{ color: "var(--yellow)", marginTop: 4 }}>{result.errors.slice(0,3).map((e,i) => <div key={i}>⚠ {e}</div>)}</div>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const labelStyle = { display: "block", color: "var(--text3)", fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 6, fontFamily: "DM Mono, monospace" };
const inputStyle = { width: "100%", background: "var(--surface2)", border: "1px solid var(--border2)", borderRadius: "var(--radius)", padding: "9px 12px", color: "var(--text)", fontSize: 13, fontFamily: "Syne, sans-serif", outline: "none" };
const btnStyle = (bg, color) => ({ background: bg, color, border: "none", borderRadius: "var(--radius)", padding: "9px 18px", fontFamily: "Syne, sans-serif", fontWeight: 700, fontSize: 13, cursor: "pointer", transition: "opacity .15s" });

// ── Review Row ────────────────────────────────────────────────────────────────
function ReviewRow({ rec, onAction }) {
  const [note, setNote] = useState("");
  const [open, setOpen] = useState(false);
  const sc = statusColor[rec.status] || statusColor.pending;
  const act = async (action) => {
    const r = await fetch(`${API}/emissions/${rec.id}/${action}/`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviewed_by: "analyst", note }),
    });
    if (r.ok) onAction();
  };

  return (
    <div style={{ borderBottom: "1px solid var(--border)", padding: "0" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{ display: "grid", gridTemplateColumns: "40px 90px 80px 1fr 90px 110px 90px", alignItems: "center", padding: "12px 16px", gap: 12, cursor: "pointer", transition: "background .1s" }}
        onMouseEnter={e => e.currentTarget.style.background = "var(--surface2)"}
        onMouseLeave={e => e.currentTarget.style.background = ""}
      >
        <span style={{ color: "var(--text3)", fontFamily: "DM Mono, monospace", fontSize: 11 }}>#{rec.id}</span>
        <Badge label={rec.source_type.toUpperCase()} color={rec.source_type === "sap" ? "#ff9f43" : rec.source_type === "utility" ? "#4db8ff" : "#a29bfe"} bg={rec.source_type === "sap" ? "var(--orange-dim)" : rec.source_type === "utility" ? "var(--blue-dim)" : "rgba(162,155,254,0.12)"} />
        <Badge label={scopeLabel[rec.scope] || rec.scope} color={scopeColor[rec.scope] || "var(--text2)"} bg={`${scopeColor[rec.scope]}22` || "var(--surface2)"} />
        <div>
          <div style={{ fontWeight: 600, fontSize: 13 }}>{rec.category}</div>
          <div style={{ color: "var(--text3)", fontSize: 11, fontFamily: "DM Mono, monospace", marginTop: 2, maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{rec.description}</div>
        </div>
        <div style={{ textAlign: "right", fontFamily: "DM Mono, monospace" }}>
          <div style={{ fontSize: 13, fontWeight: 600 }}>{fmt(rec.raw_value)}</div>
          <div style={{ color: "var(--text3)", fontSize: 11 }}>{rec.raw_unit}</div>
        </div>
        <div style={{ textAlign: "right", fontFamily: "DM Mono, monospace" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#00e5a0" }}>{fmt(rec.normalized_value_kg_co2e)}</div>
          <div style={{ color: "var(--text3)", fontSize: 10 }}>kg CO₂e</div>
        </div>
        <Badge label={rec.status} color={sc.text} bg={sc.bg} />
      </div>

      {open && (
        <div style={{ background: "var(--surface2)", borderTop: "1px solid var(--border)", padding: "16px 20px", display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, fontSize: 12, fontFamily: "DM Mono, monospace" }}>
            <div><span style={{ color: "var(--text3)" }}>Source file: </span><span style={{ color: "var(--text2)" }}>{rec.source_file}</span></div>
            <div><span style={{ color: "var(--text3)" }}>Source row: </span><span style={{ color: "var(--text2)" }}>{rec.source_row}</span></div>
            <div><span style={{ color: "var(--text3)" }}>Ingested: </span><span style={{ color: "var(--text2)" }}>{new Date(rec.ingested_at).toLocaleDateString()}</span></div>
            <div><span style={{ color: "var(--text3)" }}>Period: </span><span style={{ color: "var(--text2)" }}>{rec.activity_period_start || "—"} → {rec.activity_period_end || "—"}</span></div>
            <div><span style={{ color: "var(--text3)" }}>Location: </span><span style={{ color: "var(--text2)" }}>{rec.location || "—"}</span></div>
            <div><span style={{ color: "var(--text3)" }}>Company: </span><span style={{ color: "var(--text2)" }}>{rec.company_name}</span></div>
          </div>
          {rec.flag_reason && (
            <div style={{ background: "var(--red-dim)", border: "1px solid rgba(255,92,92,0.3)", borderRadius: 6, padding: "10px 14px", color: "var(--red)", fontSize: 12, fontFamily: "DM Mono, monospace" }}>
              ⚠ {rec.flag_reason}
            </div>
          )}
          {rec.status === "pending" || rec.status === "suspicious" ? (
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <input placeholder="Review note (optional)…" value={note} onChange={e => setNote(e.target.value)}
                style={{ ...inputStyle, flex: 1, height: 36, padding: "6px 12px", fontSize: 12 }} />
              <button onClick={() => act("approve")} style={btnStyle("var(--green)", "#0a0e0f")}>✓ Approve</button>
              <button onClick={() => act("reject")} style={btnStyle("var(--red-dim)", "var(--red)")}>✗ Reject</button>
            </div>
          ) : (
            <div style={{ fontSize: 12, color: "var(--text3)", fontFamily: "DM Mono, monospace" }}>
              {rec.reviewed_by && <span>Reviewed by {rec.reviewed_by}</span>}
              {rec.review_note && <span> · "{rec.review_note}"</span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [companies, setCompanies] = useState([]);
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [batches, setBatches] = useState([]);
  const [filters, setFilters] = useState({ status: "", source_type: "", scope: "", company: "" });

  const load = useCallback(async () => {
    try {
      const [co, em, sm, ba] = await Promise.all([
        fetch(`${API}/companies/`).then(r => r.json()),
        fetch(`${API}/emissions/?${new URLSearchParams(Object.fromEntries(Object.entries(filters).filter(([,v])=>v)))}`).then(r => r.json()),
        fetch(`${API}/emissions/summary/`).then(r => r.json()),
        fetch(`${API}/ingestion/batches/`).then(r => r.json()),
      ]);
      setCompanies(co.results || co);
      setRecords(em.results || em);
      setSummary(sm);
      setBatches(ba.results || ba);
    } catch (e) { console.error(e); }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  const tabs = [
    { id: "dashboard", label: "Dashboard" },
    { id: "review", label: `Review ${summary ? `(${summary.pending + summary.suspicious})` : ""}` },
    { id: "ingest", label: "Ingest Data" },
    { id: "batches", label: "Upload History" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid var(--border)", padding: "0 32px", display: "flex", alignItems: "center", justifyContent: "space-between", height: 56 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 28, height: 28, background: "var(--green)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🌿</div>
          <div>
            <span style={{ fontWeight: 800, fontSize: 16, letterSpacing: "-0.02em" }}>Breathe ESG</span>
            <span style={{ color: "var(--text3)", fontSize: 12, marginLeft: 10, fontFamily: "DM Mono, monospace" }}>emissions ingestion</span>
          </div>
        </div>
        <nav style={{ display: "flex", gap: 2 }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              background: tab === t.id ? "var(--surface2)" : "transparent",
              color: tab === t.id ? "var(--text)" : "var(--text3)",
              border: tab === t.id ? "1px solid var(--border2)" : "1px solid transparent",
              borderRadius: "var(--radius)", padding: "6px 14px", fontFamily: "Syne, sans-serif",
              fontWeight: 600, fontSize: 13, cursor: "pointer",
            }}>{t.label}</button>
          ))}
        </nav>
      </header>

      <main style={{ padding: "28px 32px", maxWidth: 1280, margin: "0 auto" }}>
        {/* DASHBOARD */}
        {tab === "dashboard" && summary && (
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>Emissions Overview</h1>
              <p style={{ color: "var(--text3)", fontSize: 13, marginTop: 4 }}>All companies · All periods · Live data</p>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12 }}>
              <StatCard label="Total Records" value={summary.total_records} accent="var(--text2)" />
              <StatCard label="Pending Review" value={summary.pending} accent="var(--yellow)" sub="awaiting analyst" />
              <StatCard label="Approved" value={summary.approved} accent="var(--green)" sub="ready for audit" />
              <StatCard label="Suspicious" value={summary.suspicious} accent="var(--red)" sub="flagged for review" />
              <StatCard label="Total CO₂e" value={`${fmt(summary.total_kg_co2e / 1000)} t`} accent="var(--green)" sub="approved records only" />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              {["scope1","scope2","scope3"].map(s => (
                <div key={s} style={{ background: "var(--surface)", border: `1px solid var(--border)`, borderLeft: `3px solid ${scopeColor[s]}`, borderRadius: "var(--radius)", padding: "18px 20px" }}>
                  <div style={{ color: "var(--text3)", fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "DM Mono, monospace" }}>{scopeLabel[s]}</div>
                  <div style={{ fontSize: 26, fontWeight: 800, marginTop: 6, color: scopeColor[s] }}>{fmt(summary.by_scope[s] / 1000)} <span style={{ fontSize: 14, fontWeight: 400, color: "var(--text3)" }}>t CO₂e</span></div>
                  <div style={{ marginTop: 10, color: "var(--text3)", fontSize: 12, fontFamily: "DM Mono, monospace" }}>
                    {s === "scope1" && "Direct: Fuel combustion"}
                    {s === "scope2" && "Indirect: Purchased electricity"}
                    {s === "scope3" && "Value chain: Business travel"}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
              {Object.entries(summary.by_source).map(([src, count]) => (
                <div key={src} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "16px 20px", display: "flex", alignItems: "center", gap: 14 }}>
                  <div style={{ fontSize: 28 }}>{sourceIcon[src]}</div>
                  <div>
                    <div style={{ fontWeight: 700 }}>{sourceLabel[src]}</div>
                    <div style={{ color: "var(--text3)", fontSize: 12, fontFamily: "DM Mono, monospace" }}>{count} records ingested</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* REVIEW */}
        {tab === "review" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>Analyst Review</h1>
              <p style={{ color: "var(--text3)", fontSize: 13, marginTop: 4 }}>Click any row to expand · Approve or reject before audit lock</p>
            </div>
            {/* Filters */}
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {[
                { key: "status", opts: [["","All Status"],["pending","Pending"],["approved","Approved"],["rejected","Rejected"],["suspicious","Suspicious"]] },
                { key: "source_type", opts: [["","All Sources"],["sap","SAP"],["utility","Utility"],["travel","Travel"]] },
                { key: "scope", opts: [["","All Scopes"],["scope1","Scope 1"],["scope2","Scope 2"],["scope3","Scope 3"]] },
                { key: "company", opts: [["","All Companies"], ...companies.map(c=>[c.id, c.name])] },
              ].map(({ key, opts }) => (
                <select key={key} value={filters[key]} onChange={e => setFilters(f => ({...f, [key]: e.target.value}))}
                  style={{ ...inputStyle, width: "auto", fontSize: 12, padding: "7px 10px" }}>
                  {opts.map(([v,l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              ))}
              <button onClick={load} style={btnStyle("var(--surface2)", "var(--text2)")}>↻ Refresh</button>
            </div>
            {/* Table */}
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
              <div style={{ display: "grid", gridTemplateColumns: "40px 90px 80px 1fr 90px 110px 90px", padding: "10px 16px", background: "var(--surface2)", borderBottom: "1px solid var(--border)", gap: 12 }}>
                {["ID","Source","Scope","Details","Volume","CO₂e","Status"].map(h => (
                  <div key={h} style={{ color: "var(--text3)", fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", fontFamily: "DM Mono, monospace" }}>{h}</div>
                ))}
              </div>
              {records.length === 0 && (
                <div style={{ padding: "40px", textAlign: "center", color: "var(--text3)" }}>No records found</div>
              )}
              {records.map(r => <ReviewRow key={r.id} rec={r} onAction={load} />)}
            </div>
          </div>
        )}

        {/* INGEST */}
        {tab === "ingest" && (
          <div style={{ maxWidth: 600 }}>
            <div style={{ marginBottom: 24 }}>
              <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>Ingest Data</h1>
              <p style={{ color: "var(--text3)", fontSize: 13, marginTop: 4 }}>Upload CSV from SAP, utility portal, or Concur/Navan</p>
            </div>
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "24px" }}>
              <UploadPanel companies={companies} onDone={() => { load(); setTab("review"); }} />
            </div>
            <div style={{ marginTop: 20, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "18px 20px" }}>
              <div style={{ fontWeight: 700, marginBottom: 12 }}>Format Guide</div>
              {[
                { src: "SAP (Scope 1)", cols: "PLANT, MATERIAL, DESCRIPTION, QUANTITY, UNIT, POSTING_DATE, DOC_NUMBER", note: "German headers (WERK, MENGE, EINHEIT) supported. Date: DD.MM.YYYY or YYYY-MM-DD" },
                { src: "Utility (Scope 2)", cols: "METER_ID, ACCOUNT_NUMBER, BILLING_PERIOD_START, BILLING_PERIOD_END, CONSUMPTION_KWH, TARIFF_CATEGORY, LOCATION, BILL_NUMBER", note: "Billing periods can span across months" },
                { src: "Travel (Scope 3)", cols: "EMPLOYEE_ID, TRAVEL_DATE, CATEGORY, ORIGIN, DESTINATION, DISTANCE_KM, TRANSPORT_MODE, HOTEL_NAME, NIGHTS", note: "Categories: flight, hotel, taxi, train, rental_car. Airport codes auto-resolve distance." },
              ].map(({ src, cols, note }) => (
                <div key={src} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid var(--border)" }}>
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>{src}</div>
                  <div style={{ fontFamily: "DM Mono, monospace", fontSize: 11, color: "var(--text3)", marginBottom: 4 }}>{cols}</div>
                  <div style={{ fontSize: 11, color: "var(--text2)" }}>{note}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* BATCHES */}
        {tab === "batches" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>Upload History</h1>
              <p style={{ color: "var(--text3)", fontSize: 13, marginTop: 4 }}>All ingestion batches with parse results</p>
            </div>
            <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 90px 1fr 60px 60px 60px 60px 80px", padding: "10px 16px", background: "var(--surface2)", borderBottom: "1px solid var(--border)", gap: 12 }}>
                {["File","Source","Company","Total","OK","Failed","Flagged","Status"].map(h => (
                  <div key={h} style={{ color: "var(--text3)", fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", fontFamily: "DM Mono, monospace" }}>{h}</div>
                ))}
              </div>
              {batches.map(b => {
                const sc = { done: statusColor.approved, failed: statusColor.rejected, processing: statusColor.pending }[b.status] || statusColor.pending;
                return (
                  <div key={b.id} style={{ display: "grid", gridTemplateColumns: "1fr 90px 1fr 60px 60px 60px 60px 80px", padding: "12px 16px", borderBottom: "1px solid var(--border)", gap: 12, alignItems: "center", fontSize: 13 }}>
                    <div style={{ fontFamily: "DM Mono, monospace", fontSize: 11, color: "var(--text2)" }}>{b.filename}</div>
                    <Badge label={b.source_type.toUpperCase()} color={b.source_type === "sap" ? "#ff9f43" : b.source_type === "utility" ? "#4db8ff" : "#a29bfe"} bg={b.source_type === "sap" ? "var(--orange-dim)" : b.source_type === "utility" ? "var(--blue-dim)" : "rgba(162,155,254,0.12)"} />
                    <div>{b.company_name}</div>
                    <div style={{ fontFamily: "DM Mono, monospace" }}>{b.rows_total}</div>
                    <div style={{ fontFamily: "DM Mono, monospace", color: "var(--green)" }}>{b.rows_success}</div>
                    <div style={{ fontFamily: "DM Mono, monospace", color: b.rows_failed > 0 ? "var(--red)" : "var(--text3)" }}>{b.rows_failed}</div>
                    <div style={{ fontFamily: "DM Mono, monospace", color: b.rows_suspicious > 0 ? "var(--yellow)" : "var(--text3)" }}>{b.rows_suspicious}</div>
                    <Badge label={b.status} color={sc.text} bg={sc.bg} />
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
