import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.api import courses, documents, chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    logger.info("Starting Nota backend — initialising database...")
    init_db()
    logger.info("Database ready.")
    yield
    logger.info("Nota backend shutting down.")


app = FastAPI(
    title="Nota API",
    description="Local-first RAG study assistant API",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the Next.js dev server (port 3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(courses.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "nota-backend"}
