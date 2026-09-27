"""Owner-configured global model budgets; reservations survive request rollback."""

from alembic import op

revision = "0003_llm_budget"
down_revision = "0002_routing_reference"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA llm AUTHORIZATION aclara_owner")
    op.execute("GRANT USAGE ON SCHEMA llm TO aclara_api")
    op.execute("""
        CREATE TABLE llm.limits (
            scope text PRIMARY KEY,
            daily_usd numeric(14,8) NOT NULL CHECK (daily_usd > 0 AND daily_usd != 'NaN'),
            disabled boolean NOT NULL DEFAULT false
        );
        CREATE TABLE llm.runs (
            scope text REFERENCES llm.limits(scope), run_id text,
            limit_usd numeric(14,8) NOT NULL CHECK (limit_usd > 0 AND limit_usd != 'NaN'),
            enabled boolean NOT NULL DEFAULT true,
            PRIMARY KEY(scope,run_id)
        );
        CREATE TABLE llm.reservations (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            scope text NOT NULL REFERENCES llm.limits(scope), run_id text,
            day date NOT NULL,
            reserved_usd numeric(14,8) NOT NULL CHECK (reserved_usd > 0),
            charged_usd numeric(14,8) NOT NULL CHECK (charged_usd >= 0),
            actual_usd numeric(14,8), settled boolean NOT NULL DEFAULT false,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            FOREIGN KEY(scope,run_id) REFERENCES llm.runs(scope,run_id)
        );
        CREATE INDEX ON llm.reservations(scope,day);
        CREATE INDEX ON llm.reservations(scope,run_id);
    """)
    for table in ("limits", "runs", "reservations"):
        op.execute(f"ALTER TABLE llm.{table} OWNER TO aclara_owner")
        op.execute(f"ALTER TABLE llm.{table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE llm.{table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY owner_only ON llm.{table} TO aclara_owner USING (true) WITH CHECK (true)"
        )
    op.execute("""
        CREATE FUNCTION llm.reserve(p_scope text, p_run text, p_amount numeric)
        RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,llm AS $$
        DECLARE policy llm.limits; run_policy llm.runs; used numeric; token uuid;
          today date := (clock_timestamp() AT TIME ZONE 'UTC')::date;
        BEGIN
          IF p_amount IS NULL OR p_amount <= 0 OR p_amount = 'NaN'
             OR p_amount = 'Infinity' THEN RETURN NULL; END IF;
          SELECT * INTO policy FROM llm.limits WHERE scope=p_scope FOR UPDATE;
          IF NOT FOUND OR policy.disabled THEN RETURN NULL; END IF;
          SELECT coalesce(sum(charged_usd),0) INTO used FROM llm.reservations
            WHERE scope=p_scope AND day=today;
          IF used+p_amount > policy.daily_usd THEN RETURN NULL; END IF;
          IF p_run IS NOT NULL THEN
            SELECT * INTO run_policy FROM llm.runs WHERE scope=p_scope AND run_id=p_run;
            IF NOT FOUND OR NOT run_policy.enabled THEN RETURN NULL; END IF;
            SELECT coalesce(sum(charged_usd),0) INTO used FROM llm.reservations
              WHERE scope=p_scope AND run_id=p_run;
            IF used+p_amount > run_policy.limit_usd THEN RETURN NULL; END IF;
          END IF;
          INSERT INTO llm.reservations(scope,run_id,day,reserved_usd,charged_usd)
            VALUES(p_scope,p_run,today,p_amount,p_amount) RETURNING id INTO token;
          RETURN token;
        END $$;
        CREATE FUNCTION llm.settle(p_id uuid, p_actual numeric)
        RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,llm AS $$
        DECLARE held llm.reservations; budget_scope text;
        BEGIN
          IF p_actual IS NOT NULL AND (p_actual < 0 OR p_actual = 'NaN'
             OR p_actual = 'Infinity') THEN RETURN false; END IF;
          SELECT scope INTO budget_scope FROM llm.reservations WHERE id=p_id;
          IF NOT FOUND THEN RETURN false; END IF;
          PERFORM 1 FROM llm.limits WHERE scope=budget_scope FOR UPDATE;
          SELECT * INTO held FROM llm.reservations WHERE id=p_id;
          IF held.settled THEN RETURN held.actual_usd IS NOT DISTINCT FROM p_actual; END IF;
          UPDATE llm.reservations SET charged_usd=coalesce(p_actual,reserved_usd),
            actual_usd=p_actual,settled=true WHERE id=p_id;
          IF p_actual > held.reserved_usd THEN
            UPDATE llm.limits SET disabled=true WHERE scope=budget_scope;
            RETURN false;
          END IF;
          RETURN true;
        END $$;
    """)
    for signature in ("reserve(text,text,numeric)", "settle(uuid,numeric)"):
        op.execute(f"ALTER FUNCTION llm.{signature} OWNER TO aclara_owner")
        op.execute(f"REVOKE ALL ON FUNCTION llm.{signature} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION llm.{signature} TO aclara_api")
    # These limits are owner configuration, never writable by the runtime role.
    op.execute("SET LOCAL ROLE aclara_owner")
    op.execute("INSERT INTO llm.limits(scope,daily_usd) VALUES('production',3)")
    op.execute(
        "INSERT INTO llm.runs(scope,run_id,limit_usd) VALUES('production','handoff09-smoke',0.10)"
    )
    op.execute("RESET ROLE")


def downgrade() -> None:
    raise RuntimeError("Spend records require an explicit reviewed migration")
