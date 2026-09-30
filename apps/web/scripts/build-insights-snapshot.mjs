// Read committed aggregate sources only. No lake, artifacts, cases, providers or bank API.
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../..",
);
const sources = [
  [
    "demand",
    "docs/data/problem-analysis-aggregates.json",
    "contact_reasons[Queja]; complaint_mix[Cargo no reconocido]",
  ],
  [
    "problem",
    "docs/problem-analysis.md",
    "Demand and outcomes; Interpretation of the measured results",
  ],
  [
    "policy",
    "contracts/interfaces/conversation-policy-v3.md",
    "Conversation contract; Outcomes, actions and SAR; Handoff reasons",
  ],
  [
    "v2",
    "docs/evaluation/final-v2-error-analysis.md",
    "Official headline report; Full-suite paired SAR difference",
  ],
  [
    "v3",
    "docs/evaluation/final-v3-results.md",
    "Primary results; Safety and readbacks; Repeats and judges; Latency and cost",
  ],
  [
    "matcher",
    "docs/ml/model-card-charge-matcher-v2.md",
    "Training and freeze; Reused synthetic test diagnostics; Human spot-check; Limits",
  ],
  [
    "matcherMetrics",
    "models/charge_matcher/v2/metrics.json",
    "original_3000.v2.overall; human_like_6000.v2.overall",
  ],
  [
    "tracking",
    "docs/ml/model-card-charge-matcher.md",
    "Reproduction and tracking (original v1 experiment)",
  ],
  [
    "pipeline",
    "docs/data/pipeline-runbook.md",
    "Atomic consumer interface; Gold projections; Contracts and local tracking",
  ],
  [
    "lineage",
    "docs/data/dbt-lineage.svg",
    "Committed dbt manifest lineage snapshot",
  ],
  [
    "disclosure",
    "docs/status/progress-log.md",
    "First final attempt abandoned; results never viewed",
  ],
];
function gitRead(args, options = {}) {
  try {
    return execFileSync("git", ["-C", repo, ...args], {
      maxBuffer: 1024 * 1024,
      ...options,
    });
  } catch {
    throw new Error(
      "Cannot read committed aggregate sources; no source contents are logged.",
    );
  }
}
const contents = {};
const provenance = [];
for (const [id, file, section] of sources) {
  const committed = gitRead(["show", `HEAD:${file}`]);
  const working = await readFile(path.join(repo, file));
  if (!working.equals(committed))
    throw new Error(`Commit source changes before exporting: ${file}`);
  contents[id] = committed.toString("utf8");
  provenance.push({
    id,
    path: file,
    section,
    sha256: createHash("sha256").update(committed).digest("hex"),
    commit: gitRead(["log", "-1", "--format=%H", "--", file], {
      encoding: "utf8",
    }).trim(),
  });
}
function row(source, label) {
  const line = contents[source]
    .split("\n")
    .find((line) => line.startsWith(`| ${label} |`));
  if (!line) throw new Error(`Missing aggregate row: ${source}/${label}`);
  return line
    .split("|")
    .slice(2, -1)
    .map((cell) => cell.trim());
}
function count(cell) {
  const match = cell.match(/(\d+)\/(\d+)/);
  if (!match) throw new Error("Missing count and denominator");
  return { count: Number(match[1]), denominator: Number(match[2]) };
}
function pair(cell) {
  return cell
    .match(/[\d.]+/g)
    .slice(0, 2)
    .map(Number);
}
function amount(cell) {
  return Number(cell.replace("$", ""));
}
function evaluation(source) {
  const pass = row(source, "Pass"),
    sar = row(
      source,
      source === "v2" ? "SAR / in-scope" : "SAR / in-scope (95% CI)",
    );
  const turn = row(
    source,
    source === "v2" ? "Turn latency p50 / p95" : "Turn p50 / p95",
  );
  const conversation = row(
    source,
    source === "v2" ? "Case latency p50 / p95" : "Case p50 / p95",
  );
  const cost = row(source, "Model cost / workload case");
  return {
    source,
    systems: Object.fromEntries(
      ["B1", "P"].map((system, index) => [
        system,
        {
          pass: count(pass[index]),
          sar: count(sar[index]),
          turn_seconds: pair(turn[index]),
          conversation_seconds: pair(conversation[index]),
          model_cost_per_conversation_usd: amount(cost[index]),
        },
      ]),
    ),
  };
}
const demand = JSON.parse(contents.demand),
  matcher = JSON.parse(contents.matcherMetrics);
const complaint = demand.contact_reasons.find(
  (item) => item.contact_reason === "Queja",
);
const charge = demand.complaint_mix.find(
  (item) => item.subcategory === "Cargo no reconocido",
);
const v2 = evaluation("v2"),
  v3 = evaluation("v3");
const v2Delta = contents.v2.match(
  /SAR difference: \*\*([−-][\d.]+) percentage points\*\*,\s*95% paired interval \*\*([−-][\d.]+) to ([+][\d.]+)/,
);
const v3Delta = contents.v3.match(
  /difference is \+([\d.]+) percentage points \(95% CI \+([\d.]+) to \+([\d.]+)\)/,
);
const repeats = contents.v3.match(
  /each \*\*(\d+)\/(\d+)\*\*, with Wilson 95% interval \*\*([\d.]+)–([\d.]+)%\*\*/,
);
const training = contents.matcher.match(
  /uses ([\d,]+) train queries and ([\d,]+)\s*validation queries/,
);
if (
  !v2Delta ||
  !v3Delta ||
  !repeats ||
  !training ||
  !contents.disclosure.includes("first final attempt was stopped") ||
  !contents.v3.includes("Both systems failed the full safety gate")
)
  throw new Error("Aggregate source wording changed; review the export.");
const signed = (text) => Number(text.replace("−", "-"));
v2.sar_difference_pp = {
  estimate: signed(v2Delta[1]),
  ci95: [signed(v2Delta[2]), signed(v2Delta[3])],
};
v3.sar_difference_pp = {
  estimate: Number(v3Delta[1]),
  ci95: [Number(v3Delta[2]), Number(v3Delta[3])],
};
v3.unauthorized_actions = {
  B1: count(row("v3", "unauthorized_action")[0]),
  P: count(row("v3", "unauthorized_action")[1]),
  p_wilson_upper95_percent: 3.7,
};
if (!contents.v3.includes("3.70% for P (n=100)"))
  throw new Error("Safety upper-bound source changed");
v3.repeats = {
  count: Number(repeats[1]),
  denominator: Number(repeats[2]),
  ci95_percent: [Number(repeats[3]), Number(repeats[4])],
};
v3.judging = { completed: 28, planned: 60 };
if (!contents.v3.includes("28/60 paired"))
  throw new Error("Judge coverage source changed");
const snapshot = {
  schema_version: 1,
  sources: provenance,
  problem: {
    source: "demand",
    contact_volume: complaint.n,
    fcr_denominator: complaint.fcr_denominator,
    volume_share: complaint.volume_share,
    handle_time_share: complaint.handle_time_share,
    fcr: complaint.fcr,
    charge_complaints: charge.n,
    sla_breach_share: charge.sla_breach_share,
    mean_resolution_calendar_days: charge.mean_resolution_calendar_days,
    resolution_days_n: charge.resolution_days_n,
  },
  evaluations: { v1: { status: "abandoned", source: "disclosure" }, v2, v3 },
  matcher: {
    source: "matcher",
    metrics_source: "matcherMetrics",
    training_queries: Number(training[1].replaceAll(",", "")),
    validation_queries: Number(training[2].replaceAll(",", "")),
    workloads: ["original_3000", "human_like_6000"].map((name) => ({
      name,
      ...Object.fromEntries(
        ["v1", "v2"].map((version) => {
          const value = matcher[name][version].overall;
          return [
            version,
            {
              queries: value.n,
              targets: value.match_queries,
              top1: value.top1_accuracy,
              recall3: value.recall_at_3,
              wrong_proposals: value.wrong_proposals,
              proposals: value.proposal_count,
              cost_per_query_units: value.mean_cost,
            },
          ];
        }),
      ),
    })),
  },
};
const target = path.join(repo, "apps/web/src/data/insights.json");
const serialized = JSON.stringify(snapshot, null, 2) + "\n";
if (process.argv.includes("--check")) {
  const saved = JSON.parse(await readFile(target, "utf8"));
  // Keep historical source pins stable across unrelated documentation edits.
  // Recompute every published aggregate from current committed source fields;
  // a source's last-changing commit alone is not a changed measurement.
  if (saved.sources.length !== provenance.length)
    throw new Error("Unexpected source registry");
  for (const [index, pin] of saved.sources.entries()) {
    const expected = provenance[index];
    if (
      pin.id !== expected.id ||
      pin.path !== expected.path ||
      pin.section !== expected.section ||
      !/^[a-f0-9]{40}$/.test(pin.commit) ||
      !/^[a-f0-9]{64}$/.test(pin.sha256)
    )
      throw new Error("Invalid source pin");
    let historyAvailable = true;
    try {
      execFileSync(
        "git",
        ["-C", repo, "cat-file", "-e", `${pin.commit}^{commit}`],
        { stdio: "ignore" },
      );
    } catch {
      historyAvailable = false;
    } // A shallow CI checkout may omit historical objects.
    if (historyAvailable) {
      const bytes = gitRead(["show", `${pin.commit}:${pin.path}`]);
      if (createHash("sha256").update(bytes).digest("hex") !== pin.sha256)
        throw new Error("Source pin digest mismatch");
    }
  }
  const { sources: savedSources, ...savedMeasurements } = saved;
  const { sources: currentSources, ...currentMeasurements } = snapshot;
  void savedSources;
  void currentSources;
  if (JSON.stringify(savedMeasurements) !== JSON.stringify(currentMeasurements))
    throw new Error("Aggregate snapshot differs from committed sources");
} else {
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, serialized);
}
console.log(
  JSON.stringify({
    aggregate_snapshot: true,
    sources: provenance.length,
    bytes: Buffer.byteLength(JSON.stringify(snapshot)),
  }),
);
