from __future__ import annotations

from pathlib import Path

TUNNEL_URL_FILE = Path("/run/tunnel/tunnel_url.txt")


def read_tunnel_base_url() -> str:
    """
    Ожидаем строку вида: https://xxxxx.trycloudflare.com
    """
    if not TUNNEL_URL_FILE.exists():
        return ""
    url = TUNNEL_URL_FILE.read_text(encoding="utf-8").strip()
    return url.rstrip("/")
