from sqlmodel import Session

from handlers.exceptions import EventDetailsNotFound
from models.models import Event


def get_event_details(id: int, session: Session) -> Event:
    event_details = session.get(Event, id)
    if event_details is None:
        raise EventDetailsNotFound(id)
    return event_details
