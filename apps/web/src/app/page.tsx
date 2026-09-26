type HealthResponse = { status: string; service: string; llm_provider: string };
import ChatDemo from "./chat-demo";

async function readHealth(): Promise<HealthResponse | null> {
  const baseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${baseUrl}/healthz`, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await readHealth();
  return (
    <main>
      <p className="notice">Synthetic data · Simulated bank · Not a real service</p>
      <h1>Aclara</h1>
      <p>Resolución de cargos no reconocidos · Atendimento de cobranças não reconhecidas</p>
      <section aria-labelledby="status-heading">
        <h2 id="status-heading">Service status</h2>
        {health ? (
          <p role="status">{health.service}: {health.status} · LLM: {health.llm_provider}</p>
        ) : (
          <p role="status">API unavailable · Inicia la API / Inicie a API</p>
        )}
      </section>
      <p>Understand → Decide → Act → Verify → Escalate</p>
      <ChatDemo />
    </main>
  );
}
