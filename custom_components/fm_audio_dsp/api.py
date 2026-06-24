"""Runtime API for one FM-Audio DSP config entry."""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_COMMAND_VALUE,
    CONF_DELAY,
    CONF_DSP_HOST,
    CONF_DSP_PIN,
    CONF_DSP_PORT,
    CONF_PRESET_COUNT,
    CONF_TIMEOUT,
    DEFAULT_COMMAND_VALUE,
    DEFAULT_DELAY,
    DEFAULT_PORT,
    DEFAULT_PRESET_COUNT,
    DEFAULT_TIMEOUT,
    EXTRA_COMMANDS,
)
from .protocol import build_load_preset, build_standalone_command, send_telnet_commands


@dataclass
class FMAudioDspApi:
    hass: HomeAssistant
    entry_id: str
    host: str
    port: int = DEFAULT_PORT
    pin: str = ""
    preset_count: int = DEFAULT_PRESET_COUNT
    command_value: int = DEFAULT_COMMAND_VALUE
    timeout: float = DEFAULT_TIMEOUT
    delay: float = DEFAULT_DELAY

    @classmethod
    def from_entry(cls, hass: HomeAssistant, entry) -> "FMAudioDspApi":
        data = {**entry.data, **entry.options}
        return cls(
            hass=hass,
            entry_id=entry.entry_id,
            host=str(data[CONF_DSP_HOST]),
            port=int(data.get(CONF_DSP_PORT, DEFAULT_PORT)),
            pin=str(data.get(CONF_DSP_PIN, "") or ""),
            preset_count=int(data.get(CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT)),
            command_value=int(data.get(CONF_COMMAND_VALUE, DEFAULT_COMMAND_VALUE)),
            timeout=float(data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
            delay=float(data.get(CONF_DELAY, DEFAULT_DELAY)),
        )

    async def async_send_preset(self, preset: int) -> None:
        commands = build_load_preset(preset, pin=self.pin, command_value=self.command_value)
        await self.hass.async_add_executor_job(
            partial(
                send_telnet_commands,
                self.host,
                self.port,
                commands,
                timeout=self.timeout,
                delay=self.delay,
            )
        )
        self.hass.bus.async_fire("fm_audio_dsp_command_sent", {"entry_id": self.entry_id, "host": self.host, "command": f"PRESET_{preset}", "preset": preset})

    async def async_send_command(self, command: str) -> None:
        normalized = command.upper().strip()
        if normalized.startswith("PRESET_"):
            await self.async_send_preset(int(normalized.split("_", 1)[1]))
            return
        if normalized not in EXTRA_COMMANDS:
            raise ValueError(f"Unsupported DSP command: {command}")
        commands = build_standalone_command(normalized, pin=self.pin, command_value=self.command_value)
        await self.hass.async_add_executor_job(
            partial(
                send_telnet_commands,
                self.host,
                self.port,
                commands,
                timeout=self.timeout,
                delay=self.delay,
            )
        )
        self.hass.bus.async_fire("fm_audio_dsp_command_sent", {"entry_id": self.entry_id, "host": self.host, "command": normalized})

    def supported_commands(self) -> list[str]:
        return [*[f"PRESET_{i}" for i in range(1, self.preset_count + 1)], *EXTRA_COMMANDS]
