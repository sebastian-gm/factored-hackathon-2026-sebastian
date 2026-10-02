"""Customer bank state, separate from login workspaces and judge profile realms."""

from alembic import op

revision = "0004_customer_business_state"
down_revision = "0003_llm_budget"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("customer_cases", "customer_card_states"):
        op.execute(
            f"CREATE TABLE ops.{table} (customer_id text NOT NULL, realm text NOT NULL, id text NOT NULL, payload jsonb NOT NULL, updated_at timestamptz NOT NULL DEFAULT clock_timestamp(), PRIMARY KEY(customer_id,realm,id))"
        )
        op.execute(f"ALTER TABLE ops.{table} OWNER TO aclara_owner")
        op.execute(f"ALTER TABLE ops.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE ops.{table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY customer_realm ON ops.{table} TO aclara_api,aclara_ops,aclara_owner USING (customer_id = NULLIF(current_setting('app.customer_id',true),'') AND realm = NULLIF(current_setting('app.customer_realm',true),'')) WITH CHECK (customer_id = NULLIF(current_setting('app.customer_id',true),'') AND realm = NULLIF(current_setting('app.customer_realm',true),''))"
        )
        op.execute(f"GRANT SELECT ON ops.{table} TO aclara_api,aclara_ops")
        op.execute(f"GRANT INSERT,UPDATE,DELETE ON ops.{table} TO aclara_api")

    # Migration only: table locks and the enclosing migration transaction make
    # the owner's backfill atomic. API roles remain subject to RLS throughout.
    # Restore FORCE before commit; no runtime role receives owner membership.
    for table in ("cases", "card_states", "sessions", "customer_cases", "customer_card_states"):
        op.execute(f"ALTER TABLE ops.{table} NO FORCE ROW LEVEL SECURITY")
    op.execute("SET LOCAL ROLE aclara_owner")
    op.execute("""
        CREATE TEMP TABLE legacy_business_realms ON COMMIT DROP AS
        SELECT b.customer_id,b.run_id,b.sid,
          CASE
            WHEN s.payload->>'judge_reference' IS NOT NULL OR s.payload->>'username' LIKE 'judge.%'
              THEN 'judge:' || split_part(b.run_id,'_',1)
            WHEN s.id IS NOT NULL OR position('_' in b.run_id)=0 THEN 'owner'
            ELSE 'legacy:' || b.run_id
          END AS realm
        FROM (SELECT customer_id,run_id,sid FROM ops.cases UNION SELECT customer_id,run_id,sid FROM ops.card_states) b
        LEFT JOIN LATERAL (SELECT id,payload FROM ops.sessions s WHERE s.customer_id=b.customer_id AND s.run_id=b.run_id AND s.sid=b.sid LIMIT 1) s ON true
    """)
    # Logout deletes sessions. Recover normal serving realms only from the
    # authoritative persona registry; an unknown realm stays isolated.
    op.execute("""
        DO $$ BEGIN
          IF to_regclass('reference.demo_personas') IS NOT NULL THEN
            UPDATE legacy_business_realms b SET realm='owner'
            WHERE b.realm LIKE 'legacy:%' AND EXISTS (
              SELECT 1 FROM reference.demo_personas p
              WHERE p.customer_id=b.customer_id AND p.username NOT LIKE 'judge.%'
                AND split_part(b.run_id,'_',1)=left(encode(sha256(convert_to(p.username,'UTF8')),'hex'),12)
            );
          END IF;
        END $$
    """)
    # Retain every historical receipt. Only the earliest historical open case
    # for a transaction is canonical; duplicate history is never deleted.
    op.execute("""
        INSERT INTO ops.customer_cases(customer_id,realm,id,payload,updated_at)
        SELECT customer_id,realm,id,
          CASE WHEN ordinal=1 THEN payload ELSE payload || jsonb_build_object('_canonical',false) END,updated_at
        FROM (
          SELECT c.customer_id,r.realm,c.id,c.payload,c.updated_at,
            row_number() OVER (PARTITION BY c.customer_id,r.realm,coalesce(c.payload->>'transaction_id',c.id),
              coalesce(c.payload->>'status','received') NOT IN ('closed','resolved','cancelled','rejected')
              ORDER BY c.updated_at,c.id) AS ordinal,
            row_number() OVER (PARTITION BY c.customer_id,r.realm,c.id ORDER BY c.updated_at DESC) AS latest
          FROM ops.cases c JOIN legacy_business_realms r USING(customer_id,run_id,sid)
        ) ranked WHERE latest=1
    """)
    op.execute("""
        INSERT INTO ops.customer_card_states(customer_id,realm,id,payload,updated_at)
        SELECT DISTINCT ON(c.customer_id,r.realm,c.id) c.customer_id,r.realm,c.id,c.payload,c.updated_at
        FROM ops.card_states c JOIN legacy_business_realms r USING(customer_id,run_id,sid)
        ORDER BY c.customer_id,r.realm,c.id,lower(c.payload->>'status')='frozen' DESC,c.updated_at DESC
    """)
    op.execute("RESET ROLE")
    for table in ("cases", "card_states", "sessions", "customer_cases", "customer_card_states"):
        op.execute(f"ALTER TABLE ops.{table} FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE UNIQUE INDEX one_open_customer_case ON ops.customer_cases
        (customer_id,realm,(coalesce(payload->>'transaction_id',id)))
        WHERE coalesce(payload->>'status','received') NOT IN ('closed','resolved','cancelled','rejected')
          AND coalesce(payload->>'_canonical','true')='true'
    """)


def downgrade() -> None:
    raise RuntimeError("Customer bank state downgrade requires a reviewed migration")
