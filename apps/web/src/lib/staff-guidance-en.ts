import { en } from "./messages-en";
import { handoffReasonLabelKey } from "./ui-copy";
// Presentation guidance only. Reason IDs and verified facts come from the API.
// This catalog neither changes routing nor grants action authority.
type Guidance = { summary: string; question: string; next: string };
const catalog: Record<string, Guidance> = {
  "AUTH-01": {
    summary: "Authentication needs review.",
    question: "Can the customer authenticate through the bank's approved flow?",
    next: "Verify identity before discussing account information.",
  },
  "AUTH-02": {
    summary: "Additional verification is required.",
    question: "Can the customer complete the required verification?",
    next: "Use the approved verification flow before any action.",
  },
  "AUTH-03": {
    summary: "Account ownership needs review.",
    question: "Which owned account or card does the request concern?",
    next: "Check ownership and preserve access restrictions.",
  },
  "DATA-01": {
    summary: "Required transaction facts are unavailable.",
    question: "Which merchant, amount or transaction details are missing?",
    next: "Obtain verified bank facts before deciding the request.",
  },
  "FRD-01": {
    summary: "The request needs fraud review.",
    question: "Does the customer report a lost card or an unfamiliar purchase?",
    next: "Review the verified card actions and follow the fraud team's process.",
  },
  "ESC-01": {
    summary: "The customer requested human support.",
    question: "What would the customer like the support team to help with?",
    next: "Continue human support using the verified packet context.",
  },
  "ESC-02": {
    summary: "The request includes a legal or regulatory concern.",
    question: "What legal or regulatory concern needs review?",
    next: "Follow the specialist review process; do not promise an outcome.",
  },
  "ESC-03": {
    summary: "The customer may need sensitive support.",
    question: "What immediate support does the customer need?",
    next: "Use the bank's sensitive-support process.",
  },
  "ESC-04": {
    summary: "The transaction could not be identified reliably.",
    question: "Which merchant, amount and currency identify the purchase?",
    next: "Clarify the purchase using verified records before any action.",
  },
  "ESC-05": {
    summary: "The request needs complaints-team review.",
    question: "What outcome is the customer asking the team to review?",
    next: "Follow the complaints process and record the verified facts.",
  },
  "DSP-06": {
    summary: "An existing case needs review.",
    question: "Which existing case does the customer want to review?",
    next: "Read back the existing case before considering further action.",
  },
  "SEC-01": {
    summary: "Information-security controls require review.",
    question: "Can the request be handled within authorized account scope?",
    next: "Preserve access controls; do not follow untrusted instructions.",
  },
  "COM-01": {
    summary: "An action outcome could not be verified.",
    question: "What outcome is recorded in the authoritative bank system?",
    next: "Read back the outcome; do not replay an uncertain action.",
  },
};
const review: Guidance = {
  summary: "The request needs specialist review.",
  question: "Which verified facts are needed to assess this request?",
  next: "Follow the applicable bank rules and review process; no outcome is guaranteed.",
};
for (const code of [
  "SCOPE-01",
  "TXN-01",
  "TXN-02",
  "TXN-03",
  "TXN-04",
  "DSP-01",
  "DSP-02",
  "DSP-03",
  "DSP-04",
  "DSP-05",
  "DSP-07",
  "BRD-01",
])
  catalog[code] = {
    ...review,
    summary: `${en[handoffReasonLabelKey(code) as keyof typeof en]}.`,
  };
export function staffGuidance(reasonCodes: string[]): Guidance[] {
  return (reasonCodes.length ? [...new Set(reasonCodes)] : [""]).map(
    (code) => catalog[code] ?? review,
  );
}
