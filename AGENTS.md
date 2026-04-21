# AGENTS.md

Guidelines for AI agents working in this repository.

## Project Overview

**HA Findn LED BLE** is a Home Assistant custom integration that controls BLE LED strips
manufactured by FINDN LTD (marketed under the MR STAR and SYMPHONY LIGHT apps). It
communicates with devices over Bluetooth LE using a reverse-engineered binary protocol.
The integration is written in Python 3.12+ and follows standard HA custom component
conventions. All integration code lives under `custom_components/findn_led_ble/`.

## Architecture

| File | Responsibility |
|---|---|
| `device_protocol.py` | Binary BLE protocol — constructs raw command bytes sent to the device |
| `device.py` | BLE connection management and command dispatch |
| `coordinator.py` | `DataUpdateCoordinator` — polling loop, state synchronisation |
| `light.py` | `LightEntity` — exposes the device to Home Assistant |
| `entity.py` | Base entity class shared across platforms |
| `config_flow.py` | UI setup flow — device discovery and pairing |
| `const.py` | Shared constants |
| `data.py` | Typed dataclasses for config entry runtime data |
| `services.yaml` | Custom service definitions (e.g. `set_effect`) |
| `strings.json` | UI strings for config flow and services |
| `manifest.json` | Integration metadata required by Home Assistant |

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Check for lint errors
ruff check custom_components/

# Auto-fix lint errors
ruff check --fix custom_components/

# Format code
ruff format custom_components/
```

Always run `ruff check` and `ruff format` before committing. CI will fail on lint errors.

## Code Style

- Python 3.12+ — use modern built-in generics (`list[str]`, `dict[str, int]`, etc.)
- Type annotations are required on all function signatures
- All public classes and methods must have docstrings
- Linter is `ruff` with `select = ["ALL"]`; see `pyproject.toml` for the ignored rules
- Follow HA integration patterns: `DataUpdateCoordinator`, `ConfigFlow`, `CoordinatorEntity`

## Protected Files

### `custom_components/findn_led_ble/device_protocol.py` — ⚠️ DO NOT MODIFY

This file contains the reverse-engineered binary BLE protocol. A wrong byte value
silently breaks all device communication with no obvious error. **Do not change this
file unless the task explicitly asks for protocol changes or refactoring.**

### `custom_components/findn_led_ble/manifest.json` — ⚠️ HANDLE WITH CARE

Do not change `domain`, `version`, or the `bluetooth` service UUID without an explicit
instruction to do so. These fields affect device discovery and HA integration loading.
