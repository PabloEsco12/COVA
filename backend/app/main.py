"""FastAPI application entrypoint for COVA realtime messaging."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import register_routes
from .core.config import settings
from .db.redis import get_redis, redis_client
from .db.session import dispose_db_engine, init_db_engine
from .ws.router import register_websocket_routes


def create_app() -> FastAPI:
    app = FastAPI(
        title="COVA Messaging API",
        version=settings.VERSION,
        docs_url="/api/docs" if settings.DEBUG else None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routes(app)
    register_websocket_routes(app)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - framework hook
        await init_db_engine()
        await get_redis()

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover - framework hook
        await dispose_db_engine()
        if redis_client is not None:
            await redis_client.close()

    return app


app = create_app()

