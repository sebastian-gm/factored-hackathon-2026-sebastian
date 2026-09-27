"use client";
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import {
  Activity,
  CheckCheck,
  Database,
  RefreshCcw,
  ShieldCheck,
} from "lucide-react";
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
        if (!ctrl.signal.aborted) setFailed(true);
      });
    return () => ctrl.abort();
  }, [load]);
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
      {!data ? (
        <div className="panel empty" role="status">
          {t("loading")}
        </div>
      ) : (
        <>
          <div className="metric-grid">
            <div className="metric">
              <span>
                <Database size={17} />
                {t("quality")}
              </span>
              <strong>
                {data.quality.filter((q) => q.passed).length}/
                {data.quality.length}
              </strong>
              <small>{t("schema")}</small>
            </div>
            <div className="metric">
              <span>
                <RefreshCcw size={17} />
                {t("freshness")}
              </span>
              <strong className="text-metric">
                {t(data.freshness.status)}
              </strong>
              <small>{date(data.freshness.built_at, locale, true)} UTC</small>
            </div>
            <div className="metric">
              <span>
                <ShieldCheck size={17} />
                {t("dataset")}
              </span>
              <strong className="text-metric mono">
                {data.dataset_version}
              </strong>
              <small>{t("fixture")}</small>
            </div>
          </div>
          <section className="panel trace-panel">
            <header className="panel-heading">
              <h2>
                <Activity size={19} />
                {t("trace")}
              </h2>
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
                  {stage}
                </li>
              ))}
            </ol>
            {!conversation ? (
              <div className="empty">
                <Activity size={30} />
                <p>{t("traceEmpty")}</p>
              </div>
            ) : (
              <ol className="execution-list">
                {conversation.events.map((event) => (
                  <li key={event.id}>
                    <span className="event-node">
                      <span />
                    </span>
                    <div>
                      <div className="row-between">
                        <strong>
                          {event.stage}{" "}
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
                      {event.llm && (
                        <dl className="llm-metadata" aria-label={t("llm")}>
                          <div>
                            <dt>Provider / model</dt>
                            <dd>
                              {event.llm.provider} / {event.llm.model}
                            </dd>
                          </div>
                          <div>
                            <dt>Prompt</dt>
                            <dd>{event.llm.prompt_version}</dd>
                          </div>
                          <div>
                            <dt>Tokens in / out</dt>
                            <dd>
                              {event.llm.input_tokens} /{" "}
                              {event.llm.output_tokens}
                            </dd>
                          </div>
                          <div>
                            <dt>Cost / latency</dt>
                            <dd>
                              {event.llm.cost_usd === null
                                ? "—"
                                : money(event.llm.cost_usd, "USD", locale)}{" "}
                              / {event.llm.latency_ms} ms
                            </dd>
                          </div>
                        </dl>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>
          <div className="ops-grid">
            <section className="panel data-panel">
              <h2>{t("quality")}</h2>
              {data.quality.map((q) => (
                <div className="quality-row" key={q.name}>
                  <span>
                    <CheckCheck size={16} />
                    {t.has(q.name) ? t(q.name) : q.name} ·{" "}
                    {q.passed ? t("verified") : t("unverified")}
                  </span>
                  <span>
                    {q.checked} {t("checked")}
                  </span>
                </div>
              ))}
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
                  <h3>{t("daily")}</h3>
                  <div className="cost-table">
                    {data.daily_cost.map((day) => (
                      <div key={day.date}>
                        <span>{date(day.date, locale)}</span>
                        <strong>{money(day.usd, "USD", locale)}</strong>
                      </div>
                    ))}
                  </div>
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
