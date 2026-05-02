from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.routes import router
from app.core.config import get_settings
from app.db.session import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Real-time Object Detection API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(router)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()

