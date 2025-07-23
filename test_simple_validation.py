#!/usr/bin/env python3
"""
Simple validation test for Gicisky preview functionality.
This test validates the implementation without requiring Home Assistant dependencies.
"""

import os
import json
import re

def test_services_yaml_dry_run():
    """Test that dry_run parameter is properly added to services.yaml."""
    
    try:
        with open("custom_components/gicisky/services.yaml", "r") as f:
            content = f.read()
        
        # Check for dry_run field
        assert "dry_run:" in content, "dry_run field not found"
        assert "Dry Run" in content, "Dry Run name not found"
        assert "Generate image without sending to device" in content, "Dry run description not found"
        assert "boolean:" in content, "boolean selector not found for dry_run"
        
        print("✓ services.yaml dry_run parameter validation passed")
        return True
        
    except FileNotFoundError:
        print("⚠ services.yaml file not found")
        return False
    except Exception as e:
        print(f"⚠ services.yaml validation failed: {e}")
        return False

def test_init_py_platforms():
    """Test that IMAGE platform is added to PLATFORMS list."""
    
    try:
        with open("custom_components/gicisky/__init__.py", "r") as f:
            content = f.read()
        
        # Check for IMAGE platform
        assert "Platform.IMAGE" in content, "Platform.IMAGE not found in PLATFORMS"
        
        # Check for dry_run parameter extraction
        assert "dry_run = service.data.get(\"dry_run\", False)" in content, "dry_run parameter extraction not found"
        
        # Check for dry_run logic
        assert "if dry_run:" in content, "dry_run conditional logic not found"
        assert "continue" in content, "continue statement for dry_run not found"
        
        print("✓ __init__.py platform and dry_run logic validation passed")
        return True
        
    except FileNotFoundError:
        print("⚠ __init__.py file not found")
        return False
    except Exception as e:
        print(f"⚠ __init__.py validation failed: {e}")
        return False

def test_image_entity_file():
    """Test that image entity file exists and has correct structure."""
    
    try:
        with open("custom_components/gicisky/image.py", "r") as f:
            content = f.read()
        
        # Check for required imports
        assert "from homeassistant.components.image import ImageEntity" in content, "ImageEntity import not found"
        assert "from homeassistant.core import HomeAssistant, callback" in content, "callback import not found"
        
        # Check for class definition
        assert "class GiciskyImageEntity(ImageEntity):" in content, "GiciskyImageEntity class not found"
        
        # Check for event handling
        assert "_handle_image_update" in content, "Image update handler not found"
        assert "async_listen" in content, "Event listener not found"
        
        print("✓ image.py entity structure validation passed")
        return True
        
    except FileNotFoundError:
        print("⚠ image.py file not found")
        return False
    except Exception as e:
        print(f"⚠ image.py validation failed: {e}")
        return False

def test_manifest_dependencies():
    """Test that image dependency is added to manifest.json."""
    
    try:
        with open("custom_components/gicisky/manifest.json", "r") as f:
            manifest = json.load(f)
        
        dependencies = manifest.get("dependencies", [])
        assert "image" in dependencies, "image dependency not found in manifest.json"
        
        print("✓ manifest.json dependencies validation passed")
        return True
        
    except FileNotFoundError:
        print("⚠ manifest.json file not found")
        return False
    except json.JSONDecodeError:
        print("⚠ manifest.json is not valid JSON")
        return False
    except Exception as e:
        print(f"⚠ manifest.json validation failed: {e}")
        return False

def test_service_logic():
    """Test that the service logic handles dry_run correctly."""
    
    try:
        with open("custom_components/gicisky/__init__.py", "r") as f:
            content = f.read()
        
        # Check for the complete service logic flow
        lines = content.split('\n')
        
        # Find the writeservice function
        service_start = None
        for i, line in enumerate(lines):
            if "async def writeservice" in line:
                service_start = i
                break
        
        if service_start is None:
            print("⚠ writeservice function not found")
            return False
        
        # Check for key logic elements
        service_section = '\n'.join(lines[service_start:service_start+50])
        
        # Check for dry_run extraction
        assert "dry_run = service.data.get(\"dry_run\", False)" in service_section, "dry_run extraction not found"
        
        # Check for image generation
        assert "customimage" in service_section, "customimage call not found"
        
        # Check for dry_run conditional
        assert "if dry_run:" in service_section, "dry_run conditional not found"
        
        # Check for continue statement
        assert "continue" in service_section, "continue statement not found"
        
        print("✓ Service logic validation passed")
        return True
        
    except Exception as e:
        print(f"⚠ Service logic validation failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    
    required_files = [
        "custom_components/gicisky/services.yaml",
        "custom_components/gicisky/__init__.py",
        "custom_components/gicisky/image.py",
        "custom_components/gicisky/manifest.json",
        "custom_components/gicisky/util.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠ Missing required files: {missing_files}")
        return False
    else:
        print("✓ All required files exist")
        return True

def main():
    """Run all validation tests."""
    print("Running Gicisky preview feature validation tests...\n")
    
    tests = [
        test_file_structure,
        test_services_yaml_dry_run,
        test_init_py_platforms,
        test_image_entity_file,
        test_manifest_dependencies,
        test_service_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All validation tests passed!")
        print("\n🎉 Implementation Summary:")
        print("1. ✅ Added 'dry_run' parameter to the write service")
        print("2. ✅ Created image entity to display generated images")
        print("3. ✅ Modified service to skip device communication when dry_run=True")
        print("4. ✅ Added proper event handling for image updates")
        print("5. ✅ Updated dependencies and platform configuration")
        print("\n📖 Usage Instructions:")
        print("- Call the gicisky.write service with dry_run: true to preview")
        print("- The image will be generated and saved to www/gicisky/")
        print("- An image entity will display the generated image")
        print("- No data will be sent to the physical device")
        print("\n🔧 Example service call:")
        print("""
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
        """)
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the implementation.")

if __name__ == "__main__":
    main()