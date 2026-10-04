import type { FullResult, Reporter, TestCase, TestResult, TestStep } from "@playwright/test/reporter";

// No error bodies, DOM snapshots, requests, console strings or authentication values.
export default class TourReporter implements Reporter {
  private failedSteps: { project: string; check: string; step: string }[] = [];
  private checks: {
    project: string;
    check: string;
    status: string;
    duration_ms: number;
    line?: number;
    not_verified: string[];
  }[] = [];
  onTestEnd(test: TestCase, result: TestResult) {
    this.checks.push({
      project: test.parent.project()?.name ?? "unknown",
      check: test.title,
      status: result.status,
      duration_ms: result.duration,
      not_verified: test.annotations.filter((a) => ["limitation", "skip", "unverified", "simulated"].includes(a.type)).map((a) => a.description ?? a.type),
      ...(result.error?.location ? { line: result.error.location.line } : {}),
    });
  }
  onStepEnd(test: TestCase, _result: TestResult, step: TestStep) {
    if (step.category === "test.step" && step.error)
      this.failedSteps.push({
        project: test.parent.project()?.name ?? "unknown",
        check: test.title,
        step: step.title,
      });
  }
  onEnd(result: FullResult) {
    process.stdout.write(
      JSON.stringify({
        status: result.status,
        checks: this.checks,
        failed_steps: this.failedSteps,
      }) + "\n",
    );
  }
  printsToStdio() {
    // Prevent Playwright from adding its default error/DOM-printing reporter.
    return true;
  }
}
