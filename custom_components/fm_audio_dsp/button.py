"""Button entities for FM-Audio DSP commands."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, EXTRA_COMMANDS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    entities: list[FMAudioDspButton] = []
    commands = [*[f"PRESET_{preset}" for preset in range(1, api.preset_count + 1)], *EXTRA_COMMANDS]
    labels = {**{f"PRESET_{preset}": f"Preset {preset}" for preset in range(1, api.preset_count + 1)}, **{command: command.title() for command in EXTRA_COMMANDS}}

    # Default buttons control all hosts in this config entry. With one host this is the old behavior.
    prefix = "All " if len(api.hosts) > 1 else ""
    for command in commands:
        entities.append(FMAudioDspButton(api, command, f"{prefix}{labels[command]}"))

    # If multiple DSP hosts are configured in one entry, also expose one button set per host.
    if len(api.hosts) > 1:
        for host in api.hosts:
            for command in commands:
                entities.append(FMAudioDspButton(api, command, f"{host} {labels[command]}", target_host=host))

    async_add_entities(entities)


class FMAudioDspButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, api, command: str, label: str, target_host: str | None = None) -> None:
        self._api = api
        self._command = command
        self._target_host = target_host
        self._attr_name = label
        host_suffix = f"_{target_host}" if target_host else "_all" if len(api.hosts) > 1 else ""
        safe_host_suffix = host_suffix.replace(".", "_").replace(":", "_")
        self._attr_unique_id = f"{api.entry_id}{safe_host_suffix}_{command.lower()}"
        device_name = "FM-Audio DSP" if not target_host else f"FM-Audio DSP {target_host}"
        config_host = target_host or api.host
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{api.entry_id}:{target_host or 'all'}")},
            "name": device_name,
            "manufacturer": "FM-Audio",
            "model": "DSP Telnet",
            "configuration_url": f"telnet://{config_host}:{api.port}",
        }

    async def async_press(self) -> None:
        await self._api.async_send_command(self._command, target_host=self._target_host)
