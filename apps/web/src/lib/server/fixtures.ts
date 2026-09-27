import "server-only";
import {
  createHash,
  randomBytes,
  randomInt,
  timingSafeEqual,
} from "node:crypto";
import type {
  DeskPacket,
  OpsSnapshot,
  Plan,
  Session,
  TraceEvent,
  Transaction,
} from "../contracts";
import results from "../../../fixtures/results.json";
import { BANK_CLOCK, DATASET, personas, transactions } from "./fixture-data";

export class HttpError extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(code);
  }
}
type Identity = Session & { workspace: string; expires: number; otpAt: number };
type Conversation = {
  token: string;
  id: string;
  language?: "es" | "pt";
  selected?: Transaction;
  proposal?: { hash: string; expires: number };
  receipt?: Plan;
  consumed?: string;
  events: TraceEvent[];
};
type Workspace = {
  packets: DeskPacket[];
  conversations: Map<string, Conversation>;
  created: number;
};
type Store = {
  workspaces: Map<string, Workspace>;
  sessions: Map<string, Identity>;
  challenges: Map<
    string,
    {
      token: string;
      code: string;
      identity: Identity;
      expires: number;
      attempts: number;
    }
  >;
};
const scope = globalThis as typeof globalThis & {
  aclaraFrontendFixtures?: Store;
};
const store: Store = (scope.aclaraFrontendFixtures ??= {
  workspaces: new Map(),
  sessions: new Map(),
  challenges: new Map(),
});
const random = () => randomBytes(24).toString("hex");
const equal = (a: string, b: string) =>
  timingSafeEqual(
    createHash("sha256").update(a).digest(),
    createHash("sha256").update(b).digest(),
  );
export function workspace(existing?: string): string {
  // Fixture state expires and is scoped to an unguessable, httpOnly browser workspace.
  for (const [id, value] of store.workspaces)
    if (Date.now() - value.created > 3600000) store.workspaces.delete(id);
  for (const [id, value] of store.sessions)
    if (value.expires <= Date.now()) store.sessions.delete(id);
  for (const [id, value] of store.challenges)
    if (value.expires <= Date.now()) store.challenges.delete(id);
  if (existing && store.workspaces.has(existing)) return existing;
  const id = random();
  store.workspaces.set(id, {
    packets: [],
    conversations: new Map(),
    created: Date.now(),
  });
  return id;
}
export function fixtureLogin(
  username: string,
  password: string,
  space: string,
) {
  const secret = process.env.FRONTEND_FIXTURE_PASSWORD;
  if (!secret) throw new HttpError(503, "fixtures_unconfigured");
  const persona = personas.find((p) => p.username === username);
  if (!equal(secret, password) || !persona)
    throw new HttpError(401, "invalid_login");
  const id = random(),
    token = random();
  store.challenges.set(id, {
    token,
    code: String(randomInt(1000000)).padStart(6, "0"),
    expires: Date.now() + 300000,
    attempts: 0,
    identity: {
      username,
      role: persona.role,
      language: persona.locale === "pt-BR" ? "pt" : "es",
      workspace: space,
      expires: 0,
      otpAt: 0,
    },
  });
  return { challenge_id: id, preauth_token: token };
}
function challenge(id: string, token: string) {
  const item = store.challenges.get(id);
  if (
    !item ||
    item.expires <= Date.now() ||
    !equal(token, item.token) ||
    item.attempts >= 5
  )
    throw new HttpError(401, "challenge_expired");
  return item;
}
export function fixtureSms(id: string, token: string) {
  return { code: challenge(id, token).code };
}
export function fixtureVerify(id: string, token: string, code: string) {
  const item = challenge(id, token);
  item.attempts++;
  if (!equal(code, item.code)) throw new HttpError(401, "invalid_otp");
  const access = random();
  store.sessions.set(access, {
    ...item.identity,
    expires: Date.now() + 900000,
    otpAt: Date.now(),
  });
  store.challenges.delete(id);
  return { access_token: access };
}
export function fixtureLogout(token: string) {
  store.sessions.delete(token);
}
function principal(token: string, role?: Session["role"]): Identity {
  const identity = store.sessions.get(token);
  if (!identity || identity.expires <= Date.now())
    throw new HttpError(401, "session_expired");
  if (role && identity.role !== role) throw new HttpError(403, "role_required");
  return identity;
}
function add(
  c: Conversation,
  stage: TraceEvent["stage"],
  state: string,
  tool: string | null,
  rules: string[] = [],
) {
  c.events.push({
    id: `event-${c.events.length + 1}`,
    stage,
    state,
    tool,
    rules,
    verified: stage === "Verify",
    llm:
      stage === "Understand"
        ? {
            provider: "mock",
            model: "scripted-frontend-fixture",
            prompt_version: "none",
            input_tokens: 0,
            output_tokens: 0,
            cost_usd: 0,
            latency_ms: 0,
          }
        : null,
  });
}
export function fixtureRequest(
  path: string,
  method: string,
  token: string,
  body: Record<string, unknown>,
): unknown {
  const user = principal(token);
  const space = store.workspaces.get(user.workspace);
  if (!space) throw new HttpError(401, "session_expired");
  if (path === "me")
    return {
      username: user.username,
      role: user.role,
      language: user.language,
    };
  if (path.startsWith("agent/")) {
    principal(token, "agent");
    if (path === "agent/handoffs" && method === "GET") return space.packets;
    const [, , id, action] = path.split("/");
    const packet = space.packets.find((p) => p.handoff_id === id);
    if (!packet) throw new HttpError(404, "not_found");
    if (method === "GET" && !action) return packet;
    if (
      method === "POST" &&
      action === "claim" &&
      packet.status === "waiting"
    ) {
      packet.status = "claimed";
      packet.claimed_by = user.username;
      return packet;
    }
    if (
      method === "POST" &&
      action === "resolve" &&
      packet.status === "claimed" &&
      packet.claimed_by === user.username
    ) {
      packet.status = "resolved";
      return packet;
    }
    throw new HttpError(409, "state_changed");
  }
  if (path.startsWith("ops/")) {
    principal(token, "ops");
    if (path === "ops/demo/reset" && method === "POST") {
      if (Date.now() - user.otpAt > 600000)
        throw new HttpError(401, "step_up_required");
      if (body.confirmed !== true)
        throw new HttpError(400, "confirmation_required");
      space.packets = [];
      space.conversations.clear();
      for (const [sid, identity] of store.sessions)
        if (
          identity.workspace === user.workspace &&
          identity.role === "customer"
        )
          store.sessions.delete(sid);
      return {
        verified: space.packets.length === 0 && space.conversations.size === 0,
      };
    }
    if (path === "ops/overview" && method === "GET")
      return {
        dataset_version: DATASET,
        bank_clock: BANK_CLOCK,
        quality: [
          { name: "schema", passed: true, checked: 4 },
          { name: "ownership", passed: true, checked: 4 },
          { name: "unique", passed: true, checked: 4 },
        ],
        freshness: {
          built_at: "2026-06-18T05:45:00Z",
          source_as_of: "2026-06-18T05:30:00Z",
          status: "fresh",
        },
        conversations: [...space.conversations.values()].map((c) => ({
          id: c.id,
          events: c.events,
        })),
        daily_cost: [16, 17, 18].map((day) => ({
          date: `2026-06-${day}`,
          usd: 0,
        })),
        results,
      } satisfies OpsSnapshot;
    throw new HttpError(404, "not_found");
  }
  principal(token, "customer");
  if (path === "transactions" && method === "GET") return transactions;
  if (path === "chat/sessions" && method === "POST") {
    const id = random();
    space.conversations.set(id, { id, token, events: [] });
    return { conversation_id: id };
  }
  if (path.startsWith("handoffs/") && method === "GET") {
    const p = space.packets.find((p) => p.handoff_id === path.split("/")[1]);
    if (
      !p?.conversation_id ||
      space.conversations.get(p.conversation_id)?.token !== token
    )
      throw new HttpError(404, "not_found");
    return p;
  }
  if (path.startsWith("disputes/") && method === "GET") {
    const c = [...space.conversations.values()].find(
      (c) =>
        c.token === token && c.receipt?.case?.case_id === path.split("/")[1],
    );
    if (!c?.receipt?.case) throw new HttpError(404, "not_found");
    return c.receipt.case;
  }
  const [, , id, action] = path.split("/");
  const c = space.conversations.get(id);
  if (!c || c.token !== token) throw new HttpError(404, "not_found");
  if (action === "messages" && typeof body.message === "string") {
    if (/não|cobrança|cartão|primeiro|nenhuma|perdi/i.test(body.message))
      c.language = "pt";
    else if (/[¿¡]|reconozco|cargo|primero|perdí|ninguno/i.test(body.message))
      c.language = "es";
  }
  const pt = (c.language ?? user.language) === "pt";
  if (action === "confirm" && method === "POST") {
    if (
      typeof body.proposal_hash !== "string" ||
      typeof body.confirmed !== "boolean"
    )
      throw new HttpError(400, "invalid_request");
    if (c.receipt && body.confirmed && c.consumed === body.proposal_hash)
      return c.receipt;
    if (!c.proposal || !equal(c.proposal.hash, body.proposal_hash))
      throw new HttpError(409, "proposal_invalid");
    if (Date.now() > c.proposal.expires) {
      c.proposal = undefined;
      throw new HttpError(409, "proposal_expired");
    }
    if (Date.now() - user.otpAt > 600000)
      throw new HttpError(401, "step_up_required");
    c.consumed = c.proposal.hash;
    c.proposal = undefined;
    if (!body.confirmed)
      return {
        response_type: "cancelled",
        outcome: "cancelled",
        reply: pt
          ? "Cancelado. Nenhuma contestação foi registrada."
          : "Cancelado. No se registró ninguna disputa.",
      } satisfies Plan;
    if (!c.selected) throw new HttpError(409, "proposal_invalid");
    add(c, "Act", "EXECUTE", "create_dispute_case", ["DSP-02"]);
    const receipt = {
      case_id: `DSP-${random().slice(0, 6).toUpperCase()}`,
      transaction_handle: c.selected.handle,
      status: "received" as const,
      policy_rules: ["DSP-02", "AUTH-02"],
      created_at: BANK_CLOCK,
    };
    c.receipt = {
      response_type: "report_case",
      outcome: "dispute_filed",
      reply: pt
        ? "Sua contestação foi registrada. A equipe analisará o caso; isto não é uma promessa de reembolso."
        : "Tu disputa fue registrada. El equipo revisará el caso; esto no es una promesa de reembolso.",
      case: receipt,
      transaction: c.selected,
      verified: true,
    };
    add(c, "Verify", "REPORT", "verify_dispute_case", ["COM-01"]);
    return c.receipt;
  }
  if (
    action !== "messages" ||
    method !== "POST" ||
    typeof body.message !== "string"
  )
    throw new HttpError(400, "invalid_request");
  if (c.proposal) throw new HttpError(409, "proposal_pending");
  const message = body.message.toLowerCase();
  add(c, "Understand", "UNDERSTAND", null);
  if (
    /fraud|robar|perd[ií]|roub|perdi|humano/.test(message) ||
    user.username === "demo.fraud"
  ) {
    add(c, "Decide", "TRIAGE", "evaluate_policy", ["FRD-01"]);
    const existing = space.packets.find((p) => p.conversation_id === id);
    const packet: DeskPacket = existing ?? {
      schema_version: "1.0",
      handoff_id: `HO-${random().slice(0, 6).toUpperCase()}`,
      conversation_id: id,
      created_at: BANK_CLOCK,
      customer_display: "Persona demo · ••42",
      reason_codes: ["FRD-01"],
      priority: "high",
      sla_due_at: "2026-06-18T08:00:00Z",
      status: "waiting",
      claimed_by: null,
      route: {
        queue: "Fraudes",
        language: pt ? "pt" : "es",
        fallback_used: false,
      },
      verified_facts: [transactions[1]],
      actions_taken: ["create_handoff"],
      open_questions: [
        pt
          ? "Você ainda tem acesso ao cartão?"
          : "¿Conservas acceso a la tarjeta?",
      ],
      evidence: [
        {
          id: "evidence-1",
          record_ref: "txn_livraria",
          tool: "get_transaction",
          verified_at: BANK_CLOCK,
          dataset_version: DATASET,
        },
      ],
      actions: [
        {
          action: "create_handoff",
          status: "verified",
          evidence_ref: "evidence-handoff",
        },
      ],
    };
    if (!existing) {
      packet.evidence.push({
        id: "evidence-handoff",
        record_ref: packet.handoff_id,
        tool: "verify_handoff",
        verified_at: BANK_CLOCK,
        dataset_version: DATASET,
      });
      space.packets.push(packet);
    }
    add(c, "Escalate", "HANDOFF_CREATED", "create_handoff", ["FRD-01"]);
    add(c, "Verify", "CLOSE", "verify_handoff");
    return {
      response_type: "offer_human",
      outcome: "handoff_created",
      reply: pt
        ? "Encaminhei seu pedido à equipe de Fraudes. Nenhum cartão foi bloqueado."
        : "Derivé tu solicitud al equipo de Fraudes. No se bloqueó ninguna tarjeta.",
      handoff: packet,
      verified: true,
    } satisfies Plan;
  }
  if (/ninguno|nenhuma/.test(message))
    return {
      response_type: "clarify",
      outcome: "clarification",
      reply: pt
        ? "Qual valor ou estabelecimento você lembra?"
        : "¿Qué importe o comercio recuerdas?",
    } satisfies Plan;
  if (
    (pt || user.username !== "demo.es.mx") &&
    !message.includes("café horizonte")
  ) {
    const index = /primeir|primer/.test(message)
      ? 1
      : /segund/.test(message)
        ? 2
        : /terceir|tercer/.test(message)
          ? 3
          : 0;
    if (!index)
      return {
        response_type: "choose_transaction",
        outcome: "choose_transaction",
        reply: pt
          ? "Encontrei três compras parecidas. Qual delas você quer revisar?"
          : "Encontré tres compras parecidas. ¿Cuál quieres revisar?",
        candidates: transactions.slice(1),
      } satisfies Plan;
    c.selected = transactions[index];
    const expires = Date.now() + 120000;
    c.proposal = {
      hash: createHash("sha256")
        .update(
          JSON.stringify({
            token,
            id,
            target: c.selected.handle,
            expires,
            nonce: random(),
          }),
        )
        .digest("hex"),
      expires,
    };
    add(c, "Decide", "CONFIRM_ACTION", "evaluate_policy", [
      "DSP-02",
      "AUTH-02",
    ]);
    return {
      response_type: "confirm_action",
      outcome: "dispute_proposed",
      reply: pt
        ? "Posso registrar uma contestação desta compra. Revise os dados e confirme se deseja continuar."
        : "Puedo registrar una disputa por esta compra. Revisa los datos y confirma si deseas continuar.",
      transaction: c.selected,
      proposal: {
        action: "create_dispute",
        proposal_hash: c.proposal.hash,
        expires_at: new Date(expires).toISOString(),
        policy_rules: ["DSP-02", "AUTH-02"],
      },
    } satisfies Plan;
  }
  add(c, "Decide", "EXPLAIN_RESOLVE", "evaluate_policy", ["TXN-01"]);
  add(c, "Verify", "CLOSE", "get_transaction");
  return {
    response_type: "explain_status",
    outcome: "explained",
    reply: pt
      ? "A cobrança de Café Horizonte é uma autorização pendente. Normalmente é confirmada ou desaparece em até 7 dias. Não há uma data de liquidação registrada."
      : "El movimiento de Café Horizonte es una autorización pendiente. Normalmente se confirma o desaparece dentro de 7 días. No hay una fecha de liquidación registrada.",
    transaction: transactions[0],
    policy_rules: ["TXN-01"],
    verified: true,
  } satisfies Plan;
}
