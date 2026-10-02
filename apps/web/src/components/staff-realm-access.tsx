"use client";
import { useEffect, useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/client";
import { realmInvitationSchema, realmJoinSchema } from "@/lib/staff-contracts";
import { notifyProfileChange, retireWorkspace } from "@/lib/profile-workspace";
import { Button } from "./ui/button";
import { Modal } from "./ui/dialog";

export function StaffInvitation() {
  const t = useTranslations();
  const [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false);
  const [invitation, setInvitation] = useState("");
  const [expires, setExpires] = useState(0);
  const [failed, setFailed] = useState(false),
    [copied, setCopied] = useState(false);
  useEffect(() => {
    if (!expires) return;
    const timer = setTimeout(
      () => {
        setInvitation("");
        setCopied(false);
      },
      Math.max(0, expires - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [expires]);
  async function invite() {
    setBusy(true);
    setFailed(false);
    setCopied(false);
    setInvitation("");
    setOpen(true);
    try {
      const result = realmInvitationSchema.parse(
        await api("handoffs/realm-invitations", {}),
      );
      const deadline = Date.parse(result.expires_at);
      if (deadline <= Date.now() || deadline > Date.now() + 300000)
        throw new Error("Invalid expiry");
      setExpires(deadline);
      setInvitation(result.invitation);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <h2>{t("staffShareTitle")}</h2>
      <p className="muted">{t("staffShareBody")}</p>
      <Button onClick={() => void invite()} disabled={busy}>
        {t("staffInvite")}
      </Button>
      <Modal
        open={open}
        onOpenChange={(value) => {
          setOpen(value);
          if (!value) {
            setInvitation("");
            setCopied(false);
          }
        }}
        title={t("staffInvite")}
        description={t("staffSeparateBrowser")}
        closeLabel={t("close")}
        busy={busy}
      >
        {busy ? (
          <p role="status">{t("loading")}</p>
        ) : failed ? (
          <p role="alert" className="error">
            {t("staffInviteFailed")}
          </p>
        ) : invitation ? (
          <div className="form-stack">
            <label>
              {t("staffInvitation")}
              <input
                type="password"
                autoComplete="off"
                readOnly
                value={invitation}
              />
            </label>
            <p className="caption">{t("staffInviteExpiry")}</p>
            <Button
              onClick={() => {
                void navigator.clipboard
                  .writeText(invitation)
                  .then(() => setCopied(true))
                  .catch(() => setFailed(true));
              }}
            >
              {t("staffCopy")}
            </Button>
            {copied && <p role="status">{t("staffCopied")}</p>}
          </div>
        ) : (
          <p role="status">{t("staffInviteExpired")}</p>
        )}
      </Modal>
    </>
  );
}

export function StaffRealmAccess({
  connected,
  onStart,
  onFinish,
}: {
  connected: boolean;
  onStart: () => void;
  onFinish: (joined: boolean) => void;
}) {
  const t = useTranslations();
  const [invitation, setInvitation] = useState("");
  const [busy, setBusy] = useState(false),
    [failed, setFailed] = useState(false);
  async function join(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    const value = invitation.trim();
    setInvitation("");
    setBusy(true);
    setFailed(false);
    retireWorkspace(false);
    notifyProfileChange("changing");
    onStart();
    let joined = false;
    try {
      realmJoinSchema.parse(
        await api("agent/handoff-realm", { invitation: value }),
      );
      joined = true;
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
      onFinish(joined);
      notifyProfileChange("settled");
    }
  }
  return (
    <details className="staff-realm-access" open={connected ? undefined : true}>
      <summary>{t(connected ? "staffChangeVisit" : "staffConnect")}</summary>
      <p className="caption">{t("staffConnectBody")}</p>
      <form className="staff-realm-form" onSubmit={join} aria-busy={busy}>
        <label>
          {t("staffInvitation")}
          <input
            type="password"
            autoComplete="off"
            value={invitation}
            onChange={(e) => setInvitation(e.target.value)}
            required
            minLength={20}
            maxLength={160}
            disabled={busy}
          />
        </label>
        <Button type="submit" disabled={busy}>
          {t(busy ? "loading" : "staffConnect")}
        </Button>
      </form>
      {failed && (
        <p role="alert" className="error">
          {t("staffJoinFailed")}
        </p>
      )}
    </details>
  );
}
