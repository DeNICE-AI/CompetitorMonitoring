import base64
import time
from typing import Optional

import requests

from fastapi_app.core import config


class YandexArtClient:
    def __init__(self) -> None:
        self._api_key = config.YC_API_KEY
        self._model_uri = config.YC_ART_MODEL_URI

    def generate_image(self, prompt: str, mime_type: str = "image/jpeg") -> Optional[bytes]:
        if not (self._api_key and self._model_uri):
            return None

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
        headers = {"Authorization": f"Api-Key {self._api_key}", "Content-Type": "application/json"}
        payload = {
            "modelUri": self._model_uri,
            "messages": [{"text": prompt, "weight": 1}],
            "generationOptions": {"mimeType": mime_type, "seed": int(time.time())},
        }
        response = requests.post(
            url, headers=headers, json=payload, verify=not config.YC_SKIP_VERIFY, timeout=30
        )
        if response.status_code != 200:
            return None

        operation_id = response.json().get("id")
        if not operation_id:
            return None

        for _ in range(30):
            time.sleep(2)
            op_resp = requests.get(
                f"https://llm.api.cloud.yandex.net/operations/{operation_id}",
                headers=headers,
                verify=not config.YC_SKIP_VERIFY,
                timeout=30,
            )
            op_data = op_resp.json()
            if op_data.get("done", False):
                if "error" in op_data:
                    return None
                return base64.b64decode(op_data["response"]["image"])
        return None
