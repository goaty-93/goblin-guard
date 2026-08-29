import { useMemo, useState } from "react";
import { ArrowClockwise, CheckCircle, Clock, FileText, LockKey, ShieldCheck, Warning, XCircle } from "@phosphor-icons/react";
import rejectedFixture from "./fixtures/rejected.json";
import approvedFixture from "./fixtures/approved-resize.json";

const fixtures = { rejected: rejectedFixture, approved: approvedFixture };

function GuardrailRow({ item }) {
  const Icon = item.status === "pass" ? CheckCircle : item.status === "warn" ? Warning : XCircle;
  return <div className={`guardrail-row ${item.status}`}><Icon weight="regular" /><div className="guardrail-copy"><strong>{item.label}</strong><span>{item.detail}</span></div><b>{item.status === "pass" ? "PASS" : item.status === "warn" ? "WARN" : "FAIL"}</b></div>;
}

function Metric({ label, value, suffix }) {
  return <div className="metric"><span>{label}</span><strong>{value} <small>{suffix}</small></strong></div>;
}

export function App() {
  const [caseName, setCaseName] = useState("rejected");
  const [loading, setLoading] = useState(false);
  const [apiData, setApiData] = useState(null);
  const [source, setSource] = useState("bundled synthetic fallback");
  const data = apiData || fixtures[caseName];
  const failures = useMemo(() => data.guardrails.filter((item) => item.status !== "pass"), [data]);
  void failures;

  async function replay() {
    setLoading(true);
    const next = caseName === "rejected" ? "approved" : "rejected";
    try {
      const response = await fetch("/api/evaluations/synthetic", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({scenario:next}) });
      if (!response.ok) throw new Error("evaluation unavailable");
      const payload = await response.json();
      if (payload.error || payload.orderSubmission !== "disabled") throw new Error("unsafe evaluation response");
      setApiData(payload);
      setSource("api synthetic workflow");
    } catch {
      setApiData(null);
      setSource("bundled synthetic fallback");
    } finally {
      setCaseName(next);
      setLoading(false);
    }
  }

  return <main className="console-shell">
    <header className="topbar">
      <div className="brand"><img src="/goblin-shield.png" alt="Goblin Guard shield" /><h1>Goblin Guard</h1></div>
      <div className="paper-badge">PAPER TRADING ONLY</div><p>AI proposes. Rules decide.</p>
      <div className="clock-block">28 AUG 2026<br />10:42:17 UTC</div>
      <div className="kill-switch"><span>Global kill switch</span><b>SAFE LOCKED</b></div><LockKey className="lock-icon" weight="fill" />
    </header>

    <section className="workspace">
      <section className="proposal-panel">
        <div className="section-title"><FileText /><h2>Proposal</h2><div className="proposal-meta">ID: {data.id}<span></span><Clock /> 2m 14s ago</div></div>
        <article className="proposal-card">
          <div className="agent-strip">
            <div><span>AI AGENT</span><strong>Goblin Guard v0.1.0</strong></div><div><span>MODEL</span><strong>Structured proposal</strong></div><div><span>DATA AS OF</span><strong>{data.dataAsOf}</strong></div>
            {data.stale && <em>STALE <Warning weight="fill" /></em>}
          </div>
          <div className="trade-row">
            <div className="symbol"><strong>{data.symbol}</strong><span>{data.company}</span></div><div><span>ACTION</span><strong className={data.action.toLowerCase()}>{data.action}</strong></div><div><span>REQUESTED</span><strong>{data.requestedNotional} <small>USD</small></strong></div><div><span>ORDER TYPE</span><strong>LIMIT <small>{data.limitPrice} USD</small></strong></div>
          </div>
          <div className="rationale"><span>AI RATIONALE</span><p>{data.rationale}</p></div>
          <div className="metrics"><Metric label="LAST PRICE" value={data.metrics.lastPrice} suffix="USD" /><Metric label="20D EMA" value={data.metrics.ema20} suffix="USD" /><Metric label="RSI (14)" value={data.metrics.rsi} /><Metric label="VOLUME (VS 20D AVG)" value={data.metrics.volume} /><Metric label="ATR (14)" value={data.metrics.atr} suffix="USD" /></div>
          <div className="metrics lower"><Metric label="AI CONFIDENCE" value={data.confidence} /><Metric label="TIME HORIZON" value="1–3" suffix="DAYS" /><Metric label="EXPECTED MOVE" value="+1.8%" /><Metric label="STOP SUGGESTION" value="187.50" suffix="USD" /><Metric label="TARGET SUGGESTION" value="196.00" suffix="USD" /></div>
        </article>
      </section>

      <aside className="guardrails-panel">
        <div className="section-title"><ShieldCheck /><h2>Deterministic Guardrails</h2></div>
        <div className="guardrail-list">{data.guardrails.map((item) => <GuardrailRow key={item.label} item={item} />)}</div>
        <div className={`verdict ${data.decision.toLowerCase()}`}>{data.decision === "REJECTED" ? <XCircle /> : <ShieldCheck />}<strong>{data.decision}</strong><span>{data.decisionReason}</span><footer>{data.decision === "REJECTED" ? "No order submitted" : `Approved at ${data.approvedNotional} USD`}</footer></div>
      </aside>
    </section>

    <section className="trace-section"><h3>Decision trace</h3><div className="trace-grid"><div className="trace-table">{data.trace.map((row) => <div className={`trace-row ${row.status}`} key={`${row.time}-${row.event}`}><time>{row.time}</time><i></i><strong>{row.event}</strong><span>Guardrail Engine</span><b>{row.result}</b><em>{row.detail}</em></div>)}</div><button className="replay" onClick={replay} disabled={loading}><ArrowClockwise className={loading ? "spinning" : ""} /><strong>{loading ? "Re-evaluating…" : "Replay with fresh evidence"}</strong><span>Load the other synthetic case and re-run deterministic guardrails.</span></button></div></section>
    <footer className="simulation-banner"><ShieldCheck /> SYNTHETIC REPLAY · {source.toUpperCase()} · NO ORDERS</footer>
  </main>;
}
