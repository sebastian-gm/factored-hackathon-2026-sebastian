import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import {
  caseSchema,
  cardSchema,
  freezeProposalSchema,
  productSchema,
  handoffSchema,
  planSchema,
  transactionSchema,
} from "@/lib/contracts";
import {
  deskSchema,
  identitySchema,
  metricsSchema,
  opsSchema,
  personaSchema,
  resetProposalSchema,
  resetReceiptSchema,
  traceSchema,
} from "@/lib/staff-contracts";
import { BANK_CLOCK, personas } from "@/lib/server/fixture-data";
import {
  fixtureLogin,
  fixtureLogout,
  fixtureRequest,
  fixtureSms,
  fixtureVerify,
  HttpError,
  workspace,
} from "@/lib/server/fixtures";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const ACCESS = "aclara_access",
  PREAUTH = "aclara_preauth",
  SPACE = "aclara_workspace";
const fixtures = () => process.env.FRONTEND_DEMO_MODE === "fixtures";
const loginSchema = z
  .object({
    username: z.string().trim().min(1).max(80),
    password: z.string().min(1).max(256),
  })
  .strict();
const otpSchema = z
  .object({
    challenge_id: z.string().regex(/^[\w.-]{1,160}$/),
    code: z.string().regex(/^\d{6}$/),
  })
  .strict();
const allowed = (path: string, method: string) =>
  method === "GET"
    ? /^(me|accounts|cards\/[\w-]{1,80}|transactions|disputes\/[\w-]{1,80}|handoffs\/[\w-]{1,80})$/.test(
        path,
      )
    : /^(chat\/sessions|chat\/sessions\/[\w-]{1,80}\/(messages|confirm)|cards\/[\w-]{1,80}\/freeze(\/proposal)?)$/.test(
        path,
      );
function response(data: unknown, status = 200) {
  return NextResponse.json(data, {
    status,
    headers: {
      "Cache-Control": "no-store, private",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
function cookie(
  reply: NextResponse,
  name: string,
  value: string,
  maxAge: number,
) {
  reply.cookies.set(name, value, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge,
  });
}
async function upstream(
  path: string,
  method: string,
  token?: string,
  body?: unknown,
  preauth?: string,
): Promise<unknown> {
  const base =
    process.env.API_BASE_URL ??
    process.env.BROWSER_API_BASE_URL ??
    "http://127.0.0.1:8212";
  let result: Response;
  try {
    result = await fetch(`${base.replace(/\/$/, "")}/${path}`, {
      method,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(10000),
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(preauth ? { "X-Preauth-Token": preauth } : {}),
      },
      body: method === "POST" ? JSON.stringify(body ?? {}) : undefined,
    });
  } catch {
    throw new HttpError(503, "service_unavailable");
  }
  if (!result.ok)
    throw new HttpError(
      result.status,
      result.status === 401
        ? "session_or_credentials_invalid"
        : result.status === 409
          ? "proposal_invalid"
          : "request_failed",
    );
  try {
    return await result.json();
  } catch {
    throw new HttpError(502, "invalid_response");
  }
}
async function liveStaff(
  path: string,
  method: string,
  token: string,
  body: Record<string, unknown>,
) {
  const call = (p: string, m = "GET", b?: unknown) => upstream(p, m, token, b);
  if (method === "GET") {
    if (path === "agent/handoffs")
      return z.array(deskSchema).parse(await call(path));
    if (/^agent\/handoffs\/[\w-]{1,80}$/.test(path))
      return deskSchema.parse(await call(path));
    if (/^agent\/conversations\/[\w-]{1,80}$/.test(path))
      return traceSchema.parse(await call(path));
    if (path === "ops/snapshot") return opsSchema.parse(await call(path));
    if (path === "ops/metrics") return metricsSchema.parse(await call(path));
    if (/^ops\/reset\/[a-f0-9]{64}$/.test(path))
      return resetReceiptSchema.parse(await call(path));
  } else if (/^agent\/handoffs\/[\w-]{1,80}\/(claim|resolve)$/.test(path)) {
    const input = z
      .object({
        expected_version: z.number().int().positive(),
        idempotency_key: z.string().regex(/^[A-Za-z0-9_-]{8,80}$/),
        resolution: z.enum(["review_completed", "transferred"]).optional(),
      })
      .strict()
      .parse(body);
    const result = deskSchema.parse(await call(path, "POST", input));
    const actual = deskSchema.parse(
      await call(path.replace(/\/(claim|resolve)$/, "")),
    );
    if (
      actual.handoff_id !== result.handoff_id ||
      actual.version !== result.version ||
      actual.status !== result.status ||
      actual.claimed_by !== result.claimed_by
    )
      throw new HttpError(502, "readback_failed");
    return actual;
  } else if (path === "ops/reset/proposal" || path === "ops/reset") {
    if (process.env.FRONTEND_ALLOW_DEMO_RESET !== "true")
      throw new HttpError(403, "reset_disabled");
    if (path.endsWith("/proposal")) {
      z.object({}).strict().parse(body);
      return resetProposalSchema.parse(await call(path, "POST", {}));
    }
    const input = z
      .object({
        proposal_hash: z.string().regex(/^[a-f0-9]{64}$/),
        confirmed: z.boolean(),
      })
      .strict()
      .parse(body);
    const result = resetReceiptSchema.parse(await call(path, "POST", input));
    const actual = resetReceiptSchema.parse(
      await call(`ops/reset/${result.receipt_id}`),
    );
    if (
      actual.receipt_id !== result.receipt_id ||
      actual.reset !== input.confirmed ||
      actual.remaining_operations !== result.remaining_operations ||
      (input.confirmed && actual.remaining_operations !== 0)
    )
      throw new HttpError(502, "readback_failed");
    return actual;
  }
  throw new HttpError(404, "not_found");
}
async function handle(
  request: NextRequest,
  params: Promise<{ path: string[] }>,
) {
  try {
    const path = (await params).path.join("/");
    if (request.method === "POST") {
      const origin =
        process.env.WEB_APP_ORIGIN ??
        `${request.nextUrl.protocol}//${request.headers.get("host")}`;
      if (
        request.headers.get("origin") !== origin ||
        request.headers.get("sec-fetch-site") === "cross-site"
      )
        throw new HttpError(403, "origin_rejected");
      if (!request.headers.get("content-type")?.startsWith("application/json"))
        throw new HttpError(415, "json_required");
    }
    let body: Record<string, unknown> = {};
    if (request.method === "POST") {
      const raw = await request.text();
      if (raw.length > 8192) throw new HttpError(413, "request_too_large");
      try {
        body = z.record(z.string(), z.unknown()).parse(JSON.parse(raw));
      } catch {
        throw new HttpError(400, "invalid_request");
      }
    }
    const token = request.cookies.get(ACCESS)?.value ?? "";
    const preauth = request.cookies.get(PREAUTH)?.value ?? "";
    if (path === "config" && request.method === "GET")
      return response({
        fixtures: fixtures(),
        bankClock: fixtures() ? BANK_CLOCK : (process.env.BANK_CLOCK ?? null),
        resetEnabled:
          fixtures() || process.env.FRONTEND_ALLOW_DEMO_RESET === "true",
        personas: fixtures()
          ? personas
          : z.array(personaSchema).parse(await upstream("personas", "GET")),
      });
    if (path === "auth/logout" && request.method === "POST") {
      if (fixtures()) fixtureLogout(token);
      else if (token) {
        try {
          z.object({
            signed_out: z.literal(true),
            verified: z.literal(true),
          }).parse(await upstream(path, "POST", token, {}));
        } catch (error) {
          if (!(error instanceof HttpError && error.status === 401))
            throw error;
        }
        try {
          await upstream("me", "GET", token);
          throw new HttpError(502, "readback_failed");
        } catch (error) {
          if (!(error instanceof HttpError && error.status === 401))
            throw error;
        }
      }
      const reply = response({ signed_out: true });
      cookie(reply, ACCESS, "", 0);
      cookie(reply, PREAUTH, "", 0);
      return reply;
    }
    if (path === "auth/login" && request.method === "POST") {
      const input = loginSchema.parse(body);
      const space = fixtures()
        ? workspace(request.cookies.get(SPACE)?.value)
        : "";
      const auth = z
        .object({ challenge_id: z.string(), preauth_token: z.string() })
        .parse(
          fixtures()
            ? fixtureLogin(input.username, input.password, space)
            : await upstream(path, "POST", undefined, input),
        );
      const reply = response({ challenge_id: auth.challenge_id });
      cookie(reply, PREAUTH, auth.preauth_token, 300);
      cookie(reply, ACCESS, "", 0);
      if (fixtures()) cookie(reply, SPACE, space, 3600);
      return reply;
    }
    if (
      /^auth\/challenges\/[\w.-]{1,160}\/sms$/.test(path) &&
      request.method === "GET"
    ) {
      if (!preauth) throw new HttpError(401, "challenge_expired");
      return response(
        z
          .object({ code: z.string().regex(/^\d{6}$/) })
          .parse(
            fixtures()
              ? fixtureSms(path.split("/")[2], preauth)
              : await upstream(path, "GET", undefined, undefined, preauth),
          ),
      );
    }
    if (path === "auth/otp/verify" && request.method === "POST") {
      const input = otpSchema.parse(body);
      if (!preauth) throw new HttpError(401, "challenge_expired");
      const auth = z
        .object({ access_token: z.string() })
        .parse(
          fixtures()
            ? fixtureVerify(input.challenge_id, preauth, input.code)
            : await upstream(path, "POST", undefined, input, preauth),
        );
      const reply = response({ authenticated: true });
      cookie(reply, ACCESS, auth.access_token, 900);
      cookie(reply, PREAUTH, "", 0);
      return reply;
    }
    if (!token) throw new HttpError(401, "session_expired");
    if (path === "auth/step-up" && request.method === "POST") {
      if (fixtures()) throw new HttpError(501, "contract_pending");
      z.object({}).strict().parse(body);
      const auth = z
        .object({ challenge_id: z.string(), preauth_token: z.string() })
        .parse(await upstream(path, "POST", token));
      const reply = response({ challenge_id: auth.challenge_id });
      cookie(reply, PREAUTH, auth.preauth_token, 300);
      return reply;
    }
    if (path === "auth/step-up/verify" && request.method === "POST") {
      if (fixtures()) throw new HttpError(501, "contract_pending");
      if (!preauth) throw new HttpError(401, "challenge_expired");
      const verified = z
        .object({ status: z.literal("verified") })
        .parse(
          await upstream(path, "POST", token, otpSchema.parse(body), preauth),
        );
      const reply = response(verified);
      cookie(reply, PREAUTH, "", 0);
      return reply;
    }
    if (path.startsWith("agent/") || path.startsWith("ops/")) {
      if (fixtures())
        return response(fixtureRequest(path, request.method, token, body));
      return response(await liveStaff(path, request.method, token, body));
    }
    if (
      /^chat\/sessions\/[\w-]{1,80}\/trace$/.test(path) &&
      request.method === "GET"
    )
      return response(traceSchema.parse(await upstream(path, "GET", token)));
    if (!allowed(path, request.method)) throw new HttpError(404, "not_found");
    if (path.endsWith("/messages"))
      body = z
        .object({ message: z.string().trim().min(1).max(1000) })
        .strict()
        .parse(body);
    if (path.endsWith("/confirm") || path.endsWith("/freeze"))
      body = z
        .object({
          proposal_hash: z.string().regex(/^[a-f0-9]{64}$/),
          confirmed: z.boolean(),
        })
        .strict()
        .parse(body);
    if (path.endsWith("/freeze/proposal"))
      body = z
        .object({ language: z.enum(["es", "pt"]) })
        .strict()
        .parse(body);
    const call = (p: string, method = "GET", b?: Record<string, unknown>) =>
      fixtures()
        ? Promise.resolve(fixtureRequest(p, method, token, b ?? {}))
        : upstream(p, method, token, b);
    const data = await call(path, request.method, body);
    if (path === "accounts")
      return response(z.array(productSchema).parse(data));
    if (path.startsWith("cards/")) {
      const handle = path.split("/")[1];
      if (request.method === "GET") {
        const card = cardSchema.parse(data);
        if (card.handle !== handle) throw new HttpError(502, "readback_failed");
        return response(card);
      }
      const proposal = freezeProposalSchema.safeParse(data);
      if (path.endsWith("/proposal") && proposal.success) {
        if (proposal.data.handle !== handle)
          throw new HttpError(502, "invalid_response");
        return response(proposal.data);
      }
      const plan = planSchema.parse(data);
      if (plan.verified !== true) throw new HttpError(502, "readback_failed");
      if (!plan.handoff) throw new HttpError(502, "readback_failed");
      const actual = handoffSchema.parse(
        await call(`handoffs/${plan.handoff.handoff_id}`),
      );
      if (
        actual.handoff_id !== plan.handoff.handoff_id ||
        actual.freeze_outcome !== plan.handoff.freeze_outcome ||
        actual.route.queue !== plan.handoff.route.queue
      )
        throw new HttpError(502, "readback_failed");
      if (plan.card) {
        const card = cardSchema.parse(await call(`cards/${handle}`));
        if (
          card.handle !== handle ||
          plan.card.handle !== handle ||
          card.status !== "Frozen" ||
          plan.card.status !== "Frozen" ||
          actual.freeze_outcome !== "verified"
        )
          throw new HttpError(502, "readback_failed");
      } else if (actual.freeze_outcome === "verified") {
        throw new HttpError(502, "readback_failed");
      }
      return response({ ...plan, verified: true });
    }
    if (path === "me") {
      return response(
        fixtures()
          ? z
              .object({
                username: z.string(),
                language: z.enum(["es", "pt"]),
                role: z.enum(["customer", "agent", "ops"]),
              })
              .parse(data)
          : identitySchema.parse(data),
      );
    }
    if (path === "transactions")
      return response(z.array(transactionSchema).parse(data));
    if (path === "chat/sessions")
      return response(z.object({ conversation_id: z.string() }).parse(data));
    if (path.startsWith("disputes/")) return response(caseSchema.parse(data));
    if (path.startsWith("handoffs/"))
      return response(handoffSchema.parse(data));
    const plan = planSchema.parse(data);
    if (plan.session_ended) {
      // The bank has revoked this session. Show its refusal without claiming a
      // handoff receipt that can no longer be independently read with this token.
      const reply = response({ ...plan, handoff: null, verified: false });
      cookie(reply, ACCESS, "", 0);
      return reply;
    }
    if (plan.case) {
      if (plan.verified !== true) throw new HttpError(502, "readback_failed");
      const actual = caseSchema.parse(
        await call(`disputes/${encodeURIComponent(plan.case.case_id)}`),
      );
      if (
        actual.case_id !== plan.case.case_id ||
        actual.transaction_handle !== plan.case.transaction_handle ||
        actual.status !== plan.case.status
      )
        throw new HttpError(502, "readback_failed");
    }
    if (plan.handoff) {
      if (plan.verified !== true) throw new HttpError(502, "readback_failed");
      const actual = handoffSchema.parse(
        await call(`handoffs/${encodeURIComponent(plan.handoff.handoff_id)}`),
      );
      if (
        actual.handoff_id !== plan.handoff.handoff_id ||
        actual.route.queue !== plan.handoff.route.queue
      )
        throw new HttpError(502, "readback_failed");
      plan.verified = true;
    }
    return response(plan);
  } catch (error) {
    const known = error instanceof HttpError;
    const reply = response(
      {
        error: known
          ? error.code
          : error instanceof z.ZodError
            ? "invalid_response_or_request"
            : "request_failed",
      },
      known ? error.status : 502,
    );
    // Do not send upstream bodies, validation input, tokens or internal errors to the browser.
    if (
      known &&
      error.status === 401 &&
      !request.nextUrl.pathname.includes("/auth/")
    )
      cookie(reply, ACCESS, "", 0);
    return reply;
  }
}
export const GET = (
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) => handle(request, context.params);
export const POST = GET;
