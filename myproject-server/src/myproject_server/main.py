from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from myproject_core.configs import settings

from .database import init_db
from .routers import auth, files, jobs, users, workflows


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs on startup
    # 1. Pings DB (Postgres check)
    # 2. Creates tables/file (SQLite check)
    init_db()
    yield
    # Cleanup logic (if any) goes here


app = FastAPI(title="MyProject API", lifespan=lifespan)

# Set up CORS using the safe list from our Config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,  # Required for Auth headers/cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(workflows.router)
app.include_router(jobs.router)


@app.get("/health")
async def health_check():
    return {"status": "online"}
