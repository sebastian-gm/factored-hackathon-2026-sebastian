"use client";
import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { z } from "zod";
import { api, ApiError } from "@/lib/client";
import {
  deskSchema,
  realmInvitationSchema,
  realmJoinSchema,
} from "@/lib/staff-contracts";
import { AgentDesk } from "./agent-desk";
import { StaffInvitation } from "./staff-realm-access";
import { Button } from "./ui/button";

// Membership is recovered from the server, never from a browser flag or role.
// A selected judge keeps its customer scope and can only open its own visit.
export function JudgeStaffDesk() {
  const t = useTranslations();
  const [state, setState] = useState<"checking" | "invite" | "ready" | "error">(
    "checking",
  );
  const [revision, setRevision] = useState(0);
  const controller = useRef<AbortController | null>(null);
  async function readMembership(signal: AbortSignal) {
    const packets = z
      .array(deskSchema)
      .parse(await api("agent/handoffs", undefined, signal));
    if (packets.some((packet) => packet.scope !== "current_realm"))
      throw new Error("Unexpected queue scope");
  }
  useEffect(() => {
    const request = new AbortController();
    controller.current = request;
    readMembership(request.signal)
      .then(() => setState("ready"))
      .catch((error: unknown) => {
        if (!request.signal.aborted)
          setState(
            error instanceof ApiError && error.status === 403
              ? "invite"
              : "error",
          );
      });
    return () => request.abort();
  }, [revision]);
  async function openOwnVisit() {
    const signal = controller.current?.signal;
    if (!signal || signal.aborted) throw new Error("Retired workspace");
    const invitation = realmInvitationSchema.parse(
      await api("handoffs/realm-invitations", {}, signal),
    );
    const expires = Date.parse(invitation.expires_at);
    if (expires <= Date.now() || expires > Date.now() + 300000)
      throw new Error("Invalid invitation expiry");
    // Neither write is retried automatically; the capability stays in memory.
    realmJoinSchema.parse(
      await api(
        "agent/handoff-realm",
        { invitation: invitation.invitation },
        signal,
      ),
    );
    await readMembership(signal);
    if (!signal.aborted) setState("ready");
  }
  if (state === "ready") return <AgentDesk ownVisit />;
  return (
    <div className="customer-grid">
      <section className="panel login-panel">
        {state === "checking" ? (
          <p role="status">{t("loading")}</p>
        ) : state === "invite" ? (
          <StaffInvitation onOpenOwnVisit={openOwnVisit} />
        ) : (
          <div role="alert" className="load-failed">
            <p>{t("queueLoadFailed")}</p>
            <Button
              onClick={() => {
                setState("checking");
                setRevision((value) => value + 1);
              }}
            >
              {t("retry")}
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}
