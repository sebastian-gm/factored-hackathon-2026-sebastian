import type {
  Config,
  Locale,
  Surface,
  JudgeProfile,
  ProfileId,
  Transaction,
} from "./contracts";
// Authored fixtures only. Live persona bindings must come from the bank's trusted config.
export const demoStories = [
  {
    id: "explain",
    label: "ES · cargo pendiente",
    username: "demo.es.mx",
    locale: "es-MX",
    surface: "chat",
    draft: "¿Qué es el cargo de Café Horizonte?",
  },
  {
    id: "ambiguous",
    label: "PT · escolha e confirmação",
    username: "demo.pt.br",
    locale: "pt-BR",
    surface: "chat",
    draft: "Não reconheço uma compra de uns 90 dólares",
  },
  {
    id: "fraud",
    label: "ES · fraude → Agent Desk",
    username: "demo.fraud",
    locale: "es-MX",
    surface: "chat",
    draft: "Perdí mi tarjeta y no reconozco una compra",
  },
] as const satisfies readonly {
  id: string;
  label: string;
  username: string;
  locale: Locale;
  surface: Surface;
  draft: string;
}[];
export type DemoStory = (typeof demoStories)[number];
export function storyProfile(
  profiles: JudgeProfile[],
  story: DemoStory,
  current?: ProfileId | null,
) {
  const eligible = profiles.filter(
    (p) =>
      p.demo_stories.includes(story.id) &&
      p.language === (story.locale === "pt-BR" ? "pt" : "es"),
  );
  const preferred: ProfileId = story.id === "ambiguous" ? "pt" : "mx-es";
  return (
    eligible.find((p) => p.profile_id === current) ??
    eligible.find((p) => p.profile_id === preferred) ??
    eligible[0]
  );
}

export function storyPersona(
  config: Config,
  story: DemoStory,
  preferredUsername?: string,
) {
  const eligible = config.personas.filter((p) =>
    config.fixtures
      ? p.username === story.username && p.role === "customer"
      : p.demo_stories?.includes(story.id),
  );
  // A trusted hint selects a login/draft, not authority. Live Ops personas can
  // also use customer chat; /me and the API still authorize every staff/write action.
  return (
    eligible.find((p) => p.username === preferredUsername) ??
    eligible.find((p) => p.role === "customer") ??
    eligible[0]
  );
}
export function storyDraft(
  config: Pick<Config, "fixtures">,
  story: DemoStory,
  transactions?: Transaction[],
): string {
  if (config.fixtures) return story.draft;
  // Live charge drafts require the authenticated profile's visible ledger.
  if (story.id === "fraud")
    return "Perdí mi tarjeta y necesito ayuda con una compra que no reconozco.";
  if (!transactions) return "";
  return (
    ledgerStoryDraft(story, transactions) ??
    (story.locale === "pt-BR"
      ? "Quero entender uma cobrança. Quais dados preciso informar para identificar a compra?"
      : "Quiero entender un cargo. ¿Qué datos necesitas para identificarlo?")
  );
}

export function ledgerStoryDraft(
  story: DemoStory,
  transactions: Transaction[],
): string | null {
  const purchases = transactions
    .filter(
      (transaction) =>
        transaction.transaction_type === "Purchase" &&
        !!transaction.merchant?.trim() &&
        Number.isFinite(transaction.amount) &&
        transaction.amount >= 0 &&
        /^[A-Z]{3}$/.test(transaction.currency) &&
        /^\d{4}-\d{2}-\d{2}T/.test(transaction.transaction_date) &&
        Number.isFinite(Date.parse(transaction.transaction_date)),
    )
    .sort(
      (a, b) =>
        Number(a.status !== "Pending") - Number(b.status !== "Pending") ||
        Date.parse(b.transaction_date) - Date.parse(a.transaction_date) ||
        a.handle.localeCompare(b.handle),
    );
  for (const purchase of purchases) {
    // Preserve the API's numeric value without rounding or locale separators.
    const amount = String(purchase.amount);
    const day = purchase.transaction_date.slice(0, 10);
    const draft =
      story.locale === "pt-BR"
        ? `O que é a cobrança de ${purchase.merchant} por ${amount} ${purchase.currency} em ${day}?`
        : `¿Qué es el cargo de ${purchase.merchant} por ${amount} ${purchase.currency} del ${day}?`;
    if (Array.from(draft).length <= 1000) return draft;
  }
  return null;
}
