from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.database import init_db
from app.routers import file_router, auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: initialize DB (or run other startup tasks)
    init_db()
    yield
    # shutdown: add cleanup here if needed

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(file_router.router)

# TODO: (Analytics) Import and register the analytics_router.
# from .routers import analytics_router
# app.include_router(analytics_router.router, prefix="/analytics", tags=["analytics"])
