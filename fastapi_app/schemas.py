from typing import Any, Dict, List

from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TextResponse(BaseModel):
    analysis: Dict[str, Any]


class ParseDemoRequest(BaseModel):
    url: str = Field(..., min_length=1)


class ParseDemoResponse(BaseModel):
    title: str
    analysis: Dict[str, Any]


class ImageResponse(BaseModel):
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]


class OCRResponse(BaseModel):
    text: str


class HistoryItem(BaseModel):
    timestamp: str
    type: str
    input: Dict[str, Any]
    output: Dict[str, Any]


class HistoryResponse(BaseModel):
    items: List[HistoryItem]


class ErrorResponse(BaseModel):
    error: str
