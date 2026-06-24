import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "fm_audio_dsp"))

from protocol import build_load_preset, build_standalone_command


def test_build_load_preset():
    assert build_load_preset(4) == [
        "c0", "i0", "m4", "n4", "v4", "e",
        "c0", "i1", "m3", "n3", "v1", "e",
    ]


def test_build_pin_then_preset():
    assert build_load_preset(1, pin="1234")[:6] == ["c0", "i0", "m5", "n5", "v1234", "e"]


def test_utility_commands():
    assert build_standalone_command("STANDBY") == ["c0", "i4", "m3", "n3", "v1", "e"]
    assert build_standalone_command("WAKE") == ["c0", "i5", "m3", "n3", "v1", "e"]
    assert build_standalone_command("LOCATE") == ["c0", "i6", "m3", "n3", "v1", "e"]


if __name__ == "__main__":
    test_build_load_preset()
    test_build_pin_then_preset()
    test_utility_commands()
    print("protocol tests ok")
