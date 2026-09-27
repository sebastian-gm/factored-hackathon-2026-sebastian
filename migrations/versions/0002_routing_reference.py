"""Shared routing attributes: no names, contact fields or customer records."""

from alembic import op

revision = "0002_routing_reference"
down_revision = "0001_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA reference AUTHORIZATION aclara_owner")
    op.execute(
        "CREATE TABLE reference.service_agents (agent_ref text PRIMARY KEY, agent_status text NOT NULL, agent_type text NOT NULL, languages text NOT NULL, specialty text, total_monthly_interactions integer CHECK(total_monthly_interactions>=0))"
    )
    op.execute("ALTER TABLE reference.service_agents OWNER TO aclara_owner")
    op.execute("REVOKE ALL ON SCHEMA reference FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA reference TO aclara_api,aclara_ops")
    op.execute("GRANT SELECT ON reference.service_agents TO aclara_api,aclara_ops")


def downgrade() -> None:
    raise RuntimeError("Reference downgrade requires a reviewed migration")
