"use client";
import { useState, type FormEvent } from "react";
import { useTranslations } from "next-intl";
import { ArrowRight, LockKeyhole, Smartphone } from "lucide-react";
import { api } from "@/lib/client";
import type { Role } from "@/lib/contracts";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
export function Login({ role }: { role: Role }) {
  const t = useTranslations();
  const { config, signedIn, setLocale } = useApp();
  const choices = config.personas.filter(
    (p) => !config.fixtures || p.role === role,
  );
  const [username, setUsername] = useState(choices[0]?.username ?? "");
  const [password, setPassword] = useState(""),
    [otp, setOtp] = useState(""),
    [challenge, setChallenge] = useState(""),
    [sms, setSms] = useState("");
  const [busy, setBusy] = useState(false),
    [failed, setFailed] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setFailed(false);
    try {
      if (!challenge) {
        const auth = await api<{ challenge_id: string }>("auth/login", {
          username,
          password,
        });
        setPassword("");
        setChallenge(auth.challenge_id);
        const code = await api<{ code: string }>(
          `auth/challenges/${auth.challenge_id}/sms`,
        );
        setSms(code.code);
      } else {
        await api("auth/otp/verify", { challenge_id: challenge, code: otp });
        setOtp("");
        setSms("");
        await signedIn();
      }
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="hero-icon">
        <LockKeyhole size={25} />
      </div>
      <h2>{t("loginTitle")}</h2>
      <p className="muted">{t("loginBody")}</p>
      <form onSubmit={submit} className="form-stack" aria-busy={busy}>
        {!challenge ? (
          <>
            <label>
              {t("persona")}
              <select
                value={username}
                disabled={busy}
                onChange={(e) => {
                  setUsername(e.target.value);
                  const p = choices.find((x) => x.username === e.target.value);
                  if (p) setLocale(p.locale);
                }}
              >
                {choices.map((p) => (
                  <option key={p.username} value={p.username}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            {!config.fixtures && (
              <label>
                {t("username")}
                <input
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  maxLength={80}
                />
              </label>
            )}
            <label>
              {t("password")}
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={busy}
                required
                maxLength={256}
              />
            </label>
            <Button type="submit" disabled={busy}>
              {busy ? t("loading") : t("continue")}
              <ArrowRight size={17} />
            </Button>
          </>
        ) : (
          <>
            <div className="sms-panel">
              <Smartphone size={23} />
              <div>
                <strong>{t("sms")}</strong>
                <p className="sms-code" data-testid="sms-code">
                  {sms || "••••••"}
                </p>
                <span>{t("smsHelp")}</span>
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
                onChange={(e) => setOtp(e.target.value)}
                required
                disabled={busy}
              />
            </label>
            <p className="caption">{t("otpHelp")}</p>
            <Button type="submit" disabled={busy}>
              {busy ? t("loading") : t("verify")}
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={busy}
              onClick={() => {
                setChallenge("");
                setSms("");
                setOtp("");
                setFailed(false);
              }}
            >
              {t("restart")}
            </Button>
          </>
        )}
        {failed && (
          <p className="error" role="alert">
            {t("loginFail")}
          </p>
        )}
      </form>
    </>
  );
}
