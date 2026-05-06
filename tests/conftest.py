"""Pytest configuration for Findn LED BLE tests."""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).parents[1]

sys.path.insert(0, str(ROOT))

custom_components = types.ModuleType("custom_components")
custom_components.__path__ = [str(ROOT / "custom_components")]  # type: ignore[attr-defined]
findn_led_ble = types.ModuleType("custom_components.findn_led_ble")
findn_led_ble.__path__ = [str(ROOT / "custom_components/findn_led_ble")]  # type: ignore[attr-defined]
custom_components.findn_led_ble = findn_led_ble  # type: ignore[attr-defined]

sys.modules.setdefault("custom_components", custom_components)
sys.modules.setdefault("custom_components.findn_led_ble", findn_led_ble)
