"use client";
import { useTranslations } from "next-intl";
import { useApp } from "./workspace";
import { riskCues, usd, type LlmCall } from "@/lib/trace";

export function CallDetails({ call }: { call: LlmCall }) {
  const t = useTranslations();
  const { locale } = useApp();
  const risk = call.judgments;
  const flag = (value: boolean | undefined) =>
    value === undefined ? t("notRecorded") : t(value ? "flagYes" : "flagNo");
  const probability = (value: number | null | undefined) =>
    value == null ? "—" : `${(100 * value).toFixed(1)}%`;
  return (
    <div className="call-details">
      <dl className="llm-metadata" aria-label={t("llm")}>
        <div>
          <dt>Provider / model</dt>
          <dd>
            {call.provider} / {call.model}
          </dd>
        </div>
        <div>
          <dt>Prompt</dt>
          <dd>{call.prompt_version}</dd>
        </div>
        <div>
          <dt>{t("tokens")}</dt>
          <dd>
            {call.input_tokens} / {call.output_tokens}
          </dd>
        </div>
        <div>
          <dt>{t("callCostLatency")}</dt>
          <dd>
            {call.cost_usd === null
              ? t("costUnknown")
              : usd(call.cost_usd, locale)}{" "}
            / {call.latency_ms.toFixed(1)} ms
          </dd>
        </div>
        <div>
          <dt>{t("callAttempt")}</dt>
          <dd>
            {call.attempt ?? t("notRecorded")} /{" "}
            {call.status ?? t("notRecorded")}
          </dd>
        </div>
      </dl>
      {call.model === "x-ai/grok-4.20" && (
        <p className="badge amber">
          {t(
            call.route === "fallback_grok_4_20"
              ? "grokFallback"
              : "grokObserved",
          )}
        </p>
      )}
      {risk && (
        <section className="risk-panel" aria-label={t("riskUnion")}>
          <h3>{t("riskUnion")}</h3>
          <p className="caption">
            {t("riskThreshold", { threshold: probability(risk.threshold) })}
          </p>
          <div
            className="table-scroll"
            tabIndex={0}
            role="region"
            aria-label={t("riskUnion")}
          >
            <table>
              <thead>
                <tr>
                  <th>{t("riskCue")}</th>
                  <th>Gemini</th>
                  <th>Jev · p</th>
                  <th>Jev · {t("riskFlag")}</th>
                  <th>{t("union")}</th>
                </tr>
              </thead>
              <tbody>
                {riskCues.map((cue) => (
                  <tr key={cue}>
                    <th scope="row">{t(cue)}</th>
                    <td>{flag(risk.gemini_raw_flags[cue])}</td>
                    <td>{probability(risk.jev_raw_probabilities?.[cue])}</td>
                    <td>{flag(risk.jev_threshold_flags?.[cue])}</td>
                    <td>
                      <strong>{flag(risk.union_flags[cue])}</strong>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="caption">{t("geminiProbabilityMissing")}</p>
          {(risk.degradation || risk.primary_failed) && (
            <p role="status" className="badge amber">
              {t("riskDegraded")} · {risk.degradation ?? "primary_failed"}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
