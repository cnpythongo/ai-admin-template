import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.redis import redis_pool
from app.db.session import async_session, engine
from app.middleware.operation_log_middleware import OperationLogMiddleware
from app.services.log_processor import run_log_processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start background log processor
    log_processor_task = asyncio.create_task(run_log_processor(async_session))
    yield
    # Shutdown: cancel background tasks and clean up resources
    log_processor_task.cancel()
    try:
        await log_processor_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()
    if redis_pool:
        await redis_pool.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(OperationLogMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


from app.api.v1 import router as v1_router  # noqa: E402

app.include_router(v1_router, prefix="/api/v1")
