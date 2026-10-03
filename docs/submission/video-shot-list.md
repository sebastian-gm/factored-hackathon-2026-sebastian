# Video shot list — v0.8.1, 2:55 editorial plan

Targets deployed **v0.8.1**, SHA `3bc06d0db1c9b38233c04558f8093ce956258ab2`.
The [release receipt](../history/evaluation/v0.8.1-release-notes.md) verifies the large-COP
explanation→offer→denial→read-back receipt, concurrent ES/PT attribution, and a
separately authenticated staff invitation/claim. **Judge access remains OFF**;
judge-profile footage requires the owner's submission Gate B activation and
visit-realm checks. This docs-only pass makes **no model calls** and performs no
new rehearsal. The assembled recording, transitions and duration remain unverified.

The cut totals **2:55 (175 seconds)**, inside the [three-minute limit](../00-build-brief.md).
Times are editing targets, not latency measurements. The final fifteen seconds
are reserved for limits. Preserve the simulated-bank banner throughout.

## Prepare off camera

1. Verify the recording release against the [release notes](../history/evaluation/v0.8.1-release-notes.md)
   and [submission checklist](checklist.md#prepare-judge-access-and-rehearse-the-deployed-product).
   Use desktop Chromium **1440 × 1000**, normal zoom. Warm startup and authenticate
   with owner-supplied credentials/current simulated OTP off camera. This document
   does not authorize a paid rehearsal, access change or reset.
2. After approved judge activation, select **CO · ES** for the COP clip. Identify
   an owned, eligible, unfiled charge off camera; record the actual selection if
   the filmed inquiry asks for it. Every `<importe mostrado>` below is a placeholder
   for that record's amount, filled privately at filming time, never literal text
   to send or an organizer value to commit. Prefer one ordinary amount with its
   **COP** currency; do not add an ID, phone number or competing amount. The
   [privacy-first money recovery](../history/evaluation/v0.8.1-release-notes.md#privacy-and-delegation-changes)
   can deliberately ask for clarification when context is ambiguous.
3. Record the CO explanation, dispute and contextual handoff consecutively, then
   its staff claim, **before** capturing the PT clip. The edited cut moves PT
   between CO segments. Keep the customer controller session open: logout/expiry
   revokes delegated staff access. Switching profiles clears the chat and drafts,
   not bank cases; do not pretend a later profile switch retained a selected charge.
4. Open a **separate browser profile/context** for staff. Click **Agent Desk**
   before login; sign in with the authorized staff account and its own OTP.
   Another customer tab shares cookies and is not a staff login. On the customer
   side: **Agent Desk → Crear invitación para Agent Desk → Copiar invitación**.
   On staff: paste into **Invitación temporal → Conectar esta visita**. Copy/paste
   and credentials stay off camera; never send the invitation into chat. The
   one-use invitation lasts up to five minutes and grants only masked queue/claim
   access. [Contract](../handoff-queue.md), [shipped labels](../../apps/web/src/lib/messages.ts).
5. For PT, the trusted **Elegir una compra · PT / Escolher compra · PT** shortcut
   selects the hinted PT-speaker profile and inserts a draft; it never sends.
   A PT speaker still banks in MX/CO/AR: keep the actual USD/COP/ARS currency,
   never invent BRL or a Brazilian bank persona. Wait for profile rotation/new
   workspace before sending. Ordinary persona mode may require a separate login;
   a language toggle alone is not evidence of Portuguese NLU.
6. Capture clean model-backed stories only within a separately approved filming
   budget. If a primary story becomes **Modo básico**, stop that story take;
   do not present a deterministic fallback as the real-model demonstration.
   The short basic-mode insert below is separately labelled authored UI evidence.
   Do not force provider errors, exhaust a purse or change live settings to stage it.
7. Mask organizer merchant/amount/date values, handles, customer/account details
   and case/handoff/evidence references before export; retain **COP** and labels,
   never substitute an invented number as a real record. Credentials, OTPs,
   invitations, cookies and capabilities remain absent. [Export checklist](checklist.md#record-and-export).
   A previously filed charge may return a verified **existing-case status**, not a
   new proposal. Use that wording honestly or another eligible charge; no erasure,
   reset, forced confirmation or staged OTP screen.

## Edited sequence — exact actions and narration cues

| Time | Clicks / text / framing | Narration or evidence cue |
|---|---|---|
| **0:00–0:12** | **Insights** in ES: hero and complaint FCR label; brief problem chart. | “A charge you don't recognize should lead to an answer, a choice, or a person.” **43.6%** is complaint-contact FCR in the synthetic dataset, not an Aclara outcome or savings claim. [Source](../../apps/web/src/data/insights.json). |
| **0:12–0:32** | **Mi chat**, CO profile. Open **Prueba esto → Cargo desconocido**: it inserts **`No reconozco este cargo.`**, focuses the composer and collapses. Press **Enviar mensaje** yourself. If identification is needed, edit to **`No reconozco este cargo de <importe mostrado> COP.`**, send, then choose the matching owned card. Hold the explanation and **¿Reconoces este movimiento?** offer; keep COP visible while masking organizer digits. | “A message is a draft, not authority. Non-recognition gets facts and an offer.” No write has occurred. Show any actual clarification/choice rather than cutting it into an apparently immediate match. [Drafts](../../apps/web/src/components/judge-try-panel.tsx), [flow](../../contracts/interfaces/conversation-policy-v3.md). |
| **0:32–1:00** | Click **No la reconozco, quiero disputarla**; inspect the separate action dialog, then **Confirmar**. Handle any real fresh-action OTP challenge off camera. Hold **Tu caso está registrado**, verification and intake/no-refund wording. Open **¿Por qué? → Ver IDs de reglas → Cerrar** with technical/record references masked. | “Explicit intent, exact confirmation, fresh verification when required, then committed read-back.” Login/profile selection is not write confirmation; a receipt is dispute intake, not a refund. Show an existing-case receipt honestly if that is the actual outcome. [Current release proof](../history/evaluation/v0.8.1-release-notes.md#verified-release). |
| **1:00–1:23** | PT clip: **Escolher compra · PT** prepares **`Quero entender uma cobrança no meu cartão. Quais compras posso revisar?`**. **Enviar mensagem → Revisar este movimento** on the intended card. Hold the Portuguese facts/explanation and actual currency. | “When the description is ambiguous, you choose the purchase.” Selecting a card identifies a transaction; it confirms no write. If unfamiliarity is needed, **Experimente → Cobrança desconhecida** inserts **`Não reconheço esta cobrança.`**; send manually and retain any second selection. [Story draft](../../apps/web/src/lib/demo-stories.ts). |
| **1:23–1:40** | Return to the earlier CO clip **in its original conversation**. Type **`Perdí mi tarjeta y necesito ayuda con una compra que no reconozco.`**; send. Hold **Tu solicitud está en buenas manos**, verified action and reason labels. | “A card concern brings in a person with context.” Show actual selected-charge facts, or the explicit no-facts state. A handoff is not a freeze; do not claim blocking unless a separately confirmed, verified freeze was captured. |
| **1:40–2:07** | Staff clip after off-camera invitation redemption: **Agent Desk → Solicitudes de esta visita → new packet**. Frame **Motivo principal**, other reasons, **Hechos verificados**, **Acciones registradas**, open questions and sane SLA. Click **Tomar solicitud**; hold **Asignación verificada en registros** and **En atención**. | “A separately signed-in person receives the masked packet and claims it after read-back.” This visit queue grants claim only, not final resolution, other visits, bank records, transcripts or traces. Do not show a workspace resolve button as a realm feature. [Queue boundary](../handoff-queue.md), [UI read-back](../../apps/web/src/components/agent-desk.tsx). |
| **2:07–2:20** | Customer clip: frame the chat's **Entender → Decidir → Actuar → Verificar → Derivar** indicator and the recorded **¿Por qué?** rules/receipt. If using Ops footage instead, use an independently authorized owner's **own** workspace trace and label it as a separate visit; delegated staff cannot open the customer's trace. | “Language helps us understand. Code decides what is allowed and verifies what happened.” Live Jev is OFF; do not narrate a live risk second opinion. [Decision](../adr/0017-drop-jev-from-live-path.md), [current release](../history/evaluation/v0.8.1-release-notes.md#limits-and-deferred-gates). |
| **2:20–2:31** | On a paused product frame, insert a compact sourced **dev evidence** card: **5 sessions · 1.03 s wall · warm local/mock · one-second simulated NLU**. Do not splice sequential profile clips into a claim of simultaneous execution. Any optional live split-screen must use distinct authenticated browser contexts and actual overlapping turns. | “Our five-session local mock check took about one second, with separate request context.” This is ASGI/memory, no BFF/TLS/Azure/provider, not a cloud SLO. The release's two-session live overlap is a separate small probe, not this benchmark. [Exact 1.026 s source](../history/evaluation/request-scoped-concurrency.md#measured-result), [release overlap](../history/evaluation/v0.8.1-release-notes.md#verified-release). |
| **2:31–2:40** | Separate authored fixture/UI insert, labelled **Ejemplo de interfaz · modo básico / Exemplo de interface · modo básico**: show the subtle **Modo básico · Puedes seguir con tu consulta. / Modo básico · Você pode continuar sua consulta.** notice and usable composer. If no such clip exists, use a labelled still; do not fake a live failure. | “If the language service is unavailable, the interface explains the basic mode calmly.” This illustrates a trusted `degraded=true` reply, not measured fallback quality or a healthy Azure model turn. [Notice contract](../../apps/web/README.md#basic-mode-expiry-and-handoff-scope), [copy](../../apps/web/src/lib/messages.ts). |
| **2:40–2:55** | **Insights → Explorar la evidencia ↓**: official v4, model-cost/latency labels, failed-safety disclosure. Keep any dev overlay visibly separate. End on Aclara. | “Official v4: 88 of 100 pass; safe automation is 32 of 100 overall, 32 of 47 eligible. Both full safety gates failed. This is simulated banking, with synthetic language evidence and production work still ahead.” [Official results](../evaluation/final-v4-results.md), [limits](../production-readiness.md). |

Capture first, then add voiceover. The cues above supersede the
[historical video-script draft](video-script.md) for this cut: no pending-charge
assumption, live Jev claim, automatic dispute, mandatory OTP popup, refund,
production savings or pending-v4 narration. Trim holds/transitions against the
actual exported duration; do not accelerate footage to conceal a failed action.

## Preserved rehearsal evidence — historical, not this recording

- The [92994d9 rehearsal receipt](video-rehearsal-92994d9.json) remains unchanged:
  ten turns, ten valid Gemini/Jev calls, **$0.008335678** known model cost, no
  unknown usage/provider error/fallback. That earlier image had no current
  judge-profile panel or realm staff-claim recording. Its timings are not
  v0.8.1 latency or five-session concurrency evidence.
- Historical captures remain ignored in
  `artifacts/ux-audit/azure-rehearsal-92994d9/` (0700 directory, 0600 images):
  **41 views / 82 PNGs**. They contain private organizer facts and are not export
  assets. [Older failure receipt](video-rehearsal-conversations.json) also remains.
- The [v0.8.1 release smoke](../history/evaluation/v0.8.1-release-notes.md#cost-and-preserved-history)
  separately charged **$0.00776**, four provider calls and six conversation
  attempts. These are preserved release observations, not spend for this
  docs-only update and not an estimate or authorization for another take.
