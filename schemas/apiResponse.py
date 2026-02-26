from schemas.event import EventCore, EventPayload


class EventListItem(EventCore):
    id: int


class EventDetail(EventCore, EventPayload):
    id: int
