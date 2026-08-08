"""Tests for the Findn LED BLE config flow."""

from unittest.mock import AsyncMock, patch

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.findn_led_ble.const import DOMAIN

TEST_ADDRESS = "AA:BB:CC:DD:EE:FF"
TEST_NAME = "GATT--DEMO"
FLOW_SOURCE = "source"
RESULT_TYPE = "type"
ADVERTISEMENT_TIME = float("0")


def _service_info(name: str = TEST_NAME) -> BluetoothServiceInfoBleak:
    """Create Bluetooth service info for config-flow tests."""
    device = BLEDevice(TEST_ADDRESS, name, {})
    advertisement = AdvertisementData(name, {}, {}, [], None, -60, ())
    return BluetoothServiceInfoBleak.from_device_and_advertisement_data(
        device,
        advertisement,
        "local",
        ADVERTISEMENT_TIME,
        connectable=True,
    )


async def test_user_step_shows_discovered_devices(
    hass: object,
    enable_custom_integrations: None,  # noqa: ARG001
) -> None:
    """Test user step form includes discovered Findn devices."""
    with patch(
        "custom_components.findn_led_ble.config_flow.async_discovered_service_info",
        return_value=[_service_info(), _service_info("Other")],
    ):
        flow_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={FLOW_SOURCE: config_entries.SOURCE_USER},
        )

    assert flow_result[RESULT_TYPE] is FlowResultType.FORM
    assert flow_result["step_id"] == "user"
    assert flow_result["errors"] == {}


async def test_user_step_creates_entry_after_identify(
    hass: object,
    enable_custom_integrations: None,  # noqa: ARG001
) -> None:
    """Test user step creates an entry after validating the BLE device."""
    service_info = _service_info()
    mock_device = AsyncMock()

    with patch(
        "custom_components.findn_led_ble.config_flow.async_discovered_service_info",
        return_value=[service_info],
    ):
        flow_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={FLOW_SOURCE: config_entries.SOURCE_USER},
        )

    with (
        patch(
            "custom_components.findn_led_ble.config_flow.FindnLedDevice",
            return_value=mock_device,
        ),
        patch(
            "custom_components.findn_led_ble.async_setup_entry",
            return_value=True,
        ) as setup_entry,
    ):
        flow_result = await hass.config_entries.flow.async_configure(
            flow_result["flow_id"],
            {CONF_ADDRESS: TEST_ADDRESS},
        )
        await hass.async_block_till_done()

    assert flow_result[RESULT_TYPE] is FlowResultType.CREATE_ENTRY
    assert flow_result["title"] == TEST_NAME
    assert flow_result["data"] == {CONF_ADDRESS: TEST_ADDRESS}
    mock_device.identify.assert_awaited_once()
    mock_device.stop.assert_awaited_once()
    assert len(setup_entry.mock_calls) == 1


async def test_user_step_shows_identify_error(
    hass: object,
    enable_custom_integrations: None,  # noqa: ARG001
) -> None:
    """Test user step reports validation errors."""
    service_info = _service_info()
    mock_device = AsyncMock()
    mock_device.identify.side_effect = RuntimeError

    with patch(
        "custom_components.findn_led_ble.config_flow.async_discovered_service_info",
        return_value=[service_info],
    ):
        flow_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={FLOW_SOURCE: config_entries.SOURCE_USER},
        )

    with patch(
        "custom_components.findn_led_ble.config_flow.FindnLedDevice",
        return_value=mock_device,
    ):
        flow_result = await hass.config_entries.flow.async_configure(
            flow_result["flow_id"],
            {CONF_ADDRESS: TEST_ADDRESS},
        )

    assert flow_result[RESULT_TYPE] is FlowResultType.FORM
    assert flow_result["step_id"] == "user"
    assert flow_result["errors"] == {"base": "unknown"}
    mock_device.stop.assert_awaited_once()


async def test_bluetooth_step_for_existing_entry_aborts(
    hass: object,
    enable_custom_integrations: None,  # noqa: ARG001
) -> None:
    """Test bluetooth discovery aborts for configured devices."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ADDRESS: TEST_ADDRESS},
        unique_id=TEST_ADDRESS,
    ).add_to_hass(hass)

    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={FLOW_SOURCE: config_entries.SOURCE_BLUETOOTH},
        data=_service_info(),
    )

    assert flow_result[RESULT_TYPE] is FlowResultType.ABORT
    assert flow_result["reason"] == "already_configured"
