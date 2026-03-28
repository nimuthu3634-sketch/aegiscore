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


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
