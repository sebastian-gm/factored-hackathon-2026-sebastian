"use client";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { z } from "zod";
import { api } from "@/lib/client";
import { transactionSchema } from "@/lib/contracts";
import {
  ledgerStoryDraft,
  storyDraft,
  type DemoStory,
} from "@/lib/demo-stories";
import { useApp } from "./workspace";
import { CustomerChat } from "./customer-chat";

export function StoryChat({
  story,
  onPendingChange,
}: {
  story: DemoStory | null;
  onPendingChange: (locked: boolean) => void;
}) {
  const t = useTranslations();
  const { config, profileFlow } = useApp();
  const live = profileFlow || !config.fixtures;
  const needsLedger = live && !!story && story.id !== "fraud";
  const [loading, setLoading] = useState(needsLedger);
  const [draft, setDraft] = useState(
    story ? storyDraft({ ...config, fixtures: !live }, story) : "",
  );
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    if (!needsLedger || !story) return;
    const controller = new AbortController();
    onPendingChange(true);
    void api("transactions", undefined, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const transactions = z.array(transactionSchema).parse(data);
        setDraft(storyDraft({ fixtures: false }, story, transactions));
        setUnavailable(ledgerStoryDraft(story, transactions) === null);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setDraft(storyDraft({ fixtures: false }, story, []));
          setUnavailable(true);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
          onPendingChange(false);
        }
      });
    return () => {
      controller.abort();
      onPendingChange(false);
    };
  }, [needsLedger, story, onPendingChange]);
  if (loading)
    return (
      <section className="panel" aria-busy="true">
        <p role="status">{t("loading")}</p>
      </section>
    );
  return (
    <>
      {unavailable && (
        <p className="error" role="alert">
          {t("storyLedgerUnavailable")}
        </p>
      )}
      <CustomerChat initialDraft={draft} onPendingChange={onPendingChange} />
    </>
  );
}
