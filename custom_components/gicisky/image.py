import os
from homeassistant.components.image import ImageEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .util import get_image_path

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    # Get the device id and address
    address = entry.unique_id
    entity_id = entry.entry_id
    async_add_entities([GiciskyImageEntity(hass, entity_id, address)])

class GiciskyImageEntity(ImageEntity):
    def __init__(self, hass: HomeAssistant, entity_id: str, address: str):
        super().__init__()
        self.hass = hass
        self._entity_id = entity_id
        self._address = address
        self._attr_name = f"Gicisky Label Preview {address}"
        self._attr_unique_id = f"gicisky_image_{address}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            connections={("bluetooth", address)},
        )

    async def async_image(self):
        path = get_image_path(self.hass, self._entity_id)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()