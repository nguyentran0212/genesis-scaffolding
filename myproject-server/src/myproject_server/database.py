from myproject_core.configs import settings
from sqlmodel import Session, SQLModel, create_engine, select

from .models.user import User

# SQLite specific: check_same_thread=False is needed for FastAPI's concurrency
connect_args = {"check_same_thread": False} if "sqlite" in str(settings.db.connection_string) else {}

engine = create_engine(
    str(settings.db.connection_string), echo=settings.db.echo_sql, connect_args=connect_args
)


def seed_admin_user(session: Session):
    """Injects the initial admin user if configured and missing."""
    admin_username = settings.server.admin_username
    admin_password = settings.server.admin_password

    # Only proceed if both username and password are provided in settings
    if not admin_username or not admin_password:
        return

    # Check if the user already exists
    statement = select(User).where(User.username == admin_username)
    existing_admin = session.exec(statement).first()

    if not existing_admin:
        print(f"Creating initial admin account: {admin_username}...")

        # Import here to avoid top-level circular dependency
        from myproject_server.auth.security import get_password_hash

        new_admin = User(
            username=admin_username,
            email=settings.server.admin_email,
            hashed_password=get_password_hash(admin_password),
            disabled=False,
        )
        session.add(new_admin)
        session.commit()
        print("Admin account created successfully.")
    else:
        # Account exists, do nothing
        pass


def init_db():
    """
    Initializes the database.
    1. Validates connection (especially for Postgres).
    2. Creates tables if they don't exist (SQLite).
    """
    try:
        # This creates the .db file and tables if missing
        SQLModel.metadata.create_all(engine)

        # Seed admin user
        with Session(engine) as session:
            seed_admin_user(session)

        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise e


def get_session():
    """Dependency for FastAPI routes"""
    with Session(engine) as session:
        yield session
