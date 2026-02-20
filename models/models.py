# pyright: reportIncompatibleVariableOverride=false, reportUnannotatedClassAttribute=false
from __future__ import annotations
from typing import ClassVar
from sqlmodel import Field
from sqlalchemy import Index
from schemas.event import EventCore, EventPayload
from schemas.fileoffset import FileOffsetBase


class Event(EventCore, EventPayload, table=True):
    __tablename__: ClassVar[str] = "events"

    id: int | None = Field(default=None, primary_key=True)

    __table_args__: ClassVar[tuple[object, ...]] = (
        Index("events_ts_desc", "ts"),
        Index("events_app_ts", "app", "ts"),
        Index("events_event_type_ts", "event_type", "ts"),
        Index("events_src_ip_ts", "src_ip", "ts"),
        Index("events_user_id_ts", "user_id", "ts"),
        Index("events_request_id", "request_id"),
        {"sqlite_autoincrement": True},
    )


class FileOffset(FileOffsetBase, table=True):
    __tablename__: ClassVar[str] = "file_offsets"
    path: str = Field(primary_key=True)
