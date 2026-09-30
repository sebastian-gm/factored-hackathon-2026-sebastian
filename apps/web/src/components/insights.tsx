"use client";

import Image from "next/image";
import { useEffect, useState, type ReactNode } from "react";
import { ArrowRight, Check, Database, ShieldCheck } from "lucide-react";
import snapshot from "@/data/insights.json";
import { insightsEs, insightsPt } from "@/lib/insights-copy";
import {
  insightsResultsSchema,
  type InsightsResults,
} from "@/lib/insights-results";
import { useApp } from "./workspace";
import { Button } from "./ui/button";

type Count = { count: number; denominator: number };
const sourceUrl = (source: { path: string; commit: string }) =>
  `https://github.com/sebastian-gm/bank-agent-lab/blob/${source.commit}/${source.path}`;

function useInsightsFormat() {
  const { locale } = useApp();
  const c = locale === "pt-BR" ? insightsPt : insightsEs;
  const number = (n: number, digits = 0) =>
    new Intl.NumberFormat(locale, {
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(n);
  const percent = (n: number, digits = 1) =>
    new Intl.NumberFormat(locale, {
      style: "percent",
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(n);
  const ratio = (value: Count) =>
    `${number(value.count)} / ${number(value.denominator)}`;
  const signed = (n: number) =>
    `${n > 0 ? "+" : ""}${number(n, Number.isInteger(n) ? 0 : 2)}`;
  return { c, number, percent, ratio, signed };
}

function Source({ id }: { id: string }) {
  const { c } = useInsightsFormat();
  const index = snapshot.sources.findIndex((s) => s.id === id);
  const source = snapshot.sources[index];
  return (
    <a
      className="insights-ref"
      href={`#insights-source-${id}`}
      aria-label={`${c.source}: ${source.path}`}
    >
      [{index + 1}]
    </a>
  );
}
function Metric({
  title,
  value,
  note,
  source,
}: {
  title: string;
  value: ReactNode;
  note?: ReactNode;
  source: string;
}) {
  return (
    <div className="insights-metric">
      <p>
        {title} <Source id={source} />
      </p>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}
function Bar({
  label,
  value,
  detail,
  variant = "p",
}: {
  label: string;
  value: number;
  detail: string;
  variant?: "p" | "b1";
}) {
  return (
    <div className={`insights-bar ${variant}`}>
      <div>
        <span>{label}</span>
        <strong>{detail}</strong>
      </div>
      <div className="insights-bar-track" aria-hidden="true">
        <span style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}
function Interval({ delta }: { delta: { estimate: number; ci95: number[] } }) {
  const { c, signed } = useInsightsFormat();
  const bound = Math.max(20, ...delta.ci95.map(Math.abs)) * 1.2;
  const x = (n: number) => 30 + ((n + bound) / (2 * bound)) * 340;
  const description = `${c.sarShort}: ${signed(delta.estimate)} ${c.pp}. ${c.ci}: ${signed(delta.ci95[0])} ${c.pp} — ${signed(delta.ci95[1])} ${c.pp}.`;
  return (
    <figure className="insights-interval">
      <figcaption>
        {c.sarShort}
        <strong>
          {signed(delta.estimate)} {c.pp}
        </strong>
      </figcaption>
      <svg viewBox="0 0 400 68" role="img" aria-label={description}>
        <line x1="30" x2="370" y1="30" y2="30" className="interval-axis" />
        <line x1={x(0)} x2={x(0)} y1="8" y2="54" className="interval-zero" />
        <line
          x1={x(delta.ci95[0])}
          x2={x(delta.ci95[1])}
          y1="30"
          y2="30"
          className="interval-range"
        />
        <circle cx={x(delta.estimate)} cy="30" r="7" className="interval-dot" />
      </svg>
      <p>
        {c.ci}:{" "}
        <strong>
          {signed(delta.ci95[0])} → {signed(delta.ci95[1])} {c.pp}
        </strong>
      </p>
    </figure>
  );
}

export function Insights({ onTry }: { onTry: () => void }) {
  const { locale } = useApp();
  const c = locale === "pt-BR" ? insightsPt : insightsEs;
  const [version, setVersion] = useState<"v2" | "v3">("v3");
  const [step, setStep] = useState(0);
  const [workloadIndex, setWorkloadIndex] = useState(1);
  const [publication, setPublication] = useState<InsightsResults | null>(null);
  const [publicationError, setPublicationError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/insights-results.json", { cache: "no-store", signal: ctrl.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Publication unavailable");
        return insightsResultsSchema.parse(await response.json());
      })
      .then(setPublication)
      .catch(() => {
        if (!ctrl.signal.aborted) setPublicationError(true);
      });
    return () => ctrl.abort();
  }, [retry]);
  const { number, percent, ratio } = useInsightsFormat();
  const problem = snapshot.problem;
  const evaluation = snapshot.evaluations[version];
  const v3 = snapshot.evaluations.v3;
  const matcher = snapshot.matcher;
  const workload = matcher.workloads[workloadIndex];
  return (
    <div className="insights-page">
      <section className="insights-hero" aria-labelledby="insights-hero-title">
        <div>
          <span className="insights-data-badge">
            <Database size={14} />
            {c.dataBadge}
          </span>
          <h2 id="insights-hero-title">{c.hero}</h2>
          <p>{c.heroBody}</p>
          <div className="insights-hero-actions">
            <Button onClick={onTry}>
              {c.try}
              <ArrowRight size={16} />
            </Button>
            <a href="#insights-evidence">{c.explore} ↓</a>
          </div>
        </div>
        <div className="insights-hero-stat">
          <strong>{percent(problem.fcr)}</strong>
          <p>
            {c.fcr} <Source id={problem.source} />
          </p>
          <small>
            {number(problem.fcr_denominator)} {c.contacts}
          </small>
        </div>
      </section>

      <section
        className="insights-section"
        aria-labelledby="insights-problem-title"
      >
        <div className="insights-section-heading">
          <p className="eyebrow">{c.problem}</p>
          <h2 id="insights-problem-title">{c.problemBody}</h2>
        </div>
        <div className="insights-problem-grid">
          <div className="insights-card">
            <h3>
              {c.complaints} <Source id="demand" />
            </h3>
            <Bar
              label={c.volume}
              value={problem.volume_share}
              detail={percent(problem.volume_share)}
              variant="b1"
            />
            <Bar
              label={c.handle}
              value={problem.handle_time_share}
              detail={percent(problem.handle_time_share)}
            />
            <p className="insights-note">
              {c.fcrNote} <Source id="problem" />
            </p>
          </div>
          <div className="insights-kpis">
            <Metric
              title={c.unrecognized}
              value={number(problem.charge_complaints)}
              source="demand"
            />
            <Metric
              title={c.sla}
              value={percent(problem.sla_breach_share)}
              source="demand"
            />
            <Metric
              title={c.resolution}
              value={number(problem.mean_resolution_calendar_days, 1)}
              source="demand"
              note={
                <>
                  {c.resolutionNote} · {number(problem.resolution_days_n)}{" "}
                  {c.records}
                </>
              }
            />
          </div>
        </div>
      </section>

      <section
        className="insights-section"
        aria-labelledby="insights-decide-title"
      >
        <div className="insights-section-heading">
          <p className="eyebrow">{c.loop}</p>
          <h2 id="insights-decide-title">{c.decide}</h2>
          <p>
            {c.decideBody} <Source id="policy" />
          </p>
        </div>
        <div className="insights-loop" role="tablist" aria-label={c.loopAria}>
          {c.steps.map((s, i) => (
            <button
              key={s.english}
              id={`insights-step-${i}`}
              role="tab"
              type="button"
              aria-selected={step === i}
              tabIndex={step === i ? 0 : -1}
              aria-controls="insights-step-panel"
              onClick={() => setStep(i)}
              onKeyDown={(event) => {
                if (
                  !["ArrowRight", "ArrowLeft", "Home", "End"].includes(
                    event.key,
                  )
                )
                  return;
                event.preventDefault();
                const next =
                  event.key === "Home"
                    ? 0
                    : event.key === "End"
                      ? c.steps.length - 1
                      : (i +
                          (event.key === "ArrowRight" ? 1 : -1) +
                          c.steps.length) %
                        c.steps.length;
                setStep(next);
                document.getElementById(`insights-step-${next}`)?.focus();
              }}
            >
              <span className="insights-step-symbol" aria-hidden="true">
                {i === 3 ? <Check size={18} /> : ["◎", "◇", "↗", "✓", "↪"][i]}
              </span>
              <strong>{s.title}</strong>
              <small>{s.english}</small>
            </button>
          ))}
        </div>
        <div
          className="insights-step-panel"
          id="insights-step-panel"
          role="tabpanel"
          tabIndex={0}
          aria-labelledby={`insights-step-${step}`}
        >
          <ShieldCheck size={22} />
          <p>
            {c.steps[step].body} <Source id="policy" />
          </p>
        </div>
        <h3 className="insights-subheading">
          {c.autonomy} <Source id="policy" />
        </h3>
        <div className="insights-autonomy">
          {c.autonomyColumns.map((title, column) => (
            <div className="insights-card" key={title}>
              <span className="insights-category-dot" aria-hidden="true" />
              <h4>{title}</h4>
              <ul>
                {c.autonomyRows.map((row) => (
                  <li key={row[column]}>{row[column]}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="insights-note">
          {c.authorityNote} <Source id="policy" />
        </p>
      </section>

      <section
        id="insights-evidence"
        className="insights-section"
        aria-labelledby="insights-evidence-title"
      >
        <div className="insights-section-heading">
          <p className="eyebrow">{c.comparison}</p>
          <h2 id="insights-evidence-title">{c.evidence}</h2>
          <p>{c.evidenceBody}</p>
        </div>
        <ol className="insights-timeline">
          {[
            {
              id: "v1",
              status: c.abandoned,
              note: c.v1Note,
              source: "disclosure",
            },
            { id: "v2", status: c.official, note: c.v2Note, source: "v2" },
            { id: "v3", status: c.fresh, note: c.v3Note, source: "v3" },
            {
              id: "v4",
              status:
                publication && publication.status !== "pending"
                  ? c[publication.status]
                  : c.pending,
              note:
                publication && publication.status !== "pending"
                  ? c.v4PublishedNote
                  : c.v4Note,
              source: null,
            },
          ].map((item) => (
            <li key={item.id}>
              <span>{item.id}</span>
              <strong>
                {item.status} {item.source && <Source id={item.source} />}
              </strong>
              <p>{item.note}</p>
            </li>
          ))}
        </ol>
        <div
          className="insights-segmented"
          role="group"
          aria-label={c.comparison}
        >
          {(["v2", "v3"] as const).map((v) => (
            <button
              key={v}
              aria-pressed={version === v}
              onClick={() => setVersion(v)}
            >
              {v} · {v === "v2" ? c.official : c.fresh}
            </button>
          ))}
        </div>
        <div
          className="insights-results-grid"
          data-testid="insights-comparison"
        >
          <div className="insights-card">
            <h3>
              {c.pass} <Source id={evaluation.source} />
            </h3>
            {(["B1", "P"] as const).map((system) => {
              const value = evaluation.systems[system].pass;
              return (
                <Bar
                  key={system}
                  label={system === "P" ? c.p : c.b1}
                  value={value.count / value.denominator}
                  variant={system === "P" ? "p" : "b1"}
                  detail={`${percent(value.count / value.denominator)} · ${ratio(value)}`}
                />
              );
            })}
            <h3 className="insights-subheading">
              {c.sar} <Source id={evaluation.source} />
            </h3>
            {(["B1", "P"] as const).map((system) => {
              const value = evaluation.systems[system].sar;
              return (
                <Bar
                  key={system}
                  label={system === "P" ? c.p : c.b1}
                  value={value.count / value.denominator}
                  variant={system === "P" ? "p" : "b1"}
                  detail={`${percent(value.count / value.denominator)} · ${ratio(value)}`}
                />
              );
            })}
          </div>
          <div className="insights-card">
            <Interval delta={evaluation.sar_difference_pp} />
            <Source id={evaluation.source} />
            <p className="insights-note">{c.notComparable}</p>
          </div>
        </div>
        <div className="insights-safety">
          <div>
            <ShieldCheck size={24} />
            <Metric
              title={`${c.safety} · v3`}
              value={ratio(v3.unauthorized_actions.P)}
              source="v3"
              note={`${c.safetyLimit}: ${number(v3.unauthorized_actions.p_wilson_upper95_percent, 2)}%`}
            />
          </div>
          <div>
            <Metric
              title={`${c.flips} · v3`}
              value={ratio(v3.repeats)}
              source="v3"
              note={`${c.ci}: ${v3.repeats.ci95_percent.map((n) => number(n, n === 0 ? 0 : 2)).join("–")}%`}
            />
            <p className="insights-note">{c.flipsNote}</p>
          </div>
          <p className="insights-caution">
            {c.safetyGate} <Source id="v3" />
          </p>
          <p className="insights-note">
            {c.judging} · v3: {number(v3.judging.completed)} /{" "}
            {number(v3.judging.planned)}. {c.humanPending} <Source id="v3" />
          </p>
        </div>
        <div className="insights-results-grid">
          <div className="insights-card">
            <Metric
              title={`${c.cost} · P · ${version}`}
              value={`US$ ${number(evaluation.systems.P.model_cost_per_conversation_usd, 4)}`}
              source={evaluation.source}
              note={c.costNote}
            />
          </div>
          <div className="insights-card">
            <Metric
              title={`${c.turn} · P · ${version}`}
              value={`${number(evaluation.systems.P.turn_seconds[0], 2)} ${c.seconds}`}
              source={evaluation.source}
              note={`${c.median} · ${c.p95}: ${number(evaluation.systems.P.turn_seconds[1], 2)} ${c.seconds}`}
            />
            <p className="insights-note">{c.latencyNote}</p>
          </div>
        </div>
        <section
          className="insights-publication insights-card"
          aria-labelledby="v4-title"
          data-testid="insights-v4"
        >
          <h3 id="v4-title">
            v4 ·{" "}
            {publication && publication.status !== "pending"
              ? c[publication.status]
              : c.pending}
          </h3>
          {publicationError ? (
            <>
              <p role="alert">{c.v4Unavailable}</p>
              <Button
                variant="secondary"
                onClick={() => {
                  setPublication(null);
                  setPublicationError(false);
                  setRetry((n) => n + 1);
                }}
              >
                {c.retry}
              </Button>
            </>
          ) : !publication ? (
            <p role="status">{c.v4Loading}</p>
          ) : publication.status === "pending" ? (
            <p>{c.v4Note}</p>
          ) : (
            <>
              <div className="insights-results-grid">
                {(["B1", "P"] as const).map((s) => (
                  <div key={s}>
                    <h4>{s === "P" ? c.p : c.b1}</h4>
                    <p>
                      {c.pass}:{" "}
                      <strong>{ratio(publication.systems[s].pass)}</strong>
                    </p>
                    <p>
                      {c.sar}:{" "}
                      <strong>{ratio(publication.systems[s].sar)}</strong>
                    </p>
                  </div>
                ))}
              </div>
              <Interval delta={publication.sar_difference_pp} />
              <p>
                {c.safety}:{" "}
                <strong>{ratio(publication.unauthorized_actions)}</strong>
              </p>
              <p
                className={
                  publication.safety_gate === "passed"
                    ? "insights-note"
                    : "insights-caution"
                }
              >
                {publication.safety_gate === "passed"
                  ? c.gatePassed
                  : c.gateFailed}
              </p>
              <a
                href={sourceUrl(publication.source)}
                target="_blank"
                rel="noreferrer"
              >
                {c.viewSource}: {publication.source.path}
              </a>
              <details>
                <summary>
                  {c.hash} / {c.sourceCommit}
                </summary>
                <code>{publication.source.sha256}</code>
                <code>{publication.source.commit}</code>
              </details>
            </>
          )}
        </section>
      </section>

      <section className="insights-section" aria-labelledby="insights-ml-title">
        <div className="insights-section-heading">
          <p className="eyebrow">Charge matcher v2</p>
          <h2 id="insights-ml-title">{c.ml}</h2>
          <p>
            {c.mlBody} <Source id="matcher" />
          </p>
        </div>
        <div className="insights-training">
          <Metric
            title={c.train}
            value={number(matcher.training_queries)}
            source="matcher"
          />
          <Metric
            title={c.validation}
            value={number(matcher.validation_queries)}
            source="matcher"
          />
        </div>
        <div
          className="insights-segmented"
          role="group"
          aria-label={c.matcherAria}
        >
          {[c.original, c.sparse].map((label, i) => (
            <button
              key={label}
              aria-pressed={workloadIndex === i}
              onClick={() => setWorkloadIndex(i)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="insights-card" data-testid="insights-matcher">
          <h3>
            {c.diagnostic} <Source id="matcher" />
          </h3>
          <p className="insights-note">
            {number(workload.v2.queries)} {c.queries} ·{" "}
            {number(workload.v2.targets)} {c.targets}{" "}
            <Source id="matcherMetrics" />
          </p>
          <div className="insights-results-grid">
            <div>
              {(["v1", "v2"] as const).map((v) => (
                <Bar
                  key={v}
                  label={`${c.top1} · ${v}`}
                  value={workload[v].top1}
                  detail={percent(workload[v].top1, 2)}
                  variant={v === "v1" ? "b1" : "p"}
                />
              ))}
            </div>
            <div className="insights-kpis">
              <Metric
                title={`${c.recall3} · v2`}
                value={percent(workload.v2.recall3, 2)}
                source="matcherMetrics"
              />
              <Metric
                title={`${c.wrong} · v2`}
                value={`${number(workload.v2.wrong_proposals)} / ${number(workload.v2.proposals)}`}
                source="matcherMetrics"
              />
            </div>
          </div>
          <p className="insights-note">{c.matcherLimit}</p>
          <p className="insights-caution">{c.matcherTradeoff}</p>
        </div>
        <div className="insights-tracking">
          <Database size={23} />
          <div>
            <h3>{c.tracking}</h3>
            <p>
              {c.trackingBody} <Source id="tracking" />
              <Source id="matcher" />
            </p>
          </div>
        </div>
      </section>

      <section
        className="insights-section"
        aria-labelledby="insights-pipeline-title"
      >
        <div className="insights-section-heading">
          <p className="eyebrow">dbt · {c.pipeline}</p>
          <h2 id="insights-pipeline-title">
            {c.pipelineBody} <Source id="pipeline" />
          </h2>
        </div>
        <ol className="insights-pipeline">
          {c.pipelineSteps.map((s) => (
            <li key={s.title}>
              <Database size={22} />
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </li>
          ))}
        </ol>
        <details className="insights-lineage insights-card">
          <summary>{c.lineage}</summary>
          <p className="insights-note">
            {c.lineageNote} <Source id="lineage" />
          </p>
          <a href="/dbt-lineage.svg" target="_blank" rel="noreferrer">
            <Image
              unoptimized
              src="/dbt-lineage.svg"
              alt={c.lineageAlt}
              width="960"
              height="640"
              loading="lazy"
            />
          </a>
        </details>
      </section>

      <section
        id="insights-sources"
        className="insights-section insights-sources"
        aria-labelledby="insights-sources-title"
      >
        <h2 id="insights-sources-title">{c.sources}</h2>
        <p>{c.sourcesBody}</p>
        <ol>
          {snapshot.sources.map((source) => (
            <li key={source.id} id={`insights-source-${source.id}`}>
              <a href={sourceUrl(source)} target="_blank" rel="noreferrer">
                {source.path} <ArrowRight size={14} />
              </a>
              <details>
                <summary>
                  {c.hash} / {c.sourceCommit}
                </summary>
                <p>{c.hash}</p>
                <code>{source.sha256}</code>
                <p>{c.sourceCommit}</p>
                <code>{source.commit}</code>
              </details>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
