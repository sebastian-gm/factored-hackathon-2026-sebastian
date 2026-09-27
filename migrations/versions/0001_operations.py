"""Durable operations, forced RLS, and append-only per-session hash chains."""

from alembic import op

revision = "0001_operations"
down_revision = None
branch_labels = None
depends_on = None

TABLES = (
    "cases",
    "card_states",
    "handoffs",
    "conversations",
    "turns",
    "execution_records",
    "idempotency_keys",
    "otp_challenges",
    "sessions",
    "demo_identities",
)


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ops AUTHORIZATION aclara_owner")
    op.execute("GRANT USAGE ON SCHEMA ops TO aclara_api,aclara_ops")
    for table in TABLES:
        op.execute(
            f"CREATE TABLE ops.{table} (customer_id text NOT NULL, run_id text NOT NULL, sid text NOT NULL, id text NOT NULL, payload jsonb NOT NULL, updated_at timestamptz NOT NULL DEFAULT clock_timestamp(), PRIMARY KEY(customer_id,run_id,sid,id))"
        )
    op.execute(
        "CREATE TABLE ops.audit_log (customer_id text NOT NULL, run_id text NOT NULL, sid text NOT NULL, sequence bigint NOT NULL, canonical text NOT NULL, prev_hash text NOT NULL, row_hash text NOT NULL, PRIMARY KEY(customer_id,run_id,sid,sequence))"
    )
    for table in (*TABLES, "audit_log"):
        op.execute(f"ALTER TABLE ops.{table} OWNER TO aclara_owner")
        op.execute(f"ALTER TABLE ops.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE ops.{table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE INDEX ON ops.{table} (customer_id)")
        op.execute(
            f"CREATE POLICY customer_scope ON ops.{table} TO aclara_api,aclara_owner,aclara_ops USING (customer_id = NULLIF(current_setting('app.customer_id', true), '')) WITH CHECK (customer_id = NULLIF(current_setting('app.customer_id', true), ''))"
        )
        op.execute(
            f"CREATE POLICY run_scope ON ops.{table} AS RESTRICTIVE TO aclara_api,aclara_owner,aclara_ops USING (run_id = NULLIF(current_setting('app.run_id',true),'') AND sid = NULLIF(current_setting('app.sid',true),'')) WITH CHECK (run_id = NULLIF(current_setting('app.run_id',true),'') AND sid = NULLIF(current_setting('app.sid',true),''))"
        )
        op.execute(f"GRANT SELECT ON ops.{table} TO aclara_api,aclara_ops")
        if table != "audit_log":
            op.execute(f"GRANT INSERT,UPDATE,DELETE ON ops.{table} TO aclara_api")
    op.execute("CREATE VIEW ops.case_view WITH (security_invoker=true) AS SELECT * FROM ops.cases")
    op.execute("GRANT SELECT ON ops.case_view TO aclara_api,aclara_ops")
    op.execute(
        "CREATE FUNCTION ops.case_count() RETURNS bigint LANGUAGE sql SECURITY INVOKER SET search_path=pg_catalog,ops AS 'SELECT count(*) FROM ops.cases'"
    )
    op.execute("REVOKE ALL ON FUNCTION ops.case_count() FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION ops.case_count() TO aclara_api,aclara_ops")
    op.execute("""
    CREATE FUNCTION ops.append_audit(event jsonb) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,ops AS $$
    DECLARE
      cid text := NULLIF(current_setting('app.customer_id',true),'');
      rid text := NULLIF(current_setting('app.run_id',true),'');
      sess text := NULLIF(current_setting('app.sid',true),'');
      previous text; ordinal bigint; serialized text;
    BEGIN
      IF cid IS NULL OR rid IS NULL OR sess IS NULL THEN RAISE EXCEPTION 'Missing audit context'; END IF;
      PERFORM pg_advisory_xact_lock(hashtextextended(json_build_array(cid,rid,sess)::text,0));
      SELECT sequence,row_hash INTO ordinal,previous FROM ops.audit_log ORDER BY sequence DESC LIMIT 1;
      ordinal := coalesce(ordinal,0)+1;
      previous := coalesce(previous,repeat('0',64));
      serialized := jsonb_build_object('customer_id',cid,'run_id',rid,'sid',sess,'sequence',ordinal,'event',event,'occurred_at',clock_timestamp())::text;
      INSERT INTO ops.audit_log VALUES(cid,rid,sess,ordinal,serialized,previous,encode(sha256(convert_to(previous||serialized,'UTF8')),'hex'));
    END $$
    """)
    op.execute("ALTER FUNCTION ops.append_audit(jsonb) OWNER TO aclara_owner")
    op.execute("REVOKE ALL ON FUNCTION ops.append_audit(jsonb) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION ops.append_audit(jsonb) TO aclara_api")


def downgrade() -> None:
    raise RuntimeError("Operational data downgrade requires an explicit reviewed migration")
