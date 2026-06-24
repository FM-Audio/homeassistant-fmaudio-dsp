"""Home Assistant integration for FM-Audio DSP Telnet control."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_COMMAND
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import FMAudioDspApi
from .const import (
    CONF_X2_DEVICE_ID,
    CONF_X2_KEY_MAP,
    CONF_X2_MQTT_TOPIC,
    DOMAIN,
    EXTRA_COMMANDS,
    MAX_PRESETS,
    MIN_PRESET_NUMBER,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SEND_PRESET = "send_preset"
SERVICE_SEND_COMMAND = "send_command"
ATTR_ENTRY_ID = "entry_id"
ATTR_PRESET = "preset"
ATTR_TARGET_HOST = "target_host"

SEND_PRESET_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_TARGET_HOST): cv.string,
        vol.Required(ATTR_PRESET): vol.All(int, vol.Range(min=MIN_PRESET_NUMBER, max=MAX_PRESETS)),
    }
)
SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_TARGET_HOST): cv.string,
        vol.Required(CONF_COMMAND): vol.In([*[f"PRESET_{i}" for i in range(MIN_PRESET_NUMBER, MAX_PRESETS + 1)], *EXTRA_COMMANDS]),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = FMAudioDspApi.from_entry(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"api": api, "unsub_mqtt": None}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_setup_services(hass)
    await _async_setup_x2_mqtt(hass, entry, api)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if data and data.get("unsub_mqtt"):
        data["unsub_mqtt"]()
    return unload_ok


async def _async_setup_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEND_PRESET):
        return

    async def _apis_for_call(call: ServiceCall) -> list[FMAudioDspApi]:
        entry_id = call.data.get(ATTR_ENTRY_ID)
        target_host = call.data.get(ATTR_TARGET_HOST)
        entries = hass.data.get(DOMAIN, {})
        if entry_id:
            if entry_id not in entries:
                raise HomeAssistantError(f"Unknown FM-Audio DSP entry_id: {entry_id}")
            return [entries[entry_id]["api"]]
        apis = [entry["api"] for entry in entries.values()]
        if target_host:
            apis = [api for api in apis if target_host in api.hosts]
            if not apis:
                raise HomeAssistantError(f"Unknown FM-Audio DSP target_host: {target_host}")
        return apis

    async def handle_send_preset(call: ServiceCall) -> None:
        preset = int(call.data[ATTR_PRESET])
        target_host = call.data.get(ATTR_TARGET_HOST)
        for api in await _apis_for_call(call):
            await api.async_send_preset(preset, target_host=target_host)

    async def handle_send_command(call: ServiceCall) -> None:
        command = str(call.data[CONF_COMMAND])
        target_host = call.data.get(ATTR_TARGET_HOST)
        for api in await _apis_for_call(call):
            await api.async_send_command(command, target_host=target_host)

    hass.services.async_register(DOMAIN, SERVICE_SEND_PRESET, handle_send_preset, schema=SEND_PRESET_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SEND_COMMAND, handle_send_command, schema=SEND_COMMAND_SCHEMA)


async def _async_setup_x2_mqtt(hass: HomeAssistant, entry: ConfigEntry, api: FMAudioDspApi) -> None:
    data = {**entry.data, **entry.options}
    topic = str(data.get(CONF_X2_MQTT_TOPIC) or "").strip()
    if not topic:
        return
    try:
        from homeassistant.components.mqtt import async_subscribe
    except Exception as exc:
        _LOGGER.warning("SofaBaton X2 MQTT bridge not enabled because MQTT integration is unavailable: %s", exc)
        return

    device_id_filter = str(data.get(CONF_X2_DEVICE_ID) or "").strip()
    try:
        key_map = json.loads(str(data.get(CONF_X2_KEY_MAP) or "{}"))
    except json.JSONDecodeError:
        _LOGGER.warning("Ignoring invalid SofaBaton X2 key map JSON")
        return

    @callback
    def mqtt_message_received(msg) -> None:
        try:
            payload: dict[str, Any] = json.loads(msg.payload)
        except Exception:
            _LOGGER.debug("Ignoring non-JSON SofaBaton X2 MQTT payload: %s", msg.payload)
            return
        if device_id_filter and str(payload.get("device_id")) != device_id_filter:
            return
        key_id = str(payload.get("key_id"))
        command = key_map.get(key_id)
        if not command:
            return
        hass.async_create_task(_send_x2_command(api, command, payload))

    unsub = await async_subscribe(hass, topic, mqtt_message_received, 0)
    hass.data[DOMAIN][entry.entry_id]["unsub_mqtt"] = unsub
    _LOGGER.info("Enabled SofaBaton X2 MQTT bridge for topic %s", topic)


async def _send_x2_command(api: FMAudioDspApi, command: str, payload: dict[str, Any]) -> None:
    try:
        await api.async_send_command(command)
        api.hass.bus.async_fire("fm_audio_dsp_x2_command", {"entry_id": api.entry_id, "command": command, "payload": payload})
    except Exception as exc:
        _LOGGER.exception("Failed to execute SofaBaton X2 DSP command %s: %s", command, exc)
