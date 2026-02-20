from sqlmodel import SQLModel


class EventCore(SQLModel):
    ts: str
    received_at: str

    app: str | None = None
    host: str | None = None
    level: str | None = None
    event_type: str | None = None
    message: str | None = None

    request_id: str | None = None
    user_id: str | None = None
    src_ip: str | None = None
    user_agent: str | None = None

    http_method: str | None = None
    http_path: str | None = None
    http_status: int | None = None
    latency_ms: float | None = None

    error_type: str | None = None


class EventPayload(SQLModel):
    data_json: str | None = None
    raw_json: str | None = None
    source_file: str | None = None
    source_offset: int | None = None
