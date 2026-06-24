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
    CONF_DSP_HOSTS,
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


def parse_hosts(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Parse one or more DSP hosts from text, comma/semicolon separated text, or a list."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.replace(";", ",").replace("\n", ",").split(",")
    else:
        raw_items = list(value)
    hosts: list[str] = []
    for item in raw_items:
        host = str(item).strip()
        if host and host not in hosts:
            hosts.append(host)
    return hosts


@dataclass
class FMAudioDspApi:
    hass: HomeAssistant
    entry_id: str
    hosts: list[str]
    port: int = DEFAULT_PORT
    pin: str = ""
    preset_count: int = DEFAULT_PRESET_COUNT
    command_value: int = DEFAULT_COMMAND_VALUE
    timeout: float = DEFAULT_TIMEOUT
    delay: float = DEFAULT_DELAY

    @property
    def host(self) -> str:
        """Return the primary host for backward-compatible display/device info."""
        return self.hosts[0]

    @classmethod
    def from_entry(cls, hass: HomeAssistant, entry) -> "FMAudioDspApi":
        data = {**entry.data, **entry.options}
        hosts = parse_hosts(data.get(CONF_DSP_HOSTS) or data.get(CONF_DSP_HOST))
        return cls(
            hass=hass,
            entry_id=entry.entry_id,
            hosts=hosts,
            port=int(data.get(CONF_DSP_PORT, DEFAULT_PORT)),
            pin=str(data.get(CONF_DSP_PIN, "") or ""),
            preset_count=int(data.get(CONF_PRESET_COUNT, DEFAULT_PRESET_COUNT)),
            command_value=int(data.get(CONF_COMMAND_VALUE, DEFAULT_COMMAND_VALUE)),
            timeout=float(data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
            delay=float(data.get(CONF_DELAY, DEFAULT_DELAY)),
        )

    def _target_hosts(self, target_host: str | None = None) -> list[str]:
        if target_host:
            normalized = target_host.strip()
            if normalized not in self.hosts:
                raise ValueError(f"Unknown DSP target host for this entry: {target_host}")
            return [normalized]
        return self.hosts

    async def _async_send_to_hosts(self, hosts: list[str], commands: list[str]) -> None:
        for host in hosts:
            await self.hass.async_add_executor_job(
                partial(
                    send_telnet_commands,
                    host,
                    self.port,
                    commands,
                    timeout=self.timeout,
                    delay=self.delay,
                )
            )

    async def async_send_preset(self, preset: int, target_host: str | None = None) -> None:
        commands = build_load_preset(preset, pin=self.pin, command_value=self.command_value)
        hosts = self._target_hosts(target_host)
        await self._async_send_to_hosts(hosts, commands)
        self.hass.bus.async_fire(
            "fm_audio_dsp_command_sent",
            {"entry_id": self.entry_id, "hosts": hosts, "command": f"PRESET_{preset}", "preset": preset},
        )

    async def async_send_command(self, command: str, target_host: str | None = None) -> None:
        normalized = command.upper().strip()
        if normalized.startswith("PRESET_"):
            await self.async_send_preset(int(normalized.split("_", 1)[1]), target_host=target_host)
            return
        if normalized not in EXTRA_COMMANDS:
            raise ValueError(f"Unsupported DSP command: {command}")
        commands = build_standalone_command(normalized, pin=self.pin, command_value=self.command_value)
        hosts = self._target_hosts(target_host)
        await self._async_send_to_hosts(hosts, commands)
        self.hass.bus.async_fire(
            "fm_audio_dsp_command_sent",
            {"entry_id": self.entry_id, "hosts": hosts, "command": normalized},
        )

    def supported_commands(self) -> list[str]:
        return [*[f"PRESET_{i}" for i in range(1, self.preset_count + 1)], *EXTRA_COMMANDS]
