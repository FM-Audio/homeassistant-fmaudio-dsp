# FM-Audio DSP Home Assistant Integration

Custom Home Assistant integration to control FM-Audio DSP devices locally via Telnet.

It is designed for broad customer use:

- direct Home Assistant buttons for presets and utility commands
- Home Assistant services for automations, scripts, dashboards and voice routines
- optional SofaBaton X2 MQTT button mapping, so X2 buttons can trigger DSP commands through Home Assistant
- no external bridge server required

## Features

- Config flow in Home Assistant UI
- Configurable DSP host, Telnet port, optional PIN and preset count
- Preset buttons: `Preset 1` ... `Preset N` with N from 2 to 100
- Utility buttons:
  - `Standby`
  - `Wake`
  - `Locate`
- Services:
  - `fm_audio_dsp.send_preset`
  - `fm_audio_dsp.send_command`
- Optional SofaBaton X2 MQTT bridge:
  - subscribe to an X2 MQTT topic
  - filter by `device_id`
  - map `key_id` values to `PRESET_1`, `STANDBY`, etc.

## Recommended customer architecture

```text
SofaBaton X2 button
→ Home Assistant MQTT payload
→ FM-Audio DSP integration key map
→ DSP Telnet command
```

This reaches more customers than a Remote-3-only solution because Home Assistant can also be used from dashboards, automations, scenes, voice assistants and other remotes.

## Manual install

Copy this folder into Home Assistant:

```text
/config/custom_components/fm_audio_dsp
```

Restart Home Assistant, then add:

```text
Settings → Devices & services → Add integration → FM-Audio DSP
```

## SofaBaton X2 mapping example

If the X2 sends JSON payloads like this on MQTT:

```json
{"device_id": 3, "key_id": 9}
```

Use:

- Topic: `80F1B29866A8/up`
- Device ID: `3`
- Key map JSON:

```json
{"9":"PRESET_1","10":"PRESET_2","11":"PRESET_3","12":"PRESET_4","13":"STANDBY","14":"WAKE","15":"LOCATE"}
```

## Services

Load preset 1:

```yaml
service: fm_audio_dsp.send_preset
data:
  preset: 1
```

Standby:

```yaml
service: fm_audio_dsp.send_command
data:
  command: STANDBY
```

Wake:

```yaml
service: fm_audio_dsp.send_command
data:
  command: WAKE
```

Locate:

```yaml
service: fm_audio_dsp.send_command
data:
  command: LOCATE
```

## Telnet commands

Preset `N`:

```text
c0
i0
m4
n4
vN
e
c0
i1
m3
n3
v1
e
```

Utility commands use item `3`, sub-item `3`, value `1` with indexes:

- `i4` = standby
- `i5` = wake / exit standby
- `i6` = locate / wink

Optional PIN is sent first using item `5`, sub-item `5`.
