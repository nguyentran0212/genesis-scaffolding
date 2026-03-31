from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import or_, select
from sqlalchemy.sql import cast
from sqlalchemy.types import String
from sqlmodel import Session, col

from .models import EventLog, MemorySource, TopicalMemory


# --- EVENT LOG ---


def create_event_log(session: Session, data: dict[str, Any]) -> EventLog:
    """Create a new event log entry."""
    db_entry = EventLog.model_validate(data)
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry


def get_event_log(session: Session, event_id: int) -> EventLog | None:
    """Get a specific event log by ID."""
    return session.get(EventLog, event_id)


def list_event_logs(
    session: Session,
    tag: str | None = None,
    importance: int | None = None,
    source: MemorySource | None = None,
    sort_by: Literal["event_time", "created_at", "importance"] = "event_time",
    order: Literal["asc", "desc"] = "desc",
    limit: int = 50,
    offset: int = 0,
) -> list[EventLog]:
    """List event logs with optional filtering."""
    statement = select(EventLog)

    if tag:
        tag_pattern = f'%"{tag}"%'
        statement = statement.where(cast(EventLog.tags, String).like(tag_pattern))  # type: ignore[arg-type]
    if importance is not None:
        statement = statement.where(EventLog.importance == importance)  # type: ignore[arg-type]
    if source is not None:
        statement = statement.where(EventLog.source == source)  # type: ignore

    order_field = getattr(EventLog, sort_by)
    if order == "desc":
        statement = statement.order_by(col(order_field).desc())
    else:
        statement = statement.order_by(col(order_field).asc())
    statement = statement.limit(limit).offset(offset)

    return session.exec(statement).all()  # type: ignore[return-value]


def delete_event_log(session: Session, event_id: int) -> bool:
    """Delete an event log. Returns True if deleted, False if not found."""
    entry = session.get(EventLog, event_id)
    if not entry:
        return False
    session.delete(entry)
    session.commit()
    return True


# --- TOPICAL MEMORY ---


def create_topical_memory(session: Session, data: dict[str, Any]) -> TopicalMemory:
    """Create a new topical memory entry."""
    db_entry = TopicalMemory.model_validate(data)
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry


def get_topical_memory(session: Session, memory_id: int) -> TopicalMemory | None:
    """Get a specific topical memory by ID."""
    return session.get(TopicalMemory, memory_id)


def list_topical_memories(
    session: Session,
    superseded: bool = False,
    tag: str | None = None,
    importance: int | None = None,
    source: MemorySource | None = None,
    sort_by: Literal["created_at", "updated_at", "importance"] = "updated_at",
    order: Literal["asc", "desc"] = "desc",
    limit: int = 50,
    offset: int = 0,
) -> list[TopicalMemory]:
    """List topical memories. By default excludes superseded (old) entries."""
    statement = select(TopicalMemory)

    if not superseded:
        statement = statement.where(TopicalMemory.superseded_by_id is None)  # type: ignore
    else:
        statement = statement.where(TopicalMemory.superseded_by_id is not None)  # type: ignore

    if tag:
        tag_pattern = f'%"{tag}"%'
        statement = statement.where(cast(TopicalMemory.tags, String).like(tag_pattern))  # type: ignore[arg-type]
    if importance is not None:
        statement = statement.where(TopicalMemory.importance == importance)  # type: ignore
    if source is not None:
        statement = statement.where(TopicalMemory.source == source)  # type: ignore

    order_field = getattr(TopicalMemory, sort_by)
    if order == "desc":
        statement = statement.order_by(col(order_field).desc())
    else:
        statement = statement.order_by(col(order_field).asc())
    statement = statement.limit(limit).offset(offset)

    return session.exec(statement).all()  # type: ignore[return-value]


def update_topical_memory(
    session: Session,
    memory_id: int,
    data: dict[str, Any],
) -> TopicalMemory | None:
    """Update a topical memory's fields in-place. Use supersede_topical_memory for revision history."""
    db_entry = session.get(TopicalMemory, memory_id)
    if not db_entry:
        return None
    for key, value in data.items():
        if hasattr(db_entry, key):
            setattr(db_entry, key, value)
    db_entry.updated_at = datetime.now(UTC)
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry


def supersede_topical_memory(
    session: Session,
    memory_id: int,
    new_content: str,
    new_subject: str | None = None,
    new_tags: list[str] | None = None,
) -> TopicalMemory | None:
    """Create a new revision, marking the old one as superseded.

    This preserves the full revision chain instead of overwriting in-place.
    """
    old_entry = session.get(TopicalMemory, memory_id)
    if not old_entry:
        return None
    if old_entry.superseded_by_id is not None:
        # Already superseded — creating a new revision from an already-superseded entry
        # We could either reject this or walk back to find the actual current entry.
        # For safety, we reject.
        return None

    new_entry = TopicalMemory(
        subject=new_subject if new_subject is not None else old_entry.subject,
        content=new_content,
        tags=new_tags if new_tags is not None else old_entry.tags,
        importance=old_entry.importance,
        source=MemorySource.AGENT_TOOL,
        superseded_by_id=None,
        supersedes_ids=[memory_id],
    )
    session.add(new_entry)
    session.flush()  # Get new_entry.id

    # Mark old entry as superseded
    old_entry.superseded_by_id = new_entry.id
    session.add(old_entry)
    session.commit()
    session.refresh(new_entry)
    return new_entry


def get_revision_chain(
    session: Session,
    memory_id: int,
) -> list[TopicalMemory]:
    """Walk the revision chain backwards from a memory ID.

    Returns list from oldest to newest (the chain from original to current).
    """
    chain = []
    current_id = memory_id

    while current_id is not None:
        entry = session.get(TopicalMemory, current_id)
        if not entry:
            break
        chain.append(entry)
        current_id = entry.superseded_by_id

    return chain


def delete_topical_memory(session: Session, memory_id: int) -> bool:
    """Delete a topical memory. Returns True if deleted, False if not found."""
    entry = session.get(TopicalMemory, memory_id)
    if not entry:
        return False
    session.delete(entry)
    session.commit()
    return True


# --- UNIFIED SEARCH ---


def search_memories(
    session: Session,
    query: str,
    memory_type: Literal["event", "topic", "all"] = "all",
    limit: int = 20,
) -> dict[str, list[EventLog | TopicalMemory]]:
    """Keyword search across subject and content.

    Returns dict with 'events' and 'topics' keys.
    Only returns current (non-superseded) topical memories.
    """
    results: dict[str, list[EventLog | TopicalMemory]] = {"events": [], "topics": []}
    pattern = f"%{query}%"

    if memory_type in ("all", "event"):
        event_stmt = (
            select(EventLog)
            .where(or_(EventLog.subject.ilike(pattern), EventLog.content.ilike(pattern)))  # type: ignore[arg-type]
            .limit(limit)
        )
        results["events"] = session.exec(event_stmt).all()  # type: ignore[return-value]

    if memory_type in ("all", "topic"):
        topic_stmt = (
            select(TopicalMemory)
            .where(or_(TopicalMemory.subject.ilike(pattern), TopicalMemory.content.ilike(pattern)))  # type: ignore[arg-type]
            .where(TopicalMemory.superseded_by_id is None)  # type: ignore
            .limit(limit)
        )
        results["topics"] = session.exec(topic_stmt).all()  # type: ignore[return-value]

    return results
