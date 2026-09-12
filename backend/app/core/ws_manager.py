"""Quan ly ket noi WebSocket cho kenh Tin nhan Tac chien thoi gian thuc.

Luu ket noi trong bo nho tien trinh (in-memory) - phu hop mo hinh 1 tien trinh
uvicorn phuc vu toan he thong LAN noi bo. Neu sau nay chay nhieu worker / nhieu
may thi thay lop nay bang ban co Redis pub/sub (giu nguyen interface).
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterable

from starlette.websockets import WebSocket


class ChatConnectionManager:
    """So dang ky socket theo user_id (moi tab / thiet bi la 1 socket)."""

    def __init__(self) -> None:
        self._conns: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self._conns.setdefault(user_id, set()).add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._conns.get(user_id)
            if not conns:
                return
            conns.discard(websocket)
            if not conns:
                self._conns.pop(user_id, None)

    def is_online(self, user_id: int) -> bool:
        return bool(self._conns.get(user_id))

    async def broadcast_to_users(
        self, user_ids: Iterable[int], payload: dict[str, Any]
    ) -> None:
        """Gui 1 goi JSON toi moi socket cua cac user chi dinh; loai socket hong."""
        async with self._lock:
            targets = [
                (uid, ws)
                for uid in set(user_ids)
                for ws in list(self._conns.get(uid, set()))
            ]

        dead: list[tuple[int, WebSocket]] = []
        for uid, ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001 - socket dut thi don dep
                dead.append((uid, ws))

        for uid, ws in dead:
            await self.disconnect(uid, ws)


# Singleton dung chung toan ung dung
manager = ChatConnectionManager()
