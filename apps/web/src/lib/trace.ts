import { z } from "zod";

export const riskCues = [
  "lost_stolen",
  "regulator",
  "legal",
  "distress",
  "injection_suspected",
  "human_requested",
] as const;
const flags = z.object({
  lost_stolen: z.boolean(),
  regulator: z.boolean(),
  legal: z.boolean(),
  distress: z.boolean(),
  injection_suspected: z.boolean(),
  human_requested: z.boolean(),
});
const probability = z.number().min(0).max(1).nullable();
const probabilities = z.object({
  lost_stolen: probability,
  regulator: probability,
  legal: probability,
  distress: probability,
  injection_suspected: probability,
  human_requested: probability,
});
// Additive staff projection proposal: only known metadata, never arbitrary judgments/text.
export const riskSchema = z.object({
  gemini_raw_flags: flags,
  gemini_raw_probabilities: probabilities,
  jev_raw_probabilities: probabilities.partial().nullable(),
  jev_threshold_flags: flags.nullable(),
  union_flags: flags,
  threshold: z.number().min(0).max(1),
  degradation: z.string().max(100).nullable(),
  primary_failed: z.boolean(),
});
export const llmSchema = z.object({
  provider: z.string(),
  model: z.string(),
  prompt_version: z.string(),
  input_tokens: z.number().int().nonnegative(),
  output_tokens: z.number().int().nonnegative(),
  cost_usd: z.number().nonnegative().nullable(),
  latency_ms: z.number().nonnegative(),
  route: z.string().nullish(),
  status: z
    .enum(["valid", "invalid_json", "provider_error", "refusal", "skipped"])
    .nullish(),
  attempt: z.number().int().positive().nullish(),
  judgments: riskSchema.nullish(),
});
export const traceEventSchema = z.object({
  id: z.string(),
  stage: z.enum(["Understand", "Decide", "Act", "Verify", "Escalate"]),
  state: z.string(),
  tool: z.string().nullable(),
  rules: z.array(z.string()),
  verified: z.boolean(),
  llm: llmSchema.nullable(),
});
export type TraceEvent = z.infer<typeof traceEventSchema>;
export type LlmCall = z.infer<typeof llmSchema>;
export function callTotals(events: TraceEvent[]) {
  const calls = [...new Map(events.map((e) => [e.id, e])).values()].flatMap(
    (e) => (e.llm ? [e.llm] : []),
  );
  return {
    count: calls.length,
    known: calls.reduce((total, call) => total + (call.cost_usd ?? 0), 0),
    unknown: calls.filter((call) => call.cost_usd === null).length,
    grok: calls.filter((call) => call.model === "x-ai/grok-4.20").length,
    fallback: calls.filter((call) => call.route === "fallback_grok_4_20")
      .length,
  };
}
export function usd(value: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "USD",
    currencyDisplay: "code",
    minimumFractionDigits: 6,
    maximumFractionDigits: 8,
  }).format(value);
}
