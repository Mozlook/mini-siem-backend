from __future__ import annotations

import argparse
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, cast
from collections.abc import Sequence

from sqlalchemy import func
from sqlmodel import Session, desc, select

from config import settings
from db import db_engine, init_db

from models.models import Event, FileOffset  # noqa: F401


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _try_import_repo_functions() -> tuple[
    Callable[[Session, Sequence[Event]], int] | None,
    Callable[[Session, int], list[Event]] | None,
]:
    candidates = [
        "repositories.events",
        "repositories.events_repo",
        "repo.events",
        "storage.events",
        "events_repo",
    ]
    for mod_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue

        insert_fn = getattr(mod, "insert_events_batch", None)
        query_fn = getattr(mod, "query_latest_events", None)

        if callable(insert_fn) and callable(query_fn):
            return (
                cast(Callable[[Session, Sequence[Event]], int], insert_fn),
                cast(Callable[[Session, int], list[Event]], query_fn),
            )

    return (None, None)


def _insert_events_batch_fallback(session: Session, events: Sequence[Event]) -> int:
    session.add_all(list(events))
    return len(events)


def _query_latest_events_fallback(session: Session, limit: int) -> list[Event]:
    stmt = select(Event).order_by(desc(Event.ts), desc(Event.id)).limit(limit)
    return list(session.exec(stmt).all())


def main() -> int:
    parser = argparse.ArgumentParser(description="Mini-SIEM DB smoke test (S2).")
    parser.add_argument(
        "--limit", type=int, default=10, help="How many latest events to print."
    )
    parser.add_argument(
        "--no-insert",
        action="store_true",
        help="Do not insert demo events, only query.",
    )
    args = parser.parse_args()

    db_path = Path(settings.SIEM_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    init_db()

    insert_fn, query_fn = _try_import_repo_functions()
    if insert_fn is None or query_fn is None:
        insert_fn = _insert_events_batch_fallback
        query_fn = _query_latest_events_fallback
        print("[db_smoke] Using fallback insert/query (repo functions not found).")
    else:
        print("[db_smoke] Using repo insert/query functions.")

    inserted = 0

    with Session(db_engine) as session:
        try:
            if not args.no_insert:
                now = _now_iso()

                demo_events = [
                    Event(
                        ts=now,
                        received_at=now,
                        app="demo",
                        host="local",
                        level="INFO",
                        event_type="smoke_test",
                        message="hello from db_smoke",
                        source_file="scripts/db_smoke.py",
                        source_offset=0,
                        raw_json='{"demo":true}',
                        data_json='{"kind":"smoke"}',
                    ),
                    Event(
                        ts=now,
                        received_at=now,
                        app="demo",
                        host="local",
                        level="ERROR",
                        event_type="smoke_test_error",
                        message="boom (test)",
                        error_type="DemoError",
                        src_ip="127.0.0.1",
                        http_method="GET",
                        http_path="/health",
                        http_status=200,
                        latency_ms=12.3,
                        source_file="scripts/db_smoke.py",
                        source_offset=1,
                    ),
                ]

                inserted = insert_fn(session, demo_events)
                session.commit()

            # count total
            total = session.exec(select(func.count()).select_from(Event)).one()

            # query latest
            rows = query_fn(session, args.limit)

        except Exception as e:
            session.rollback()
            raise

    print()
    print(f"[db_smoke] DB path: {db_path.resolve()}")
    print(f"[db_smoke] Inserted this run: {inserted}")
    print(f"[db_smoke] Total events in DB: {total}")
    print(f"[db_smoke] Latest {len(rows)} events:")
    for ev in rows:
        print(
            f"  - id={ev.id} ts={ev.ts} app={ev.app} type={ev.event_type} level={ev.level} msg={ev.message!r}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
