"""FM-Audio DSP Telnet protocol helpers."""
from __future__ import annotations

import socket
import time
from collections.abc import Iterable

DSP_COMMAND_VALUE = 1
DSP_COMMANDS = {
    "LOAD_PRESET": 1,
    "STANDBY": 4,
    "WAKE": 5,
    "LOCATE": 6,
}


def normalize_pin(value: str | None) -> str:
    return str(value or "").strip()


def build_set_value(item: int, subitem: int, value: int | str, *, channel: int = 0, index: int = 0) -> list[str]:
    return [f"c{channel}", f"i{index}", f"m{item}", f"n{subitem}", f"v{value}", "e"]


def build_enter_pin(pin: str | None) -> list[str]:
    normalized = normalize_pin(pin)
    return build_set_value(5, 5, normalized) if normalized else []


def build_load_preset(preset: int, *, pin: str | None = None, command_value: int = DSP_COMMAND_VALUE) -> list[str]:
    if preset < 1:
        raise ValueError("preset must be >= 1")
    return [
        *build_enter_pin(pin),
        *build_set_value(4, 4, preset),
        *build_set_value(3, 3, command_value, index=DSP_COMMANDS["LOAD_PRESET"]),
    ]


def build_standalone_command(command: str, *, pin: str | None = None, command_value: int = DSP_COMMAND_VALUE) -> list[str]:
    normalized = command.upper().strip()
    if normalized not in {"STANDBY", "WAKE", "LOCATE"}:
        raise ValueError(f"Unsupported DSP command: {command}")
    return [
        *build_enter_pin(pin),
        *build_set_value(3, 3, command_value, index=DSP_COMMANDS[normalized]),
    ]


def read_available(sock: socket.socket, quiet_time: float = 0.15, max_time: float = 0.8) -> str:
    chunks: list[bytes] = []
    end = time.monotonic() + max_time
    last_data = time.monotonic()
    sock.setblocking(False)
    try:
        while time.monotonic() < end:
            try:
                data = sock.recv(4096)
                if data:
                    chunks.append(data)
                    last_data = time.monotonic()
                else:
                    break
            except BlockingIOError:
                if time.monotonic() - last_data >= quiet_time:
                    break
                time.sleep(0.02)
            except socket.timeout:
                break
    finally:
        sock.setblocking(True)
    return b"".join(chunks).decode("utf-8", errors="replace")


def send_telnet_commands(host: str, port: int, commands: Iterable[str], *, timeout: float, delay: float) -> None:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        read_available(sock)
        for command in commands:
            sock.sendall((command + "\r\n").encode("ascii"))
            time.sleep(delay)
            read_available(sock, max_time=max(0.25, delay * 2))
