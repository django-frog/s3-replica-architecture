from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="Cloud-Native Object Storage Microservice",
    version="1.0.0"
)

# --- UPDATED CORS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS, # Dynamically loaded
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------

app.include_router(router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}
