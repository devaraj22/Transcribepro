from fastapi import APIRouter

from .endpoints import enhance, history, process, rag, report

api_router = APIRouter()
api_router.include_router(process.router, tags=["process"])
api_router.include_router(enhance.router, tags=["enhance"])
api_router.include_router(rag.router, tags=["rag"])
api_router.include_router(report.router, tags=["report"])
api_router.include_router(history.router, tags=["history"])
