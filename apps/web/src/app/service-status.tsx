"use client";

import { useEffect, useState } from "react";

type Health = { status: string; service: string; llm_provider: string };

export default function ServiceStatus({ apiBase }: { apiBase: string }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${apiBase}/healthz`, { cache: "no-store", signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json() as Promise<Health>;
      })
      .then(setHealth)
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [apiBase]);
  return <p role="status">{health
    ? `${health.service}: ${health.status} · LLM: ${health.llm_provider}`
    : failed ? "API unavailable · Inicia la API / Inicie a API" : "Conectando…"}</p>;
}
