"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import {
  ArrowRight,
  CheckCheck,
  CircleHelp,
  CircleSlash2,
  FileCheck2,
  Headphones,
  Send,
  ShieldCheck,
} from "lucide-react";
import { api, ApiError } from "@/lib/client";
import { planSchema, type Plan } from "@/lib/contracts";
import { date } from "@/lib/format";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
import { Modal } from "./ui/dialog";
import { TransactionCard } from "./transaction-card";
import { FreezeCard } from "./freeze-card";
import { ChatStages, responseStage } from "./chat-stages";
import { queueLabelKey, ruleLabelKey } from "@/lib/ui-copy";

type Line = {
  id: number;
  text: string;
  speaker: "customer" | "aclara";
  plan?: Plan;
};
export function CustomerChat({
  initialDraft = "",
  onPendingChange,
}: {
  initialDraft?: string;
  onPendingChange?: (locked: boolean) => void;
}) {
  const t = useTranslations();
  const { locale, config, session, signOut } = useApp();
  const [conversation, setConversation] = useState("");
  const [lines, setLines] = useState<Line[]>([]);
  const [draft, setDraft] = useState(initialDraft),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [latest, setLatest] = useState<Plan | null>(null),
    [why, setWhy] = useState<Plan | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false),
    [expired, setExpired] = useState(false),
    [renew, setRenew] = useState(false);
  // A stale OTP keeps the exact pending proposal: renew step-up, then confirm again.
  const [stepUp, setStepUp] = useState<{
      challenge: string;
      sms: string;
    } | null>(null),
    [otp, setOtp] = useState("");
  const lock = useRef(false),
    log = useRef<HTMLDivElement>(null);
  const decision = useRef<HTMLElement>(null);
  const receipt = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const [uncertain, setUncertain] = useState(false),
    [notice, setNotice] = useState("");
  const proposal = latest?.proposal;
  useEffect(() => {
    onPendingChange?.(!!proposal || busy || renew || uncertain);
    return () => onPendingChange?.(false);
  }, [proposal, busy, renew, uncertain, onPendingChange]);
  useEffect(() => {
    if (!latest || busy || confirmOpen) return;
    const frame = requestAnimationFrame(() =>
      (decision.current ?? receipt.current)?.scrollIntoView({
        block: "nearest",
      }),
    );
    return () => cancelAnimationFrame(frame);
  }, [latest, busy, confirmOpen]);
  useEffect(() => {
    if (!notice || busy) return;
    const frame = requestAnimationFrame(() => {
      composer.current?.focus();
      composer.current?.scrollIntoView({ block: "nearest" });
    });
    return () => cancelAnimationFrame(frame);
  }, [notice, busy]);
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [lines]);
  useEffect(() => {
    if (!proposal) return;
    const check = () =>
      setExpired(Date.now() >= Date.parse(proposal.expires_at));
    check();
    const timer = setInterval(check, 1000);
    return () => clearInterval(timer);
  }, [proposal]);
  function failed(caught: unknown, mutation = false) {
    setUncertain(mutation);
    if (caught instanceof ApiError && caught.status === 401) {
      setRenew(true);
      setError(t("renew"));
    } else setError(t(mutation ? "mutationUnknown" : "error"));
  }
  function receive(plan: Plan) {
    setUncertain(false);
    setLatest(plan);
    setExpired(false);
    setLines((current) => [
      ...current,
      { id: current.length, speaker: "aclara", text: plan.reply, plan },
    ]);
    if (plan.proposal) setConfirmOpen(true);
    if (plan.session_ended) {
      setRenew(true);
      setError(t("renew"));
    }
  }
  async function send(text: string) {
    if (lock.current || !text.trim() || proposal || renew) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    setDraft("");
    setLines((current) => [
      ...current,
      { id: current.length, speaker: "customer", text },
    ]);
    try {
      let id = conversation;
      if (!id) {
        id = (await api<{ conversation_id: string }>("chat/sessions", {}))
          .conversation_id;
        setConversation(id);
      }
      receive(
        planSchema.parse(
          await api(`chat/sessions/${id}/messages`, { message: text }),
        ),
      );
    } catch (caught) {
      setDraft(text);
      failed(caught);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  function prepareQuery(text: string) {
    setDraft(text);
    composer.current?.focus();
    composer.current?.scrollIntoView({ block: "nearest" });
  }
  async function newReview() {
    if (lock.current || !proposal || !expired) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      // Explicitly start a new conversation. Never confirm/replay the expired hash.
      const next = await api<{ conversation_id: string }>("chat/sessions", {});
      setConversation(next.conversation_id);
      setLatest(null);
      setConfirmOpen(false);
      setStepUp(null);
      setOtp("");
      setNotice(t("newReviewReady"));
    } catch (caught) {
      failed(caught);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function confirm(confirmed: boolean) {
    if (lock.current || !proposal || (confirmed && expired)) return;
    const exact = proposal.proposal_hash;
    lock.current = true;
    setBusy(true);
    setError("");
    let keepOpen = false;
    try {
      receive(
        planSchema.parse(
          await api(`chat/sessions/${conversation}/confirm`, {
            proposal_hash: exact,
            confirmed,
          }),
        ),
      );
    } catch (caught) {
      if (
        confirmed &&
        caught instanceof ApiError &&
        caught.status === 401 &&
        caught.code === "step_up_required"
      ) {
        try {
          const auth = await api<{ challenge_id: string }>("auth/step-up", {});
          const sms = await api<{ code: string }>(
            `auth/challenges/${auth.challenge_id}/sms`,
          );
          setStepUp({ challenge: auth.challenge_id, sms: sms.code });
          setError(t("stepUpRequired"));
          keepOpen = true;
        } catch (renewal) {
          setLatest(null);
          failed(renewal, true);
        }
      } else {
        setLatest(null);
        failed(caught, true);
      }
    } finally {
      if (!keepOpen) setConfirmOpen(false);
      lock.current = false;
      setBusy(false);
    }
  }
  async function renewAndConfirm() {
    if (lock.current || !stepUp) return;
    lock.current = true;
    setBusy(true);
    try {
      await api("auth/step-up/verify", {
        challenge_id: stepUp.challenge,
        code: otp,
      });
    } catch (caught) {
      lock.current = false;
      setBusy(false);
      if (
        caught instanceof ApiError &&
        caught.status === 401 &&
        caught.code === "invalid_otp_code"
      ) {
        // The server retained this challenge and pending proposal. A wrong
        // code is retryable by the customer, within its five-attempt limit.
        setOtp("");
        setError(t("otpRetry"));
        return;
      }
      setStepUp(null);
      setOtp("");
      setLatest(null);
      setConfirmOpen(false);
      failed(caught, true);
      return;
    }
    setStepUp(null);
    setOtp("");
    lock.current = false;
    setBusy(false);
    await confirm(true);
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    void send(draft);
  }
  const examples =
    session?.username === "demo.fraud"
      ? ["fraudPrompt"]
      : locale === "pt-BR"
        ? ["ambiguousPrompt", "fraudPrompt"]
        : ["normalPrompt", "fraudPrompt"];
  return (
    <section className="panel chat-panel" aria-labelledby="conversation-title">
      <header className="chat-header">
        <span className="chat-avatar">a</span>
        <div>
          <h2 id="conversation-title">Aclara</h2>
          <span>
            <span className={`dot ${renew ? "paused" : ""}`} />
            {t(renew ? "signInAgain" : "active")}
          </span>
        </div>
        <span className="secure-pill">
          <ShieldCheck size={14} />
          {t(renew ? "signInAgain" : "secure")}
        </span>
      </header>
      <ChatStages plan={latest} />
      <div
        ref={log}
        className="conversation-log"
        role="log"
        aria-label={t("conversation")}
        aria-live="polite"
        aria-relevant="additions"
      >
        {lines.length === 0 && (
          <div className="chat-welcome">
            <div className="welcome-glyph">
              <MessageGlyph />
            </div>
            <h3>{t("greeting")}</h3>
            <p>{t("chatIntro")}</p>
            {config.fixtures && (
              <div className="suggestions" aria-label={t("example")}>
                {examples.map((key) => (
                  <button
                    key={key}
                    onClick={() => void send(t(key))}
                    disabled={busy}
                  >
                    {t(key)}
                    <ArrowRight size={15} />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {lines.map((line) => (
          <div key={line.id} className={`chat-line ${line.speaker}`}>
            <span className="speaker">
              {line.speaker === "customer" ? t("you") : "Aclara"}
            </span>
            <div className="bubble">
              <p>{line.text}</p>
              {line.plan?.transaction && (
                <TransactionCard transaction={line.plan.transaction} />
              )}
              {line.plan && (
                <span className="turn-stage" aria-label={t("turnStage")}>
                  {t(`stage_${responseStage(line.plan)}`)}
                </span>
              )}
              {line.plan?.outcome === "cancelled" && (
                <div className="cancelled-notice" role="status">
                  <CircleSlash2 size={21} aria-hidden="true" />
                  <div>
                    <h3>{t("cancelledTitle")}</h3>
                    <p>{t("cancelledBody")}</p>
                  </div>
                </div>
              )}
              {line.plan?.case && line.plan.verified === true && (
                <div
                  ref={line.plan === latest ? receipt : undefined}
                  className="receipt"
                >
                  <FileCheck2 size={24} />
                  <div>
                    <h3>
                      {t(
                        line.plan.response_type === "report_status"
                          ? "statusTitle"
                          : "receipt",
                      )}
                    </h3>
                    <details className="case-reference">
                      <summary>{t("caseReference")}</summary>
                      <strong>{line.plan.case.case_id}</strong>
                    </details>
                    <p>
                      {line.plan.case.status === "received"
                        ? t("caseStatus")
                        : t("caseStatusOther")}{" "}
                      · <CheckCheck size={14} /> {t("verified")}
                    </p>
                    <small>{t("receiptNote")}</small>
                    {line.plan.case.review_flag && <p>{t("reviewFlag")}</p>}
                  </div>
                </div>
              )}
              {line.plan?.handoff && line.plan.verified === true && (
                <div
                  ref={line.plan === latest ? receipt : undefined}
                  className="receipt handoff-receipt"
                >
                  <Headphones size={25} />
                  <div>
                    <h3>{t("handoff")}</h3>
                    <strong>
                      {t(queueLabelKey(line.plan.handoff.route.queue))}
                    </strong>
                    <p>{t("handoffNote")}</p>
                    <small>
                      {t(
                        line.plan.card?.verified
                          ? "freezeVerified"
                          : line.plan.handoff.freeze_outcome === "unverified"
                            ? "mutationUnknown"
                            : "noFreeze",
                      )}
                    </small>
                    {line.plan.handoff.route.assignment_pending && (
                      <p>{t("assignmentPending")}</p>
                    )}
                    {line.plan.handoff.route.fallback_used && (
                      <p>{t("fallback")}</p>
                    )}
                  </div>
                </div>
              )}
              {line.plan && (
                <Button
                  variant="ghost"
                  size="small"
                  onClick={() => setWhy(line.plan!)}
                >
                  <CircleHelp size={15} />
                  {t("why")}
                </Button>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <p className="busy-indicator" role="status">
            <span /> {t("loading")}
          </p>
        )}
      </div>
      {latest?.response_type === "choose_transaction" && !busy && (
        <section ref={decision} className="chooser" aria-label={t("choose")}>
          <h3>{t("choose")}</h3>
          <div className="candidate-grid">
            {latest.candidates?.slice(0, 3).map((tx, i) => (
              <TransactionCard
                key={tx.handle}
                transaction={tx}
                disabled={busy}
                onChoose={() =>
                  void send(
                    locale === "pt-BR"
                      ? `o ${["primeiro", "segundo", "terceiro"][i]}`
                      : `el ${["primero", "segundo", "tercero"][i]}`,
                  )
                }
              />
            ))}
          </div>
          <Button
            variant="ghost"
            size="small"
            onClick={() =>
              void send(
                locale === "pt-BR" ? "nenhuma dessas" : "ninguno de estos",
              )
            }
          >
            {t("none")}
          </Button>
        </section>
      )}
      {proposal && (
        <div className="proposal-bar">
          <ShieldCheck size={19} />
          <p>{expired ? t("expired") : t("dialogDismissed")}</p>
          <Button
            size="small"
            onClick={() => (expired ? void newReview() : setConfirmOpen(true))}
            disabled={busy}
          >
            {t(expired ? "newReview" : "reviewAction")}
          </Button>
        </div>
      )}
      {latest?.response_type === "offer_dispute" && !renew && (
        <section
          ref={decision}
          className="recognition-actions"
          aria-labelledby="recognition-title"
        >
          <h3 id="recognition-title">{t("recognitionTitle")}</h3>
          <div className="recognition-buttons">
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => void send(t("recognizeChargeMessage"))}
            >
              {t("recognizeCharge")}
            </Button>
            <Button
              disabled={busy}
              onClick={() => void send(t("disputeCharge"))}
            >
              {t("disputeCharge")}
            </Button>
          </div>
          <p className="caption">{t("recognitionHint")}</p>
        </section>
      )}
      {!config.fixtures &&
      latest?.freeze_offer?.length &&
      latest.handoff &&
      !renew ? (
        <FreezeCard
          key={latest.handoff?.handoff_id}
          products={latest.freeze_offer}
          handoffId={latest.handoff.handoff_id}
          onResult={receive}
        />
      ) : null}
      {notice && (
        <p className="review-notice" role="status">
          {notice}
        </p>
      )}
      {error && !(stepUp && confirmOpen) && (
        <div className="error" role="alert">
          {error}
          {renew && (
            <Button
              variant="secondary"
              onClick={() => void signOut().catch(() => setError(t("error")))}
            >
              {t("signInAgain")}
            </Button>
          )}
          {uncertain && !renew && (
            <div className="recovery-actions">
              <Button
                variant="secondary"
                onClick={() => prepareQuery(t("statusPrompt"))}
              >
                {t("prepareStatus")}
              </Button>
              <Button
                variant="secondary"
                onClick={() => prepareQuery(t("humanPrompt"))}
              >
                {t("askHuman")}
              </Button>
            </div>
          )}
        </div>
      )}
      <form className="composer" onSubmit={submit}>
        <label className="sr-only" htmlFor="message">
          {t("message")}
        </label>
        <textarea
          ref={composer}
          id="message"
          rows={2}
          maxLength={1000}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={t("placeholder")}
          disabled={busy || !!proposal || renew}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send(draft);
            }
          }}
        />
        <Button
          size="icon"
          aria-label={t("send")}
          type="submit"
          disabled={busy || !draft.trim() || !!proposal || renew}
        >
          <Send size={19} />
        </Button>
        <small>{t("privacy")}</small>
      </form>
      <Modal
        open={confirmOpen && !!proposal}
        onOpenChange={setConfirmOpen}
        title={t("actionTitle")}
        description={t("actionBody")}
        closeLabel={t("close")}
        busy={busy}
      >
        {latest?.transaction && (
          <TransactionCard transaction={latest.transaction} />
        )}
        <p className="confirmation-action">
          <ShieldCheck size={18} />
          {t("action")}
        </p>
        <p className="caption">{t("validConfirmation")}</p>
        {proposal && (
          <p className={expired ? "error" : "caption"}>
            {expired
              ? t("expired")
              : `${t("expires")}: ${date(proposal.expires_at, locale, true)} UTC`}
          </p>
        )}
        {expired ? (
          <Button disabled={busy} onClick={() => void newReview()}>
            {t("newReview")}
          </Button>
        ) : stepUp ? (
          <form
            className="form-stack"
            onSubmit={(event) => {
              event.preventDefault();
              void renewAndConfirm();
            }}
          >
            <p className="error" role="alert">
              {error || t("stepUpRequired")}
            </p>
            <div className="sms-panel">
              <div>
                <strong>{t("sms")}</strong>
                <p className="sms-code" data-testid="confirm-step-up-code">
                  {stepUp.sms || "••••••"}
                </p>
              </div>
            </div>
            <label>
              {t("otp")}
              <input
                autoFocus
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]{6}"
                maxLength={6}
                value={otp}
                onChange={(event) => setOtp(event.target.value)}
                required
                disabled={busy}
              />
            </label>
            <Button type="submit" disabled={busy || expired}>
              {busy ? t("loading") : t("verifyAndConfirm")}
            </Button>
          </form>
        ) : (
          <div className="dialog-actions">
            <Button
              variant="secondary"
              onClick={() => void confirm(false)}
              disabled={busy}
            >
              {t("cancel")}
            </Button>
            <Button
              onClick={() => void confirm(true)}
              disabled={busy || expired}
            >
              {busy ? t("loading") : t("confirm")}
            </Button>
          </div>
        )}
        {!expired && <p className="caption">{t("expiryHint")}</p>}
      </Modal>
      <Modal
        open={!!why}
        onOpenChange={(open) => {
          if (!open) setWhy(null);
        }}
        title={t("why")}
        description={t("whyBody")}
        closeLabel={t("close")}
        drawer
      >
        <p className="why-explanation">{why?.reply}</p>
        <div className="drawer-section">
          <h3>{t("evidence")}</h3>
          {why?.transaction ? (
            <TransactionCard transaction={why.transaction} />
          ) : why?.handoff?.verified_facts.length ? (
            why.handoff.verified_facts.map((fact) => (
              <TransactionCard key={fact.handle} transaction={fact} />
            ))
          ) : (
            <p className="muted">{t("noEvidence")}</p>
          )}
        </div>
        <div className="drawer-section">
          <h3>{t("rules")}</h3>
          <div className="rule-list">
            {(
              why?.policy_rules ??
              why?.proposal?.policy_rules ??
              why?.case?.policy_rules ??
              why?.handoff?.reason_codes ??
              []
            )
              .map(ruleLabelKey)
              .filter((key, index, keys) => keys.indexOf(key) === index)
              .map((rule) => (
                <span className="rule" key={rule}>
                  {t(rule)}
                </span>
              ))}
          </div>
          {!(
            why?.policy_rules?.length ||
            why?.proposal ||
            why?.case ||
            why?.handoff
          ) && <p className="muted">{t("noRules")}</p>}
        </div>
        {why?.verified && (
          <p className="verified-note">
            <CheckCheck size={18} />
            {t("readback")}
          </p>
        )}
        <p className="caption">{t("noThinking")}</p>
      </Modal>
    </section>
  );
}
function MessageGlyph() {
  return (
    <span aria-hidden="true">
      a<span>✦</span>
    </span>
  );
}
