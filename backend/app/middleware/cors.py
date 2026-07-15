from fastapi.middleware.cors import CORSMiddleware

from ..core.config import settings


def add_cors(app):
    allowed_origins = [
        settings.FRONTEND_ORIGIN,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
