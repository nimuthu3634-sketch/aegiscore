"""Initial AegisCore schema — explicit DDL.

Revision ID: 20260329_0001
Revises:
Create Date: 2026-03-29 09:15:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260329_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Sequence for collision-free incident reference numbers ----------------
    op.execute("CREATE SEQUENCE IF NOT EXISTS incident_reference_seq START 1 INCREMENT 1")

    # --- roles -----------------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("name", sa.String(20), primary_key=True),
        sa.Column("description", sa.String(255), nullable=False),
    )

    # --- users -----------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), sa.ForeignKey("roles.name"), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    # --- assets ----------------------------------------------------------------
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("hostname", sa.String(255), nullable=False, unique=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("operating_system", sa.String(255), nullable=True),
        sa.Column("business_unit", sa.String(255), nullable=True),
        sa.Column("criticality", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("risk_summary", sa.Text(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_assets_hostname", "assets", ["hostname"])

    # --- integrations ----------------------------------------------------------
    op.create_table(
        "integrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("health_status", sa.String(20), nullable=False, server_default="healthy"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_integrations_slug", "integrations", ["slug"])

    # --- integration_runs ------------------------------------------------------
    op.create_table(
        "integration_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("integration_id", sa.String(36), sa.ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_filename", sa.String(255), nullable=True),
        sa.Column("records_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_integration_runs_integration_id", "integration_runs", ["integration_id"])

    # --- alerts ----------------------------------------------------------------
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="telemetry"),
        sa.Column("event_type", sa.String(100), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("risk_label", sa.String(50), nullable=True),
        sa.Column("explainability", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("explanation_summary", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("integration_id", sa.String(36), sa.ForeignKey("integrations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("parsed_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_external_id", "alerts", ["external_id"])
    op.create_index("ix_alerts_source", "alerts", ["source"])
    op.create_index("ix_alerts_source_type", "alerts", ["source_type"])
    op.create_index("ix_alerts_event_type", "alerts", ["event_type"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_occurred_at", "alerts", ["occurred_at"])
    op.create_index("ix_alerts_detected_at", "alerts", ["detected_at"])
    op.create_index("ix_alerts_asset_id", "alerts", ["asset_id"])
    op.create_index("ix_alerts_integration_id", "alerts", ["integration_id"])
    op.create_index("ix_alerts_assigned_to_id", "alerts", ["assigned_to_id"])

    # --- response_recommendations ----------------------------------------------
    op.create_table(
        "response_recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_response_recommendations_alert_id", "response_recommendations", ["alert_id"])

    # --- alert_comments --------------------------------------------------------
    op.create_table(
        "alert_comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alert_comments_alert_id", "alert_comments", ["alert_id"])

    # --- incidents -------------------------------------------------------------
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reference", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(10), nullable=False, server_default="P3"),
        sa.Column("assignee_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incidents_reference", "incidents", ["reference"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_priority", "incidents", ["priority"])

    # --- incident_events -------------------------------------------------------
    op.create_table(
        "incident_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False, server_default="note"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_timeline_event", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incident_events_incident_id", "incident_events", ["incident_id"])
    op.create_index("ix_incident_events_event_type", "incident_events", ["event_type"])

    # --- incident_alert_links --------------------------------------------------
    op.create_table(
        "incident_alert_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("incident_id", "alert_id", name="uq_incident_alert_link"),
    )
    op.create_index("ix_incident_alert_links_incident_id", "incident_alert_links", ["incident_id"])
    op.create_index("ix_incident_alert_links_alert_id", "incident_alert_links", ["alert_id"])

    # --- log_entries -----------------------------------------------------------
    op.create_table(
        "log_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("integration_id", sa.String(36), sa.ForeignKey("integrations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("parsed_payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("fingerprint", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_log_entries_source", "log_entries", ["source"])
    op.create_index("ix_log_entries_category", "log_entries", ["category"])
    op.create_index("ix_log_entries_event_timestamp", "log_entries", ["event_timestamp"])
    op.create_index("ix_log_entries_asset_id", "log_entries", ["asset_id"])
    op.create_index("ix_log_entries_integration_id", "log_entries", ["integration_id"])
    op.create_index("ix_log_entries_fingerprint", "log_entries", ["fingerprint"])

    # --- audit_logs ------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # --- risk_model_metadata ---------------------------------------------------
    op.create_table(
        "risk_model_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(100), nullable=False, unique=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("feature_names", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("training_parameters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_risk_model_metadata_version", "risk_model_metadata", ["version"])

    # --- job_records -----------------------------------------------------------
    op.create_table(
        "job_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("requested_by_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_job_records_job_type", "job_records", ["job_type"])
    op.create_index("ix_job_records_status", "job_records", ["status"])


def downgrade() -> None:
    op.drop_table("job_records")
    op.drop_table("risk_model_metadata")
    op.drop_table("audit_logs")
    op.drop_table("log_entries")
    op.drop_table("incident_alert_links")
    op.drop_table("incident_events")
    op.drop_table("incidents")
    op.drop_table("alert_comments")
    op.drop_table("response_recommendations")
    op.drop_table("alerts")
    op.drop_table("integration_runs")
    op.drop_table("integrations")
    op.drop_table("assets")
    op.drop_table("users")
    op.drop_table("roles")
    op.execute("DROP SEQUENCE IF EXISTS incident_reference_seq")
