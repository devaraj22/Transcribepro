from typing import Dict, List

from ...schemas.process import Segment
from ...core.config import settings
from backend.services.ollama_service import llm_complete


def chunk_segments(segments: List[Segment], chunk_length: int) -> List[Dict]:
    """Group consecutive segments into ~chunk_length-second windows for map-reduce and RAG indexing."""
    chunks: List[Dict] = []
    current_texts: List[str] = []
    chunk_start = None
    chunk_end = None

    for seg in segments:
        if chunk_start is None:
            chunk_start = seg.start
        current_texts.append(f"{seg.speaker or 'Speaker'}: {seg.text}")
        chunk_end = seg.end
        if chunk_end - chunk_start >= chunk_length:
            chunks.append({"start": chunk_start, "end": chunk_end, "text": "\n".join(current_texts)})
            current_texts = []
            chunk_start = None

    if current_texts:
        chunks.append({"start": chunk_start or 0.0, "end": chunk_end or 0.0, "text": "\n".join(current_texts)})

    return chunks


def _map_reduce(chunks: List[Dict], map_prompt_template: str, reduce_prompt_template: str, task: str) -> str:
    partials = []
    for chunk in chunks:
        prompt = map_prompt_template.format(text=chunk["text"])
        partials.append(llm_complete(prompt, task=task, max_tokens=512))
    combined = "\n\n".join(partials)
    reduce_prompt = reduce_prompt_template.format(text=combined)
    return llm_complete(reduce_prompt, task=task, max_tokens=768)


def map_reduce_summary(full_text: str) -> str:
    chunks = [{"text": full_text[i : i + 4000]} for i in range(0, len(full_text), 4000)] or [{"text": full_text}]
    return _map_reduce(
        chunks,
        map_prompt_template="Summarize this transcript excerpt concisely:\n\n{text}\n\nSummary:",
        reduce_prompt_template="Combine these partial summaries into one cohesive summary:\n\n{text}\n\nFinal summary:",
        task="summarize",
    )


def map_reduce_action_items(full_text: str) -> str:
    chunks = [{"text": full_text[i : i + 4000]} for i in range(0, len(full_text), 4000)] or [{"text": full_text}]
    return _map_reduce(
        chunks,
        map_prompt_template="List action items and decisions from this excerpt, one per line:\n\n{text}\n\nAction items:",
        reduce_prompt_template="Deduplicate and merge these action item lists into one clean list, one per line:\n\n{text}\n\nFinal action items:",
        task="action_items",
    )
