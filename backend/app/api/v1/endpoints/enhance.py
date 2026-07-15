from fastapi import APIRouter

from ....modules.meeting_mode.text_chunker import map_reduce_action_items, map_reduce_summary
from ....schemas.enhance import (
    ActionItemsResponse,
    EnhanceRequest,
    SummaryResponse,
    TitleResponse,
    TranslateRequest,
)
from backend.services.ollama_service import llm_complete

router = APIRouter()


@router.post("/enhance/cleanup")
def enhance_cleanup(request: EnhanceRequest):
    prompt = (
        "Clean up the following transcript by restoring punctuation and removing filler words:\n\n"
        f"{request.text}\n\nCleaned transcript:"
    )
    return {"text": llm_complete(prompt, task="cleanup", max_tokens=1024)}


@router.post("/enhance/summarize", response_model=SummaryResponse)
def enhance_summarize(request: EnhanceRequest):
    return SummaryResponse(summary=map_reduce_summary(request.text))


@router.post("/enhance/action-items", response_model=ActionItemsResponse)
def enhance_action_items(request: EnhanceRequest):
    output = map_reduce_action_items(request.text)
    items = [line.strip("- ").strip() for line in output.splitlines() if line.strip()]
    return ActionItemsResponse(items=items)


@router.post("/enhance/translate")
def enhance_translate(request: TranslateRequest):
    prompt = (
        f"Translate the following text to {request.target_language}, preserving meaning and speaker labels if present:\n\n"
        f"{request.text}\n\nTranslated text:"
    )
    return {"text": llm_complete(prompt, task="translate", max_tokens=1024)}


@router.post("/enhance/title", response_model=TitleResponse)
def enhance_title(request: EnhanceRequest):
    prompt = f"Generate a short, descriptive title for the following transcript or meeting notes:\n\n{request.text}\n\nTitle:"
    return TitleResponse(title=llm_complete(prompt, task="title", max_tokens=64))
