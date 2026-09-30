# Azure video shot list — partial rehearsal

**Read-only footage is rehearsed. The three conversation stories are pending.**
On 2026-09-30, both deployed image tags matched
`c32fd6429281a764ee33dd96622f237c7c0289c3`. The owner paused model-dependent
steps because the OpenRouter balance was exhausted, before any chat message was
sent. Authentication, ES/PT navigation, Insights, the empty Agent Desk and Ops
were inspected with Playwright on Azure. Rehearsal model spend: **US$0.00**.
[Aggregate receipt](video-rehearsal-static.json).

The sequence below targets **2:55**, leaving five seconds below the
[brief's three-minute limit](../00-build-brief.md). Its conversation rows are an
execution draft from the shipped copy and
[conversation contract](../../contracts/interfaces/conversation-policy-v3.md),
not observed successful replies. Do not record them until the owner announces
the credit top-up and the story-availability blockers below are resolved.

## Prepare off camera

1. Open the restricted Azure URL supplied by the owner at `/?grabar=1`, in a
   desktop Chromium viewport of **1440 × 1000**, at normal zoom. Wait for
   **Accede a Aclara**; initial service readiness took **99.28 s** in this
   visit, including startup captures. No cold restart was forced. The next visit
   took **1.26 s**. These are individual browser observations, not a latency SLA.
   [Timing source](video-rehearsal-static.json).
2. Select **México · cargo pendiente** for the ES workspace. Retrieve the demo
   password from Key Vault directly into the login process; keep it out of
   files, shell arguments and frames. Click **Continuar**, enter the current
   simulated SMS code, then **Verificar y entrar**. Do not record credential
   entry or the SMS/code fields. Access values and account identifiers remain
   in the owner's external instructions.
3. Open **Preparar grabación**. After availability is repaired, its story
   buttons should prepare the appropriate persona and draft without sending.
   Close the helper after preparation so the chat occupies the frame. Persona
   changes still require authentication. Do not use a demo reset or change
   cloud settings.
4. Begin with **Insights** in the sidebar, language **ES · México**. Do not
   navigate to a private source file in the filmed browser. Source references
   remain visible on the page. Keep the simulation banner visible.
5. Keep raw captures private. Before any video export, mask account identifiers,
   passwords, OTPs, transaction merchant/amount/date/handles, customer details
   and case/handoff references. Generic messages below contain no organizer
   fields. A pending authorization is not a settled charge; choosing a card
   is not confirmation of a write. Use only receipts actually read back.
   [Recording checklist](checklist.md#record-and-export).

## Edited sequence and exact interactions

| Clip time | Clicks and messages                                                                                                                                                                                                                                                                                                                                                         | Hold on screen / narration cue                                                                                                                                                                                                                                             | Rehearsal status                                                                                                                           |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 0:00–0:10 | **Insights**, at the hero.                                                                                                                                                                                                                                                                                                                                                  | “An unfamiliar charge should lead to an answer, a choice, or a person.” Product is on screen immediately; the FCR label explicitly refers to complaints.                                                                                                                   | Verified static view.                                                                                                                      |
| 0:10–0:22 | Scroll to **El problema, visto en los datos**.                                                                                                                                                                                                                                                                                                                              | Complaint volume versus handle time. Say these are organizer workload aggregates, not Aclara's realized savings. Numbers and denominators come from the [page snapshot](../../apps/web/src/data/insights.json).                                                            | Verified static view.                                                                                                                      |
| 0:22–0:55 | **Mi conversación** → **Preparar grabación** → **Entender un cargo · ES**. Close the helper. The draft is **`Quiero entender un cargo pendiente.`** Click **Enviar mensaje**. If the bank offers candidates, inspect them and click **Revisar este movimiento** on the chosen card.                                                                                         | Explanation, transaction status, and **Entender → Decidir → Actuar → Verificar → Derivar**. Click the latest **¿Por qué?**, hold briefly, then **Cerrar**. If an offer appears, **Sí, la reconozco** ends this inquiry; it does not file a dispute.                        | Pending credit top-up and enabled story. Selection/explanation are not yet rehearsed.                                                      |
| 0:55–1:35 | **Preparar grabación** → **Elegir una compra · PT** (or **Escolher compra · PT** when already in PT). Complete persona login off camera if requested. Close the helper. Send **`Não reconheço uma compra. Preciso escolher qual movimento.`** with **Enviar mensagem**. On actual choices, inspect the cards and click **Revisar este movimento** on the selected purchase. | Hold the choice grid, then the explained charge and **Você reconhece este movimento?**. If offered, click **Não reconheço, quero contestar**. Show the resulting review dialog; selection and denial remain separate from confirmation.                                    | Pending; the live config currently supplies no ambiguous-story hint. A choice grid must actually appear before this scene can be approved. |
| 1:35–1:50 | Only for an eligible reviewed proposal: read the dialog, then click **Confirmar**. If a fresh OTP is requested, enter the current code off camera and click **Verificar e confirmar**.                                                                                                                                                                                      | Hold **Seu caso está registrado** only after the committed read-back succeeds. If there is a handoff, clarification or failure instead, preserve it and rewrite this shot; never substitute a receipt.                                                                     | Pending real reply, explicit confirmation and read-back.                                                                                   |
| 1:50–2:18 | **Preparar gravação** → **Pedir ajuda · ES** (or **Pedir ayuda · ES** in ES). Complete any persona login off camera. Close the helper. Send **`Perdí mi tarjeta y necesito ayuda con una compra que no reconozco.`** with **Enviar mensaje**. Then click **Agent Desk** in the same authorized ES workspace.                                                                | Customer handoff → newly created queue item → **Motivos de la derivación** → **Motivo principal** → **Acciones realizadas**. Show the actual primary/other reasons and verified read-back. This shot does not freeze a card, claim or resolve a packet.                    | Pending conversation and handoff. Current Desk queue is empty.                                                                             |
| 2:18–2:40 | **Insights** → **Explorar la evidencia ↓**. Keep **v3 · Después de las correcciones** selected; briefly show the v2/v3/v4 timeline and comparison. Scroll to the cost/latency cards, then **Fuentes y trazabilidad**.                                                                                                                                                       | Historical v3 result and safety limits; v4 stays **Pendiente**. Cost is inference-only; Azure timing is labeled partial and separate from offline timing. Use the [committed snapshot](../../apps/web/src/data/insights.json), not new rehearsal timings as model results. | Verified static views.                                                                                                                     |
| 2:40–2:55 | Hold the visible safety caveat and v4 pending panel.                                                                                                                                                                                                                                                                                                                        | “A simulated bank, limited human language review, and no production safety guarantee. We keep failures visible and verify actions in code.” Limits occupy their own final fifteen seconds.                                                                                 | Static footage available; final narration and export duration remain to be checked.                                                        |

On the credit-top-up ping, run each story once before filming and replace the
pending cells with the observed clicks, replies and turn timings. A helper hint
is availability metadata, not proof that a generic draft will select a dispute-
eligible purchase. If the service asks for missing details, requires a person,
or reports degraded/unknown usage, retain that observation and stop the
successful-demo take. Do not tune the system or invent transaction details to
force this sequence. Do not use a frozen suite or gold label.

## Observed timing and captures

Every value below is a single operation from
[video-rehearsal-static.json](video-rehearsal-static.json). Browser wall time
runs from navigation/click to a rendered ready selector; it includes the
workstation network. BFF read times use `Server-Timing`, exclude browser
rendering and are not conversation/model timings. Screenshot writes follow the
measured operation, except the initial startup observation noted above.

| Operation               |       Browser wall time |                      Related BFF GET |
| ----------------------- | ----------------------: | -----------------------------------: |
| Initial login readiness |                 99.28 s |    Not retained for that first visit |
| Warm login readiness    |                  1.26 s |                       Config 0.243 s |
| ES password → OTP ready |                  0.30 s |                     SMS read 0.015 s |
| ES OTP → chat ready     |                  0.33 s |                Identity read 0.017 s |
| ES Insights open        |                 0.145 s | Bundled aggregates; no model request |
| ES Agent Desk open      |                 0.179 s |  Queue read 0.025 s, HTTP 200, empty |
| ES Ops open             |                 0.235 s |      Snapshot read 0.047 s, HTTP 200 |
| PT Agent Desk open      |                 0.159 s |  Queue read 0.021 s, HTTP 200, empty |
| PT Insights open        |                 0.040 s | Bundled aggregates; no model request |
| Conversation turns      | **Pending — none sent** |                          **Pending** |

PT captures show the same authorized ES workspace with the language selector
set to **PT · Português brasileiro**. They verify localization and navigation,
not a PT-persona conversation or PT NLU performance. No banking action, claim,
resolution or reset was performed.

Private evidence: `artifacts/ux-audit/azure-rehearsal-c32fd64/index.html`,
**18 read-only views / 36 PNGs**, plus the initial startup/login captures
(**40 PNGs total**), all mode **0600**. Each view has a viewport and full-page
capture, with password, username and OTP fields masked. There were **zero page
errors, zero horizontal-overflow captures**, and the dark sidebar started at
the top in all read-only views. Only aggregates are committed; no screenshot,
credential, row, transcript or model thinking is in Git.

## Items to resolve for the video

| Priority | Observed issue                                                                                                                                                                          | Recording consequence / next action                                                                                                                                                                                                                                  |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P0       | Owner reports exhausted OpenRouter credit.                                                                                                                                              | Model stories are paused. Wait for the explicit top-up ping; deterministic or degraded replies are not real-model demo footage.                                                                                                                                      |
| P0       | All three quickstart and helper story buttons are disabled. ES explain/fraud hints exist on an **Ops** persona, while the frontend accepts only **customer** personas for live stories. | Frontend story eligibility needs review against the bank's already-authorized roles. Do not change server authority or silently switch identities. [Availability counts](video-rehearsal-static.json); [frontend predicate](../../apps/web/src/lib/demo-stories.ts). |
| P0       | The live config has **zero** ambiguous-story hints, including the PT persona.                                                                                                           | Lead must verify intended scoped serving availability. Do not remove the availability gate, borrow another customer's purchase or manufacture a successful choice path.                                                                                              |
| P1       | Initial readiness took 99.28 s; the warm visit took 1.26 s.                                                                                                                             | Prepare login off camera; preserve this startup finding. No forced-restart conclusion or replica change is implied.                                                                                                                                                  |
| P1       | Agent Desk and Ops have no conversation evidence in this fresh authenticated workspace.                                                                                                 | Capture the actual fraud handoff and execution record after resumed rehearsal, in the same workspace. Current empty-state footage cannot demonstrate a packet or a successful action.                                                                                |
| P2       | Recording-helper actions extend below the fold when the chat is visible.                                                                                                                | Open/scroll to prepare each scene off camera, then close the helper. Keep the customer stage indicator and decision in frame.                                                                                                                                        |
| P2       | Ops exposes technical quality labels and a long dataset hash; Insights has a long evidence/source section.                                                                              | Prefer Insights for the judge-facing data shot. For live glass-box footage, frame the new execution and verified action rather than lingering on internal identifiers or an empty log.                                                                               |

The static scenes are ready to capture; the full three-story recording is not
approved by this partial rehearsal. Retain [the narration draft](video-script.md)
as a separate track and review its claims against the final observed stories.
