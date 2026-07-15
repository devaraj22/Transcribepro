from typing import List

import ollama

from ..app.core.config import settings
from ..app.core.exceptions import LLMServiceError

THINKING_TASKS = {t.strip() for t in settings.LLM_THINKING_MODE_TASKS.split(",")}


def llm_complete(prompt: str, task: str = "cleanup", max_tokens: int = 512) -> str:
    try:
        response = ollama.generate(
            model=settings.LLM_MODEL,
            prompt=prompt,
            options={"num_predict": max_tokens},
        )
        return response.get("response", "").strip()
    except Exception as exc:  # noqa: BLE001
        raise LLMServiceError(str(exc)) from exc


def llm_embed(text: str) -> List[float]:
    try:
        response = ollama.embeddings(model=settings.EMBEDDING_MODEL, prompt=text)
        return response.get("embedding", [])
    except Exception as exc:  # noqa: BLE001
        raise LLMServiceError(str(exc)) from exc
