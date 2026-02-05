import socket
import sys
import threading
from pathlib import Path
from typing import Optional

import requests
import uvicorn

APP_ROOT = Path(__file__).resolve().parent


def _sanitize_sys_path() -> None:
    app_root = str(APP_ROOT)
    sanitized = []
    for entry in sys.path:
        if not entry:
            continue
        if "Проект fastapi" in entry and entry != app_root:
            continue
        sanitized.append(entry)
    if app_root not in sanitized:
        sanitized.insert(0, app_root)
    sys.path = sanitized


_sanitize_sys_path()

from fastapi_app.main import app


class BackendServer:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[uvicorn.Server] = None
        self._port: Optional[int] = None

    @property
    def base_url(self) -> str:
        if self._port is None:
            raise RuntimeError("Backend is not started")
        return f"http://127.0.0.1:{self._port}"

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._port = self._pick_free_port()
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self._port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        self._wait_ready()

    def stop(self) -> None:
        if self._server:
            self._server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _wait_ready(self) -> None:
        if not self._port:
            return
        for _ in range(30):
            try:
                requests.get(f"http://127.0.0.1:{self._port}/history", timeout=1)
                return
            except Exception:
                continue

    @staticmethod
    def _pick_free_port() -> int:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        _, port = sock.getsockname()
        sock.close()
        return int(port)
