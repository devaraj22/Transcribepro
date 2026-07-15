from typing import List
from pydantic import BaseModel


class EnhanceRequest(BaseModel):
    text: str


class SummaryResponse(BaseModel):
    summary: str


class ActionItemsResponse(BaseModel):
    items: List[str]


class TranslateRequest(BaseModel):
    text: str
    target_language: str


class TitleResponse(BaseModel):
    title: str
