"""Тонкий async-клиент к Wildberries Statistics API.

Docs: https://openapi.wildberries.ru/ (Statistics)
Все эндпоинты принимают параметр dateFrom (RFC3339) и отдают данные
с момента dateFrom. flag=0 — инкрементально по lastChangeDate.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings


class WBAPIError(Exception):
    """Ошибка обращения к WB API."""


class WBClient:
    def __init__(self, token: str, base_url: str | None = None, timeout: float = 60.0):
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.WB_STATISTICS_BASE_URL,
            headers={"Authorization": token},
            timeout=timeout,
        )

    async def __aenter__(self) -> WBClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, WBAPIError)),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        resp = await self._client.get(path, params=params)

        if resp.status_code == 429:
            raise WBAPIError("WB rate limit (429)")
        if resp.status_code == 401:
            raise WBAPIError("WB token invalid (401)")
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []

    async def get_sales(self, date_from: datetime, flag: int = 0) -> list[dict[str, Any]]:
        return await self._get(
            "/api/v1/supplier/sales",
            {"dateFrom": date_from.isoformat(), "flag": flag},
        )

    async def get_orders(self, date_from: datetime, flag: int = 0) -> list[dict[str, Any]]:
        return await self._get(
            "/api/v1/supplier/orders",
            {"dateFrom": date_from.isoformat(), "flag": flag},
        )

    async def get_stocks(self, date_from: datetime) -> list[dict[str, Any]]:
        return await self._get(
            "/api/v1/supplier/stocks",
            {"dateFrom": date_from.isoformat()},
        )

    async def check_token(self) -> tuple[bool, str]:
        """Проверить токен через официальный WB /ping. Возвращает (ok, причина)."""
        try:
            resp = await self._client.get("/ping")
        except httpx.HTTPError as e:
            return False, f"Не удалось связаться с Wildberries: {e}"

        if resp.status_code == 200:
            return True, ""
        if resp.status_code in (401, 403):
            return False, (
                "Токен недействителен или не той категории. "
                "Нужен токен с доступом к «Статистике»."
            )
        if resp.status_code == 429:
            return False, "Wildberries временно ограничил запросы (429). Попробуйте через минуту."
        return False, f"Wildberries вернул код {resp.status_code}. Попробуйте позже."

    async def ping(self) -> bool:
        ok, _ = await self.check_token()
        return ok
