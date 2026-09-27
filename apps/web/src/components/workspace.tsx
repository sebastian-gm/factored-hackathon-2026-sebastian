"use client";
import Link from "next/link";
import { createContext, useContext, useEffect, useState } from "react";
import { NextIntlClientProvider, useTranslations } from "next-intl";
import {
  ArrowUpRight,
  CheckCheck,
  CircleHelp,
  Headphones,
  LayoutDashboard,
  LogOut,
  MessageCircle,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { Config, Locale, Session, Surface } from "@/lib/contracts";
import { api } from "@/lib/client";
import { date } from "@/lib/format";
import { es, pt } from "@/lib/messages";
import { Button } from "./ui/button";
import { Login } from "./login";
import { CustomerChat } from "./customer-chat";
import { AgentDesk } from "./agent-desk";
import { Ops } from "./ops";

type AppContext = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  config: Config;
  session: Session | null;
  signedIn: () => Promise<void>;
  signOut: () => Promise<void>;
};
const Context = createContext<AppContext | null>(null);
export function useApp() {
  const value = useContext(Context);
  if (!value) throw new Error("Workspace required");
  return value;
}
export default function Workspace() {
  const [locale, setLocale] = useState<Locale>("es-MX");
  const [config, setConfig] = useState<Config>({
    fixtures: false,
    bankClock: null,
    personas: [],
  });
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false),
    [failed, setFailed] = useState(false);
  async function signedIn() {
    const current = await api<Session>("me");
    setSession(current);
    if (current.bank_clock)
      setConfig((c) => ({ ...c, bankClock: current.bank_clock! }));
    if (current.locale) setLocale(current.locale);
  }
  async function signOut() {
    await api("auth/logout", {});
    setSession(null);
  }
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  useEffect(() => {
    const ctrl = new AbortController();
    Promise.all([
      api<Config>("config", undefined, ctrl.signal),
      api<Session>("me", undefined, ctrl.signal).catch(() => null),
    ])
      .then(([configuration, current]) => {
        setConfig({
          ...configuration,
          bankClock: current?.bank_clock ?? configuration.bankClock,
        });
        setSession(current);
        setReady(true);
      })
      .catch(() => {
        if (!ctrl.signal.aborted) {
          setFailed(true);
          setReady(true);
        }
      });
    return () => ctrl.abort();
  }, []);
  return (
    <NextIntlClientProvider
      locale={locale}
      messages={locale === "pt-BR" ? pt : es}
      timeZone="UTC"
    >
      <Context.Provider
        value={{ locale, setLocale, config, session, signedIn, signOut }}
      >
        <Shell ready={ready} failed={failed} />
      </Context.Provider>
    </NextIntlClientProvider>
  );
}
function Shell({ ready, failed }: { ready: boolean; failed: boolean }) {
  const t = useTranslations();
  const { locale, setLocale, config, session, signOut } = useApp();
  const [surface, setSurface] = useState<Surface>("chat"),
    [authError, setAuthError] = useState(false);
  const role =
    surface === "chat" ? "customer" : surface === "desk" ? "agent" : "ops";
  const allowed =
    session?.role === role ||
    (!config.fixtures &&
      !!session &&
      (surface === "chat" || (surface === "desk" && session.role === "ops")));
  const nav = [
    { id: "chat" as const, icon: MessageCircle },
    { id: "desk" as const, icon: Headphones },
    { id: "ops" as const, icon: LayoutDashboard },
  ];
  async function exit() {
    try {
      await signOut();
      setAuthError(false);
    } catch {
      setAuthError(true);
    }
  }
  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        {locale === "pt-BR" ? "Ir ao conteúdo" : "Ir al contenido"}
      </a>
      <aside className="sidebar">
        <Link className="brand" href="/" aria-label="Aclara">
          <span className="brand-mark">
            a<span />
          </span>
          <span>
            aclara<span className="brand-dot">.</span>
          </span>
        </Link>
        <p className="brand-subtitle">{t("subtitle")}</p>
        <p className="nav-caption">{t("workspace")}</p>
        <nav aria-label={t("workspace")}>
          {nav.map(({ id, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${surface === id ? "active" : ""}`}
              aria-current={surface === id ? "page" : undefined}
              onClick={() => setSurface(id)}
            >
              <Icon size={19} />
              <span>{t(id)}</span>
              {surface === id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="small-brand-orbit">
            <ShieldCheck size={23} />
          </div>
          <p>{t("journeyTitle")}</p>
          <span>{t("journeyBody")}</span>
          <div className="sidebar-version">
            ACLARA / LAB 2026 <ArrowUpRight size={14} />
          </div>
        </div>
      </aside>
      <div className="workspace">
        <div className="synthetic-banner">
          <ShieldCheck size={13} />
          <span>Synthetic data · Simulated bank · Not a real service</span>
        </div>
        <header className="topbar">
          <div className="breadcrumb">
            <span>Aclara</span>
            <span>/</span>
            <strong>{t(surface)}</strong>
          </div>
          <div className="topbar-controls">
            <label className="locale-select">
              <span className="sr-only">{t("language")}</span>
              <select
                value={locale}
                onChange={(e) => setLocale(e.target.value as Locale)}
              >
                <option value="es-MX">ES · México</option>
                <option value="es-CO">ES · Colombia</option>
                <option value="es-AR">ES · Argentina</option>
                <option value="pt-BR">PT · Brasil</option>
              </select>
            </label>
            {session && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => void exit()}
                aria-label={t("signOut")}
              >
                <LogOut size={18} />
              </Button>
            )}
            <span className="avatar" aria-hidden="true">
              {surface === "chat" ? "C" : surface === "desk" ? "A" : "O"}
            </span>
          </div>
        </header>
        <main id="main-content" className="main-content">
          <div className="environment-row">
            <span className={`status-pill ${config.fixtures ? "amber" : ""}`}>
              <span className="dot" />
              {config.fixtures ? t("fixture") : t("live")}
            </span>
            <span className="clock">
              {config.bankClock
                ? `${t("simulated")} · ${date(config.bankClock, locale)}`
                : t("noClock")}
            </span>
          </div>
          {config.fixtures && (
            <p className="fixture-note">{t("fixtureNote")}</p>
          )}
          <div className="page-heading">
            <p className="eyebrow">
              {surface === "chat"
                ? "TU BANCO, MÁS CERCA / SEU BANCO, MAIS PERTO"
                : surface === "desk"
                  ? "HUMAN IN THE LOOP"
                  : "OPERATIONS & EVIDENCE"}
            </p>
            <h1>
              {t(
                surface === "chat"
                  ? "greeting"
                  : surface === "desk"
                    ? "deskTitle"
                    : "opsTitle",
              )}
            </h1>
            <p>
              {t(
                surface === "chat"
                  ? "chatIntro"
                  : surface === "desk"
                    ? "deskIntro"
                    : "opsIntro",
              )}
            </p>
          </div>
          {authError && (
            <p className="error" role="alert">
              {t("error")}
            </p>
          )}
          {!ready ? (
            <div className="panel loading" role="status">
              {t("loading")}
            </div>
          ) : failed ? (
            <div className="panel empty">
              <CircleHelp />
              <h2>{t("error")}</h2>
              <Button onClick={() => location.reload()}>{t("retry")}</Button>
            </div>
          ) : !allowed ? (
            <div className="customer-grid">
              <section className="panel login-panel">
                {session ? (
                  <>
                    <div className="hero-icon">
                      <ShieldCheck />
                    </div>
                    <h2>{t("roleTitle")}</h2>
                    <p className="muted">{t("roleBody")}</p>
                    <Button onClick={() => void exit()}>{t("restart")}</Button>
                  </>
                ) : (
                  <Login role={role} />
                )}
              </section>
              <Journey />
            </div>
          ) : surface === "chat" ? (
            <div className="customer-grid">
              <CustomerChat key={session.username} />
              <Journey />
            </div>
          ) : surface === "desk" ? (
            <AgentDesk />
          ) : (
            <Ops />
          )}
          <footer className="page-footer">
            <span>
              <ShieldCheck size={14} />{" "}
              {session ? t("secure") : "Password + OTP"}
            </span>
            <span>Understand → Decide → Act → Verify → Escalate</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
export function Journey() {
  const t = useTranslations();
  return (
    <aside className="journey">
      <div className="journey-card">
        <span className="eyebrow">ACLARA, CONTIGO / COM VOCÊ</span>
        <h2>{t("journeyTitle")}</h2>
        <p>{t("journeyBody")}</p>
        <ol>
          {["step1", "step2", "step3", "step4"].map((step, i) => (
            <li key={step}>
              <span>{i === 3 ? <CheckCheck size={17} /> : `0${i + 1}`}</span>
              {t(step)}
            </li>
          ))}
        </ol>
        <div className="orbit-art" aria-hidden="true">
          <div />
          <div />
          <span>
            <Sparkles size={25} />
          </span>
        </div>
      </div>
      <div className="human-note">
        <Headphones size={23} />
        <h3>{t("helpTitle")}</h3>
        <p>{t("helpBody")}</p>
      </div>
    </aside>
  );
}
