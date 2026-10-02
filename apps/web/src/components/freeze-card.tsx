"use client";
import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { api, ApiError } from "@/lib/client";
import {
  freezeProposalSchema,
  planSchema,
  type FreezeProposal,
  type Plan,
  type Product,
} from "@/lib/contracts";
import { cardTypeLabelKey } from "@/lib/ui-copy";
import { date } from "@/lib/format";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
import { Modal } from "./ui/dialog";

// Every action originates in the bank's offer and proposal. No local policy decision.
export function FreezeCard({
  products,
  handoffId,
  onResult,
  onPendingChange,
}: {
  products: Product[];
  handoffId: string;
  onResult: (plan: Plan) => void;
  onPendingChange?: (pending: boolean) => void;
}) {
  const t = useTranslations();
  const { locale } = useApp();
  const [product, setProduct] = useState<Product | null>(null);
  const [challenge, setChallenge] = useState("");
  const [sms, setSms] = useState("");
  const [code, setCode] = useState("");
  const [proposal, setProposal] = useState<FreezeProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false);
  const [expired, setExpired] = useState(false);
  const lock = useRef(false);
  useEffect(() => {
    onPendingChange?.(!!product || busy || uncertain);
    return () => onPendingChange?.(false);
  }, [product, busy, uncertain, onPendingChange]);
  useEffect(() => {
    if (!proposal) return;
    const check = () =>
      setExpired(Date.now() >= Date.parse(proposal.expires_at));
    check();
    const timer = setInterval(check, 1000);
    return () => clearInterval(timer);
  }, [proposal]);
  async function run(action: () => Promise<void>, mutation = false) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (caught) {
      if (caught instanceof ApiError && caught.code === "admission_limited") {
        setCode("");
        setError(t("rateLimited", { seconds: caught.retryAfter }));
        return;
      }
      if (mutation) {
        setProposal(null);
        setUncertain(true);
      }
      if (caught instanceof ApiError && caught.code === "invalid_otp_code") {
        setCode("");
        setError(t("otpRetry"));
        return;
      }
      setError(
        t(
          mutation
            ? "mutationUnknown"
            : caught instanceof ApiError && caught.status === 401
              ? "loginFail"
              : "error",
        ),
      );
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function start(selected: Product) {
    setProduct(selected);
    setChallenge("");
    setSms("");
    setCode("");
    setProposal(null);
    await run(async () => {
      const auth = await api<{ challenge_id: string }>("auth/step-up", {});
      setChallenge(auth.challenge_id);
      const sms = await api<{ code: string }>(
        `auth/challenges/${auth.challenge_id}/sms`,
      );
      setSms(sms.code);
    });
  }
  async function verify() {
    if (!product) return;
    await run(async () => {
      await api("auth/step-up/verify", { challenge_id: challenge, code });
      setCode("");
      setSms("");
      setChallenge("");
      const data = await api(`cards/${product.handle}/freeze/proposal`, {
        language: locale === "pt-BR" ? "pt" : "es",
        handoff_id: handoffId,
      });
      const proposed = freezeProposalSchema.safeParse(data);
      if (proposed.success) setProposal(proposed.data);
      else {
        onResult(planSchema.parse(data));
        setProduct(null);
      }
    });
  }
  async function confirm(confirmed: boolean) {
    if (!proposal || !product) return;
    if (confirmed && expired) {
      setError(t("expired"));
      return;
    }
    await run(async () => {
      const result = planSchema.parse(
        await api(`cards/${product.handle}/freeze`, {
          proposal_hash: proposal.proposal_hash,
          confirmed,
        }),
      );
      onResult(result);
      setProposal(null);
      setProduct(null);
    }, true);
  }
  return (
    <section className="proposal-bar" aria-label={t("freezeOffer")}>
      <p>{t("freezeOffer")}</p>
      {products.map((item, index) => (
        <Button
          key={item.handle}
          size="small"
          disabled={busy || uncertain}
          onClick={() => void start(item)}
        >
          {t("freezeAction")} · {t("cardNumber", { number: index + 1 })} ·{" "}
          {t(cardTypeLabelKey(item.product_type))}
        </Button>
      ))}
      <Modal
        open={!!product}
        onOpenChange={(open) => {
          if (!open) setProduct(null);
        }}
        title={t("freezeAction")}
        description={t("freezeBody")}
        closeLabel={t("close")}
        busy={busy}
      >
        <p>
          {product && t(cardTypeLabelKey(product.product_type))} ·{" "}
          {product &&
            t("cardNumber", {
              number:
                products.findIndex((item) => item.handle === product.handle) +
                1,
            })}
        </p>
        {challenge && !proposal && (
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              void verify();
            }}
          >
            <div className="sms-panel">
              <div>
                <strong>{t("sms")}</strong>
                <p className="sms-code" data-testid="step-up-code">
                  {sms || "••••••"}
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
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                disabled={busy}
              />
            </label>
            <Button type="submit" disabled={busy}>
              {t("verifyAction")}
            </Button>
          </form>
        )}
        {proposal && (
          <>
            <p>{proposal.reply}</p>
            <p className={expired ? "error" : "caption"}>
              {expired
                ? t("expired")
                : `${t("expires")}: ${date(proposal.expires_at, locale, true)} UTC`}
            </p>
            <p>{t("validConfirmation")}</p>
            {expired ? (
              <Button
                disabled={busy}
                onClick={() => product && void start(product)}
              >
                {t("newReview")}
              </Button>
            ) : (
              <div className="dialog-actions">
                <Button
                  variant="secondary"
                  disabled={busy}
                  onClick={() => void confirm(false)}
                >
                  {t("cancel")}
                </Button>
                <Button disabled={busy} onClick={() => void confirm(true)}>
                  {t("confirm")}
                </Button>
              </div>
            )}
            <p className="caption">{t("expiryHint")}</p>
          </>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {!challenge && !proposal && !uncertain && !busy && product && (
          <Button onClick={() => void start(product)}>{t("retry")}</Button>
        )}
      </Modal>
      {uncertain && (
        <p role="alert" className="error">
          {t("mutationUnknown")}
        </p>
      )}
    </section>
  );
}
