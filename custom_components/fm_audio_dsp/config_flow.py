"""Config flow for FM-Audio DSP."""
from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .api import parse_hosts
from .const import (
    CONF_COMMAND_VALUE,
    CONF_DELAY,
    CONF_DSP_HOST,
    CONF_DSP_HOSTS,
    CONF_DSP_PIN,
    CONF_DSP_PORT,
    CONF_PRESET_COUNT,
    CONF_TIMEOUT,
    CONF_X2_DEVICE_ID,
    CONF_X2_KEY_MAP,
    CONF_X2_MQTT_TOPIC,
    DEFAULT_COMMAND_VALUE,
    DEFAULT_DELAY,
    DEFAULT_PORT,
    DEFAULT_PRESET_COUNT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_PRESETS,
    MIN_PRESET_COUNT,
)


def _host_text(defaults: dict[str, Any]) -> str:
    hosts = parse_hosts(defaults.get(CONF_DSP_HOSTS) or defaults.get(CONF_DSP_HOST))
    return "\n".join(hosts) if hosts else "192.168.178.192"


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_DSP_HOSTS, default=_host_text(defaults)): str,
            vol.Required(CONF_DSP_PORT, default=defaults.get(CONF_DSP_PORT, DEFAULT_PORT)): vol.All(int, vol.Range(min=1, max=65535)),
            vol.Required(CONF_PRESET_COUNT, default=defaults.get(CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT)): vol.All(int, vol.Range(min=MIN_PRESET_COUNT, max=MAX_PRESETS)),
            vol.Optional(CONF_DSP_PIN, default=defaults.get(CONF_DSP_PIN, "")): str,
            vol.Optional(CONF_COMMAND_VALUE, default=defaults.get(CONF_COMMAND_VALUE, DEFAULT_COMMAND_VALUE)): vol.All(int, vol.Range(min=0, max=1)),
            vol.Optional(CONF_TIMEOUT, default=defaults.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): vol.Coerce(float),
            vol.Optional(CONF_DELAY, default=defaults.get(CONF_DELAY, DEFAULT_DELAY)): vol.Coerce(float),
            vol.Optional(CONF_X2_MQTT_TOPIC, default=defaults.get(CONF_X2_MQTT_TOPIC, "")): str,
            vol.Optional(CONF_X2_DEVICE_ID, default=defaults.get(CONF_X2_DEVICE_ID, "")): str,
            vol.Optional(CONF_X2_KEY_MAP, default=defaults.get(CONF_X2_KEY_MAP, '{"9":"PRESET_1","10":"PRESET_2","11":"PRESET_3","12":"PRESET_4"}')): str,
        }
    )


def _normalize_user_input(user_input: dict[str, Any]) -> list[str]:
    hosts = parse_hosts(user_input.get(CONF_DSP_HOSTS) or user_input.get(CONF_DSP_HOST))
    user_input[CONF_DSP_HOSTS] = hosts
    if hosts:
        user_input[CONF_DSP_HOST] = hosts[0]
    return hosts


class FMAudioDspConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            hosts = _normalize_user_input(user_input)
            if not hosts:
                errors[CONF_DSP_HOSTS] = "no_hosts"
            if user_input.get(CONF_X2_KEY_MAP):
                try:
                    parsed = json.loads(user_input[CONF_X2_KEY_MAP])
                    if not isinstance(parsed, dict):
                        raise ValueError
                except Exception:
                    errors[CONF_X2_KEY_MAP] = "invalid_json"
            if not errors:
                unique_id = ",".join(hosts)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                title = "FM-Audio DSP " + (hosts[0] if len(hosts) == 1 else f"{len(hosts)} Geräte")
                return self.async_create_entry(title=title, data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(user_input), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return FMAudioDspOptionsFlow(config_entry)


class FMAudioDspOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            _normalize_user_input(user_input)
            return self.async_create_entry(title="", data=user_input)
        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
