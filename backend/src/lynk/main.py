from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import companies, imports, notes, people
from .api.routes.tags import people_tags_router, tags_router
from .config import settings

app = FastAPI(title="Lynk API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(people.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(tags_router, prefix="/api")
app.include_router(people_tags_router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(imports.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
