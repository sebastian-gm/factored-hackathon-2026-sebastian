import type { insightsEs } from "./insights-copy";

// Keep every heading, note and nested section aligned with the original copy.
export const insightsEn: typeof insightsEs = {
  final: "Final",
  share: "Share of complaints",
  percentTotal: "Percentage of the total (%)",
  percentCases: "Percentage of cases (%)",
  percentTargets: "Percentage of known targets (%)",
  problemDenominators: "Volume: all contacts. Service time: total minutes.",
  strict_escalation: "Complete and correct handoffs",
  missed: "Missed handoffs",
  unnecessary: "Unnecessary handoffs",
  materially_incorrect: "Material errors",
  escalationDenominators:
    "53 cases require a person; 47 allow automation. Errors: rules only executed 98 cases, Aclara 100. Categories overlap.",
  languageLimit:
    "The mix of rules changes: this does not establish fairness or dialect quality.",
  mixed: "Mixed cases",
  unverified: "Outcomes reported without verification",
  localTurn: "v4 evaluation · local server",
  localLatencyNote:
    "Includes remote providers. Does not measure the Azure browser or directly compare with v2/v3 infrastructure.",
  postV4:
    "Improvements measured after the final evaluation do not change v4. Human review and a second Portuguese review remain pending.",
  v4PublishedNote: "Published results. Safety limitations still apply.",
  hero: "Complaints take more time than their numbers suggest.",
  heroBody:
    "Aclara explains your charges, lets you choose, and brings matters that require judgment to the human team.",
  dataBadge: "Synthetic bank · aggregate data",
  try: "Try Aclara",
  explore: "Explore the evidence",
  source: "Source",
  problem: "The problem in the data",
  problemBody: "Less volume. More service time.",
  volume: "Contact volume",
  handle: "Service time",
  complaints: "Complaints",
  fcr: "of complaints are resolved on the first contact",
  fcrNote:
    "Average of available responses. This is not a measured improvement from Aclara.",
  unrecognized: "Complaints about unrecognized charges",
  sla: "Beyond the service deadline",
  resolution: "Days to resolution",
  resolutionNote: "Average calendar days, only where a duration was recorded",
  contacts: "contacts",
  records: "records",
  decide: "The model understands. Code authorizes.",
  decideBody:
    "First we explain the charge. You decide whether you recognize it or want to dispute it; a dispute requires another confirmation.",
  loop: "How Aclara decides",
  loopAria: "Stages in Aclara's process",
  steps: [
    {
      title: "Understand",
      english: "Understand",
      body: "We understand your question and search only your transactions.",
    },
    {
      title: "Decide",
      english: "Decide",
      body: "Rules in code check ownership, status, date, amount and risk signals. Uncertainty leads to choices or human review.",
    },
    {
      title: "Act",
      english: "Act",
      body: "An eligible dispute or card freeze requires an exact proposal, your confirmation and additional verification. Model text does not execute actions.",
    },
    {
      title: "Verify",
      english: "Verify",
      body: "We read the record again. We only show an outcome we could verify.",
    },
    {
      title: "Escalate",
      english: "Escalate",
      body: "The team receives facts, all applicable reasons, the primary reason and verified actions. Your context comes with you.",
    },
  ],
  autonomy: "Autonomy with clear limits",
  autonomyColumns: [
    "After signing in",
    "With confirmation and a code",
    "Human team only",
  ],
  autonomyRows: [
    [
      "Read your transactions and explain their status",
      "File an eligible dispute",
      "Decide reviews outside the eligibility requirements",
    ],
    [
      "Offer choices, refuse access to other accounts and prepare a handoff",
      "Freeze your own eligible card",
      "Handle fraud, legal matters, distress or a request for a person",
    ],
    [
      "Read and verify an existing case",
      "Check the rules again",
      "Review fees, transfers, missing data and cases near eligibility limits",
    ],
  ],
  authorityNote:
    "We do not promise refunds. Finding a charge does not authorize a dispute.",
  evidence:
    "Final evaluation (v4): {pass} of {total} cases meet every requirement.",
  evidenceBody:
    "Each version uses different cases. The comparison shows the history, not a causal improvement.",
  abandoned: "Abandoned",
  official: "Official result",
  fresh: "After corrections",
  pending: "Pending",
  v1Note: "Discarded attempt. Its results were not inspected or reused.",
  v2Note:
    "Aclara did not outperform rules only. Fewer handoffs did not mean more success.",
  v3Note:
    "Independent cases. The original result is preserved; these cases are now used for development.",
  v4Note: "Results will appear when they are published.",
  comparison: "Compare on the same cases",
  b1: "Rules only",
  p: "Aclara",
  pass: "Cases that meet every requirement",
  sar: "Resolved safely without a person",
  sarShort: "Difference in resolution without a person",
  pp: "pp",
  ci: "95% confidence interval",
  notComparable:
    "Compare systems within each version. Cases, rules and infrastructure change between v2, v3 and v4.",
  safety: "Unauthorized actions",
  safetyLimit: "Observing zero does not prove zero risk. 95% upper bound",
  safetyGate:
    "Both failed the safety checks. There were unauthorized actions and unverified outcomes. Zero material errors does not mean zero risk.",
  flips: "Outcomes that changed on repeat",
  flipsNote: "Repeats are correlated; a consistent failure is still a failure.",
  judging: "Evaluation across models",
  humanPending:
    "Human language review is pending; agreement between models does not replace it.",
  cost: "Model cost per case",
  turn: "Latency per turn",
  azureTurn: "Web server in Azure",
  offlineTurn: "Evaluation from a workstation",
  azurePartial: "Small partial sample",
  conversations: "conversations",
  turns: "turns",
  startupExcluded: "Startup excluded · first conversation omitted",
  azureLatencyNote:
    "Web controller time inside Azure; excludes ingress and module startup. No cold start was forced. This partial sample does not establish an SLA or a cold-start limit.",
  median: "Median",
  p95: "95th percentile",
  seconds: "s",
  costNote:
    "Average per case in the primary pass; inference only. Excludes infrastructure, repeats and judges.",
  latencyNote:
    "Evaluation measured from a workstation to Azure Postgres. Includes that network hop; does not measure the production experience or later optimizations.",
  v4Loading: "Checking the v4 publication…",
  v4Unavailable:
    "We could not check the v4 publication. Earlier results remain visible.",
  retry: "Check again",
  partial: "Partial publication",
  complete: "Complete publication",
  gatePassed: "Safety checks passed",
  gateFailed: "Safety checks failed",
  ml: "Find the right charge",
  mlBody:
    "We rank only your transactions. When details are missing, we offer choices; this does not authorize a dispute.",
  train: "Training queries",
  validation: "Validation queries",
  original: "Original queries",
  sparse: "Incomplete language",
  matcherAria: "Charge search test",
  diagnostic: "Reused synthetic test · not a new evaluation",
  top1: "Correct charge ranked first",
  recall3: "Correct charge among the three choices",
  wrong: "Wrong proposals / proposals",
  queries: "queries",
  targets: "with a known target",
  matcherLimit:
    "Only charges with a known target. We simulate missing dates, approximate amounts and spelling errors; we do not measure a real language model or production safety.",
  matcherTradeoff:
    "Finding more charges can also produce wrong proposals. Selecting one does not confirm an action.",
  tracking: "How we verify the search",
  trackingBody:
    "The original v1 experiment documents MLflow in a private local store. v2 preserves versioned parameters, calibrators, metrics and hashes; selection uses training and validation, without tuning to the human test.",
  pipeline: "Verified data before a reply",
  pipelineBody: "We receive, review and prepare data before using it.",
  pipelineSteps: [
    { title: "Input", body: "Private source and control file" },
    { title: "Review", body: "Types, normalization and quality checks" },
    { title: "Ready data", body: "Data prepared for serving" },
  ],
  lineage: "See how the data is prepared",
  lineageAlt:
    "dbt lineage from the committed manifest: sources, silver and gold",
  lineageNote: "A map of the project, not a live view of the bank.",
  sources: "Sources",
  sourcesBody:
    "Each figure links to its source. Displayed percentages are rounded.",
  viewSource: "View source",
  hash: "File fingerprint",
  sourceCommit: "Source version",
};
