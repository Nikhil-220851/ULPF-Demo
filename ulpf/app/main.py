from fastapi import FastAPI
# Reload trigger AI unknown workflow fix
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, process, plugins, ai, events
from app.database.connection import init_db

app = FastAPI(title="ULPF API", description="Universal Log Pre-processing Framework")

@app.on_event("startup")
def on_startup():
    init_db()

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
app.include_router(ai.router)
app.include_router(events.router)
