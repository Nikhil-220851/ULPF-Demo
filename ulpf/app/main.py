from fastapi import FastAPI
from app.api.routes import health

app = FastAPI(title="ULPF API", description="Universal Log Pre-processing Framework")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "ULPF"
    }

app.include_router(health.router)
