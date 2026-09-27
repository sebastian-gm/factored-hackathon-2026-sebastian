# Handoff routing and fraud flags

Generated from local source aggregates; no source rows are committed.

- **total_agents**: 1200
- **active_agents**: 1090
- **pt_fraud_agents**: 7
- **active_pt_fraud_agents**: 7
- **projection_fields**: ["agent_ref", "agent_status", "agent_type", "languages", "specialty", "total_monthly_interactions"]
- **bank_clock**: "2026-06-18T06:00:00+00:00"
- **ledger_120_days**: 492414
- **fraud_score_gt_30**: 254
- **score_flag_rate**: 0.0005158261137985516
- **scope**: "Owned 120-day ledger; score trigger only. Lost/stolen and simulated operational case bursts are separate triggers."

Routing requires Active agents, prefers Digital/Hybrid, then selects the least monthly interactions with a stable opaque-reference tie-break. PT fraud uses PT/Fraudes, then PT/Quejas y Reclamos with specialty fallback, then ES/Fraudes with language fallback. No eligible agent leaves an explicit pending assignment; it never invents an agent.

The database projection contains only the six routing attributes listed above. The API role can read it but cannot change it. Existing forced customer/run/session RLS continues to protect operational records. The Azure deployment uses the same projection loader; no raw organizer file is embedded in an image or committed.
