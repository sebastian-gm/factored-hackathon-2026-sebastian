"use client";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import {
  ArrowUpRight,
  CheckCheck,
  ClipboardCheck,
  Clock3,
  FileSearch,
  Headphones,
} from "lucide-react";
import type { DeskPacket } from "@/lib/contracts";
import { api } from "@/lib/client";
import { date, remaining } from "@/lib/format";
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
  const [evidence, setEvidence] = useState<
      DeskPacket["evidence"][number] | null
    >(null),
    [tick, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick((v) => v + 1), 60000);
    return () => clearInterval(timer);
  }, []);
  async function load() {
    setLoading(true);
    try {
      const values = await api<DeskPacket[]>("agent/handoffs");
      setPackets(values);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    const c = new AbortController();
    api<DeskPacket[]>("agent/handoffs", undefined, c.signal)
      .then(setPackets)
      .catch(() => {
        if (!c.signal.aborted) setError(true);
      })
      .finally(() => {
        if (!c.signal.aborted) setLoading(false);
      });
    return () => c.abort();
  }, []);
  const current = packets.find((p) => p.handoff_id === selected) ?? packets[0];
  const clock = new Date(
    Date.parse(config.bankClock ?? "") + tick * 60000,
  ).toISOString();
  async function act(action: "claim" | "resolve") {
    if (!current || busy) return;
    setBusy(true);
    setError(false);
    try {
      await api(`agent/handoffs/${current.handoff_id}/${action}`, {});
      const verified = await api<DeskPacket>(
        `agent/handoffs/${current.handoff_id}`,
      );
      if (
        verified.handoff_id !== current.handoff_id ||
        verified.status !== (action === "claim" ? "claimed" : "resolved")
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
      <div className="desk-grid">
        <section className="panel queue-panel">
          <header className="panel-heading">
            <h2>{t("queue")}</h2>
            <span className="count-badge">
              {packets.filter((p) => p.status !== "resolved").length}
            </span>
          </header>
          {loading ? (
            <p role="status" className="empty">
              {t("loading")}
            </p>
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
                  onClick={() => setSelected(p.handoff_id)}
                  aria-pressed={current?.handoff_id === p.handoff_id}
                >
                  <span className="row-between">
                    <strong>{p.handoff_id}</strong>
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
                  <span className="caption">{p.customer_display}</span>
                  <span className="row-between">
                    <span className="rule">{p.reason_codes.join(" · ")}</span>
                    <span className="caption">
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
        <section className="panel packet-panel">
          {current ? (
            <>
              <header className="packet-heading">
                <div>
                  <p className="eyebrow">{t("packet")}</p>
                  <h2>{current.handoff_id}</h2>
                  <p>
                    {current.route.queue} ·{" "}
                    {current.route.language.toUpperCase()} · {t(current.status)}
                  </p>
                </div>
                <span className="hero-icon">
                  <Headphones />
                </span>
              </header>
              <p className="routing-note">
                {t(current.route.fallback_used ? "fallback" : "noFallback")}
              </p>
              <section className="packet-section">
                <h3>{t("facts")}</h3>
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
                        {t("evidenceTitle")} · {current.evidence[i].id}
                        <ArrowUpRight size={14} />
                      </Button>
                    )}
                  </div>
                ))}
              </section>
              <section className="packet-section">
                <h3>{t("actions")}</h3>
                <ol className="action-timeline">
                  {current.actions.map((action, i) => (
                    <li key={i}>
                      <span className="timeline-check">
                        <CheckCheck size={17} />
                      </span>
                      <div>
                        <strong>{action.action}</strong>
                        <p>
                          <span className="badge">
                            {t(
                              action.status === "verified"
                                ? "verified"
                                : "unverified",
                            )}
                          </span>{" "}
                          <code>{action.evidence_ref}</code>
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
              <section className="packet-section">
                <h3>{t("questions")}</h3>
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
