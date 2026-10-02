"""Add a masked staff queue with forced realm RLS and immutable packet payloads."""

from alembic import op

revision = "0005_staff_realm_queue"
down_revision = "0004_customer_business_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""CREATE TABLE ops.realm_handoffs (
        customer_id text NOT NULL, realm text NOT NULL, id text NOT NULL,
        payload jsonb NOT NULL, status text NOT NULL DEFAULT 'waiting' CHECK(status IN ('waiting','claimed')),
        claimed_by text, version integer NOT NULL DEFAULT 1 CHECK(version > 0),
        PRIMARY KEY(realm,id))""")
    op.execute("ALTER TABLE ops.realm_handoffs OWNER TO aclara_owner")
    op.execute("ALTER TABLE ops.realm_handoffs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ops.realm_handoffs FORCE ROW LEVEL SECURITY")
    op.execute("""CREATE POLICY realm_read ON ops.realm_handoffs FOR SELECT TO aclara_api,aclara_owner
        USING (realm=NULLIF(current_setting('app.handoff_realm',true),'') AND
        (current_setting('app.handoff_staff',true)='yes' OR customer_id=NULLIF(current_setting('app.customer_id',true),'')))""")
    op.execute("""CREATE POLICY realm_publish ON ops.realm_handoffs FOR INSERT TO aclara_api,aclara_owner
        WITH CHECK (realm=NULLIF(current_setting('app.handoff_realm',true),'') AND
        current_setting('app.handoff_staff',true)='no' AND customer_id=NULLIF(current_setting('app.customer_id',true),''))""")
    op.execute("""CREATE POLICY realm_claim ON ops.realm_handoffs FOR UPDATE TO aclara_api,aclara_owner
        USING (realm=NULLIF(current_setting('app.handoff_realm',true),'') AND current_setting('app.handoff_staff',true)='yes')
        WITH CHECK (realm=NULLIF(current_setting('app.handoff_realm',true),'') AND current_setting('app.handoff_staff',true)='yes')""")
    op.execute("GRANT SELECT ON ops.realm_handoffs TO aclara_api")
    op.execute("GRANT INSERT(customer_id,realm,id,payload) ON ops.realm_handoffs TO aclara_api")
    op.execute("GRANT UPDATE(status,claimed_by,version) ON ops.realm_handoffs TO aclara_api")


def downgrade() -> None:
    raise RuntimeError("Queue downgrade requires a reviewed data-retention decision")
