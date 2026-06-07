from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import build_router
from app.core.config import Settings
from app.db import models as _models
from app.db.session import Base, make_engine, make_session_factory

_ = _models


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)
    Base.metadata.create_all(engine)
    session_factory = make_session_factory(settings.database_url)

    app = FastAPI(title="Physical Systems Intelligence", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_router(settings, session_factory))
    return app


app = create_app()
