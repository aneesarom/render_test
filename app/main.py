from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users, tasks, suggest, metrics
from app.middleware import LoggingMiddleware
from app.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


# Create FastAPI app
app = FastAPI(
    title="SprintSync",
    description="Backend API for SprintSync application",
    version="1.0.0",
)

app.add_middleware(LoggingMiddleware)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(suggest.router)
app.include_router(metrics.router)