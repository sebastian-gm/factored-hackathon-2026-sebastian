"use client";
import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import {
  ArrowUpRight,
  CheckCheck,
  ClipboardCheck,
  Clock3,
  FileSearch,
  CircleAlert,
} from "lucide-react";
import { orderedReasons, type DeskPacket } from "@/lib/contracts";
import { api } from "@/lib/client";
import { date, remaining } from "@/lib/format";
import {
  deskActionLabelKey,
  handoffReasonLabelKey,
  riskFlagLabelKey,
} from "@/lib/ui-copy";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
import { Modal } from "./ui/dialog";
import { TransactionCard } from "./transaction-card";
export function AgentDesk() {
  const t = useTranslations();
  const { config, locale } = useApp();
  const [packets, setPackets] = useState<DeskPacket[]>([]),
    [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(false),
    [resolve, setResolve] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const packetPanel = useRef<HTMLElement>(null);
  const [evidence, setEvidence] = useState<
      DeskPacket["evidence"][number] | null
    >(null),
    [clock, setClock] = useState("");
  useEffect(() => {
    let tick = 0;
    const base = Date.parse(config.bankClock ?? "");
    const advance = () => {
      // Operational deadlines use wall time. Only authored fixtures share the
      // frozen ledger clock; transaction eligibility still uses bankClock.
      const now = config.fixtures ? base + tick++ * 60000 : Date.now();
      setClock(Number.isFinite(now) ? new Date(now).toISOString() : "");
    };
    advance();
    const timer = setInterval(advance, 60000);
    return () => clearInterval(timer);
  }, [config.fixtures, config.bankClock]);
  async function load() {
    setLoading(true);
    setLoadError(false);
    try {
      const values = await api<DeskPacket[]>("agent/handoffs");
      setPackets(values);
      setLoadError(false);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    const c = new AbortController();
    api<DeskPacket[]>("agent/handoffs", undefined, c.signal)
      .then(setPackets)
      .catch(() => {
        if (!c.signal.aborted) setLoadError(true);
      })
      .finally(() => {
        if (!c.signal.aborted) setLoading(false);
      });
    return () => c.abort();
  }, []);
  const current = packets.find((p) => p.handoff_id === selected) ?? packets[0];
  async function act(action: "claim" | "resolve") {
    if (!current || busy) return;
    setBusy(true);
    setError(false);
    try {
      if (!config.fixtures && !current.version)
        throw new Error("Missing version");
      await api(
        `agent/handoffs/${current.handoff_id}/${action}`,
        config.fixtures
          ? {}
          : {
              expected_version: current.version,
              idempotency_key: crypto.randomUUID(),
              ...(action === "resolve"
                ? { resolution: "review_completed" }
                : {}),
            },
      );
      const verified = await api<DeskPacket>(
        `agent/handoffs/${current.handoff_id}`,
      );
      if (
        verified.handoff_id !== current.handoff_id ||
        verified.status !== (action === "claim" ? "claimed" : "resolved") ||
        (!config.fixtures &&
          (verified.version !== current.version! + 1 || !verified.verified))
      )
        throw new Error("Read-back failed");
      setPackets((items) =>
        items.map((p) => (p.handoff_id === verified.handoff_id ? verified : p)),
      );
      setResolve(false);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      {!config.fixtures && (
        <p className="fixture-note">{t("workspaceScope")}</p>
      )}
      <div className="desk-grid">
        <section className="panel queue-panel">
          <header className="panel-heading">
            <h2>{t("queue")}</h2>
            <span className="count-badge">
              {loadError
                ? "—"
                : packets.filter((p) => p.status !== "resolved").length}
            </span>
          </header>
          {loading ? (
            <p role="status" className="empty">
              {t("loading")}
            </p>
          ) : loadError ? (
            <div className="empty load-failed" role="alert">
              <CircleAlert size={30} />
              <p>{t("queueLoadFailed")}</p>
              <Button variant="secondary" onClick={() => void load()}>
                {t("retry")}
              </Button>
            </div>
          ) : !packets.length ? (
            <div className="empty">
              <ClipboardCheck size={34} />
              <h3>{t("emptyQueue")}</h3>
              <p>{t("emptyQueueBody")}</p>
            </div>
          ) : (
            <div className="queue-list">
              {packets.map((p) => (
                <button
                  key={p.handoff_id}
                  className={`queue-item ${current?.handoff_id === p.handoff_id ? "selected" : ""}`}
                  onClick={() => {
                    setSelected(p.handoff_id);
                    requestAnimationFrame(() =>
                      packetPanel.current?.scrollIntoView({ block: "nearest" }),
                    );
                  }}
                  aria-pressed={current?.handoff_id === p.handoff_id}
                >
                  <span className="row-between">
                    <strong>{p.customer_display || t("packet")}</strong>
                    <span
                      className={`badge ${p.priority === "high" ? "red" : ""}`}
                    >
                      {t(p.priority)}
                    </span>
                  </span>
                  <span>
                    {p.route.queue}{" "}
                    <span className="language-flag">
                      {p.route.language.toUpperCase()}
                    </span>
                  </span>
                  <span className="technical-reference">{p.handoff_id}</span>
                  <span className="row-between">
                    <span className="queue-reasons">
                      {orderedReasons(p)
                        .map((reason) => t(handoffReasonLabelKey(reason)))
                        .join(" · ")}
                    </span>
                    <span
                      className="caption sla-countdown"
                      title={date(p.sla_due_at, locale, true)}
                    >
                      <Clock3 size={12} /> {t("sla")}:{" "}
                      {p.status === "resolved"
                        ? "—"
                        : remaining(p.sla_due_at, clock)}
                    </span>
                  </span>
                  <span className="caption">{t(p.status)}</span>
                </button>
              ))}
            </div>
          )}
        </section>
        <section ref={packetPanel} className="panel packet-panel">
          {current ? (
            <>
              <header className="packet-heading">
                <div>
                  <h2>{t("packet")}</h2>
                  <p className="technical-reference">{current.handoff_id}</p>
                  <p>
                    {current.route.queue} ·{" "}
                    {current.route.language.toUpperCase()} · {t(current.status)}
                  </p>
                </div>
              </header>
              <p className="routing-note">
                {t(current.route.fallback_used ? "fallback" : "noFallback")}
              </p>
              <section
                className="packet-section"
                aria-labelledby="handoff-reasons-title"
              >
                <h3 id="handoff-reasons-title">{t("handoffReasons")}</h3>
                <ul className="handoff-reasons">
                  {orderedReasons(current).map((reason) => (
                    <li
                      key={reason}
                      className={
                        reason === current.primary_reason ? "primary" : ""
                      }
                    >
                      {reason === current.primary_reason && (
                        <span className="reason-kind">
                          {t("primaryReason")}
                        </span>
                      )}
                      <strong>{t(handoffReasonLabelKey(reason))}</strong>
                      <code className="technical-reference">{reason}</code>
                    </li>
                  ))}
                </ul>
                {!current.primary_reason && (
                  <p className="caption">{t("primaryReasonMissing")}</p>
                )}
                <p className="caption">{t("reasonControls")}</p>
              </section>
              <section className="packet-section">
                <h3>{t("facts")}</h3>
                {!current.verified_facts.length && (
                  <p className="caption packet-empty">
                    {t("packetFactsEmpty")}
                  </p>
                )}
                {current.verified_facts.map((fact, i) => (
                  <div key={fact.handle}>
                    <TransactionCard transaction={fact} />
                    {current.evidence[i] && (
                      <Button
                        variant="ghost"
                        size="small"
                        onClick={() => setEvidence(current.evidence[i])}
                      >
                        <FileSearch size={15} />
                        {t("evidenceTitle")}
                        <code className="technical-reference">
                          {current.evidence[i].id}
                        </code>
                        <ArrowUpRight size={14} />
                      </Button>
                    )}
                  </div>
                ))}
              </section>
              <section className="packet-section">
                <h3>{t("actions")}</h3>
                {!current.actions.length && (
                  <p className="caption packet-empty">
                    {t("packetActionsEmpty")}
                  </p>
                )}
                <ol className="action-timeline">
                  {current.actions.map((action, i) => (
                    <li key={i}>
                      <span
                        className={`timeline-check ${action.status === "verified" ? "" : "failed"}`}
                        data-status={action.status}
                      >
                        {action.status === "verified" ? (
                          <CheckCheck size={17} />
                        ) : (
                          <CircleAlert size={17} />
                        )}
                      </span>
                      <div>
                        <strong>
                          {t(
                            deskActionLabelKey(
                              action.action,
                              action.status === "verified",
                            ),
                          )}
                        </strong>
                        <p>
                          <span
                            className={`badge ${action.status === "verified" ? "" : "red"}`}
                          >
                            {t(
                              action.status === "verified"
                                ? "verifiedInRecords"
                                : "failedAction",
                            )}
                          </span>
                        </p>
                        <details className="action-references">
                          <summary>{t("technicalReferences")}</summary>
                          <code className="technical-reference">
                            {action.action}
                          </code>
                          <code className="technical-reference">
                            {action.evidence_ref}
                          </code>
                        </details>
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
              {current.risk_flags?.length ? (
                <section className="routing-note packet-risks">
                  <h3>{t("riskIndicators")}</h3>
                  <p>
                    {current.risk_flags
                      .map((flag) => t(riskFlagLabelKey(flag)))
                      .join(" · ")}
                  </p>
                  <details className="action-references">
                    <summary>{t("technicalReferences")}</summary>
                    {current.risk_flags.map((flag) => (
                      <code className="technical-reference" key={flag}>
                        {flag}
                      </code>
                    ))}
                  </details>
                </section>
              ) : null}
              {current.suggested_next_steps?.length ? (
                <section className="packet-section">
                  <h3>{t("nextSteps")}</h3>
                  <ul>
                    {current.suggested_next_steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ul>
                </section>
              ) : null}
              <section className="packet-section">
                <h3>{t("questions")}</h3>
                {!current.open_questions.length && (
                  <p className="caption packet-empty">
                    {t("packetQuestionsEmpty")}
                  </p>
                )}
                <ul className="questions">
                  {current.open_questions.map((q) => (
                    <li key={q}>{q}</li>
                  ))}
                </ul>
                <p className="caption">{t("customerStatements")}</p>
              </section>
              <div className="packet-actions">
                {current.status === "waiting" ? (
                  <Button disabled={busy} onClick={() => void act("claim")}>
                    {busy ? t("loading") : t("claim")}
                    <ArrowUpRight size={17} />
                  </Button>
                ) : current.status === "claimed" ? (
                  <Button disabled={busy} onClick={() => setResolve(true)}>
                    {t("resolve")}
                    <CheckCheck size={17} />
                  </Button>
                ) : (
                  <p className="verified-note">
                    <CheckCheck size={18} />
                    {t("resolved")} · {t("verified")}
                  </p>
                )}
              </div>
            </>
          ) : loading || loadError ? (
            <div className="empty">
              <p>{t(loading ? "loading" : "queueLoadFailed")}</p>
            </div>
          ) : (
            <div className="empty">
              <FileSearch size={36} />
              <p>{t("selectPacket")}</p>
            </div>
          )}
        </section>
      </div>
      {error && (
        <p className="error" role="alert">
          {t("mutationUnknown")}{" "}
          <Button
            variant="secondary"
            onClick={() => void load()}
            disabled={busy}
          >
            {t("retry")}
          </Button>
        </p>
      )}
      <Modal
        open={resolve}
        onOpenChange={setResolve}
        title={t("resolveTitle")}
        description={t("resolveBody")}
        closeLabel={t("close")}
        busy={busy}
      >
        <div className="dialog-actions">
          <Button
            variant="secondary"
            onClick={() => setResolve(false)}
            disabled={busy}
          >
            {t("cancel")}
          </Button>
          <Button onClick={() => void act("resolve")} disabled={busy}>
            {busy ? t("loading") : t("confirm")}
          </Button>
        </div>
      </Modal>
      <Modal
        open={!!evidence}
        onOpenChange={(open) => {
          if (!open) setEvidence(null);
        }}
        title={t("evidenceTitle")}
        description={t("facts")}
        closeLabel={t("close")}
        drawer
      >
        {evidence && (
          <dl className="metadata-list">
            <dt>ID</dt>
            <dd>{evidence.id}</dd>
            <dt>{t("source")}</dt>
            <dd>{evidence.tool}</dd>
            <dt>{t("evidence")}</dt>
            <dd>{evidence.record_ref}</dd>
            <dt>{t("dataset")}</dt>
            <dd>{evidence.dataset_version}</dd>
            <dt>{t("verified")}</dt>
            <dd>{date(evidence.verified_at, locale, true)} UTC</dd>
          </dl>
        )}
      </Modal>
    </>
  );
}
