# HA Findn LED BLE

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](https://github.com/hirotasoshu/ha-findn-led-ble/blob/main/LICENSE)

![Project Maintenance][maintenance-shield]
[![Ko-fi][ko-fi-badge]][ko-fi]
[![Boosty][boosty-badge]][boosty]

Home assistant integration to integrate with LED BLE devices, controlled via apps developed by `FINDN LTD` ([MR STAR](https://play.google.com/store/apps/details?id=com.findn.mrstar&hl=en-US) and [SYMPHONY LIGHT](https://play.google.com/store/apps/details?id=com.findn.symphonylight&hl=en)).

**This integration will set up the following platforms.**

| Platform | Description                                    |
| -------- | ---------------------------------------------- |
| `light`  | LED BLE device controlled by this integration. |

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `integration_blueprint`.
1. Download _all_ the files from the `custom_components/integration_blueprint/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Integration blueprint"

## Configuration is done in the UI

<!---->

## Contributions are welcome

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[ko-fi]: https://ko-fi.com/hirotasoshu
[ko-fi-badge]: https://img.shields.io/badge/donate-ko--fi-29abe0.svg?style=for-the-badge&logo=ko-fi
[boosty]: https://boosty.to/hirotasoshu
[boosty-badge]: https://img.shields.io/badge/donate-boosty-29abe0.svg?style=for-the-badge&logo=ko-fi
[commits-shield]: https://img.shields.io/github/commit-activity/y/hirotasoshu/ha-findn-led-ble.svg?style=for-the-badge
[commits]: https://github.com/hirotasoshu/ha-findn-led-ble/commits/main
[license-shield]: https://img.shields.io/github/license/hirotasoshu/ha-findn-led-ble.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Maksim%20Zayakin%20%40hirotasoshu-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/hirotasoshu/ha-findn-led-ble.svg?style=for-the-badge
[releases]: https://github.com/hirotasoshu/ha-findn-led-ble/releases
