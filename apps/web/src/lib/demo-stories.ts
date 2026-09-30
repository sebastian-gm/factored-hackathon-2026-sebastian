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
    draft: "Não reconheço uma compra de uns 90 reais",
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
      : p.role === "customer" && p.demo_stories?.includes(story.id),
  );
  return eligible.find((p) => p.username === preferredUsername) ?? eligible[0];
}
export function storyDraft(config: Config, story: DemoStory): string {
  if (config.fixtures) return story.draft;
  // Generic language only: live transaction values must be supplied by the owner.
  return story.id === "explain"
    ? "Quiero entender un cargo pendiente."
    : story.id === "ambiguous"
      ? "Não reconheço uma compra. Preciso escolher qual movimento."
      : "Perdí mi tarjeta y necesito ayuda con una compra que no reconozco.";
}
