"use client";
import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { demoStories, storyPersona, type DemoStory } from "@/lib/demo-stories";
import { useApp } from "./workspace";
import { Button } from "./ui/button";

export function JudgeQuickstart({
  onStory,
  selected,
  locked,
  onInsights,
}: {
  onStory: (story: DemoStory) => Promise<void>;
  selected: DemoStory | null;
  locked: boolean;
  onInsights: () => void;
}) {
  const t = useTranslations();
  const { config, session } = useApp();
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
        <button className="insights-quick-link" onClick={onInsights}>
          {t("quickstartInsights")} <span aria-hidden="true">↗</span>
        </button>
      </div>
      <div className="story-picker" aria-label={t("quickstartStories")}>
        {demoStories.map((story) => (
          <Button
            key={story.id}
            variant="secondary"
            data-testid={`quickstart-${story.id}`}
            aria-pressed={selected?.id === story.id}
            disabled={
              busy || locked || !storyPersona(config, story, session?.username)
            }
            onClick={() => void prepare(story)}
          >
            {t(`story_${story.id}`)}
            <span className="story-language">
              {story.locale === "pt-BR" ? "PT" : "ES"}
            </span>
          </Button>
        ))}
      </div>
      {demoStories.some(
        (story) => !storyPersona(config, story, session?.username),
      ) && <p className="caption">{t("recordingUnavailable")}</p>}
      {failed && (
        <p className="error" role="alert">
          {t("storyFailed")}
        </p>
      )}
      {locked && <p className="caption">{t("finishPending")}</p>}
    </section>
  );
}
