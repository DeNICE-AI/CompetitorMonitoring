import base64
import time
import uuid
from typing import Optional

import requests

from fastapi_app.core import config


class GigaChatClient:
    def __init__(self) -> None:
        self._client_id = config.GIGACHAT_CLIENT_ID
        self._client_secret = config.GIGACHAT_CLIENT_SECRET
        self._access_token: Optional[str] = None
        self._token_expiry = 0.0
        self._base_url = "https://gigachat.devices.sberbank.ru/api/v1"

    def _get_verify(self):
        if config.GIGACHAT_CA_CERT:
            return config.GIGACHAT_CA_CERT
        if config.GIGACHAT_SKIP_VERIFY:
            return False
        default_cert = config.PROJECT_ROOT / "certs" / "russian_trusted_root_ca.pem"
        if default_cert.exists():
            return str(default_cert)
        return True

    def _refresh_token(self) -> str:
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        auth_payload = f"{self._client_id}:{self._client_secret}".encode("utf-8")
        headers = {
            "Authorization": f"Basic {base64.b64encode(auth_payload).decode('utf-8')}",
            "Content-Type": "application/x-www-form-urlencoded",
            "RqUID": str(uuid.uuid4()),
        }
        response = requests.post(
            url,
            data="scope=GIGACHAT_API_PERS",
            headers=headers,
            timeout=30,
            verify=self._get_verify(),
        )
        response.raise_for_status()
        payload = response.json()
        self._access_token = payload["access_token"]
        expires_in = payload.get("expires_in", 1800)
        self._token_expiry = time.time() + expires_in - 30
        return self._access_token

    def _get_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expiry:
            return self._refresh_token()
        return self._access_token

    def chat(self, prompt: str, temperature: float = 0.2) -> str:
        url = f"{self._base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self._get_token()}"}
        payload = {
            "model": config.GIGACHAT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60,
            verify=self._get_verify(),
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
