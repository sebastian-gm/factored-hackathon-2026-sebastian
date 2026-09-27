"use client";
import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { api } from "@/lib/client";
import type { OpsSnapshot } from "@/lib/contracts";
import { demoStories, storyPersona, type DemoStory } from "@/lib/demo-stories";
import { useApp } from "./workspace";
import { Button } from "./ui/button";
import { LiveReset } from "./live-reset";

export function RecordingHelper({
  onStory,
  onStaff,
  onLiveReset,
}: {
  onStory: (story: DemoStory) => Promise<void>;
  onStaff: (surface: "ops" | "desk") => Promise<void>;
  onLiveReset: () => Promise<void>;
}) {
  const t = useTranslations();
  const { config, session } = useApp();
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(false),
    [verified, setVerified] = useState(false);
  const lock = useRef(false);
  async function run(action: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError(false);
    try {
      await action();
    } catch {
      setError(true);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function prepare() {
    setVerified(false);
    const receipt = await api<{ verified: boolean }>("ops/demo/reset", {
      confirmed: true,
    });
    const overview = await api<OpsSnapshot>("ops/overview");
    if (!receipt.verified || overview.conversations.length)
      throw new Error("Reset not verified");
    setVerified(true);
    await onStory(demoStories[0]);
  }
  return (
    <details className="panel recording-helper">
      <summary>{t("recordingHelper")}</summary>
      <p>{t(config.fixtures ? "recordingBody" : "recordingLive")}</p>
      {config.fixtures ? (
        <>
          <div className="recording-actions">
            {session?.role === "ops" ? (
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() => void run(prepare)}
              >
                {t("resetAndStart")}
              </Button>
            ) : (
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() => void run(() => onStaff("ops"))}
              >
                {t("recordingOpsLogin")}
              </Button>
            )}
            {demoStories.map((story) => (
              <Button
                key={story.id}
                variant="secondary"
                disabled={busy}
                onClick={() => void run(() => onStory(story))}
              >
                {story.label}
              </Button>
            ))}
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => void run(() => onStaff("desk"))}
            >
              {t("recordingDesk")}
            </Button>
          </div>
          <p className="caption">{t("recordingAuth")}</p>
        </>
      ) : (
        <>
          {demoStories.some((story) => !storyPersona(config, story)) && (
            <p className="caption">{t("recordingUnavailable")}</p>
          )}
          <div className="recording-actions">
            {demoStories.map((story) => (
              <Button
                key={story.id}
                variant="secondary"
                disabled={busy || !storyPersona(config, story)}
                onClick={() => void run(() => onStory(story))}
              >
                {story.label}
              </Button>
            ))}
            {(session?.role === "ops" || session?.role === "agent") && (
              <Button
                variant="secondary"
                onClick={() => void run(() => onStaff("desk"))}
                disabled={busy}
              >
                {t("recordingDesk")}
              </Button>
            )}
          </div>
          {session?.role === "ops" ? (
            <LiveReset
              enabled={config.resetEnabled === true}
              onReset={async () => {
                await onLiveReset();
                if (storyPersona(config, demoStories[0]))
                  await onStory(demoStories[0]);
              }}
            />
          ) : (
            <p className="caption">{t("recordingRequiresOps")}</p>
          )}
          <p className="caption">{t("recordingAuth")}</p>
        </>
      )}
      {verified && (
        <p role="status" className="verified-note">
          {t("resetDone")}
        </p>
      )}
      {error && (
        <p role="alert" className="error">
          {t("recordingFailed")}
        </p>
      )}
    </details>
  );
}
