"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useSyncExternalStore,
} from "react";
import { NextIntlClientProvider, useTranslations } from "next-intl";
import { CircleHelp, ShieldCheck, LogOut } from "lucide-react";
import type { Config, Locale, Session, Surface } from "@/lib/contracts";
import { api, ApiError } from "@/lib/client";
import { date } from "@/lib/format";
import { es, pt } from "@/lib/messages";
import { Button } from "./ui/button";
import { Login } from "./login";
import { CustomerChat } from "./customer-chat";
import { AgentDesk } from "./agent-desk";
import { RecordingHelper } from "./recording-helper";
import { storyPersona, storyDraft, type DemoStory } from "@/lib/demo-stories";
import { Ops } from "./ops";
import { JudgeQuickstart } from "./judge-quickstart";
import { Insights } from "./insights";

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
export default function Workspace({
  initialSurface = "chat",
}: {
  initialSurface?: Surface;
}) {
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
      api<Session>("me", undefined, ctrl.signal).catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }),
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
        <Shell ready={ready} failed={failed} initialSurface={initialSurface} />
      </Context.Provider>
    </NextIntlClientProvider>
  );
}
function subscribeRecordingFlag(changed: () => void) {
  window.addEventListener("popstate", changed);
  return () => window.removeEventListener("popstate", changed);
}
function recordingFlagEnabled() {
  return new URLSearchParams(window.location.search).get("grabar") === "1";
}
function Shell({
  ready,
  failed,
  initialSurface,
}: {
  ready: boolean;
  failed: boolean;
  initialSurface: Surface;
}) {
  const t = useTranslations();
  const pathname = usePathname();
  const { locale, setLocale, config, session, signOut } = useApp();
  const [preferredPersona, setPreferredPersona] = useState("");
  const [story, setStory] = useState<DemoStory | null>(null);
  const [workspaceRevision, setWorkspaceRevision] = useState(0);
  const [chatLocked, setChatLocked] = useState(false);
  const [workspaceSurface, setWorkspaceSurface] = useState<
    Exclude<Surface, "insights">
  >(initialSurface === "insights" ? "chat" : initialSurface);
  const [workspaceVisited, setWorkspaceVisited] = useState(
    initialSurface !== "insights",
  );
  const surface = pathname === "/insights" ? "insights" : workspaceSurface;
  function setSurface(next: Surface) {
    const path = next === "insights" ? "/insights" : "/";
    // Native history is integrated with Next's router. Retain a mounted chat
    // and its pending proposal while browsing the read-only aggregate page.
    if (window.location.pathname !== path)
      window.history.pushState(null, "", path + window.location.search);
    if (next !== "insights") {
      setWorkspaceSurface(next);
      setWorkspaceVisited(true);
    }
    window.scrollTo(0, 0);
  }
  // Hidden in server HTML. Opt-in visibility grants no action authority.
  const recordingEnabled = useSyncExternalStore(
    subscribeRecordingFlag,
    recordingFlagEnabled,
    () => false,
  );
  function showRecordingTools() {
    const helper =
      document.querySelector<HTMLDetailsElement>("#recording-helper");
    if (!helper) return;
    helper.open = true;
    helper.scrollIntoView({ block: "start" });
    helper.querySelector("summary")?.focus({ preventScroll: true });
  }
  async function openStory(next: DemoStory) {
    if (chatLocked) throw new Error("Pending customer decision");
    const persona = storyPersona(config, next, session?.username);
    if (!persona) throw new Error("Persona unavailable");
    if (session && session.username !== persona.username) await signOut();
    setPreferredPersona(persona.username);
    setLocale(persona.locale);
    setStory(next);
    setSurface("chat");
    setWorkspaceRevision((n) => n + 1);
  }
  async function openStaff(next: "ops" | "desk") {
    if (!config.fixtures) {
      if (
        next === "desk" &&
        (session?.role === "ops" || session?.role === "agent")
      )
        setSurface(next);
      return;
    }
    const username = next === "ops" ? "demo.ops" : "demo.agent";
    if (session && session.username !== username) await signOut();
    setPreferredPersona(username);
    setLocale("es-MX");
    setSurface(next);
  }
  const [authError, setAuthError] = useState(false);
  const role =
    workspaceSurface === "chat"
      ? "customer"
      : workspaceSurface === "desk"
        ? "agent"
        : "ops";
  const allowed =
    session?.role === role ||
    (!config.fixtures &&
      !!session &&
      (workspaceSurface === "chat" ||
        (workspaceSurface === "desk" && session.role === "ops")));
  const nav = [
    { id: "chat" as const },
    { id: "desk" as const },
    { id: "ops" as const },
    { id: "insights" as const },
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
    <div className={`app-shell surface-${surface}`}>
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
          {nav.map(({ id }) => (
            <button
              key={id}
              className={`nav-item ${surface === id ? "active" : ""}`}
              aria-current={surface === id ? "page" : undefined}
              onClick={() => setSurface(id)}
            >
              <span>{t(id)}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <p>{t("journeyTitle")}</p>
          <span>{t("journeyBody")}</span>
          <div className="sidebar-version">ACLARA / LAB 2026</div>
        </div>
      </aside>
      <div className="workspace">
        <header className="workspace-header">
          <div className="synthetic-banner">
            <span>{t("demoNotice")}</span>
          </div>
          <div className="topbar">
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
                  <option value="pt-BR">PT · Português brasileiro</option>
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
            </div>
          </div>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1}>
          {surface !== "insights" && (
            <div className="environment-row">
              <span
                className={`status-pill ${!ready || failed ? "neutral" : config.fixtures ? "amber" : ""}`}
              >
                <span className="dot" />
                {!ready
                  ? t("connecting")
                  : failed
                    ? t("unavailable")
                    : config.fixtures
                      ? t("fixture")
                      : t("live")}
              </span>
              <span className="clock">
                {!ready || failed
                  ? t(failed ? "unavailable" : "starting")
                  : config.bankClock
                    ? `${t("simulated")} · ${date(config.bankClock, locale)}`
                    : t("noClock")}
              </span>
            </div>
          )}
          {config.fixtures && surface !== "insights" && (
            <p className="fixture-note">{t("fixtureNote")}</p>
          )}
          <div className="page-heading">
            <p className="eyebrow">
              {surface === "insights"
                ? t("insightsEyebrow")
                : surface === "chat"
                  ? t("chatEyebrow")
                  : surface === "desk"
                    ? t("deskEyebrow")
                    : t("opsEyebrow")}
            </p>
            <h1>
              {t(
                surface === "insights"
                  ? "insightsTitle"
                  : surface === "chat"
                    ? "greeting"
                    : surface === "desk"
                      ? "deskTitle"
                      : "opsTitle",
              )}
            </h1>
            <p>
              {t(
                surface === "insights"
                  ? "insightsIntro"
                  : surface === "chat"
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
          {surface === "insights" && (
            <Insights onTry={() => setSurface("chat")} />
          )}
          {workspaceVisited && (
            <div className="workspace-pane" hidden={surface === "insights"}>
              {ready && !failed && workspaceSurface === "chat" && (
                <JudgeQuickstart
                  onStory={openStory}
                  onInsights={() => setSurface("insights")}
                  onRecording={
                    recordingEnabled ? showRecordingTools : undefined
                  }
                  selected={story}
                  locked={chatLocked}
                />
              )}
              {!ready ? (
                <div className="panel loading" role="status">
                  {t("starting")}
                </div>
              ) : failed ? (
                <div className="panel empty" role="alert">
                  <CircleHelp />
                  <h2>{t("startupUnavailable")}</h2>
                  <Button onClick={() => location.reload()}>
                    {t("retry")}
                  </Button>
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
                        <Button onClick={() => void exit()}>
                          {t("restart")}
                        </Button>
                      </>
                    ) : (
                      <Login
                        key={`${role}:${preferredPersona}`}
                        role={role}
                        preferredUsername={preferredPersona}
                      />
                    )}
                  </section>
                </div>
              ) : workspaceSurface === "chat" ? (
                <div className="customer-grid">
                  <CustomerChat
                    key={`${session.username}:${workspaceRevision}`}
                    onPendingChange={setChatLocked}
                    initialDraft={
                      story &&
                      session.username ===
                        storyPersona(config, story, session?.username)?.username
                        ? storyDraft(config, story)
                        : ""
                    }
                  />
                </div>
              ) : workspaceSurface === "desk" ? (
                <AgentDesk key={workspaceRevision} />
              ) : (
                <Ops key={workspaceRevision} />
              )}
            </div>
          )}
          {surface !== "insights" && recordingEnabled && ready && !failed && (
            <RecordingHelper
              onStory={openStory}
              onStaff={openStaff}
              onLiveReset={async () => {
                setWorkspaceRevision((n) => n + 1);
              }}
            />
          )}
          <footer className="page-footer">
            <span>
              <ShieldCheck size={14} /> {t("accessNotice")}
            </span>
            <span>{t("allStages")}</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
