import type { Config, Locale, Surface } from "./contracts";
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
export function storyDraft(config: Config, story: DemoStory): string {
  if (config.fixtures) return story.draft;
  // Generic language only: live transaction values must be supplied by the owner.
  return story.id === "explain"
    ? "Quiero entender un cargo en mi tarjeta."
    : story.id === "ambiguous"
      ? "Quero entender uma cobrança no meu cartão. Quais compras posso revisar?"
      : "Perdí mi tarjeta y necesito ayuda con una compra que no reconozco.";
}
