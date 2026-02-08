from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.Base import Base
from db.engine import engine
import db.models

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(lifespan=lifespan)