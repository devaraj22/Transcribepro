from typing import List
from pydantic import BaseModel


class AskRequest(BaseModel):
    job_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[str]
