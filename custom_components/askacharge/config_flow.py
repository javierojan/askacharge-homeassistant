"""Set-up with an askacharge.com API key (Settings → API keys in the panel)."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AskachargeApi, AskachargeAuthError, AskachargeError
from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN


class AskachargeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _probar(self, api_key: str, base_url: str) -> dict[str, str]:
        api = AskachargeApi(async_get_clientsession(self.hass), api_key, base_url)
        try:
            await api.live()
        except AskachargeAuthError:
            return {"base": "invalid_auth"}
        except AskachargeError:
            return {"base": "cannot_connect"}
        return {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input.get(CONF_BASE_URL) or DEFAULT_BASE_URL
            # One entry per key: the key identifies the brand on askacharge.com
            await self.async_set_unique_id(user_input[CONF_API_KEY][-12:])
            self._abort_if_unique_id_configured()
            errors = await self._probar(user_input[CONF_API_KEY], base_url)
            if not errors:
                return self.async_create_entry(title="askacharge.com",
                                               data={CONF_API_KEY: user_input[CONF_API_KEY], CONF_BASE_URL: base_url})
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
            }),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            errors = await self._probar(user_input[CONF_API_KEY], entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL))
            if not errors:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_API_KEY: user_input[CONF_API_KEY]})
        return self.async_show_form(step_id="reauth_confirm",
                                    data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}), errors=errors)
