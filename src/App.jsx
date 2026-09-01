import { useMemo, useState } from "react";
import { ArrowClockwise, CheckCircle, Clock, FileText, Fingerprint, GithubLogo, LockKey, PaperPlaneTilt, Scan, ShieldCheck, UserCheck, Warning, XCircle } from "@phosphor-icons/react";
import rejectedFixture from "./fixtures/rejected.json";
import approvedFixture from "./fixtures/approved-resize.json";
import verifiedExecution from "./fixtures/verified-execution.json";
import "./proof.css";

const fixtures = { rejected: rejectedFixture, approved: approvedFixture };

function GuardrailRow({ item }) {
  const Icon = item.status === "pass" ? CheckCircle : item.status === "warn" ? Warning : XCircle;
  return <div className={`guardrail-row ${item.status}`}><Icon weight="regular" /><div className="guardrail-copy"><strong>{item.label}</strong><span>{item.detail}</span></div><b>{item.status === "pass" ? "PASS" : item.status === "warn" ? "WARN" : "FAIL"}</b></div>;
}

function Metric({ label, value, suffix }) {
  return <div className="metric"><span>{label}</span><strong>{value} <small>{suffix}</small></strong></div>;
}

function VerifiedRun() {
  const receipt = verifiedExecution.receipt;
  return <section className="proof-view" aria-label="Verified paper execution">
    <div className="proof-hero"><div><span className="eyebrow"><CheckCircle weight="fill" /> VERIFIED PAPER EXECUTION</span><h2>One opportunity. Four independent checkpoints.</h2><p>A sanitized receipt from the operator-only workflow proves that selection, approval, authorization and broker reconciliation work end to end. The public demo cannot repeat the trade.</p></div><div className="proof-stamp"><ShieldCheck weight="duotone" /><strong>FILLED</strong><span>ALPACA PAPER</span></div></div>
    <div className="proof-flow" aria-label="Execution flow"><div><Scan /><b>01 · SCAN</b><strong>6 symbols</strong><span>One evidence pass each</span></div><i>→</i><div><ShieldCheck /><b>02 · GOVERN</b><strong>MSFT selected</strong><span>Highest eligible confidence</span></div><i>→</i><div><UserCheck /><b>03 · AUTHORIZE</b><strong>Human confirmed</strong><span>Exact $1.00 paper buy</span></div><i>→</i><div><PaperPlaneTilt /><b>04 · RECONCILE</b><strong>Broker filled</strong><span>One POST · no retry</span></div></div>
    <div className="proof-grid">
      <article className="scan-card"><header><div><span>FIXED UNIVERSE SCAN</span><strong>{verifiedExecution.evaluatedAt}</strong></div><em>ORDERLESS PREVIEW</em></header><div className="scan-head"><span>SYMBOL</span><span>PROPOSAL</span><span>CONFIDENCE</span><span>OUTCOME</span></div>{verifiedExecution.universe.map((row) => <div className={`scan-row ${row.status === "Selected" ? "selected" : ""}`} key={row.symbol}><strong>{row.symbol}</strong><b className={row.action.toLowerCase()}>{row.action}</b><span>{row.confidence}</span><em>{row.status === "Selected" && <CheckCircle weight="fill" />}{row.status}</em></div>)}<footer><Fingerprint /><span><b>DETERMINISTIC SELECTION</b>{verifiedExecution.selectionRule}</span></footer></article>
      <article className="receipt-card"><header><span>VERIFIED BROKER RECEIPT</span><b><CheckCircle weight="fill" /> {receipt.status}</b></header><div className="receipt-trade"><div><span>SYMBOL</span><strong>{receipt.symbol}</strong></div><div><span>SIDE</span><strong className="buy">{receipt.side}</strong></div><div><span>NOTIONAL</span><strong>{receipt.notional}</strong></div></div><dl><div><dt>Filled quantity</dt><dd>{receipt.filledQuantity}</dd></div><div><dt>Average price</dt><dd>{receipt.averagePrice}</dd></div><div><dt>Filled at</dt><dd>{receipt.filledAt}</dd></div><div><dt>Order ID</dt><dd>{receipt.orderId}</dd></div><div><dt>Client order ID</dt><dd>{receipt.clientOrderId}</dd></div></dl><footer><LockKey weight="fill" /><span><b>PAPER ACCOUNT · SANITIZED</b>No credentials, balances or account identifiers are present.</span></footer></article>
    </div>
    <div className="proof-boundary"><ShieldCheck /><b>WHAT THIS PROVES</b><span>Fresh evidence → constrained AI proposal → deterministic policy → explicit human authorization → one reconciled Alpaca paper fill.</span><em>Not proof of profitability or unattended autonomy.</em></div>
  </section>;
}

export function App() {
  const isHostedDemo = !["localhost", "127.0.0.1"].includes(window.location.hostname);
  const [caseName, setCaseName] = useState("rejected");
  const [loading, setLoading] = useState(false);
  const [liveLoading, setLiveLoading] = useState(false);
  const [apiData, setApiData] = useState(null);
  const [source, setSource] = useState("bundled synthetic fallback");
  const [view, setView] = useState("proof");
  const data = apiData || fixtures[caseName];
  const failures = useMemo(() => data.guardrails.filter((item) => item.status !== "pass"), [data]);
  void failures;

  async function replay() {
    setLoading(true);
    const next = caseName === "rejected" ? "approved" : "rejected";
    if (isHostedDemo) {
      await new Promise((resolve) => window.setTimeout(resolve, 320));
      setApiData(null);
      setCaseName(next);
      setSource("public synthetic replay");
      setLoading(false);
      return;
    }
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

  async function runLive() {
    setLiveLoading(true);
    try {
      const response = await fetch("/api/evaluations/live", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({symbol:"AAPL"}) });
      const payload = await response.json();
      if (!response.ok || payload.error || payload.orderSubmission !== "disabled") throw new Error("live evaluation unavailable");
      setApiData(payload);
      setSource("live read-only workflow");
    } catch {
      setSource("live unavailable · safe fallback retained");
    } finally {
      setLiveLoading(false);
    }
  }

  return <main className="console-shell">
    <header className="topbar">
      <div className="brand"><img src="/goblin-shield.png" alt="Goblin Guard shield" /><h1>Goblin Guard</h1></div>
      <div className="paper-badge">PAPER TRADING ONLY</div><p>AI proposes. Rules decide.</p>
      <div className="clock-block">28 AUG 2026<br />10:42:17 UTC</div>
      <div className="kill-switch"><span>Global kill switch</span><b>SAFE LOCKED</b></div><LockKey className="lock-icon" weight="fill" />
    </header>

    <section className="demo-guide" aria-label="Demo guide">
      <div className="demo-kicker"><b>PUBLIC DEMO</b><span>Verified proof. Zero broker controls.</span></div>
      <div className="view-switch" role="tablist" aria-label="Demo view"><button role="tab" aria-selected={view === "proof"} onClick={() => setView("proof")}>Verified run</button><button role="tab" aria-selected={view === "cases"} onClick={() => setView("cases")}>Decision cases</button></div>
      <a href="https://github.com/goaty-93/goblin-guard" target="_blank" rel="noreferrer"><GithubLogo weight="fill" /> View source</a>
    </section>

    {view === "proof" ? <VerifiedRun /> : <><section className="workspace">
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
        <div className={`verdict ${data.decision.toLowerCase()}`} aria-live="polite">{data.decision === "REJECTED" ? <XCircle /> : <ShieldCheck />}<strong>{data.decision}</strong><span>{data.decisionReason}</span><footer>{data.decision === "REJECTED" ? "No order submitted" : `Approved at ${data.approvedNotional} USD`}</footer></div>
      </aside>
    </section>

    <section className="trace-section"><div className="trace-heading"><h3>Decision trace</h3><span className={`case-chip ${data.decision.toLowerCase()}`}>{data.decision === "REJECTED" ? "Rejection case" : "Resize case"}</span></div><div className="trace-grid"><div className="trace-table">{data.trace.map((row) => <div className={`trace-row ${row.status}`} key={`${row.time}-${row.event}`}><time>{row.time}</time><i></i><strong>{row.event}</strong><span>Guardrail Engine</span><b>{row.result}</b><em>{row.detail}</em></div>)}</div><div className="replay-stack"><button className="replay" onClick={replay} disabled={loading || liveLoading}><ArrowClockwise className={loading ? "spinning" : ""} /><strong>{loading ? "Re-evaluating…" : data.decision === "REJECTED" ? "Run approved resize" : "Run rejection case"}</strong><span>{data.decision === "REJECTED" ? "Fresh evidence passes the gates; the oversized request is reduced by policy." : "Stale evidence and the loss circuit breaker overrule the proposal."}</span></button>{!isHostedDemo && <button className="live-run" onClick={runLive} disabled={loading || liveLoading}>{liveLoading ? "Running read-only evaluation…" : "Run live read-only evaluation"}<small>Alpaca IEX → OpenAI proposal → governor</small></button>}</div></div></section></>}
    <footer className="simulation-banner"><ShieldCheck /> {source.startsWith("live read-only") ? "LIVE READ-ONLY" : "SYNTHETIC REPLAY"} · {source.toUpperCase()} · NO ORDERS</footer>
  </main>;
}
