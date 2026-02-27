import os

from sqlmodel import select, Session


from handlers.exceptions import LogDirUnavailableError
from models.models import Event


def get_apps_from_fs(log_dir: str) -> list[str]:
    try:
        apps: list[str] = []
        with os.scandir(log_dir) as it:
            for entry in it:
                if entry.name.startswith("."):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    apps.append(entry.name)
        apps.sort(key=str.casefold)
        return apps
    except (FileNotFoundError, PermissionError) as e:
        raise LogDirUnavailableError(log_dir) from e


def get_event_types_handler(session: Session, app: str | None = None) -> list[str]:
    stmt = select(Event.event_type).distinct()
    if app is not None:
        stmt = stmt.where(Event.app == app)
    stmt = stmt.where(Event.event_type is not None).order_by(Event.event_type)

    event_types = session.exec(stmt).all()

    return list(event_types)
