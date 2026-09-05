from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, process, plugins

app = FastAPI(title="ULPF API", description="Universal Log Pre-processing Framework")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "ULPF"
    }

app.include_router(health.router)
app.include_router(process.router)
app.include_router(plugins.router)
