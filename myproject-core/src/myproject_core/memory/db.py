from collections.abc import Generator

from sqlmodel import Session, create_engine

from ..configs import Config
from .models import memory_metadata

# Dictionary to keep track of initialized memory engines in a server context
# This prevents calling create_all multiple times for the same user in one process
_memory_engines = {}


def get_memory_engine(config: Config | None = None, memory_db_url: str | None = None, echo_sql=False):
    """Returns a SQLModel engine for the user's private memory database.
    Ensures the database and tables exist.

    Accepts either a Config object (from which the memory DB URL is derived)
    or an explicit memory_db_url string.
    """
    if memory_db_url is None and config is None:
        raise ValueError("Must provide either a Config object or a memory_db_url string.")
    target_url = memory_db_url or (config.memory_db.connection_string if config else None)

    if target_url not in _memory_engines:
        engine = create_engine(
            target_url,
            echo=echo_sql,
            # SQLite specific: Needed for multi-threaded apps (FastAPI)
            connect_args={"check_same_thread": False} if target_url.startswith("sqlite") else {},
        )
        # Initialize tables for this user's memory database
        memory_metadata.create_all(engine)
        _memory_engines[target_url] = engine

    return _memory_engines[target_url]


def get_memory_session(
    config: Config | None = None,
    memory_db_url: str | None = None,
) -> Generator[Session, None, None]:
    """Context manager to get a memory session."""
    engine = get_memory_engine(config=config, memory_db_url=memory_db_url)
    with Session(engine) as session:
        yield session
