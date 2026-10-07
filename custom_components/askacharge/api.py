"""Small client for the askacharge.com brand API, authenticated with an API key.

Everything goes through the same public API the panel uses, so the key's scopes decide what
Home Assistant can do: `sessions:read` to read, `commands:remote-start` / `commands:remote-stop`
(or `commands:write`) to start and stop charging.
"""
from __future__ import annotations

from typing import Any

import aiohttp


class AskachargeError(Exception):
    """Unexpected answer from askacharge.com."""


class AskachargeAuthError(AskachargeError):
    """The API key is wrong, expired or lacks the scope."""


class AskachargeApi:
    def __init__(self, session: aiohttp.ClientSession, api_key: str, base_url: str) -> None:
        self._session = session
        self._headers = {"X-Api-Key": api_key, "User-Agent": "askacharge-homeassistant/0.1.0"}
        self._base = base_url.rstrip("/")

    async def _request(self, method: str, path: str, json: dict | None = None) -> Any:
        try:
            async with self._session.request(
                method, f"{self._base}{path}", headers=self._headers, json=json,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (401, 403):
                    raise AskachargeAuthError(await resp.text())
                if resp.status >= 400:
                    raise AskachargeError(f"{resp.status}: {await resp.text()}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise AskachargeError(str(err)) from err

    async def live(self) -> list[dict[str, Any]]:
        """One item per charger: status, online, active_session (or None)."""
        return await self._request("GET", "/brand/dashboard/live")

    async def start(self, charge_point_id: str, connector_id: int = 1) -> dict[str, Any]:
        """Without id_tag askacharge.com uses the brand's PANEL card."""
        return await self._request("POST", "/brand/commands/remote-start",
                                   {"charge_point_id": charge_point_id, "connector_id": connector_id})

    async def stop(self, charge_point_id: str) -> dict[str, Any]:
        """askacharge.com finds the session in progress itself."""
        return await self._request("POST", "/brand/commands/remote-stop", {"charge_point_id": charge_point_id})
