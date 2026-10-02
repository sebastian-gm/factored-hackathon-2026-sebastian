"use client";
import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import {
  demoStories,
  storyPersona,
  storyProfile,
  type DemoStory,
} from "@/lib/demo-stories";
import { useApp } from "./workspace";
import { Button } from "./ui/button";

export function JudgeQuickstart({
  onStory,
  selected,
  locked,
  onInsights,
  onRecording,
}: {
  onStory: (story: DemoStory) => Promise<void>;
  selected: DemoStory | null;
  locked: boolean;
  onInsights: () => void;
  onRecording?: () => void;
}) {
  const t = useTranslations();
  const { config, session, profiles, profileFlow } = useApp();
  const available = (story: DemoStory) =>
    profileFlow
      ? !!storyProfile(
          profiles?.profiles ?? [],
          story,
          session?.judge_profile_id,
        )
      : !!storyPersona(config, story, session?.username);
  const [busy, setBusy] = useState(false),
    [failed, setFailed] = useState(false);
  const lock = useRef(false);
  async function prepare(story: DemoStory) {
    if (lock.current || locked) return;
    lock.current = true;
    setBusy(true);
    setFailed(false);
    try {
      await onStory(story);
    } catch {
      setFailed(true);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  return (
    <section
      className="judge-quickstart"
      aria-labelledby="quickstart-title"
      aria-busy={busy}
    >
      <div className="quickstart-intro">
        <h2 id="quickstart-title">{t("quickstartTitle")}</h2>
        <p>{t(session ? "quickstartSignedIn" : "quickstartPurpose")}</p>
        <div className="quickstart-links">
          <button className="insights-quick-link" onClick={onInsights}>
            {t("quickstartInsights")} <span aria-hidden="true">↗</span>
          </button>
          {onRecording && (
            <button className="insights-quick-link" onClick={onRecording}>
              {t("recordingShortcut")} <span aria-hidden="true">↓</span>
            </button>
          )}
        </div>
      </div>
      <div className="story-picker" aria-label={t("quickstartStories")}>
        {demoStories.map((story) => (
          <Button
            key={story.id}
            variant="secondary"
            data-testid={`quickstart-${story.id}`}
            aria-pressed={selected?.id === story.id}
            disabled={busy || locked || !available(story)}
            onClick={() => void prepare(story)}
          >
            {t(`story_${story.id}`)}
            <span className="story-language">
              {story.locale === "pt-BR" ? "PT" : "ES"}
            </span>
          </Button>
        ))}
      </div>
      {demoStories.some((story) => !available(story)) && (
        <p className="caption">{t("recordingUnavailable")}</p>
      )}
      {failed && (
        <p className="error" role="alert">
          {t("storyFailed")}
        </p>
      )}
      {locked && <p className="caption">{t("finishPending")}</p>}
    </section>
  );
}
