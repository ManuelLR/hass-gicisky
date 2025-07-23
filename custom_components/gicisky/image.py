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

from .const import DOMAIN
from .util import get_image_path

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gicisky Image from a config entry."""
    address = config_entry.unique_id
    name = config_entry.data.get(CONF_NAME, f"Gicisky {address}")
    
    # Create image entity for this device
    image_entity = GiciskyImageEntity(
        hass=hass,
        config_entry=config_entry,
        address=address,
        name=name,
    )
    
    async_add_entities([image_entity])


class GiciskyImageEntity(ImageEntity):
    """Representation of a Gicisky Image entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        address: str,
        name: str,
    ) -> None:
        """Initialize the Gicisky Image entity."""
        super().__init__(hass)
        self._config_entry = config_entry
        self._address = address
        self._attr_name = f"{name} Image"
        self._attr_unique_id = f"{address}_image"
        self._image_path = get_image_path(hass, address)
        self._attr_image_last_updated = None
        
        # Listen for image update events
        self._unsub_update = hass.bus.async_listen(
            f"{DOMAIN}_image_updated",
            self._handle_image_update
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._address)},
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