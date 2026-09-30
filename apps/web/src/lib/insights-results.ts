import { z } from "zod";

const count = z
  .object({
    count: z.number().int().nonnegative(),
    denominator: z.number().int().positive(),
  })
  .strict()
  .refine((value) => value.count <= value.denominator);
const system = z.object({ pass: count, sar: count }).strict();
const source = z
  .object({
    path: z.string().regex(/^docs\/evaluation\/[a-zA-Z0-9._-]+\.(json|md)$/),
    commit: z.string().regex(/^[a-f0-9]{40}$/),
    sha256: z.string().regex(/^[a-f0-9]{64}$/),
  })
  .strict();
const published = z
  .object({
    schema_version: z.literal(1),
    version: z.literal("v4"),
    status: z.enum(["partial", "complete"]),
    source,
    systems: z.object({ B1: system, P: system }).strict(),
    sar_difference_pp: z
      .object({
        estimate: z.number().min(-100).max(100),
        ci95: z.tuple([
          z.number().min(-100).max(100),
          z.number().min(-100).max(100),
        ]),
      })
      .strict()
      .refine(
        (value) =>
          value.ci95[0] <= value.estimate && value.estimate <= value.ci95[1],
      ),
    unauthorized_actions: count,
    safety_gate: z.enum(["passed", "failed"]),
  })
  .strict();

export const insightsResultsSchema = z.union([
  z
    .object({
      schema_version: z.literal(1),
      version: z.literal("v4"),
      status: z.literal("pending"),
    })
    .strict(),
  published,
]);
export type InsightsResults = z.infer<typeof insightsResultsSchema>;
