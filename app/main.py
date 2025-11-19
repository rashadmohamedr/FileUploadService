from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.database import init_db
from app.routers import file_router, auth_router, analytics_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: initialize DB (or run other startup tasks)
    init_db()
    yield
    # shutdown: add cleanup here if needed

app = FastAPI(
    title="File Upload Service",
    description="A production-ready RESTful API for secure file upload and management.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth_router.router)
app.include_router(file_router.router)

# Include the new analytics router
app.include_router(analytics_router.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the File Upload Service API!"}
