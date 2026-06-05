from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
MINIAPP_DIR = BASE_DIR / "miniapp"

app = FastAPI(title="Astra Tarot API")


@app.get("/")
async def root():
    return {
        "ok": True,
        "project": "Astra Tarot",
        "miniapp": "/miniapp/",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


app.mount(
    "/miniapp",
    StaticFiles(directory=MINIAPP_DIR, html=True),
    name="miniapp",
)