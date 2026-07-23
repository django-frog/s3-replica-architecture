from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.seeder import seed_sandbox

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_ENV != "production":
        await seed_sandbox()

    yield  # Hand over control to FastAPI to start accepting HTTP requests

    pass


app = FastAPI(
    title="Cloud-Native Object Storage Microservice",
    version="1.0.0",
    lifespan=lifespan  # Attach the context manager here
)

# Strip trailing slashes to prevent browser CORS preflight failures
cors_origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------

app.include_router(router)

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
