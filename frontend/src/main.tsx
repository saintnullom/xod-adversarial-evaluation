import { FormEvent, StrictMode, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { FailureReportPayload, submitFailureReport } from "./failureReportSubmission";
import "./styles.css";

type Mode = "SPAR" | "TRIBUNAL";
type Verdict = "ROBUST" | "PLAUSIBLE" | "UNDERTESTED" | "SPECULATIVE" | "FRAGILE" | "CONTRADICTORY" | "SELF_SEALING";
type BeliefStatus = "ACTIVE_TEST" | "ACTIVE" | "REVISED" | "ABANDONED";
type EvidenceDirection = "SUPPORTS" | "CONTRADICTS";
type PredictionImpact = "SUPPORTS" | "WEAKENS" | "INCONCLUSIVE";
type ReasoningItem = { claim: string; kind: "EVIDENCE" | "OBSERVATION" | "INFERENCE" | "SPECULATION"; source: string | null; url: string | null };
type TribunalAnalysis = { proposition: string; user_confidence: number | null; assumptions: string[]; evidence_for: ReasoningItem[]; evidence_against: ReasoningItem[]; strongest_objection: string; alternative_explanations: string[]; bias_risks: string[]; falsification_conditions: string[]; cheapest_experiment: string; steelman: string; verdict: Verdict; recommended_confidence: { minimum: number; maximum: number }; xod_self_critique: string };
type SelfCritiqueEvaluation = { message_id: string; rubric_version: string; score: number; verdict: "USEFUL" | "NEEDS_WORK"; checks: { key: string; passed: boolean; rationale: string }[]; created_at: string; interpretation: string };
type SpecialistCase = { id: string; domain: string; proposition: string; expected_behavior: string };
type SpecialistReadiness = { decision: "INSUFFICIENT_EVIDENCE" | "HOLD" | "ELIGIBLE_FOR_PILOT"; required_case_count: number; measured_case_count: number; missing_case_ids: string[]; quality_lift: number | null; cost_ratio: number | null; latency_ratio: number | null; regressed_case_ids: string[]; rationale: string[] };
type Analytics = { belief_count: number; revised_belief_count: number; abandoned_belief_count: number; resolved_prediction_count: number; epistemic_delta: { availability: "AVAILABLE" | "INSUFFICIENT_DATA"; beliefs_with_comparable_confidence: number; mean_delta: number | null; decreased_count: number; increased_count: number; unchanged_count: number; interpretation: string }; calibration: { availability: "AVAILABLE" | "INSUFFICIENT_DATA"; resolved_prediction_count: number; scorable_prediction_count: number; mean_confidence: number | null; observed_support_rate: number | null; mean_absolute_error: number | null; interpretation: string }; revision_history: { belief_id: string; proposition: string; current_version: number; status: BeliefStatus; initial_confidence: number | null; current_confidence: number | null; epistemic_delta: number | null; revised_at: string }[] };
type RelationshipType = "SUPPORTS" | "CONTRADICTS" | "DEPENDS_ON" | "DERIVED_FROM" | "ALTERNATIVE_TO" | "EVIDENCE_FOR" | "EVIDENCE_AGAINST" | "REQUIRES" | "UNTESTED_DEPENDENCY";
type BeliefRelationship = { id: string; source_belief_id: string; source_proposition: string; target_belief_id: string; target_proposition: string; relationship_type: RelationshipType; note: string | null; created_at: string };
type BeliefRelationships = { outgoing: BeliefRelationship[]; incoming: BeliefRelationship[] };
type EvaluationCase = { id: string; domain: string; proposition: string; expected_behavior: string; primary_risk: string };
type FailureReport = { id: string; category: string; summary: string; expected_behavior: string | null; evaluation_case_id: string | null; source_analysis_message_id: string | null; created_at: string };
type Message = { id: string; conversation_id: string; role: "USER" | "XOD" | "SYSTEM"; content: string; created_at: string; analysis: TribunalAnalysis | null };
type Conversation = { id: string; title: string; created_at: string; messages: Message[] };
type BeliefVersion = { id: string; belief_id: string; version: number; proposition: string; user_confidence: number | null; status: BeliefStatus; change_reason: string | null; source_analysis_message_id: string | null; created_at: string };
type Evidence = { id: string; belief_id: string; claim: string; source: string; source_type: string; url: string | null; retrieved_at: string | null; reliability: number | null; relevance: number | null; direction: EvidenceDirection; created_at: string };
type Prediction = { id: string; belief_id: string; statement: string; success_criteria: string; created_at: string; belief_confidence_at_commit: number | null; expected_resolution_at: string | null; result: string | null; status: "OPEN" | "RESOLVED" | "CANCELLED"; impact: PredictionImpact | null; resolved_at: string | null };
type FalsificationCondition = { id: string; belief_id: string; condition: string; created_at: string };
type BeliefSummary = { id: string; proposition: string; current_version: number; user_confidence: number | null; xod_confidence: number | null; status: BeliefStatus; created_at: string; updated_at: string };
type Belief = BeliefSummary & { versions: BeliefVersion[]; evidence: Evidence[]; predictions: Prediction[]; falsification_conditions: FalsificationCondition[] };

const apiUrl = import.meta.env.VITE_XOD_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init?.headers } });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({ detail: "The request failed." }))) as { detail?: string | { message?: string; category?: string; error_id?: string; retryable?: boolean } };
    if (typeof body.detail === "object" && body.detail !== null) {
      const detail = body.detail;
      const category = detail.category ? ` Category: ${detail.category}.` : "";
      const errorId = detail.error_id ? ` Error ID: ${detail.error_id}.` : "";
      const retryHint = detail.retryable ? " You can retry." : "";
      throw new Error(`${detail.message ?? "The request failed."}${category}${errorId}${retryHint}`);
    }
    throw new Error(body.detail ?? "The request failed.");
  }
  return response.json() as Promise<T>;
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return <section className="tribunal-section"><h3>{title}</h3>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="empty-field">No material items identified.</p>}</section>;
}

function EvidenceSection({ title, items }: { title: string; items: ReasoningItem[] }) {
  return <section className="tribunal-section"><h3>{title}</h3>{items.length ? <ul className="evidence-list">{items.map((item) => <li key={`${item.kind}-${item.claim}`}><span>{item.kind}</span>{item.claim}{item.source && <small>Source: {item.source}</small>}</li>)}</ul> : <p className="empty-field">No material evidence identified.</p>}</section>;
}

function TribunalPanel({ analysis, onSave, onEvaluate, evaluation, pending }: { analysis: TribunalAnalysis; onSave: () => void; onEvaluate: () => void; evaluation?: SelfCritiqueEvaluation; pending: boolean }) {
  return <section className="tribunal-panel" aria-label="Tribunal analysis">
    <div className="verdict-row"><div><p className="message-label">XOD VERDICT</p><strong className={`verdict ${analysis.verdict.toLowerCase()}`}>{analysis.verdict.replace("_", " ")}</strong></div><div><p className="message-label">RECOMMENDED CONFIDENCE</p><strong>{Math.round(analysis.recommended_confidence.minimum * 100)}-{Math.round(analysis.recommended_confidence.maximum * 100)}%</strong></div></div>
    <section className="tribunal-section full"><h3>Proposition</h3><p>{analysis.proposition}</p></section>
    <ListSection title="Assumptions" items={analysis.assumptions} />
    <EvidenceSection title="Evidence for" items={analysis.evidence_for} />
    <EvidenceSection title="Evidence against" items={analysis.evidence_against} />
    <section className="tribunal-section full"><h3>Strongest objection</h3><p>{analysis.strongest_objection}</p></section>
    <ListSection title="Alternative explanations" items={analysis.alternative_explanations} />
    <ListSection title="Bias risks" items={analysis.bias_risks} />
    <ListSection title="Falsification conditions" items={analysis.falsification_conditions} />
    <section className="tribunal-section"><h3>Cheapest experiment</h3><p>{analysis.cheapest_experiment}</p></section>
    <section className="tribunal-section"><h3>Steelman</h3><p>{analysis.steelman}</p></section>
    <section className="tribunal-section self-critique full"><h3>XOD&apos;s objection to XOD</h3><p>{analysis.xod_self_critique}</p>{evaluation && <div className={`self-critique-evaluation ${evaluation.verdict.toLowerCase()}`}><strong>{evaluation.verdict.replace("_", " ")} / {evaluation.score} OF 4</strong><ul>{evaluation.checks.map((check) => <li className={check.passed ? "pass" : "needs-work"} key={check.key}><span>{check.passed ? "PASS" : "NEEDS WORK"}</span>{check.rationale}</li>)}</ul><small>{evaluation.interpretation}</small></div>}</section>
    <div className="tribunal-actions"><button type="button" onClick={onSave} disabled={pending}>Save as belief</button><button type="button" onClick={onEvaluate} disabled={pending}>Evaluate self-critique</button></div>
  </section>;
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleString() : "Not set";
}

type LedgerProps = {
  beliefs: BeliefSummary[];
  selected: Belief | null;
  pending: boolean;
  onSelect: (id: string) => void;
  onAddEvidence: (event: FormEvent<HTMLFormElement>, beliefId: string) => void;
  onAddPrediction: (event: FormEvent<HTMLFormElement>, beliefId: string) => void;
  onResolvePrediction: (event: FormEvent<HTMLFormElement>, predictionId: string, beliefId: string) => void;
  onAddFalsificationCondition: (event: FormEvent<HTMLFormElement>, beliefId: string) => void;
  relationships: BeliefRelationships | null;
  onAddRelationship: (event: FormEvent<HTMLFormElement>, beliefId: string) => void;
};

function Ledger({ beliefs, selected, pending, onSelect, onAddEvidence, onAddPrediction, onResolvePrediction, onAddFalsificationCondition, relationships, onAddRelationship }: LedgerProps) {
  return <section className="ledger" aria-label="Belief Ledger"><p className="eyebrow">BELIEF LEDGER</p>{beliefs.length ? <div className="belief-list">{beliefs.map((belief) => <button className={selected?.id === belief.id ? "selected" : ""} key={belief.id} type="button" onClick={() => onSelect(belief.id)}><span>{belief.status.replace("_", " ")}</span>{belief.proposition}</button>)}</div> : <p className="empty-field">No beliefs saved yet.</p>}{selected && <div className="belief-detail"><p className="message-label">CURRENT / V{selected.current_version} / {selected.status.replace("_", " ")}</p><h3>{selected.proposition}</h3><p>{selected.user_confidence === null ? "Confidence not stated" : `Your confidence: ${Math.round(selected.user_confidence * 100)}%`}</p><small>Created {formatDate(selected.created_at)} · Updated {formatDate(selected.updated_at)}</small><p className="message-label">VERSION HISTORY</p><ol>{selected.versions.map((version) => <li key={version.id}><strong>V{version.version} / {version.status.replace("_", " ")}</strong><span>{version.proposition}</span>{version.change_reason && <small>{version.change_reason}</small>}</li>)}</ol>
    <p className="message-label">RELATIONSHIPS</p><ul className="record-list">{relationships && [...relationships.outgoing, ...relationships.incoming].length ? [...relationships.outgoing.map((item) => ({ ...item, direction: "OUTGOING" })), ...relationships.incoming.map((item) => ({ ...item, direction: "INCOMING" }))].map((item) => <li key={item.id}><strong>{item.direction} / {item.relationship_type.replaceAll("_", " ")}</strong><span>{item.direction === "OUTGOING" ? item.target_proposition : item.source_proposition}</span>{item.note && <small>{item.note}</small>}</li>) : <li className="empty-field">No belief links recorded.</li>}</ul><details><summary>Link another belief</summary><form className="ledger-form" onSubmit={(event) => onAddRelationship(event, selected.id)}><select name="target_belief_id" required disabled={pending}><option value="">Choose another belief</option>{beliefs.filter((belief) => belief.id !== selected.id).map((belief) => <option key={belief.id} value={belief.id}>{belief.proposition}</option>)}</select><select name="relationship_type" defaultValue="DEPENDS_ON" disabled={pending}><option value="SUPPORTS">Supports</option><option value="CONTRADICTS">Contradicts</option><option value="DEPENDS_ON">Depends on</option><option value="DERIVED_FROM">Derived from</option><option value="ALTERNATIVE_TO">Alternative to</option><option value="EVIDENCE_FOR">Evidence for</option><option value="EVIDENCE_AGAINST">Evidence against</option><option value="REQUIRES">Requires</option><option value="UNTESTED_DEPENDENCY">Untested dependency</option></select><textarea name="note" rows={2} placeholder="Optional explanation" disabled={pending} /><button type="submit" disabled={pending || beliefs.length < 2}>Record relationship</button></form></details>
    <p className="message-label">FALSIFICATION CONDITIONS</p><ul className="record-list">{selected.falsification_conditions.length ? selected.falsification_conditions.map((item) => <li key={item.id}>{item.condition}</li>) : <li className="empty-field">No observable revision condition recorded.</li>}</ul><details><summary>Add a condition</summary><form className="ledger-form" onSubmit={(event) => onAddFalsificationCondition(event, selected.id)}><textarea name="condition" required rows={3} placeholder="What observable result would make this belief require revision?" disabled={pending} /><button type="submit" disabled={pending}>Record condition</button></form></details>
    <p className="message-label">EVIDENCE</p><ul className="record-list">{selected.evidence.length ? selected.evidence.map((item) => <li key={item.id}><strong className={`direction ${item.direction.toLowerCase()}`}>{item.direction}</strong><span>{item.claim}</span><small>{item.source_type}: {item.source}{item.retrieved_at ? ` · retrieved ${formatDate(item.retrieved_at)}` : ""}{item.reliability !== null ? ` · reliability ${Math.round(item.reliability * 100)}%` : ""}{item.relevance !== null ? ` · relevance ${Math.round(item.relevance * 100)}%` : ""}</small>{item.url && <a className="record-link" href={item.url} target="_blank" rel="noreferrer">Open source</a>}</li>) : <li className="empty-field">No evidence recorded.</li>}</ul><details><summary>Add evidence</summary><form className="ledger-form" onSubmit={(event) => onAddEvidence(event, selected.id)}><textarea name="claim" required rows={3} placeholder="What does this evidence actually support or contradict?" disabled={pending} /><input name="source" required placeholder="Source or observation" disabled={pending} /><input name="source_type" defaultValue="USER_NOTE" placeholder="Source type" disabled={pending} /><select name="direction" defaultValue="SUPPORTS" disabled={pending}><option value="SUPPORTS">Supports belief</option><option value="CONTRADICTS">Contradicts belief</option></select><input name="url" type="url" placeholder="Optional source URL" disabled={pending} /><label className="date-label">Retrieved at<input name="retrieved_at" type="datetime-local" disabled={pending} /></label><div className="record-metrics"><input name="reliability" type="number" min="0" max="1" step="0.05" placeholder="Reliability 0-1" disabled={pending} /><input name="relevance" type="number" min="0" max="1" step="0.05" placeholder="Relevance 0-1" disabled={pending} /></div><button type="submit" disabled={pending}>Record evidence</button></form></details>
    <p className="message-label">PREDICTIONS</p><ul className="record-list">{selected.predictions.length ? selected.predictions.map((item) => <li key={item.id}><strong>{item.status}{item.impact ? ` / ${item.impact}` : ""}</strong><span>{item.statement}</span><small>Criteria: {item.success_criteria}{item.expected_resolution_at ? ` · resolve by ${formatDate(item.expected_resolution_at)}` : ""}</small>{item.result && <small>Result: {item.result}</small>}{item.status === "OPEN" && <details><summary>Resolve prediction</summary><form className="ledger-form" onSubmit={(event) => onResolvePrediction(event, item.id, selected.id)}><textarea name="result" required rows={2} placeholder="Observed result" disabled={pending} /><select name="impact" defaultValue="INCONCLUSIVE" disabled={pending}><option value="SUPPORTS">Supports belief</option><option value="WEAKENS">Weakens belief</option><option value="INCONCLUSIVE">Inconclusive</option></select><button type="submit" disabled={pending}>Resolve</button></form></details>}</li>) : <li className="empty-field">No precommitted predictions recorded.</li>}</ul><details><summary>Add prediction</summary><form className="ledger-form" onSubmit={(event) => onAddPrediction(event, selected.id)}><textarea name="statement" required rows={3} placeholder="Prediction statement" disabled={pending} /><textarea name="success_criteria" required rows={3} placeholder="Measurable success or failure criteria" disabled={pending} /><label className="date-label">Expected resolution<input name="expected_resolution_at" type="datetime-local" disabled={pending} /></label><button type="submit" disabled={pending}>Precommit prediction</button></form></details>
  </div>}</section>;
}

function SpecialistGate({ cases, readiness, pending, onRecord }: { cases: SpecialistCase[]; readiness: SpecialistReadiness | null; pending: boolean; onRecord: (event: FormEvent<HTMLFormElement>) => void }) {
  return <section className="specialist-gate" aria-label="Specialist reasoning evaluation"><p className="eyebrow">SPECIALIST GATE</p><p>The candidate may earn a bounded pilot only after paired measurements cover every case. No specialist calls are made here.</p>{readiness && <div className={`readiness ${readiness.decision.toLowerCase()}`}><strong>{readiness.decision.replaceAll("_", " ")}</strong><span>{readiness.measured_case_count}/{readiness.required_case_count} cases measured</span>{readiness.quality_lift !== null && <small>Quality lift {readiness.quality_lift.toFixed(2)} · Cost {readiness.cost_ratio?.toFixed(2) ?? "n/a"}x · Latency {readiness.latency_ratio?.toFixed(2) ?? "n/a"}x</small>}{readiness.missing_case_ids.length > 0 && <small>Missing: {readiness.missing_case_ids.join(", ")}</small>}{readiness.regressed_case_ids.length > 0 && <small>Regressions: {readiness.regressed_case_ids.join(", ")}</small>}<ul>{readiness.rationale.map((item) => <li key={item}>{item}</li>)}</ul></div>}<details><summary>Record paired measurement</summary><form className="ledger-form" onSubmit={onRecord}><select name="case_id" required disabled={pending}>{cases.map((item) => <option key={item.id} value={item.id}>{item.domain}: {item.proposition}</option>)}</select><div className="record-metrics"><input name="baseline_quality" type="number" min="0" max="4" step="0.25" required placeholder="Baseline quality 0-4" disabled={pending} /><input name="specialist_quality" type="number" min="0" max="4" step="0.25" required placeholder="Specialist quality 0-4" disabled={pending} /></div><div className="record-metrics"><input name="baseline_cost_usd" type="number" min="0" step="0.0001" required placeholder="Baseline cost USD" disabled={pending} /><input name="specialist_cost_usd" type="number" min="0" step="0.0001" required placeholder="Specialist cost USD" disabled={pending} /></div><div className="record-metrics"><input name="baseline_latency_ms" type="number" min="0" step="1" required placeholder="Baseline latency ms" disabled={pending} /><input name="specialist_latency_ms" type="number" min="0" step="1" required placeholder="Specialist latency ms" disabled={pending} /></div><button type="submit" disabled={pending || !cases.length}>Record measurement</button></form></details></section>;
}

function AnalyticsPanel({ analytics }: { analytics: Analytics | null }) {
  return <section className="analytics-panel" aria-label="Epistemic analytics"><p className="eyebrow">EPISTEMIC ANALYTICS</p>{analytics && <><p>{analytics.belief_count} beliefs · {analytics.revised_belief_count} revised · {analytics.abandoned_belief_count} abandoned · {analytics.resolved_prediction_count} predictions resolved</p><div className="analytics-metric"><strong>CONFIDENCE DELTA / {analytics.epistemic_delta.availability.replace("_", " ")}</strong><span>{analytics.epistemic_delta.mean_delta === null ? "No comparable confidence history yet." : `${(analytics.epistemic_delta.mean_delta * 100).toFixed(1)} percentage points on average`}</span><small>{analytics.epistemic_delta.interpretation}</small></div><div className="analytics-metric"><strong>CALIBRATION PROXY / {analytics.calibration.availability.replace("_", " ")}</strong><span>{analytics.calibration.mean_absolute_error === null ? `${analytics.calibration.scorable_prediction_count}/5 scorable predictions` : `Mean absolute error ${(analytics.calibration.mean_absolute_error * 100).toFixed(1)}%`}</span><small>{analytics.calibration.interpretation}</small></div>{analytics.revision_history.length > 0 && <><p className="message-label">REVISION HISTORY</p><ol>{analytics.revision_history.map((item) => <li key={item.belief_id}><strong>V{item.current_version} / {item.status.replace("_", " ")}</strong><span>{item.proposition}</span><small>{item.epistemic_delta === null ? "Confidence unavailable" : `Delta ${(item.epistemic_delta * 100).toFixed(1)} points`}</small></li>)}</ol></>}</>}</section>;
}

function EvaluationPanel({ cases, reports, pending, notice, onRecord }: { cases: EvaluationCase[]; reports: FailureReport[]; pending: boolean; notice: string | null; onRecord: (event: FormEvent<HTMLFormElement>) => void }) {
  return <section className="evaluation-panel" aria-label="XOD evaluation suite"><p className="eyebrow">EVALUATION + FAILURE LOG</p><p>Expected behaviors are a regression suite, not truth labels. Record a failure only when you observed one.</p>{notice && <p className="success" role="status">{notice}</p>}<details><summary>View {cases.length} evaluation cases</summary><ol>{cases.map((item) => <li key={item.id}><strong>{item.domain}</strong><span>{item.proposition}</span><small>Expected: {item.expected_behavior}</small></li>)}</ol></details><details><summary>Record observed failure</summary><form className="ledger-form" onSubmit={onRecord}><select name="category" defaultValue="MISUNDERSTOOD_PROPOSITION" disabled={pending}><option value="INCORRECT_OBJECTION">Incorrect objection</option><option value="MISUNDERSTOOD_PROPOSITION">Misunderstood proposition</option><option value="IGNORED_CONTEXT">Ignored context</option><option value="HALLUCINATED_EVIDENCE">Hallucinated evidence</option><option value="TOO_CONFIDENT">Too confident</option><option value="MISSED_CONTRADICTION">Missed contradiction</option><option value="OTHER">Other</option></select><select name="evaluation_case_id" defaultValue="" disabled={pending}><option value="">No suite case</option>{cases.map((item) => <option key={item.id} value={item.id}>{item.domain}: {item.proposition}</option>)}</select><textarea name="summary" required rows={3} placeholder="What did XOD get wrong?" disabled={pending} /><textarea name="expected_behavior" rows={2} placeholder="What should it have done instead?" disabled={pending} /><button type="submit" disabled={pending}>Record failure</button></form></details><p className="message-label">OBSERVED FAILURES</p>{reports.length ? <ol>{reports.map((report) => <li key={report.id}><strong>{report.category.replaceAll("_", " ")}</strong><span>{report.summary}</span>{report.expected_behavior && <small>Expected: {report.expected_behavior}</small>}</li>)}</ol> : <p className="empty-field">No failures recorded.</p>}</section>;
}

function App() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [draft, setDraft] = useState("");
  const [mode, setMode] = useState<Mode>("SPAR");
  const [confidence, setConfidence] = useState(70);
  const [ledgerOpen, setLedgerOpen] = useState(false);
  const [beliefs, setBeliefs] = useState<BeliefSummary[]>([]);
  const [selectedBelief, setSelectedBelief] = useState<Belief | null>(null);
  const [selectedRelationships, setSelectedRelationships] = useState<BeliefRelationships | null>(null);
  const [selfCritiqueEvaluations, setSelfCritiqueEvaluations] = useState<Record<string, SelfCritiqueEvaluation>>({});
  const [specialistGateOpen, setSpecialistGateOpen] = useState(false);
  const [specialistCases, setSpecialistCases] = useState<SpecialistCase[]>([]);
  const [specialistReadiness, setSpecialistReadiness] = useState<SpecialistReadiness | null>(null);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [evaluationOpen, setEvaluationOpen] = useState(false);
  const [evaluationCases, setEvaluationCases] = useState<EvaluationCase[]>([]);
  const [failureReports, setFailureReports] = useState<FailureReport[]>([]);
  const [failureSubmissionNotice, setFailureSubmissionNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const failureSubmissionInFlight = useRef(false);

  async function beginConversation() {
    setError(null); setPending(true);
    try { setConversation(await request<Conversation>("/api/conversations", { method: "POST", body: JSON.stringify({}) })); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to start a conversation."); }
    finally { setPending(false); }
  }

  async function refreshLedger(selectId?: string) {
    const summaries = await request<BeliefSummary[]>("/api/beliefs");
    setBeliefs(summaries);
    const target = selectId ?? selectedBelief?.id ?? summaries[0]?.id;
    if (target) { const [belief, relationships] = await Promise.all([request<Belief>(`/api/beliefs/${target}`), request<BeliefRelationships>(`/api/beliefs/${target}/relationships`)]); setSelectedBelief(belief); setSelectedRelationships(relationships); } else { setSelectedBelief(null); setSelectedRelationships(null); }
  }

  async function openLedger() {
    setError(null); setPending(true);
    try { await refreshLedger(); setLedgerOpen(true); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load the Belief Ledger."); }
    finally { setPending(false); }
  }

  async function saveBelief(analysis: TribunalAnalysis, messageId: string) {
    setError(null); setPending(true);
    try {
      const belief = await request<Belief>("/api/beliefs", { method: "POST", body: JSON.stringify({ proposition: analysis.proposition, user_confidence: analysis.user_confidence, source_analysis_message_id: messageId, falsification_conditions: analysis.falsification_conditions }) });
      setLedgerOpen(true); await refreshLedger(belief.id);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to save this belief."); }
    finally { setPending(false); }
  }

  async function evaluateSelfCritique(messageId: string) {
    setError(null); setPending(true);
    try {
      const evaluation = await request<SelfCritiqueEvaluation>(`/api/analyses/${messageId}/self-critique-evaluation`, { method: "POST" });
      setSelfCritiqueEvaluations((current) => ({ ...current, [messageId]: evaluation }));
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to evaluate XOD's self-critique."); }
    finally { setPending(false); }
  }

  async function refreshSpecialistGate() {
    const [cases, readiness] = await Promise.all([
      request<SpecialistCase[]>("/api/specialist-readiness/cases"),
      request<SpecialistReadiness>("/api/specialist-readiness"),
    ]);
    setSpecialistCases(cases); setSpecialistReadiness(readiness);
  }

  async function openSpecialistGate() {
    setError(null); setPending(true);
    try { await refreshSpecialistGate(); setSpecialistGateOpen(true); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load the specialist evaluation gate."); }
    finally { setPending(false); }
  }

  async function openAnalytics() {
    setError(null); setPending(true);
    try { setAnalytics(await request<Analytics>("/api/analytics")); setAnalyticsOpen(true); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load epistemic analytics."); }
    finally { setPending(false); }
  }

  async function refreshEvaluationPanel() {
    const [cases, reports] = await Promise.all([request<EvaluationCase[]>("/api/evaluation-suite/cases"), request<FailureReport[]>("/api/failure-reports")]);
    setEvaluationCases(cases); setFailureReports(reports);
  }

  async function openEvaluationPanel() {
    setError(null); setPending(true);
    try { await refreshEvaluationPanel(); setEvaluationOpen(true); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load the evaluation suite."); }
    finally { setPending(false); }
  }

  async function recordFailure(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (failureSubmissionInFlight.current) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const payload: FailureReportPayload = { category: String(data.get("category")), summary: String(data.get("summary")), expected_behavior: String(data.get("expected_behavior") || "") || null, evaluation_case_id: String(data.get("evaluation_case_id") || "") || null };
    setError(null); setFailureSubmissionNotice(null); setPending(true);
    try {
      const submitted = await submitFailureReport({ form, payload, inFlight: failureSubmissionInFlight, createReport: (report) => request("/api/failure-reports", { method: "POST", body: JSON.stringify(report) }) });
      if (!submitted) return;
      setFailureSubmissionNotice("Observed failure recorded.");
      await refreshEvaluationPanel();
    }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to record the observed failure."); }
    finally { setPending(false); }
  }

  async function recordSpecialistMeasurement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setError(null); setPending(true);
    const number = (name: string) => Number(data.get(name));
    try { await request("/api/specialist-readiness/measurements", { method: "POST", body: JSON.stringify({ case_id: data.get("case_id"), baseline_quality: number("baseline_quality"), specialist_quality: number("specialist_quality"), baseline_cost_usd: number("baseline_cost_usd"), specialist_cost_usd: number("specialist_cost_usd"), baseline_latency_ms: number("baseline_latency_ms"), specialist_latency_ms: number("specialist_latency_ms") }) }); event.currentTarget.reset(); await refreshSpecialistGate(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to record the paired measurement."); }
    finally { setPending(false); }
  }

  async function selectBelief(id: string) {
    setError(null); setPending(true);
    try { const [belief, relationships] = await Promise.all([request<Belief>(`/api/beliefs/${id}`), request<BeliefRelationships>(`/api/beliefs/${id}/relationships`)]); setSelectedBelief(belief); setSelectedRelationships(relationships); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load this belief."); }
    finally { setPending(false); }
  }

  async function addEvidence(event: FormEvent<HTMLFormElement>, beliefId: string) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setError(null); setPending(true);
    const numberOrNull = (name: string) => data.get(name) === "" ? null : Number(data.get(name));
    try { await request(`/api/beliefs/${beliefId}/evidence`, { method: "POST", body: JSON.stringify({ claim: data.get("claim"), source: data.get("source"), source_type: data.get("source_type"), direction: data.get("direction"), url: data.get("url") || null, retrieved_at: data.get("retrieved_at") || null, reliability: numberOrNull("reliability"), relevance: numberOrNull("relevance") }) }); event.currentTarget.reset(); await refreshLedger(beliefId); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to record evidence."); }
    finally { setPending(false); }
  }

  async function addPrediction(event: FormEvent<HTMLFormElement>, beliefId: string) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setError(null); setPending(true);
    try { await request(`/api/beliefs/${beliefId}/predictions`, { method: "POST", body: JSON.stringify({ statement: data.get("statement"), success_criteria: data.get("success_criteria"), expected_resolution_at: data.get("expected_resolution_at") || null }) }); event.currentTarget.reset(); await refreshLedger(beliefId); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to record prediction."); }
    finally { setPending(false); }
  }

  async function resolvePrediction(event: FormEvent<HTMLFormElement>, predictionId: string, beliefId: string) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setError(null); setPending(true);
    try { await request(`/api/predictions/${predictionId}/resolve`, { method: "PATCH", body: JSON.stringify({ result: data.get("result"), impact: data.get("impact") }) }); await refreshLedger(beliefId); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to resolve prediction."); }
    finally { setPending(false); }
  }

  async function addFalsificationCondition(event: FormEvent<HTMLFormElement>, beliefId: string) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setError(null); setPending(true);
    try { await request(`/api/beliefs/${beliefId}/falsification-conditions`, { method: "POST", body: JSON.stringify({ condition: data.get("condition") }) }); event.currentTarget.reset(); await refreshLedger(beliefId); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to record a falsification condition."); }
    finally { setPending(false); }
  }

  async function addRelationship(event: FormEvent<HTMLFormElement>, beliefId: string) {
    event.preventDefault(); const data = new FormData(event.currentTarget); setError(null); setPending(true);
    try { await request(`/api/beliefs/${beliefId}/relationships`, { method: "POST", body: JSON.stringify({ target_belief_id: data.get("target_belief_id"), relationship_type: data.get("relationship_type"), note: data.get("note") || null }) }); event.currentTarget.reset(); await refreshLedger(beliefId); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to record the belief relationship."); }
    finally { setPending(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const content = draft.trim(); if (!content || pending) return;
    setError(null); setPending(true);
    try {
      let active = conversation;
      if (!active) { active = await request<Conversation>("/api/conversations", { method: "POST", body: JSON.stringify({}) }); setConversation(active); }
      const path = mode === "TRIBUNAL" ? `/api/conversations/${active.id}/tribunal` : `/api/conversations/${active.id}/messages`;
      const body = mode === "TRIBUNAL" ? { content, user_confidence: confidence / 100 } : { content };
      setConversation(await request<Conversation>(path, { method: "POST", body: JSON.stringify(body) })); setDraft("");
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to complete this interrogation."); }
    finally { setPending(false); }
  }

  return <main>
    <header><div><p className="eyebrow">STATUS / ACTIVE</p><h1>XOD</h1><p className="subtitle">Executive Objection Daemon</p></div><div className="controls"><div className="mode-selector" role="group" aria-label="Analysis mode"><button className={mode === "SPAR" ? "selected" : ""} type="button" onClick={() => setMode("SPAR")}>SPAR</button><button className={mode === "TRIBUNAL" ? "selected" : ""} type="button" onClick={() => setMode("TRIBUNAL")}>TRIBUNAL</button><span>PHASE 9</span></div><div className="header-actions"><button className="quiet-button" type="button" onClick={openLedger} disabled={pending}>Belief Ledger</button><button className="quiet-button" type="button" onClick={openAnalytics} disabled={pending}>Analytics</button><button className="quiet-button" type="button" onClick={openEvaluationPanel} disabled={pending}>Evaluation</button><button className="quiet-button" type="button" onClick={openSpecialistGate} disabled={pending}>Specialist Gate</button><button className="quiet-button" type="button" onClick={beginConversation} disabled={pending}>New interrogation</button></div></div></header>
    <section className="workbench" aria-label="XOD conversation"><aside><p className="eyebrow">{mode} PROTOCOL</p><h2>{mode === "SPAR" ? "Expose the load-bearing claim." : "Put the proposition on record."}</h2><p>{mode === "SPAR" ? "XOD identifies an assumption, objection, alternative, and cheapest test." : "XOD returns a validated record of what supports, weakens, and could falsify the claim."}</p><p className="sidebar-note">Not truth. Pressure.</p>{ledgerOpen && <Ledger beliefs={beliefs} selected={selectedBelief} pending={pending} relationships={selectedRelationships} onSelect={(id) => void selectBelief(id)} onAddEvidence={(event, id) => void addEvidence(event, id)} onAddPrediction={(event, id) => void addPrediction(event, id)} onResolvePrediction={(event, predictionId, id) => void resolvePrediction(event, predictionId, id)} onAddFalsificationCondition={(event, id) => void addFalsificationCondition(event, id)} onAddRelationship={(event, id) => void addRelationship(event, id)} />}{analyticsOpen && <AnalyticsPanel analytics={analytics} />}{evaluationOpen && <EvaluationPanel cases={evaluationCases} reports={failureReports} pending={pending} notice={failureSubmissionNotice} onRecord={(event) => void recordFailure(event)} />}{specialistGateOpen && <SpecialistGate cases={specialistCases} readiness={specialistReadiness} pending={pending} onRecord={(event) => void recordSpecialistMeasurement(event)} />}</aside><section className="conversation" aria-live="polite">
      {conversation?.messages.length ? <div className="messages">{conversation.messages.map((message) => <article className={`message ${message.role.toLowerCase()}`} key={message.id}><p className="message-label">{message.role === "XOD" ? "XOD" : "YOU"}</p>{message.analysis ? <TribunalPanel analysis={message.analysis} onSave={() => void saveBelief(message.analysis!, message.id)} onEvaluate={() => void evaluateSelfCritique(message.id)} evaluation={selfCritiqueEvaluations[message.id]} pending={pending} /> : <p>{message.content}</p>}</article>)}{pending && <p className="thinking">XOD is inspecting the premise...</p>}</div> : <div className="empty-state"><p className="eyebrow">BEGIN</p><h2>State a proposition worth surviving.</h2><p>Choose SPAR for fast pressure or Tribunal for a structured record.</p></div>}
      <form onSubmit={submit}><label htmlFor="proposition">Proposition</label><textarea id="proposition" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="What would have to be true for you to be wrong?" rows={4} disabled={pending} />
        {mode === "TRIBUNAL" && <label className="confidence" htmlFor="confidence">Your confidence <output>{confidence}%</output><input id="confidence" type="range" min="0" max="100" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} disabled={pending} /></label>}
        <div className="form-footer">{error ? <p className="error" role="alert">{error}</p> : <p>Local history. Records preserve provenance and outcomes; they do not calculate truth.</p>}<button className="submit" type="submit" disabled={!draft.trim() || pending}>{pending ? "Interrogating..." : mode === "TRIBUNAL" ? "Convene Tribunal" : "Interrogate claim"}</button></div>
      </form>
    </section></section>
  </main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
