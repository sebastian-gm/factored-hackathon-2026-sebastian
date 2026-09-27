"use client";
import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/client";
import {
  resetProposalSchema,
  resetReceiptSchema,
  type ResetProposal,
} from "@/lib/staff-contracts";
import { date } from "@/lib/format";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
import { Modal } from "./ui/dialog";

export function LiveReset({
  enabled,
  onReset,
}: {
  enabled: boolean;
  onReset: () => Promise<void>;
}) {
  const t = useTranslations();
  const { locale } = useApp();
  const [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [challenge, setChallenge] = useState(""),
    [sms, setSms] = useState(""),
    [code, setCode] = useState("");
  const [proposal, setProposal] = useState<ResetProposal | null>(null),
    [done, setDone] = useState(false);
  const lock = useRef(false);
  async function run(action: () => Promise<void>, write = false) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch {
      setError(t(write ? "mutationUnknown" : "error"));
      if (write) setProposal(null);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function start() {
    if (!enabled) return;
    setOpen(true);
    setDone(false);
    setProposal(null);
    setChallenge("");
    setSms("");
    setCode("");
    await run(async () => {
      const auth = await api<{ challenge_id: string }>("auth/step-up", {});
      setChallenge(auth.challenge_id);
      setSms(
        (
          await api<{ code: string }>(
            `auth/challenges/${auth.challenge_id}/sms`,
          )
        ).code,
      );
    });
  }
  async function verify() {
    await run(async () => {
      await api("auth/step-up/verify", { challenge_id: challenge, code });
      setCode("");
      setSms("");
      setChallenge("");
      setProposal(
        resetProposalSchema.parse(await api("ops/reset/proposal", {})),
      );
    });
  }
  async function confirm(confirmed: boolean) {
    if (!proposal) return;
    await run(async () => {
      const result = resetReceiptSchema.parse(
        await api("ops/reset", {
          proposal_hash: proposal.proposal_hash,
          confirmed,
        }),
      );
      if (
        result.reset !== confirmed ||
        !result.verified ||
        (confirmed && result.remaining_operations !== 0)
      )
        throw new Error("Readback failed");
      if (confirmed) await onReset();
      setDone(confirmed);
      setOpen(false);
      setProposal(null);
    }, true);
  }
  return (
    <div className="reset-panel">
      <div>
        <h3>{t("reset")}</h3>
        <p>{t(enabled ? "liveResetBody" : "resetDisabled")}</p>
        {done && (
          <p className="verified-note" role="status">
            {t("resetDone")}
          </p>
        )}
      </div>
      <Button
        variant="secondary"
        disabled={!enabled || busy}
        onClick={() => void start()}
      >
        {t("reset")}
      </Button>
      <Modal
        open={open}
        onOpenChange={setOpen}
        title={t("resetTitle")}
        description={t("liveResetBody")}
        closeLabel={t("close")}
        busy={busy}
      >
        {challenge && (
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
                <p className="sms-code" data-testid="reset-otp">
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
                required
                value={code}
                onChange={(e) => setCode(e.target.value)}
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
            <p>
              {t("expires")}: {date(proposal.expires_at, locale, true)} UTC
            </p>
            <p>{t("validConfirmation")}</p>
            <div className="dialog-actions">
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() => void confirm(false)}
              >
                {t("cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={busy}
                onClick={() => void confirm(true)}
              >
                {t("confirm")}
              </Button>
            </div>
          </>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </Modal>
    </div>
  );
}
