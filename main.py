# main.py
import asyncio
import os
import contextlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.Base import Base
from db.engine import engine, SessionLocal
import db.models  # noqa: F401
from routes import tracked_games_routes
from services.game_aggregator_service import GameAggregatorService

@asynccontextmanager
async def lifespan(_app: FastAPI):
    interval_seconds = int(os.getenv("PRICE_UPDATE_INTERVAL_SECONDS", "1800"))

    async def price_update_loop():
        while True:
            db = SessionLocal()
            try:
                service = GameAggregatorService(db)
                await service.update_all_tracked_deals()
            finally:
                db.close()
            await asyncio.sleep(interval_seconds)

    task = asyncio.create_task(price_update_loop())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

app = FastAPI(
    title="Game Price Tracker API",
    description="API para rastrear preços de jogos usando CheapShark",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracked_games_routes.router)

@app.get("/")
def read_root():
    return {
        "message": "Game Price Tracker API",
        "docs": "/docs",
        "stores": "/games/stores"
    }
