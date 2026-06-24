"""Button entities for FM-Audio DSP commands."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, EXTRA_COMMANDS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    entities = [FMAudioDspButton(api, f"PRESET_{preset}", f"Preset {preset}") for preset in range(1, api.preset_count + 1)]
    entities.extend(FMAudioDspButton(api, command, command.title()) for command in EXTRA_COMMANDS)
    async_add_entities(entities)


class FMAudioDspButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, api, command: str, label: str) -> None:
        self._api = api
        self._command = command
        self._attr_name = label
        self._attr_unique_id = f"{api.entry_id}_{command.lower()}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, api.entry_id)},
            "name": "FM-Audio DSP",
            "manufacturer": "FM-Audio",
            "model": "DSP Telnet",
            "configuration_url": f"telnet://{api.host}:{api.port}",
        }

    async def async_press(self) -> None:
        await self._api.async_send_command(self._command)
