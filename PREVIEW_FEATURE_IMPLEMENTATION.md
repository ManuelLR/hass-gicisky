# Gicisky Preview Feature Implementation

## Overview

This implementation adds a preview functionality to the Gicisky integration, allowing users to generate and preview images without sending them to the physical device. This feature addresses the request from the GitHub discussion #5 where users wanted to save time by previewing images before committing them to the device.

## Features Implemented

### 1. Dry Run Parameter
- Added `dry_run` parameter to the existing `gicisky.write` service
- When `dry_run: true`, the image is generated but not sent to the device
- Default value is `false` to maintain backward compatibility

### 2. Image Entity
- Created a new image entity that displays the generated images
- Automatically updates when new images are generated
- Provides a visual preview in the Home Assistant UI
- **Integrated with existing device**: Uses same device identifier as sensors to appear as part of the same device

### 3. Event-Driven Updates
- Implemented event system to notify image entities of updates
- Ensures real-time preview updates when images are generated

## Implementation Details

### Files Modified

#### 1. `custom_components/gicisky/services.yaml`
```yaml
dry_run:
  name: Dry Run
  description: "Generate image without sending to device (preview only), default: false"
  required: false
  example: false
  selector:
    boolean:
```

#### 2. `custom_components/gicisky/__init__.py`
- Added `Platform.IMAGE` to the PLATFORMS list
- Modified the `writeservice` function to handle `dry_run` parameter
- Added image entity update logic

Key changes:
```python
# Extract dry_run parameter
dry_run = service.data.get("dry_run", False)

# Generate the image
image = await hass.async_add_executor_job(customimage, entry_id, data.device, service, hass)

# Update image entity if it exists
try:
    image_entity_id = f"image.gicisky_{address.lower()}_image"
    image_entity = hass.states.get(image_entity_id)
    if image_entity:
        # Trigger image entity update
        hass.bus.async_fire(f"{DOMAIN}_image_updated", {"entity_id": image_entity_id})
except Exception as e:
    _LOGGER.debug(f"Could not update image entity: {e}")

# If dry_run is True, skip sending to device
if dry_run:
    _LOGGER.info(f"Dry run mode: Image generated for {address} but not sent to device")
    continue
```

#### 3. `custom_components/gicisky/image.py` (New File)
- Created new image entity class `GiciskyImageEntity`
- Implements event listening for image updates
- Provides device information and image display functionality
- **Device Integration**: Uses same device identifier as sensors (`address.replace(":", "")[-8:]`)
- **Entity Naming**: Entity ID format `image.gicisky_{DEVICE_ID}_image`

#### 4. `custom_components/gicisky/manifest.json`
- Added `"image"` to the dependencies list

## Usage

### Basic Preview Usage
```yaml
service: gicisky.write
data:
  device_id: your_device_id
  payload:
    - type: text
      value: "Hello World!"
      x: 10
      y: 10
      size: 40
  dry_run: true
```

### Advanced Preview with Multiple Elements
```yaml
service: gicisky.write
data:
  device_id: your_device_id
  payload:
    - type: text
      value: "Temperature"
      x: 10
      y: 10
      size: 30
    - type: text
      value: "22°C"
      x: 10
      y: 50
      size: 40
    - type: rectangle
      x_start: 5
      x_end: 395
      y_start: 5
      y_end: 95
      outline: "black"
      width: 2
  background: "white"
  dry_run: true
```

## Benefits

1. **Time Saving**: Users can preview designs without waiting for device communication
2. **Design Iteration**: Quick iteration on layouts and content
3. **Offline Design**: Design images even when devices are not available
4. **Visual Feedback**: Immediate visual feedback in the Home Assistant UI
5. **Backward Compatibility**: Existing functionality remains unchanged

## Technical Implementation

### Image Storage
- Images are saved to `www/gicisky/` directory
- File naming follows the pattern: `gicisky.{device_address}.jpg`
- Images are accessible via web interface

### Event System
- Uses Home Assistant's event bus for communication
- Events are fired when images are updated
- Image entities listen for these events to update their display

### Error Handling
- Graceful handling of missing image entities
- Proper logging for dry run operations
- Fallback behavior when image updates fail

## Testing

The implementation includes comprehensive tests:

1. **Unit Tests**: Validate parameter extraction and logic flow
2. **Integration Tests**: Verify file structure and dependencies
3. **Validation Tests**: Ensure all components work together

Run tests with:
```bash
python3 test_simple_validation.py
```

## Migration Notes

- **No Breaking Changes**: Existing service calls continue to work unchanged
- **Optional Feature**: `dry_run` parameter defaults to `false`
- **Automatic Setup**: Image entities are created automatically for existing devices

## Future Enhancements

Potential improvements for future versions:

1. **Multiple Preview Modes**: Different preview layouts or orientations
2. **Preview History**: Keep multiple versions of generated images
3. **Template Support**: Preview with dynamic data
4. **Export Options**: Save previews in different formats
5. **Comparison View**: Side-by-side comparison of current vs preview

## Troubleshooting

### Common Issues

1. **Image Entity Not Appearing**
   - Check that the device is properly configured
   - Verify that the image platform is loaded
   - Check Home Assistant logs for errors

2. **Preview Not Updating**
   - Ensure the service call includes `dry_run: true`
   - Check that the image file is being generated
   - Verify event system is working

3. **Permission Issues**
   - Ensure Home Assistant has write access to `www/gicisky/` directory
   - Check file permissions on generated images

### Debug Information

Enable debug logging for the gicisky integration:
```yaml
logger:
  custom_components.gicisky: debug
```

## Conclusion

This implementation successfully addresses the user request for preview functionality while maintaining backward compatibility and following Home Assistant best practices. The feature provides immediate value for users who want to iterate on their Gicisky display designs without the overhead of device communication.