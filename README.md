# FM-Audio DSP Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.6%2B-blue.svg)
![Local control](https://img.shields.io/badge/Control-local%20Telnet-green.svg)

Control FM-Audio DSP devices locally from Home Assistant.

The integration exposes preset and utility commands as Home Assistant buttons and services. It also includes optional SofaBaton X2 MQTT key mapping, so X2 buttons can trigger DSP presets, standby, wake and locate through Home Assistant.

## Why Home Assistant?

Recommended customer architecture:

```text
SofaBaton X2 button
→ Home Assistant / MQTT
→ FM-Audio DSP integration
→ DSP Telnet command
```

This makes the DSP available not only to SofaBaton X2 users, but also to Home Assistant dashboards, automations, scripts, scenes, voice assistants and other remotes.

## Features

- Home Assistant UI setup via config flow
- Local DSP control over Telnet
- Configurable DSP host(s), Telnet port, optional PIN and preset count
- Multiple DSP IP addresses can be entered comma-separated or one per line
- Preset buttons: `Preset 1` ... `Preset N` with N from 2 to 100
- With multiple hosts in one config entry, Home Assistant exposes `All ...` buttons plus per-DSP host buttons
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
  - map `key_id` values to `PRESET_1`, `STANDBY`, `WAKE`, `LOCATE`, etc.

## Requirements

- Home Assistant 2024.6 or newer
- HACS for easiest installation, or manual custom integration install
- DSP reachable from Home Assistant over the local network
- Telnet enabled on the DSP
- Optional: Home Assistant MQTT integration when using SofaBaton X2 MQTT mapping

## HACS installation

Until the integration is added to the default HACS repository list, install it as a custom repository:

1. Open Home Assistant.
2. Go to **HACS → Integrations**.
3. Open the menu in the top-right corner.
4. Select **Custom repositories**.
5. Add this repository URL:

   ```text
   https://github.com/FM-Audio/homeassistant-fmaudio-dsp
   ```

6. Set category to **Integration**.
7. Click **Add**.
8. Search for **FM-Audio DSP** in HACS and install it.
9. Restart Home Assistant.
10. Go to **Settings → Devices & services → Add integration → FM-Audio DSP**.

## Manual installation

Copy the integration folder into Home Assistant:

```text
/config/custom_components/fm_audio_dsp
```

The folder must contain files like:

```text
/config/custom_components/fm_audio_dsp/manifest.json
/config/custom_components/fm_audio_dsp/__init__.py
/config/custom_components/fm_audio_dsp/protocol.py
```

Restart Home Assistant, then add:

```text
Settings → Devices & services → Add integration → FM-Audio DSP
```

## Basic configuration

Recommended first setup values:

- DSP host(s): one or more IP addresses of the DSPs, for example `192.168.178.192`; separate multiple hosts with commas or new lines
- DSP Telnet port: `23`
- Preset count: `4` for a simple customer layout, or up to `100`
- DSP PIN: leave empty unless the DSP requires a PIN
- Command value: `1`
- Timeout: `5`
- Delay: `0.18`

## SofaBaton X2 MQTT mapping

If the SofaBaton X2 integration publishes JSON payloads like:

```json
{"device_id": 3, "key_id": 9}
```

then configure the optional X2 fields like this:

- X2 MQTT topic: your X2 MQTT topic, for example `80F1B29866A8/up`
- X2 device ID filter: `3`
- X2 key map JSON:

```json
{
  "9": "PRESET_1",
  "10": "PRESET_2",
  "11": "PRESET_3",
  "12": "PRESET_4",
  "13": "STANDBY",
  "14": "WAKE",
  "15": "LOCATE"
}
```

Only `key_id` values listed in the map are executed. If a device ID filter is configured, payloads from other X2 devices are ignored.

## Services

### Load a preset

```yaml
service: fm_audio_dsp.send_preset
data:
  preset: 1
```

### Send standby

```yaml
service: fm_audio_dsp.send_command
data:
  command: STANDBY
```

### Send wake

```yaml
service: fm_audio_dsp.send_command
data:
  command: WAKE
```

### Send locate

```yaml
service: fm_audio_dsp.send_command
data:
  command: LOCATE
```

### Target a specific DSP entry or host

If multiple DSP devices are configured as separate entries, pass the Home Assistant config entry ID:

```yaml
service: fm_audio_dsp.send_preset
data:
  entry_id: "01HZYEXAMPLE"
  preset: 2
```

If multiple DSP hosts are configured inside one entry, pass `target_host` to address only one of them:

```yaml
service: fm_audio_dsp.send_command
data:
  entry_id: "01HZYEXAMPLE"
  target_host: "192.168.178.193"
  command: PRESET_1
```

If `target_host` is omitted, every DSP host in the selected entry receives the command. If `entry_id` is also omitted, all configured FM-Audio DSP entries receive the command.

## Events for debugging

After successful commands, the integration fires Home Assistant events:

- `fm_audio_dsp_command_sent`
- `fm_audio_dsp_x2_command`

These can be inspected in **Developer Tools → Events**.

## DSP Telnet command sequences

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

Utility commands use item `3`, sub-item `3`, value `1` with these indexes:

- `i4` = standby
- `i5` = wake / exit standby
- `i6` = locate / wink

Optional PIN is sent before the command using item `5`, sub-item `5`.

## Troubleshooting

- Confirm that Telnet is enabled on the DSP.
- Confirm that Home Assistant can reach the DSP IP address and port `23`.
- If SofaBaton X2 mapping does not trigger, first verify that MQTT payloads arrive in Home Assistant.
- Check Home Assistant logs for `fm_audio_dsp` messages.
- Use **Developer Tools → Services** to test `fm_audio_dsp.send_preset` independently of the X2.

## Development verification

Local checks used for this release:

```bash
python3 -m py_compile custom_components/fm_audio_dsp/*.py
python3 tests/test_protocol.py
```

The protocol helper tests verify preset, optional PIN, standby, wake and locate command sequences.
