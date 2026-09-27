import ChatDemo from "./chat-demo";
import ServiceStatus from "./service-status";

export const dynamic = "force-dynamic";

export default function Home() {
  const apiBase = process.env.BROWSER_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return (
    <main>
      <p className="notice">Synthetic data · Simulated bank · Not a real service</p>
      <h1>Aclara</h1>
      <p>Resolución de cargos no reconocidos · Atendimento de cobranças não reconhecidas</p>
      <section aria-labelledby="status-heading">
        <h2 id="status-heading">Service status</h2>
        <ServiceStatus apiBase={apiBase} />
      </section>
      <p>Understand → Decide → Act → Verify → Escalate</p>
      <ChatDemo apiBase={apiBase} />
    </main>
  );
}
