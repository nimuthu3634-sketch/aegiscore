import logging

from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import (  # noqa: F401
    alert,
    incident,
    integration_import_state,
    integration_status,
    log_entry,
    response_action,
    user,
)

logger = logging.getLogger(__name__)
settings = get_settings()
_schema_checked = False


def _expected_table_columns() -> dict[str, set[str]]:
    return {
        table.name: {column.name for column in table.columns}
        for table in Base.metadata.sorted_tables
    }


def _schema_mismatches() -> list[tuple[str, list[str]]]:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    mismatches: list[tuple[str, list[str]]] = []

    for table_name, expected_columns in _expected_table_columns().items():
        if table_name not in existing_tables:
            continue

        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = sorted(expected_columns - actual_columns)
        if missing_columns:
            mismatches.append((table_name, missing_columns))

    return mismatches


def _reset_development_schema() -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


def init_db() -> None:
    global _schema_checked

    if _schema_checked:
        return

    if settings.app_env != "production":
        mismatches = _schema_mismatches()
        if mismatches:
            mismatch_summary = ", ".join(
                f"{table_name} missing {', '.join(columns)}"
                for table_name, columns in mismatches
            )
            logger.warning(
                "Detected outdated demo schema in development; resetting database tables: %s",
                mismatch_summary,
            )
            _reset_development_schema()

    Base.metadata.create_all(bind=engine)
    _schema_checked = True
