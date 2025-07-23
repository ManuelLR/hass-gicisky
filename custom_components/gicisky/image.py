"""The Gicisky Image integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import CONF_NAME
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info

from .const import DOMAIN
from .util import get_image_path
from .types import GiciskyConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GiciskyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gicisky Image from a config entry."""
    address = config_entry.unique_id
    name = config_entry.data.get(CONF_NAME, f"Gicisky {address}")
    
    # Get device info from the coordinator
    coordinator = config_entry.runtime_data
    device_info = None
    
    # Try to get device info from the coordinator's device data
    if hasattr(coordinator, 'device_data') and coordinator.device_data:
        if hasattr(coordinator.device_data, 'device_info') and coordinator.device_data.device_info:
            device_info = coordinator.device_data.device_info
    
    # Create image entity for this device
    image_entity = GiciskyImageEntity(
        hass=hass,
        config_entry=config_entry,
        address=address,
        name=name,
        device_info=device_info,
    )
    
    async_add_entities([image_entity])


class GiciskyImageEntity(ImageEntity):
    """Representation of a Gicisky Image entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: GiciskyConfigEntry,
        address: str,
        name: str,
        device_info=None,
    ) -> None:
        """Initialize the Gicisky Image entity."""
        super().__init__(hass)
        self._config_entry = config_entry
        self._address = address
        self._attr_name = f"{name} Image"
        # Use the same device identifier pattern as sensors
        device_id = address.replace(":", "")[-8:]
        self._attr_unique_id = f"{device_id}_image"
        self._image_path = get_image_path(hass, address)
        self._attr_image_last_updated = None
        self._device_info = device_info
        
        # Listen for image update events
        self._unsub_update = hass.bus.async_listen(
            f"{DOMAIN}_image_updated",
            self._handle_image_update
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        # Use the same device identifier as the sensors (last 8 chars of MAC without colons)
        device_id = self._address.replace(":", "")[-8:]
        
        if self._device_info:
            # Use the same device info as the original sensors
            return sensor_device_info_to_hass_device_info(self._device_info)
        else:
            # Fallback device info with correct identifier
            return DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                name=self._attr_name,
                manufacturer="Gicisky",
                model="E-Paper Display",
            )

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        try:
            with open(self._image_path, "rb") as file:
                return file.read()
        except FileNotFoundError:
            _LOGGER.debug("No image file found for %s", self._address)
            return None
        except Exception as err:
            _LOGGER.error("Error reading image for %s: %s", self._address, err)
            return None

    @callback
    def _handle_image_update(self, event) -> None:
        """Handle image update events."""
        if event.data.get("entity_id") == self.entity_id:
            self._attr_image_last_updated = datetime.now()
            self.async_write_ha_state()

    def update_image_timestamp(self) -> None:
        """Update the image timestamp when a new image is generated."""
        self._attr_image_last_updated = datetime.now()
        self.async_write_ha_state()
        
    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        if self._unsub_update:
            self._unsub_update()