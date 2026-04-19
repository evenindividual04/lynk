from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import companies, imports, notes, people
from .api.routes.email_finder import router as email_finder_router
from .api.routes.follow_ups import router as follow_ups_router
from .api.routes.inbound import router as inbound_router
from .api.routes.messages import router as messages_router
from .api.routes.tags import people_tags_router, tags_router
from .api.routes.templates import router as templates_router
from .api.routes.tracking import router as tracking_router
from .config import settings
from .services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Lynk API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 1 routes
app.include_router(people.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(tags_router, prefix="/api")
app.include_router(people_tags_router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(imports.router, prefix="/api")

# Phase 2 routes
app.include_router(templates_router, prefix="/api")
app.include_router(messages_router, prefix="/api")
app.include_router(follow_ups_router, prefix="/api")
app.include_router(tracking_router)  # No /api prefix — /t/* is public

# Phase 3 routes
app.include_router(email_finder_router, prefix="/api")
app.include_router(inbound_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
