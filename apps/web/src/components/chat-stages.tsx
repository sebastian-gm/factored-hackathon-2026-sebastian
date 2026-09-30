"use client";
import { useTranslations } from "next-intl";
import type { Plan } from "@/lib/contracts";

export const chatStages = [
  "understand",
  "decide",
  "act",
  "verify",
  "escalate",
] as const;
export function responseStage(plan?: Plan): (typeof chatStages)[number] {
  if (!plan || ["clarify", "choose_transaction"].includes(plan.response_type))
    return "understand";
  if (plan.handoff) return "escalate";
  if (plan.verified === true) return "verify";
  if (plan.proposal || plan.outcome === "cancelled") return "act";
  return "decide";
}
// A response guide, not a fabricated execution trace or a grant to act.
export function ChatStages({ plan }: { plan: Plan | null }) {
  const t = useTranslations();
  const current = responseStage(plan ?? undefined);
  return (
    <div className="chat-stages" aria-label={t("stageGuide")}>
      <ol>
        {chatStages.map((stage) => (
          <li key={stage} aria-current={current === stage ? "step" : undefined}>
            {t(`stage_${stage}`)}
          </li>
        ))}
      </ol>
      <p>{t("stageGuideBody")}</p>
    </div>
  );
}
