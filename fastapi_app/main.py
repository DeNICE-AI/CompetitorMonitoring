from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, File, HTTPException, UploadFile

from fastapi_app.core.history import get_history, save_history
from fastapi_app.schemas import (
    ErrorResponse,
    HistoryResponse,
    ImageResponse,
    OCRResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    TextRequest,
    TextResponse,
)
from fastapi_app.services.analysis import analyze_image, analyze_text
from fastapi_app.services.image_utils import summarize_image
from fastapi_app.services.parse_demo import fetch_page_text
from fastapi_app.services.yandex_vision import recognize_image_text, recognize_pdf_text

app = FastAPI(title="Competitor Monitoring Assistant", version="1.0.0")


def _normalize_url(value: str) -> Optional[str]:
    trimmed = value.strip()
    if not trimmed:
        return None
    if not trimmed.startswith(("http://", "https://")):
        trimmed = f"https://{trimmed}"
    parsed = urlparse(trimmed)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return trimmed


@app.post("/analyze_text", response_model=TextResponse, responses={400: {"model": ErrorResponse}})
def analyze_text_endpoint(payload: TextRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    analysis = analyze_text(text)
    save_history({"type": "text", "input": {"text": text[:500]}, "output": analysis})
    return {"analysis": analysis}


@app.post("/analyze_image", response_model=ImageResponse, responses={400: {"model": ErrorResponse}})
async def analyze_image_endpoint(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Image file is required")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    metadata = summarize_image(image_bytes)
    summary = (
        f"Формат: {metadata['format']}, размер {metadata['width']}x{metadata['height']}, "
        f"соотношение {metadata['aspect_ratio']}, доминирующий цвет {metadata['dominant_color']}."
    )
    analysis = analyze_image(summary)
    save_history(
        {
            "type": "image",
            "input": {"filename": file.filename, "content_type": file.content_type},
            "output": {"metadata": metadata, "analysis": analysis},
        }
    )
    return {"metadata": metadata, "analysis": analysis}


@app.post("/ocr_image", response_model=OCRResponse, responses={400: {"model": ErrorResponse}})
async def ocr_image_endpoint(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Image file is required")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    text = recognize_image_text(image_bytes)
    if not text:
        raise HTTPException(status_code=400, detail="OCR failed")

    save_history(
        {
            "type": "ocr_image",
            "input": {"filename": file.filename, "content_type": file.content_type},
            "output": {"text": text[:2000], "truncated": len(text) > 2000},
        }
    )
    return {"text": text}


@app.post("/ocr_pdf", response_model=OCRResponse, responses={400: {"model": ErrorResponse}})
async def ocr_pdf_endpoint(file: UploadFile = File(...)):
    is_pdf = file.content_type == "application/pdf"
    if not is_pdf and file.filename:
        is_pdf = file.filename.lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=400, detail="PDF file is required")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    text = recognize_pdf_text(pdf_bytes)
    if not text:
        raise HTTPException(status_code=400, detail="OCR failed")

    save_history(
        {
            "type": "ocr_pdf",
            "input": {"filename": file.filename, "content_type": file.content_type},
            "output": {"text": text[:2000], "truncated": len(text) > 2000},
        }
    )
    return {"text": text}


@app.post("/parse_demo", response_model=ParseDemoResponse, responses={400: {"model": ErrorResponse}})
def parse_demo_endpoint(payload: ParseDemoRequest):
    normalized_url = _normalize_url(payload.url)
    if not normalized_url:
        raise HTTPException(status_code=400, detail="Неверный формат URL. Пример: https://example.com")
    title, text = fetch_page_text(normalized_url)
    if not text:
        raise HTTPException(status_code=400, detail="Empty page content")
    analysis = analyze_text(text)
    save_history({"type": "parse_demo", "input": {"url": normalized_url}, "output": analysis})
    return {"title": title, "analysis": analysis}


@app.get("/history", response_model=HistoryResponse)
def history_endpoint():
    return {"items": get_history()}
