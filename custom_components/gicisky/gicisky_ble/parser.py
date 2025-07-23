from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone
from bleak.backends.device import BLEDevice
from bluetooth_sensor_state_data import BluetoothData
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from home_assistant_bluetooth import BluetoothServiceInfoBleak
from sensor_state_data import (
    SensorLibrary,
    BinarySensorDeviceClass,
    SensorDeviceInfo,
    SensorUpdate
)

from .devices import DEVICE_TYPES, DeviceEntry

_LOGGER = logging.getLogger(__name__)

def to_mac(addr: bytes) -> str:
    """Return formatted MAC address."""
    return ":".join(f"{i:02X}" for i in addr)

class GiciskyBluetoothDeviceData(BluetoothData):
    """Data for BTHome Bluetooth devices."""

    def __init__(self) -> None:
        super().__init__()

        # The last service_info we saw that had a payload
        self.last_service_info: BluetoothServiceInfoBleak | None = None

        self.device: DeviceEntry | None = None
        self.last_updated: datetime | None = None
        self.is_connected: bool = False
        self.last_event_sequence: int = 0

    def supported(self, data: BluetoothServiceInfoBleak) -> bool:
        if not super().supported(data):
            return False
        return True

    def _start_update(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Update from BLE advertisement data."""
        #_LOGGER.info("Parsing Gicisky BLE advertisement data: %s", service_info)
        if 0x5053 in service_info.manufacturer_data:
            #_LOGGER.info("BLE Info: %s", service_info)
            data = service_info.manufacturer_data[0x5053]
            for uuid in service_info.service_uuids:
                #_LOGGER.info("Gicisky %s BLE UUID %s data: %s", service_info.name, uuid, data.hex())
                if self._parse_gicisky(service_info, data):
                    self.last_service_info = service_info
        return None

    def _parse_gicisky(
        self, service_info: BluetoothServiceInfoBleak, data: bytes
    ) -> bool:
        """Parser for Gicisky sensors"""
        # Handle device info packets (5 bytes)
        if len(data) == 5:
            return self._parse_device_info(service_info, data)
        
        # Handle event packets (3-4 bytes)
        elif len(data) in (3, 4):
            return self._parse_event_data(service_info, data)
        
        return False

    def _parse_device_info(
        self, service_info: BluetoothServiceInfoBleak, data: bytes
    ) -> bool:
        """Parse device information packet."""
        # determine the device type
        device_id = data[0]
        bettery = data[1]
        firmware = (data[2] << 8) + data[3]
        hardware = (data[0] << 8) + data[4]
        try:
            device = DEVICE_TYPES[device_id]
        except KeyError:
            _LOGGER.error("Unknown Gicisky device found. Data: %s", data.hex())
            return False

        self.device = device
        self.device_id = device_id
        identifier = service_info.address.replace(":", "")[-8:]
        self.set_title(f"{identifier} ({device.model})")
        self.set_device_name(f"{device.manufacturer} {identifier}")
        self.set_device_type(f"{device.model} {device.width}x{device.height}")
        self.set_device_manufacturer(device.manufacturer)
        self.set_device_sw_version(f"0x{firmware:04X}")
        self.set_device_hw_version(f"0x{hardware:04X}")

        volt = bettery / 10
        min = device.min_voltage
        max = device.max_voltage
        batt = (volt - min) * 100 / (max - min)
        self.update_predefined_sensor(SensorLibrary.BATTERY__PERCENTAGE, round(batt, 1))
        self.update_predefined_sensor(
            SensorLibrary.VOLTAGE__ELECTRIC_POTENTIAL_VOLT, round(volt, 1)
        )
        return True

    def _parse_event_data(
        self, service_info: BluetoothServiceInfoBleak, data: bytes
    ) -> bool:
        """Parse button/dimmer event packets."""
        if len(data) < 3:
            return False

        # Event packet format:
        # Byte 0: Event type (0x01 = button, 0x02 = dimmer)
        # Byte 1: Event subtype/sequence
        # Byte 2: Event data (button press type, dimmer direction, etc.)
        # Byte 3: Optional additional data
        
        event_type = data[0]
        event_sequence = data[1]
        event_data = data[2]
        
        # Check if this is a new event (sequence number should increment)
        if event_sequence <= self.last_event_sequence:
            return False
        
        self.last_event_sequence = event_sequence
        
        # Parse button events
        if event_type == 0x01:
            return self._parse_button_event(service_info, event_data, event_sequence)
        
        # Parse dimmer events
        elif event_type == 0x02:
            return self._parse_dimmer_event(service_info, event_data, event_sequence)
        
        return False

    def _parse_button_event(
        self, service_info: BluetoothServiceInfoBleak, event_data: int, sequence: int
    ) -> bool:
        """Parse button press events."""
        # Button event data mapping:
        # 0x01 = single press
        # 0x02 = double press
        # 0x03 = triple press
        # 0x04 = long press
        # 0x05 = long double press
        # 0x06 = long triple press
        # 0x07 = hold press
        
        button_event_map = {
            0x01: "press",
            0x02: "double_press", 
            0x03: "triple_press",
            0x04: "long_press",
            0x05: "long_double_press",
            0x06: "long_triple_press",
            0x07: "hold_press",
        }
        
        event_type = button_event_map.get(event_data)
        if not event_type:
            _LOGGER.warning("Unknown button event data: 0x%02X", event_data)
            return False
        
        # Add button event
        self.add_event(
            "button",
            event_type,
            {
                "sequence": sequence,
                "raw_data": event_data,
            }
        )
        
        _LOGGER.debug("Button event: %s (sequence: %d)", event_type, sequence)
        return True

    def _parse_dimmer_event(
        self, service_info: BluetoothServiceInfoBleak, event_data: int, sequence: int
    ) -> bool:
        """Parse dimmer rotation events."""
        # Dimmer event data mapping:
        # 0x01 = rotate left
        # 0x02 = rotate right
        
        dimmer_event_map = {
            0x01: "rotate_left",
            0x02: "rotate_right",
        }
        
        event_type = dimmer_event_map.get(event_data)
        if not event_type:
            _LOGGER.warning("Unknown dimmer event data: 0x%02X", event_data)
            return False
        
        # Add dimmer event
        self.add_event(
            "dimmer",
            event_type,
            {
                "sequence": sequence,
                "raw_data": event_data,
            }
        )
        
        _LOGGER.debug("Dimmer event: %s (sequence: %d)", event_type, sequence)
        return True
    
    async def last_update(self):
        now_utc: datetime = datetime.now(timezone.utc)
        self.last_updated = now_utc

    async def set_connected(self, connected: bool):
        self.is_connected = connected
    
    async def async_poll(self) -> SensorUpdate:
        self._events_updates.clear()
        self.update_predefined_sensor(
            SensorLibrary.TIMESTAMP__NONE, self.last_updated, None, "Last Update Time"
        )
        self.update_predefined_binary_sensor(
            BinarySensorDeviceClass.CONNECTIVITY, self.is_connected
        )
        return self._finish_update()