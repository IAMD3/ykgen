#!/usr/bin/env python3
"""
Test script for config functionality.

This script tests normal mode for API key management.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kgen.config.config import Config


def test_normal_mode():
    """Test normal mode configuration."""
    print("=" * 50)
    print("🔍 Testing Normal Mode")
    print("=" * 50)
    
    # Temporarily set mode to normal
    original_mode = os.environ.get("MODE")
    os.environ["MODE"] = "normal"
    
    # Create a new config instance
    config = Config()
    
    print(f"Mode: {config.MODE}")
    print(f"SiliconFlow API Key: {'✅ Set' if config.SILICONFLOW_VIDEO_KEY else '❌ Not Set'}")
    print(f"Qwen API Key: {'✅ Set' if config.LLM_API_KEY else '❌ Not Set'}")
    
    # Test get_api_key method
    siliconflow_key = config.get_api_key("siliconflow")
    print(f"Retrieved SiliconFlow key: {'✅ Available' if siliconflow_key else '❌ None'}")
    
    # Show key status
    print("\nKey Status:")
    print(config.show_key_status())
    
    # Restore original mode
    if original_mode:
        os.environ["MODE"] = original_mode
    else:
        os.environ.pop("MODE", None)


# Agent mode has been removed from the system


def test_validation():
    """Test key validation."""
    print("\n" + "=" * 50)
    print("✅ Testing Key Validation")
    print("=" * 50)
    
    config = Config()
    
    missing_keys = config.validate_required_keys()
    print(f"Missing keys: {missing_keys if missing_keys else 'None'}")
    
    if missing_keys:
        print("⚠️ Some required keys are missing. This is expected if you haven't set up all API keys.")
    else:
        print("✅ All required keys are present!")


def main():
    """Run all configuration tests."""
    print("🔧 KGen Configuration Test")
    print("This script tests normal mode for API key management.")
    
    test_normal_mode()
    test_validation()
    
    print("\n" + "=" * 50)
    print("✨ Configuration tests completed!")
    print("=" * 50)
    
    print("\n📝 Usage Notes:")
    print("- Normal mode: Uses static API keys from .env file")
    print("- Configure SILICONFLOW_VIDEO_KEY and LLM_API_KEY in your .env file")


if __name__ == "__main__":
    main()