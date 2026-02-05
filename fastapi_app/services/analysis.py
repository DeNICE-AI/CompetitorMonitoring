import json
from typing import Any, Dict

from fastapi_app.core import config
from fastapi_app.services.gigachat import GigaChatClient


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {}
        return {}


def analyze_text(text: str) -> Dict[str, Any]:
    if not (config.GIGACHAT_CLIENT_ID and config.GIGACHAT_CLIENT_SECRET):
        return _fallback_text_analysis(text)

    prompt = (
        "Ты маркетинговый аналитик. "
        "Сделай структурированный анализ конкурентного текста. "
        "Верни ответ строго в JSON с ключами: "
        "strengths, weaknesses, unique_offers, recommendations. "
        "Каждое поле — список строк. "
        f"\n\nТекст конкурента:\n{text}"
    )
    try:
        client = GigaChatClient()
        response = client.chat(prompt)
        parsed = _extract_json(response)
        if parsed:
            return parsed
        return _fallback_text_analysis(text, response)
    except Exception:
        return _fallback_text_analysis(text)


def analyze_image(text_summary: str) -> Dict[str, Any]:
    if not (config.GIGACHAT_CLIENT_ID and config.GIGACHAT_CLIENT_SECRET):
        return _fallback_image_analysis(text_summary)

    prompt = (
        "Ты маркетинговый аналитик. "
        "На основе описания изображения дай анализ. "
        "Верни ответ строго в JSON с ключами: "
        "description, insights, style_score. "
        "description — строка, insights — список строк, "
        "style_score — число от 1 до 10.\n\n"
        f"Описание: {text_summary}"
    )
    try:
        client = GigaChatClient()
        response = client.chat(prompt)
        parsed = _extract_json(response)
        if parsed:
            return parsed
        return _fallback_image_analysis(text_summary, response)
    except Exception:
        return _fallback_image_analysis(text_summary)


def _fallback_text_analysis(text: str, raw: str | None = None) -> Dict[str, Any]:
    snippet = text.strip().split("\n")[0][:120]
    return {
        "strengths": [f"Четко сформулирован основной месседж: {snippet}"],
        "weaknesses": ["Недостаточно данных о подтверждениях и кейсах."],
        "unique_offers": ["Упоминание пользы для клиента нуждается в уточнении."],
        "recommendations": [
            "Добавить конкретные выгоды и цифры.",
            "Усилить призыв к действию.",
        ],
        "raw": raw,
    }


def _fallback_image_analysis(text_summary: str, raw: str | None = None) -> Dict[str, Any]:
    return {
        "description": f"Изображение с характеристиками: {text_summary}.",
        "insights": ["Проверьте, соответствует ли визуальный стиль бренду."],
        "style_score": 6,
        "raw": raw,
    }
