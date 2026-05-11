from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db.database import engine
from src.db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Stock Forecast Platform",
    version="0.2.0",
    lifespan=lifespan,
)


from api.routes.backtests import router as backtests_router  # noqa: E402
from api.routes.forecasts import router as forecasts_router  # noqa: E402
from api.routes.health import router as health_router  # noqa: E402

app.include_router(health_router)
app.include_router(forecasts_router)
app.include_router(backtests_router)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
