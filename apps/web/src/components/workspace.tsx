"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useSyncExternalStore,
  useRef,
  useCallback,
} from "react";
import { NextIntlClientProvider, useTranslations } from "next-intl";
import { CircleHelp, ShieldCheck, LogOut } from "lucide-react";
import type {
  Config,
  Locale,
  Session,
  Surface,
  JudgeProfiles,
  ProfileId,
} from "@/lib/contracts";
import { judgeProfilesSchema } from "@/lib/contracts";
import {
  retireWorkspace,
  configureWorkspace,
  listenProfileChanges,
  notifyProfileChange,
  SESSION_EVENT,
} from "@/lib/profile-workspace";
import { JudgeProfilePicker, profileTitle } from "./judge-profile-picker";
import { api, ApiError, setConversationLocale } from "@/lib/client";
import { date } from "@/lib/format";
import { es, pt } from "@/lib/messages";
import { en } from "@/lib/messages-en";
import type { InterfaceLocale } from "@/lib/interface-locale";
import { Button } from "./ui/button";
import { Login } from "./login";
import { StoryChat } from "./story-chat";
import { AgentDesk } from "./agent-desk";
import { StaffInvitation } from "./staff-realm-access";
import { JudgeStaffDesk } from "./judge-staff-desk";
import { RecordingHelper } from "./recording-helper";
import { storyPersona, storyProfile, type DemoStory } from "@/lib/demo-stories";
import { Ops } from "./ops";
import { JudgeQuickstart } from "./judge-quickstart";
import { Insights } from "./insights";

type AppContext = {
  locale: InterfaceLocale;
  conversationLocale: Locale;
  setLocale: (locale: InterfaceLocale) => void;
  setBankLocale: (locale: Locale) => void;
  config: Config;
  session: Session | null;
  signedIn: () => Promise<void>;
  signOut: () => Promise<void>;
  profiles: JudgeProfiles | null;
  profileFlow: boolean;
  pickerOpen: boolean;
  profileBusy: boolean;
  profileError: boolean;
  sessionExpired: boolean;
  preparedStory: DemoStory | null;
  chooseProfile: (id: ProfileId, story?: DemoStory) => Promise<void>;
  openProfiles: () => Promise<void>;
  refreshProfiles: () => Promise<void>;
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
  const [locale, setInterfaceLocale] = useState<InterfaceLocale>("en-US");
  const interfaceChoice = useRef<InterfaceLocale>("en-US");
  const [conversationLocale, setBankLocaleState] = useState<Locale>("es-MX");
  const setBankLocale = useCallback((value: Locale) => {
    setConversationLocale(value);
    setBankLocaleState(value);
  }, []);
  const setLocale = useCallback((value: InterfaceLocale) => {
    interfaceChoice.current = value;
    setInterfaceLocale(value);
    try {
      localStorage.setItem("aclara.interfaceLanguage", value);
    } catch {
      // Language selection still works when the browser blocks storage.
    }
  }, []);
  useEffect(() => {
    let saved: string | null = null;
    try {
      saved = localStorage.getItem("aclara.interfaceLanguage");
    } catch {
      // A stored preference is optional; English remains the default.
    }
    const timer = setTimeout(() => {
      if (["en-US", "es-MX", "es-CO", "es-AR", "pt-BR"].includes(saved ?? ""))
        setLocale(saved as InterfaceLocale);
    }, 0);
    return () => clearTimeout(timer);
  }, [setLocale]);
  const [config, setConfig] = useState<Config>({
    fixtures: false,
    bankClock: null,
    personas: [],
  });
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false),
    [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  const [profiles, setProfiles] = useState<JudgeProfiles | null>(null);
  const [profileFlow, setProfileFlow] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileError, setProfileError] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [preparedStory, setPreparedStory] = useState<DemoStory | null>(null);
  const judgeMode = useRef(false);
  const selectionLock = useRef(false);
  const remoteChanging = useRef(false);
  const pickerVisible = useRef(false);
  const deadline = useRef<string | null>(null);
  const configuredClock = useRef<string | null>(null);
  const clearWorkspace = useCallback(() => {
    retireWorkspace();
    setRevision((n) => n + 1);
    setSession(null);
    setProfiles(null);
    setPreparedStory(null);
    setConfig((c) => ({
      ...c,
      bankClock: null,
      personas: c.personas.filter(
        (p) => p.role === "customer" && !p.username.startsWith("judge."),
      ),
    }));
    // Do not store customer/profile state in history. Back cannot restore it.
    if (window.location.pathname !== "/")
      window.history.replaceState(null, "", "/" + window.location.search);
  }, []);
  const installSession = useCallback(
    async (current: Session | null) => {
      const isJudge = current?.judge_profiles_enabled === true;
      judgeMode.current = isJudge;
      setProfileFlow(isJudge);
      setProfileError(false);
      setSessionExpired(false);
      if (isJudge) {
        pickerVisible.current = true;
        setPickerOpen(true);
        setProfileBusy(true);
        configureWorkspace(true, true);
        const choices = judgeProfilesSchema.parse(
          await api("auth/judge/profiles"),
        );
        setProfiles(choices);
        deadline.current = choices.expires_at;
      } else {
        setProfiles(null);
        deadline.current = null;
      }
      configureWorkspace(
        isJudge,
        current?.profile_selection_required === true,
        !!current,
      );
      setSession(current);
      if (current?.role === "agent") setRevision((n) => n + 1);
      setPickerOpen(current?.profile_selection_required === true);
      pickerVisible.current = current?.profile_selection_required === true;
      setProfileBusy(false);
      if (current) {
        const bankLocale =
          current.locale ?? (current.language === "pt" ? "pt-BR" : "es-MX");
        setBankLocale(bankLocale);
        if (current.locale && interfaceChoice.current !== "en-US")
          setInterfaceLocale(current.locale);
      }
      setConfig((c) => ({
        ...c,
        bankClock: current?.bank_clock ?? configuredClock.current,
        // Only the authenticated identity supplies private account hints. Public
        // config never enumerates staff/judge identities. Logout removes them.
        personas: [
          ...c.personas.filter(
            (p) => p.role === "customer" && !p.username.startsWith("judge."),
          ),
          ...(current &&
          !isJudge &&
          !c.personas.some(
            (p) =>
              p.username === current.username &&
              p.role === "customer" &&
              !p.username.startsWith("judge."),
          )
            ? [
                {
                  username: current.username,
                  label: "",
                  role: current.role,
                  locale: current.locale!,
                  demo_stories: current.demo_stories ?? [],
                },
              ]
            : []),
        ],
      }));
    },
    [setBankLocale],
  );
  const recheckSession = useCallback(async () => {
    try {
      await installSession(await api<Session>("me"));
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      configureWorkspace(false, true);
      judgeMode.current = false;
      setSession(null);
      setProfiles(null);
      setProfileFlow(false);
      setProfileBusy(false);
      const expired = error instanceof ApiError && error.status === 401;
      setSessionExpired(expired);
      setProfileError(!expired);
    }
  }, [installSession]);
  async function signedIn() {
    const current = await api<Session>("me");
    if (current.judge_profiles_enabled) {
      judgeMode.current = true;
      setProfileFlow(true);
      clearWorkspace();
      notifyProfileChange("changing");
      try {
        await installSession(current);
      } catch (error) {
        configureWorkspace(false, true);
        judgeMode.current = false;
        setProfileFlow(false);
        setProfileBusy(false);
        setProfileError(true);
        throw error;
      } finally {
        notifyProfileChange("settled");
      }
    } else await installSession(current);
  }
  async function signOut() {
    const isJudge = judgeMode.current;
    if (isJudge) {
      clearWorkspace();
      setProfileBusy(true);
      notifyProfileChange("changing");
    }
    try {
      await api("auth/logout", {});
      if (!isJudge) {
        retireWorkspace(false);
        setSession(null);
      }
      judgeMode.current = false;
      configureWorkspace(false, false);
      setProfileFlow(false);
      setProfileBusy(false);
      setProfileError(false);
      setSessionExpired(false);
    } catch (error) {
      if (isJudge) {
        configureWorkspace(false, true);
        judgeMode.current = false;
        setProfileFlow(false);
        setProfileBusy(false);
        setProfileError(true);
      }
      throw error;
    } finally {
      if (isJudge) notifyProfileChange("settled");
    }
  }
  async function refreshProfiles() {
    setProfileBusy(true);
    setProfileError(false);
    try {
      const choices = judgeProfilesSchema.parse(
        await api("auth/judge/profiles"),
      );
      setProfiles(choices);
      deadline.current = choices.expires_at;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401)
        await recheckSession();
      else setProfileError(true);
    } finally {
      setProfileBusy(false);
    }
  }
  async function openProfiles() {
    pickerVisible.current = true;
    clearWorkspace();
    setPickerOpen(true);
    setProfileError(false);
    await refreshProfiles();
  }
  async function chooseProfile(id: ProfileId, story?: DemoStory) {
    if (selectionLock.current) return;
    selectionLock.current = true;
    const select = async () => {
      pickerVisible.current = true;
      clearWorkspace();
      setPickerOpen(true);
      setProfileBusy(true);
      setProfileError(false);
      notifyProfileChange("changing");
      try {
        // Exactly one POST. The BFF rotates the cookie; JS receives no capability.
        const result = await api<{
          verified: true;
          identity: Session;
          expires_at: string;
        }>("auth/judge/profile", { profile_id: id });
        if (!result.verified || result.identity.judge_profile_id !== id)
          throw new Error("Invalid selection");
        await installSession(result.identity);
        setPreparedStory(story ?? null);
      } catch (error) {
        // Activation may have happened. Do not recover or replay an old write.
        configureWorkspace(false, true);
        judgeMode.current = false;
        setSession(null);
        setProfiles(null);
        setProfileFlow(false);
        setProfileBusy(false);
        const expired = error instanceof ApiError && error.status === 401;
        setSessionExpired(expired);
        setProfileError(!expired);
      } finally {
        notifyProfileChange("settled");
      }
    };
    try {
      if (navigator.locks)
        await navigator.locks.request("aclara-judge-profile-selection", select);
      else await select();
    } finally {
      selectionLock.current = false;
    }
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
      .then(async ([configuration, current]) => {
        configuredClock.current = configuration.bankClock;
        setConfig({
          ...configuration,
          bankClock: current?.bank_clock ?? configuration.bankClock,
        });
        await installSession(current);
        setReady(true);
      })
      .catch((error: unknown) => {
        if (
          !ctrl.signal.aborted &&
          !(error instanceof DOMException && error.name === "AbortError")
        ) {
          setFailed(true);
          setReady(true);
        }
      });
    const expire = () => {
      clearWorkspace();
      judgeMode.current = false;
      setProfileFlow(false);
      setProfileBusy(false);
      setProfileError(false);
      setSessionExpired(true);
      notifyProfileChange("settled");
    };
    const unsubscribe = listenProfileChanges((kind) => {
      remoteChanging.current = kind === "changing";
      clearWorkspace();
      setProfileBusy(true);
      if (kind === "settled") void recheckSession();
    });
    const restore = () => {
      if (
        !judgeMode.current ||
        selectionLock.current ||
        remoteChanging.current ||
        pickerVisible.current
      )
        return;
      clearWorkspace();
      setProfileBusy(true);
      void recheckSession();
    };
    const visible = () => {
      if (document.visibilityState === "visible") restore();
    };
    window.addEventListener(SESSION_EVENT, expire);
    window.addEventListener("pageshow", restore);
    window.addEventListener("popstate", restore);
    document.addEventListener("visibilitychange", visible);
    return () => {
      ctrl.abort();
      unsubscribe();
      window.removeEventListener(SESSION_EVENT, expire);
      window.removeEventListener("pageshow", restore);
      window.removeEventListener("popstate", restore);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [clearWorkspace, installSession, recheckSession]);
  useEffect(() => {
    if (!profileFlow || !deadline.current) return;
    const timer = window.setTimeout(
      () => {
        clearWorkspace();
        void recheckSession();
      },
      Math.max(0, Date.parse(deadline.current) - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [profileFlow, profiles, clearWorkspace, recheckSession]);
  return (
    <NextIntlClientProvider
      locale={locale}
      messages={locale === "en-US" ? en : locale === "pt-BR" ? pt : es}
      timeZone="UTC"
    >
      <Context.Provider
        value={{
          locale,
          setLocale,
          conversationLocale,
          setBankLocale,
          config,
          session,
          signedIn,
          signOut,
          profiles,
          profileFlow,
          pickerOpen,
          profileBusy,
          profileError,
          sessionExpired,
          preparedStory,
          chooseProfile,
          openProfiles,
          refreshProfiles,
        }}
      >
        <Shell
          key={revision}
          ready={ready}
          failed={failed}
          initialSurface={
            profileFlow
              ? "chat"
              : session?.role === "agent" && initialSurface !== "insights"
                ? "desk"
                : initialSurface
          }
        />
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
  const {
    locale,
    setLocale,
    config,
    session,
    signOut,
    profiles,
    profileFlow,
    pickerOpen,
    profileBusy,
    profileError,
    sessionExpired,
    preparedStory,
    chooseProfile,
    openProfiles,
    refreshProfiles,
  } = useApp();
  const [preferredPersona, setPreferredPersona] = useState("");
  const [localStory, setStory] = useState<DemoStory | null>(null);
  const story = profileFlow ? preparedStory : localStory;
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
    if (profileFlow) {
      const profile = storyProfile(
        profiles?.profiles ?? [],
        next,
        session?.judge_profile_id,
      );
      if (!profile) throw new Error("Story unavailable");
      await chooseProfile(profile.profile_id, next);
      return;
    }
    const persona = storyPersona(config, next, session?.username);
    if (!persona) throw new Error("Persona unavailable");
    if (session && session.username !== persona.username) await signOut();
    setPreferredPersona(persona.username);
    if (locale !== "en-US") setLocale(persona.locale);
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
    if (locale !== "en-US") setLocale("es-MX");
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
        (workspaceSurface === "desk" &&
          session.role === "ops" &&
          !profileFlow)));
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
    <div
      className={`app-shell surface-${surface} ${profileFlow && session?.judge_profile_id ? "profile-selected" : ""}`}
    >
      <a href="#main-content" className="skip-link">
        {locale === "en-US"
          ? "Skip to content"
          : locale === "pt-BR"
            ? "Ir ao conteúdo"
            : "Ir al contenido"}
      </a>
      <aside className="sidebar">
        <Link className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">
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
              {profileFlow && session?.judge_profile_id && (
                <Button
                  variant="ghost"
                  disabled={profileBusy}
                  onClick={() => void openProfiles()}
                  aria-label={`${t("changeProfile")} · ${profileTitle(session.judge_profile_id, locale)}`}
                >
                  <span className="profile-switch-label">
                    {t("changeProfile")} ·{" "}
                  </span>
                  {profileTitle(session.judge_profile_id, locale)}
                </Button>
              )}
              {
                <label className="locale-select">
                  <span className="sr-only">{t("language")}</span>
                  <select
                    value={locale}
                    onChange={(e) =>
                      setLocale(e.target.value as InterfaceLocale)
                    }
                  >
                    <option value="en-US">English</option>
                    <option value="es-MX">ES · Español</option>
                    <option value="es-CO">ES · Colombia</option>
                    <option value="es-AR">ES · Argentina</option>
                    <option value="pt-BR">PT · Português</option>
                  </select>
                </label>
              }
              {(session || profileFlow) && (
                <Button
                  variant="ghost"
                  size="icon"
                  disabled={profileBusy}
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
          {profileFlow && session?.judge_profile_id && !pickerOpen && (
            <p role="status" className="sr-only">
              {t("profileReady", {
                profile: profileTitle(session.judge_profile_id, locale),
              })}
            </p>
          )}
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
          {(authError || profileError || sessionExpired) && (
            <p className="error" role="alert">
              {t(
                sessionExpired
                  ? "sessionExpired"
                  : profileError
                    ? profileFlow
                      ? "profileUnavailable"
                      : "profileLoginAgain"
                    : "error",
              )}
            </p>
          )}
          {surface === "insights" && (
            <Insights onTry={() => setSurface("chat")} />
          )}
          {workspaceVisited && (
            <div className="workspace-pane" hidden={surface === "insights"}>
              {ready &&
                !failed &&
                !pickerOpen &&
                !profileBusy &&
                workspaceSurface === "chat" && (
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
              ) : profileFlow &&
                (pickerOpen ||
                  profileBusy ||
                  session?.profile_selection_required) ? (
                <JudgeProfilePicker
                  profiles={profiles}
                  busy={profileBusy}
                  onSelect={chooseProfile}
                  onRetry={refreshProfiles}
                />
              ) : profileFlow && session && workspaceSurface === "desk" ? (
                <JudgeStaffDesk key={workspaceRevision} />
              ) : !allowed ? (
                <div className="customer-grid">
                  <section className="panel login-panel">
                    {!config.fixtures &&
                    session &&
                    workspaceSurface === "desk" &&
                    (session.role === "customer" || profileFlow) ? (
                      <StaffInvitation />
                    ) : session ? (
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
                  <StoryChat
                    key={`${session.username}:${workspaceRevision}:${profileFlow ? (preparedStory?.id ?? "") : ""}`}
                    onPendingChange={setChatLocked}
                    story={
                      story &&
                      (profileFlow ||
                        session.username ===
                          storyPersona(config, story, session?.username)
                            ?.username)
                        ? story
                        : null
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
          {surface !== "insights" &&
            recordingEnabled &&
            ready &&
            !failed &&
            !pickerOpen &&
            !profileBusy && (
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
