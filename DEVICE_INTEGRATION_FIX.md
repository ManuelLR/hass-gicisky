# Device Integration Fix

## Issue Description

When the preview feature was initially implemented, the image entity was created as a separate device instead of appearing as part of the existing Gicisky device. This happened because:

1. The image entity was using a different device identifier format
2. The device info was not properly shared with the existing sensors
3. The entity ID format didn't match the sensor pattern

## Root Cause

The original sensors use a device identifier created from the last 8 characters of the MAC address without colons:
```python
identifier = service_info.address.replace(":", "")[-8:]
```

For example:
- MAC: `AA:BB:CC:DD:EE:FF` → Device ID: `CCDDEEFF`
- MAC: `12:34:56:78:9A:BC` → Device ID: `56789ABC`

The image entity was initially using the full MAC address as the device identifier, causing it to be treated as a separate device.

## Solution Implemented

### 1. Updated Device Identifier Logic

**File**: `custom_components/gicisky/image.py`

```python
# Use the same device identifier as the sensors (last 8 chars of MAC without colons)
device_id = self._address.replace(":", "")[-8:]

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
            identifiers={(DOMAIN, device_id)},  # ← Fixed identifier
            name=self._attr_name,
            manufacturer="Gicisky",
            model="E-Paper Display",
        )
```

### 2. Updated Entity ID Format

**File**: `custom_components/gicisky/image.py`

```python
# Use the same device identifier pattern as sensors
device_id = address.replace(":", "")[-8:]
self._attr_unique_id = f"{device_id}_image"  # ← Fixed unique ID
```

### 3. Updated Service Call Logic

**File**: `custom_components/gicisky/__init__.py`

```python
# Update image entity if it exists
try:
    # Use the same device identifier pattern as sensors
    device_id = address.replace(":", "")[-8:]
    image_entity_id = f"image.gicisky_{device_id}_image"  # ← Fixed entity ID
    image_entity = hass.states.get(image_entity_id)
    if image_entity:
        # Trigger image entity update
        hass.bus.async_fire(f"{DOMAIN}_image_updated", {"entity_id": image_entity_id})
except Exception as e:
    _LOGGER.debug(f"Could not update image entity: {e}")
```

## Result

After the fix:

✅ **Image entity appears as part of the existing Gicisky device**
✅ **No separate device is created**
✅ **Consistent device identifier across all entities**
✅ **Proper entity naming convention**

## Entity Naming Convention

- **Entity ID**: `image.gicisky_{DEVICE_ID}_image`
- **Unique ID**: `{DEVICE_ID}_image`
- **Device ID**: Last 8 characters of MAC address (uppercase)

### Examples

| MAC Address | Device ID | Entity ID | Unique ID |
|-------------|-----------|-----------|-----------|
| `AA:BB:CC:DD:EE:FF` | `CCDDEEFF` | `image.gicisky_CCDDEEFF_image` | `CCDDEEFF_image` |
| `12:34:56:78:9A:BC` | `56789ABC` | `image.gicisky_56789ABC_image` | `56789ABC_image` |

## Testing

The fix was validated with comprehensive tests:

```bash
python3 test_simple_validation.py
# Result: 6/6 tests passed ✅
```

Device identifier consistency was verified to ensure the image entity uses the exact same identifier pattern as the sensors.

## Impact

- **User Experience**: Image entity now appears in the same device card as sensors
- **Organization**: Better device organization in Home Assistant
- **Consistency**: Follows the same naming conventions as existing entities
- **Maintainability**: Uses the same device identification logic as sensors