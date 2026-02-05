import base64
import logging
from typing import Optional

import requests

from fastapi_app.core import config

logger = logging.getLogger(__name__)

VISION_URL = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"


def _build_payload(content_base64: str, mime_type: Optional[str] = None) -> dict:
    spec = {
        "content": content_base64,
        "features": [
            {"type": "TEXT_DETECTION", "text_detection_config": {"language_codes": ["*"]}}
        ],
    }
    if mime_type:
        spec["mime_type"] = mime_type
    return {"folderId": config.YC_FOLDER_ID, "analyze_specs": [spec]}


def _request_vision(payload: dict) -> Optional[dict]:
    if not (config.YC_API_KEY and config.YC_FOLDER_ID):
        return None

    headers = {"Authorization": f"Api-Key {config.YC_API_KEY}", "Content-Type": "application/json"}
    response = requests.post(
        VISION_URL,
        headers=headers,
        json=payload,
        verify=not config.YC_SKIP_VERIFY,
        timeout=30,
    )
    if response.status_code != 200:
        logger.error("Vision OCR error %s: %s", response.status_code, response.text[:200])
        return None
    return response.json()


def _parse_text_detection(data: dict, include_page_headers: bool = False) -> Optional[str]:
    result_text = ""
    try:
        for result in data.get("results", []):
            for sub_res in result.get("results", []):
                text_detection = sub_res.get("textDetection")
                if not text_detection:
                    continue
                for page_index, page in enumerate(text_detection.get("pages", []), start=1):
                    if include_page_headers:
                        result_text += f"\n--- Page {page_index} ---\n"
                    for block in page.get("blocks", []):
                        for line in block.get("lines", []):
                            line_text = " ".join(
                                word.get("text", "") for word in line.get("words", [])
                            ).strip()
                            if line_text:
                                result_text += line_text + "\n"
                        result_text += "\n"
    except Exception as exc:
        logger.error("Vision OCR parse error: %s", exc)
        return None

    result_text = result_text.strip()
    return result_text if result_text else None


def recognize_image_text(image_bytes: bytes) -> Optional[str]:
    if not image_bytes:
        return None
    content_base64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = _build_payload(content_base64)
    logger.info("Vision OCR image request")
    data = _request_vision(payload)
    if not data:
        return None
    return _parse_text_detection(data)


def recognize_pdf_text(pdf_bytes: bytes) -> Optional[str]:
    if not pdf_bytes:
        return None
    content_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    payload = _build_payload(content_base64, mime_type="application/pdf")
    logger.info("Vision OCR pdf request")
    data = _request_vision(payload)
    if not data:
        return None
    return _parse_text_detection(data, include_page_headers=True)
