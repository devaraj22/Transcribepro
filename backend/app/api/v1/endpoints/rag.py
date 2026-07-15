from fastapi import APIRouter

from ....schemas.rag import AskRequest, AskResponse
from backend.services.faiss_service import retrieve

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    answer, sources = retrieve(request.job_id, request.question)
    return AskResponse(answer=answer, sources=sources)
