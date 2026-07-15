import os
from pathlib import Path

bin_path = Path(__file__).resolve().parents[3] / "bin"
os.environ["PATH"] += os.pathsep + str(bin_path)

from fastapi import FastAPI

from .api.v1.router import api_router
from .core.exceptions import register_exception_handlers
from .middleware.cors import add_cors
from .utils.file_handlers import ensure_storage_dirs

app = FastAPI(title="VoiceScribe AI Backend")

add_cors(app)
register_exception_handlers(app)
ensure_storage_dirs()

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
