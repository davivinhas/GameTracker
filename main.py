# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.Base import Base
from db.engine import engine
from routes import tracked_games_routes

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

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