"use client";
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Activity, CheckCheck, RefreshCcw, CircleAlert } from "lucide-react";
import { CallDetails } from "./call-details";
import { callTotals, stageCosts, usd } from "@/lib/trace";
import { EvidenceChart } from "./evidence-chart";
import { LiveReset } from "./live-reset";
import type { LiveOps, Trace } from "@/lib/staff-contracts";
import type { OpsSnapshot } from "@/lib/contracts";
import { api } from "@/lib/client";
import { date, money } from "@/lib/format";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
import { Modal } from "./ui/dialog";
const stages = ["Understand", "Decide", "Act", "Verify", "Escalate"];
export function Ops() {
  const t = useTranslations();
  const { locale, config } = useApp();
  const [data, setData] = useState<OpsSnapshot | null>(null),
    [failed, setFailed] = useState(false),
    [selected, setSelected] = useState("");
  const [reset, setReset] = useState(false),
    [busy, setBusy] = useState(false),
    [done, setDone] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);
  const load = useCallback(
    async (signal?: AbortSignal): Promise<OpsSnapshot> => {
      if (config.fixtures)
        return api<OpsSnapshot>("ops/overview", undefined, signal);
      const current = await api<LiveOps>("ops/snapshot", undefined, signal);
      const traces = await Promise.all(
        current.conversation_ids.map((id) =>
          api<Trace>(`chat/sessions/${id}/trace`, undefined, signal),
        ),
      );
      return {
        source_kind: current.source_kind,
        dataset_version: current.dataset_version,
        bank_clock: current.bank_clock,
        quality: current.quality,
        metrics: current.metrics,
        freshness: {
          built_at: current.loaded_at,
          source_as_of: current.source_as_of,
          status: "unknown",
        },
        conversations: traces.map((trace) => ({
          id: trace.conversation_id,
          events: trace.events,
        })),
        results: null,
        daily_cost: [],
      };
    },
    [config.fixtures],
  );
  useEffect(() => {
    const ctrl = new AbortController();
    load(ctrl.signal)
      .then(setData)
      .catch(() => {
        if (!ctrl.signal.aborted) setLoadFailed(true);
      });
    return () => ctrl.abort();
  }, [load]);
  async function retryLoad() {
    if (busy) return;
    setBusy(true);
    setLoadFailed(false);
    try {
      setData(await load());
    } catch {
      setLoadFailed(true);
    } finally {
      setBusy(false);
    }
  }
  async function resetSpace() {
    if (busy) return;
    setBusy(true);
    setFailed(false);
    setDone(false);
    try {
      const result = await api<{ verified: boolean }>("ops/demo/reset", {
        confirmed: true,
      });
      if (!result.verified) throw new Error("Unverified");
      const next = await api<OpsSnapshot>("ops/overview");
      if (next.conversations.length) throw new Error("Read-back failed");
      setData(next);
      setSelected("");
      setReset(false);
      setDone(true);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }
  const conversation =
    data?.conversations.find((c) => c.id === selected) ??
    data?.conversations.at(-1);
  const totals = callTotals(conversation?.events ?? []);
  const costs = stageCosts(conversation?.events ?? []);
  const costMax = costs.length
    ? Math.max(...costs.map((stage) => stage.cost))
    : 0;
  const costAxisMax = costMax > 0 ? Math.ceil(costMax * 1e6) / 1e6 : 0.000001;
  const hasRisk = conversation?.events.some((event) => event.llm?.judgments);
  return (
    <>
      {!config.fixtures && (
        <p className="fixture-note">{t("workspaceScope")}</p>
      )}
      {failed && (
        <p className="error" role="alert">
          {t("error")}{" "}
          <Button variant="secondary" onClick={() => location.reload()}>
            {t("retry")}
          </Button>
        </p>
      )}
      {loadFailed ? (
        <div className="panel empty load-failed" role="alert">
          <CircleAlert size={30} />
          <p>{t("opsLoadFailed")}</p>
          <Button
            variant="secondary"
            disabled={busy}
            onClick={() => void retryLoad()}
          >
            {t("retry")}
          </Button>
        </div>
      ) : !data ? (
        <div className="panel empty" role="status">
          {t("loading")}
        </div>
      ) : (
        <>
          <div className="metric-grid">
            <div className="metric">
              <span>{t("quality")}</span>
              <strong>
                {data.quality.length
                  ? `${data.quality.filter((q) => q.passed).length}/${data.quality.length}`
                  : t("qualityNotChecked")}
              </strong>
              <small>{t("qualityChecks")}</small>
            </div>
            <div className="metric">
              <span>{t("freshness")}</span>
              <strong className="text-metric">
                {t(data.freshness.status)}
              </strong>
              <small>{date(data.freshness.built_at, locale, true)} UTC</small>
            </div>
            <div className="metric">
              <span>{t("dataset")}</span>
              <strong className="text-metric mono">
                {data.dataset_version}
              </strong>
              <small>
                {t(
                  data.source_kind === "organizer_serving"
                    ? "organizerSource"
                    : "fixture",
                )}
              </small>
            </div>
          </div>
          <section className="panel trace-panel">
            <header className="panel-heading">
              <h2>{t("trace")}</h2>
              {data.conversations.length > 0 && (
                <label>
                  <span className="sr-only">{t("conversation")}</span>
                  <select
                    value={conversation?.id ?? ""}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    {data.conversations.map((c, i) => (
                      <option key={c.id} value={c.id}>
                        {t("conversation")} {i + 1} · {c.id.slice(0, 8)}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </header>
            <ol className="stage-strip" aria-label={t("allStages")}>
              {stages.map((stage, i) => (
                <li
                  key={stage}
                  className={
                    conversation?.events.some((e) => e.stage === stage)
                      ? "executed"
                      : ""
                  }
                >
                  <span>0{i + 1}</span>
                  {t(`stage_${stage.toLowerCase()}`)}
                </li>
              ))}
            </ol>
            {!conversation ? (
              <div className="empty">
                <Activity size={30} />
                <p>{t("traceEmpty")}</p>
              </div>
            ) : (
              <div>
                <div
                  className="conversation-cost"
                  aria-label={t("conversationCost")}
                >
                  <h3>{t("conversationCost")}</h3>
                  <strong>
                    {totals.count
                      ? totals.count === totals.unknown
                        ? t("costNotRecorded")
                        : usd(totals.known, locale)
                      : t("noModelCallsRecorded")}
                  </strong>
                  <p>
                    {t("recordedCalls", { count: totals.count })} ·{" "}
                    {t("unknownCosts", { count: totals.unknown })}
                  </p>
                  <p className="caption">
                    {t(
                      !totals.count
                        ? "noModelCostMeasurement"
                        : totals.unknown
                          ? "partialCost"
                          : "recordedCostOnly",
                    )}
                  </p>
                  {costs.length > 0 && (
                    <>
                      <EvidenceChart
                        title={t("costByStage")}
                        max={costAxisMax}
                        axisLabel={t("costAxis")}
                        tick={(n) => usd(n, locale)}
                        rows={costs.map((stage) => ({
                          label: t(`stage_${stage.stage.toLowerCase()}`),
                          value: stage.cost,
                          detail: `${usd(stage.cost, locale)} · ${stage.knownCount}/${stage.count}`,
                        }))}
                      />
                      <p className="caption">
                        {t("costChartSource", {
                          known: totals.count - totals.unknown,
                          total: totals.count,
                        })}
                      </p>
                    </>
                  )}
                  {totals.grok > 0 && (
                    <p className="badge amber">
                      {t(totals.fallback ? "grokFallback" : "grokObserved")}
                    </p>
                  )}
                  {!hasRisk && (
                    <p className="caption">{t("riskUnavailable")}</p>
                  )}
                </div>
                <ol className="execution-list">
                  {conversation.events.map((event) => (
                    <li key={event.id}>
                      <span className="event-node">
                        <span />
                      </span>
                      <div>
                        <div className="row-between">
                          <strong>
                            {t(`stage_${event.stage.toLowerCase()}`)}{" "}
                            <span className="caption">/ {event.state}</span>
                          </strong>
                          {event.verified && (
                            <span className="badge">
                              <CheckCheck size={13} />
                              {t("verified")}
                            </span>
                          )}
                        </div>
                        <p className="caption">
                          {event.tool
                            ? `${t("tool")}: ${event.tool}`
                            : event.llm
                              ? t("llm")
                              : t("noLlm")}
                        </p>
                        {event.rules.length > 0 && (
                          <div className="rule-list">
                            {event.rules.map((rule) => (
                              <span key={rule} className="rule">
                                {rule}
                              </span>
                            ))}
                          </div>
                        )}
                        {event.llm && <CallDetails call={event.llm} />}
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </section>
          <div className="ops-grid">
            <section className="panel data-panel">
              <h2>{t("quality")}</h2>
              {data.quality.map((q) => (
                <div className="quality-row" key={q.name}>
                  <span>
                    {q.passed ? (
                      <CheckCheck size={16} />
                    ) : (
                      <CircleAlert size={16} className="failed-icon" />
                    )}
                    {t.has(q.name) ? t(q.name) : q.name} ·{" "}
                    {q.passed ? t("verified") : t("unverified")}
                  </span>
                  <span>
                    {q.checked} {t("checked")}
                  </span>
                </div>
              ))}
              {!data.quality.length && (
                <p className="caption">{t("qualityNotChecked")}</p>
              )}
              <dl className="metadata-list compact">
                <dt>{t("built")}</dt>
                <dd>{date(data.freshness.built_at, locale, true)}</dd>
                <dt>{t("sourceAsOf")}</dt>
                <dd>{date(data.freshness.source_as_of, locale, true)}</dd>
              </dl>
              <h3>{t("lineage")}</h3>
              <a
                href="/dbt-lineage.svg"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Image
                  src="/dbt-lineage.svg"
                  width={1368}
                  height={720}
                  alt={t("lineageAlt")}
                  className="lineage-image"
                />
              </a>
              <a
                className="lineage-zoom"
                href="/dbt-lineage.svg"
                target="_blank"
                rel="noopener noreferrer"
              >
                {t("lineageZoom")}
              </a>
              <p className="caption">{t("lineageAlt")}</p>
            </section>
            <section className="panel data-panel">
              {data.results ? (
                <>
                  <h2>{t("results")}</h2>
                  <p className="badge amber">{t("illustrative")}</p>
                  <div className="result-numbers">
                    <div>
                      <strong>{data.results.cases}</strong>
                      <span>{t("cases")}</span>
                    </div>
                    <div>
                      <strong>{data.results.passed}</strong>
                      <span>{t("passed")}</span>
                    </div>
                    <div>
                      <strong>{data.results.unsafe}</strong>
                      <span>{t("unsafe")}</span>
                    </div>
                  </div>
                  <p className="caption">
                    {data.results.source} · {t("humanPending")}
                  </p>
                  {data.daily_cost.length > 0 && (
                    <EvidenceChart
                      title={t("daily")}
                      max={Math.max(
                        0.01,
                        ...data.daily_cost.map((day) => day.usd),
                      )}
                      axisLabel={t("costAxis")}
                      tick={(n) => usd(n, locale)}
                      rows={data.daily_cost.map((day) => ({
                        label: date(day.date, locale),
                        value: day.usd,
                        detail: usd(day.usd, locale),
                      }))}
                    />
                  )}
                  <p className="caption">{t("illustrativeCostSource")}</p>
                  <p className="caption">{t("zeroCost")}</p>
                </>
              ) : (
                data.metrics && (
                  <>
                    <h2>{t("workspaceMetrics")}</h2>
                    <p className="badge amber">{t("notEvaluation")}</p>
                    <dl className="metadata-list">
                      <dt>{t("cases")}</dt>
                      <dd>{data.metrics.cases}</dd>
                      <dt>{t("handoffs")}</dt>
                      <dd>{data.metrics.handoffs}</dd>
                      <dt>{t("conversationsCount")}</dt>
                      <dd>{data.metrics.conversations}</dd>
                      <dt>{t("executionRecords")}</dt>
                      <dd>{data.metrics.execution_records}</dd>
                      <dt>{t("observedCost")}</dt>
                      <dd>
                        {money(
                          data.metrics.observed_model_cost_usd,
                          "USD",
                          locale,
                        )}
                      </dd>
                      <dt>SAR</dt>
                      <dd>{t("notMeasured")}</dd>
                      <dt>{t("unsafe")}</dt>
                      <dd>{t("notMeasured")}</dd>
                    </dl>
                    <p className="caption">{t("dailyUnavailable")}</p>
                  </>
                )
              )}
            </section>
          </div>
          {!config.fixtures ? (
            <LiveReset
              enabled={config.resetEnabled === true}
              onReset={async () => {
                setData(await load());
                setSelected("");
              }}
            />
          ) : (
            <div className="reset-panel">
              <div>
                <h3>{t("reset")}</h3>
                <p>{t("fixtureNote")}</p>
                {done && (
                  <p className="verified-note" role="status">
                    <CheckCheck size={17} />
                    {t("resetDone")}
                  </p>
                )}
              </div>
              <Button variant="secondary" onClick={() => setReset(true)}>
                <RefreshCcw size={16} />
                {t("reset")}
              </Button>
            </div>
          )}
        </>
      )}
      <Modal
        open={reset}
        onOpenChange={setReset}
        title={t("resetTitle")}
        description={t("resetBody")}
        closeLabel={t("close")}
        busy={busy}
      >
        <div className="dialog-actions">
          <Button
            variant="secondary"
            onClick={() => setReset(false)}
            disabled={busy}
          >
            {t("cancel")}
          </Button>
          <Button
            variant="danger"
            onClick={() => void resetSpace()}
            disabled={busy}
          >
            {busy ? t("loading") : t("confirm")}
          </Button>
        </div>
      </Modal>
    </>
  );
}
