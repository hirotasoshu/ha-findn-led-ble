# HA Findn LED BLE

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](https://github.com/hirotasoshu/ha-findn-led-ble/blob/main/LICENSE)

![Project Maintenance][maintenance-shield]
[![Ko-fi][ko-fi-badge]][ko-fi]
[![Boosty][boosty-badge]][boosty]

Home assistant integration to integrate with LED BLE devices, controlled via apps developed by `FINDN LTD` ([MR STAR](https://play.google.com/store/apps/details?id=com.findn.mrstar&hl=en-US) and [SYMPHONY LIGHT](https://play.google.com/store/apps/details?id=com.findn.symphonylight&hl=en)).

Example of compatible device: [LED strip on Ozon](https://ozon.ru/t/sSplWg5)

**This integration will set up the following platforms.**

| Platform | Description                                    |
| -------- | ---------------------------------------------- |
| `light`  | LED BLE device controlled by this integration. |

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
1. Click on "Integrations"
1. Click the three dots in the top right corner and select "Custom repositories"
1. Add `https://github.com/hirotasoshu/ha-findn-led-ble` as repository, select "Integration" as category
1. Click "Add"
1. Find "Findn LED BLE" in the list and click "Download"
1. Restart Home Assistant
1. In the HA UI go to "Settings" -> "Devices & Services" click "+" and search for "Findn LED BLE"

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `findn_led_ble`.
1. Download _all_ the files from the `custom_components/findn_led_ble/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Settings" -> "Devices & Services" click "+" and search for "Findn LED BLE"

## Features

This integration supports the following features:

- **Turn on/off** - Control the power state of your LED strip
- **Brightness control** - Adjust brightness from 1 to 255
- **RGB color control** - Set any RGB color
- **HS color control** - Set color using hue and saturation
- **58 built-in effects** - Including colorful animations, running water effects, tailing effects, and more

### Available Effects

The integration includes 58 pre-configured effects such as:

- Automatic loop, Symphony, Colorful energy
- 7 colors effects (strobe, gradient, opening-closing, etc.)
- Running water effects (7 colors, red-green, blue-purple, etc.)
- Tailing effects (7 colors, red, green, blue, etc.)
- Running effects (all colors)
- And many more!

### Using the `set_effect` Service

You can set effects with optional direction control using the `findn_led_ble.set_effect` service.

**Example service call:**

```yaml
service: findn_led_ble.set_effect
target:
  entity_id: light.led_strip
data:
  effect: "7 colors flowing water"
  direction: forward # optional: forward or backward
```

**Turn off effect:**

```yaml
service: findn_led_ble.set_effect
target:
  entity_id: light.led_strip
data:
  effect: "off"
```

## Contributions are welcome

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[ko-fi]: https://ko-fi.com/hirotasoshu
[ko-fi-badge]: https://img.shields.io/badge/donate-ko--fi-29abe0.svg?style=for-the-badge&logo=ko-fi
[boosty]: https://boosty.to/hirotasoshu
[boosty-badge]: https://img.shields.io/badge/donate-boosty-29abe0.svg?style=for-the-badge&logo=boosty
[commits-shield]: https://img.shields.io/github/commit-activity/y/hirotasoshu/ha-findn-led-ble.svg?style=for-the-badge
[commits]: https://github.com/hirotasoshu/ha-findn-led-ble/commits/main
[license-shield]: https://img.shields.io/github/license/hirotasoshu/ha-findn-led-ble.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Maksim%20Zayakin%20%40hirotasoshu-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/hirotasoshu/ha-findn-led-ble.svg?style=for-the-badge
[releases]: https://github.com/hirotasoshu/ha-findn-led-ble/releases
