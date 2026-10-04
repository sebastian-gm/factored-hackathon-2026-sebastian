"use client";
import { useTranslations } from "next-intl";
import { useEffect, useRef } from "react";
import type { JudgeProfiles, ProfileId } from "@/lib/contracts";
import type { InterfaceLocale } from "@/lib/interface-locale";
import { Button } from "./ui/button";
const ids: ProfileId[] = ["mx-es", "co-es", "ar-es", "pt"];
export function profileTitle(id: ProfileId, locale: InterfaceLocale): string {
  return id === "pt"
    ? locale === "en-US"
      ? "Portuguese speaker"
      : locale === "pt-BR"
        ? "Falante PT"
        : "Hablante PT"
    : { "mx-es": "MX · ES", "co-es": "CO · ES", "ar-es": "AR · ES" }[id];
}
export function JudgeProfilePicker({
  profiles,
  busy,
  onSelect,
  onRetry,
}: {
  profiles: JudgeProfiles | null;
  busy: boolean;
  onSelect: (id: ProfileId) => Promise<void>;
  onRetry: () => Promise<void>;
}) {
  const t = useTranslations();
  const title = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (!profiles || busy) return;
    title.current?.focus();
  }, [profiles, busy]);
  return (
    <section
      className="profile-picker"
      aria-labelledby="profile-title"
      aria-busy={busy}
    >
      <h2 ref={title} id="profile-title" tabIndex={-1}>
        {t("profileTitle")}
      </h2>
      <p className="muted">{t("profileBody")}</p>
      {busy && <p role="status">{t("profileLoading")}</p>}
      {profiles && (
        <div className="profile-options">
          {ids.map((id) => (
            <button
              type="button"
              key={id}
              disabled={busy}
              data-testid={`profile-${id}`}
              onClick={() => void onSelect(id)}
            >
              <strong>
                {id === "pt"
                  ? t("profilePT")
                  : id.slice(0, 2).toUpperCase() + " · ES"}
              </strong>
              <span>{t(`profileDescription_${id}`)}</span>
            </button>
          ))}
        </div>
      )}
      {!profiles && !busy && (
        <Button variant="secondary" onClick={() => void onRetry()}>
          {t("retry")}
        </Button>
      )}
      <p className="caption">{t("profileFresh")}</p>
    </section>
  );
}
