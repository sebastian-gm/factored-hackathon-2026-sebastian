"use client";

import { useState } from "react";
import type { FormEvent } from "react";

type ChatResult = {
  response_type: string;
  outcome: string;
  reply: string;
  candidates?: Array<{
    handle: string;
    transaction_date: string;
    transaction_type: string;
    amount: number;
    currency: string;
    merchant: string;
    status: string;
  }>;
  proposal?: { proposal_hash: string };
  case?: { case_id: string; status: string };
  handoff?: { handoff_id: string; route?: { queue: string } };
};

type ChatLine = { id: number; speaker: "you" | "aclara"; text: string };

export default function ChatDemo({ apiBase }: { apiBase: string }) {
  const [language, setLanguage] = useState<"es" | "pt">("es");
  const [username, setUsername] = useState("demo.es.mx");
  const [password, setPassword] = useState("");
  const [preauth, setPreauth] = useState("");
  const [challengeId, setChallengeId] = useState("");
  const [otp, setOtp] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [conversationId, setConversationId] = useState("");
  const [draft, setDraft] = useState("");
  const [proposalHash, setProposalHash] = useState("");
  const [candidates, setCandidates] = useState<NonNullable<ChatResult["candidates"]>>([]);
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const spanish = language === "es";

  async function request(path: string, init: RequestInit = {}) {
    const response = await fetch(`${apiBase}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
      cache: "no-store",
    });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Request failed");
    return data;
  }

  async function beginLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const login = await request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      setChallengeId(login.challenge_id);
      setPreauth(login.preauth_token);
      const sms = await request(`/auth/challenges/${login.challenge_id}/sms`, {
        headers: { "X-Preauth-Token": login.preauth_token },
      });
      setOtp(sms.code);
      setPassword("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function verifyOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const session = await request("/auth/otp/verify", {
        method: "POST",
        headers: { "X-Preauth-Token": preauth },
        body: JSON.stringify({ challenge_id: challengeId, code: otp }),
      });
      setAccessToken(session.access_token);
      const conversation = await request("/chat/sessions", {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      setConversationId(conversation.conversation_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "OTP verification failed");
    } finally {
      setBusy(false);
    }
  }

  function appendLine(speaker: ChatLine["speaker"], text: string) {
    setLines((current) => [...current, { id: Date.now() + current.length, speaker, text }]);
  }

  function renderResult(result: ChatResult) {
    appendLine("aclara", result.reply);
    setProposalHash(result.proposal?.proposal_hash ?? "");
    setCandidates(result.candidates ?? []);
    if (result.case) appendLine("aclara", `${result.case.case_id} · ${result.case.status} · verified`);
    if (result.handoff) {
      const queue = result.handoff.route?.queue ?? "Agent Desk";
      appendLine("aclara", `${result.handoff.handoff_id} · ${queue}`);
    }
  }

  async function sendMessage(text: string) {
    if (!text.trim() || busy) return;
    setError("");
    setBusy(true);
    appendLine("you", text);
    setDraft("");
    try {
      const result = await request(`/chat/sessions/${conversationId}/messages`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ message: text }),
      });
      renderResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Message failed");
    } finally {
      setBusy(false);
    }
  }

  async function confirm(confirmed: boolean) {
    if (!proposalHash || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await request(`/chat/sessions/${conversationId}/confirm`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ proposal_hash: proposalHash, confirmed }),
      });
      renderResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Confirmation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="chat" aria-labelledby="chat-heading">
      <div className="chat-heading">
        <h2 id="chat-heading">{spanish ? "Chat de prueba" : "Chat de demonstração"}</h2>
        <label>
          <span className="sr-only">Language</span>
          <select value={language} onChange={(event) => setLanguage(event.target.value as "es" | "pt")}>
            <option value="es">Español</option>
            <option value="pt">Português</option>
          </select>
        </label>
      </div>

      {!challengeId && !accessToken && (
        <form onSubmit={beginLogin} className="form-stack">
          <label>
            {spanish ? "Usuario de prueba" : "Usuário de teste"}
            <input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required />
          </label>
          <label>
            {spanish ? "Contraseña" : "Senha"}
            <input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <button disabled={busy} type="submit">{spanish ? "Continuar" : "Continuar"}</button>
        </form>
      )}

      {challengeId && !accessToken && (
        <form onSubmit={verifyOtp} className="form-stack">
          <p>{spanish ? "Código enviado al panel de SMS simulado:" : "Código enviado ao painel de SMS simulado:"} <strong>{otp}</strong></p>
          <label>
            {spanish ? "Código OTP" : "Código OTP"}
            <input inputMode="numeric" autoComplete="one-time-code" value={otp} onChange={(event) => setOtp(event.target.value)} required />
          </label>
          <button disabled={busy} type="submit">{spanish ? "Verificar" : "Verificar"}</button>
        </form>
      )}

      {accessToken && (
        <>
          <div className="messages" aria-live="polite" role="log">
            {lines.length === 0 && <p className="muted">{spanish ? "Prueba: ¿Qué es el cargo de Café Central?" : "Experimente: O que é a cobrança de Café Central?"}</p>}
            {lines.map((line) => <p className={`message ${line.speaker}`} key={line.id}><strong>{line.speaker === "you" ? (spanish ? "Tú" : "Você") : "Aclara"}:</strong> {line.text}</p>)}
          </div>
          {lines.length > 0 && lines[lines.length - 1]?.speaker === "aclara" && proposalHash && (
            <div className="actions">
              <button disabled={busy} onClick={() => void confirm(true)}>{spanish ? "Confirmar disputa" : "Confirmar disputa"}</button>
              <button className="secondary" disabled={busy} onClick={() => void confirm(false)}>{spanish ? "Cancelar" : "Cancelar"}</button>
            </div>
          )}
          {candidates.length > 0 && (
            <div className="candidate-list" aria-label={spanish ? "Cargos posibles" : "Cobranças possíveis"}>
              {candidates.map((candidate, index) => {
                const choice = index === 0 ? "primero" : index === 1 ? "segundo" : "tercero";
                const portugueseChoice = index === 0 ? "primeiro" : index === 1 ? "segundo" : "terceiro";
                return (
                  <div className="candidate" key={candidate.handle}>
                    <p>
                      <strong>{index + 1}. {candidate.merchant || candidate.transaction_type}</strong>
                      <span>{new Date(candidate.transaction_date).toLocaleDateString(language === "es" ? "es-MX" : "pt-BR")}</span>
                    </p>
                    <p>{candidate.amount.toFixed(2)} {candidate.currency} · {candidate.status}</p>
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => void sendMessage(spanish ? `el ${choice}` : `o ${portugueseChoice}`)}
                    >
                      {spanish ? "Revisar este cargo" : "Revisar esta cobrança"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
          <form className="send-form" onSubmit={(event) => { event.preventDefault(); void sendMessage(draft); }}>
            <input value={draft} onChange={(event) => setDraft(event.target.value)} aria-label={spanish ? "Tu mensaje" : "Sua mensagem"} />
            <button disabled={busy} type="submit">{spanish ? "Enviar" : "Enviar"}</button>
          </form>
        </>
      )}
      {error && <p className="error" role="alert">{error}</p>}
    </section>
  );
}
