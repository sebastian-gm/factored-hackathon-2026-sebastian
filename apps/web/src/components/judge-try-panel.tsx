"use client";
import { useRef } from "react";
import { useTranslations } from "next-intl";

const stories = [
  "unfamiliar",
  "dispute",
  "ambiguous",
  "card",
  "human",
  "injection",
] as const;

export function JudgeTryPanel({
  disabled,
  onChoose,
}: {
  disabled: boolean;
  onChoose: (message: string) => void;
}) {
  const t = useTranslations();
  const panel = useRef<HTMLDetailsElement>(null);
  return (
    <details
      className="judge-try-panel"
      ref={panel}
      data-testid="judge-try-panel"
    >
      <summary>{t("judgeTryTitle")}</summary>
      <p className="caption">{t("judgeTryBody")}</p>
      <ul>
        {stories.map((story) => (
          <li key={story}>
            <button
              type="button"
              disabled={disabled}
              data-testid={`judge-draft-${story}`}
              onClick={() => {
                if (panel.current) panel.current.open = false;
                onChoose(t(`judgeMessage_${story}`));
              }}
            >
              <strong>{t(`judgeStory_${story}`)}</strong>
              <span>{t(`judgeMessage_${story}`)}</span>
            </button>
          </li>
        ))}
      </ul>
      {disabled && <p className="caption">{t("finishPending")}</p>}
    </details>
  );
}
