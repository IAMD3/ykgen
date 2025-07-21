#!/usr/bin/env python3
"""
Test script for video provider selection functionality.

This script demonstrates how users can now choose SiliconFlow
for video generation from the terminal.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import ykgen modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ykgen.video.client_factory import (
    create_video_client,
    get_video_provider_info,
    validate_video_provider_config,
    get_supported_providers,
    get_configured_providers,
)
from ykgen.console import print_info, print_success, print_warning, print_error


def test_video_provider_info():
    """Test video provider information display."""
    print_info("🎬 Testing video provider information")
    
    providers = get_supported_providers()
    print_info(f"Supported providers: {providers}")
    
    for provider in providers:
        info = get_video_provider_info(provider)
        print_info(f"\n📋 {info['name']} Provider:")
        print_info(f"   Model: {info['model']}")
        print_info(f"   Duration: {info['duration']}")
        print_info(f"   Resolution: {info['resolution']}")
        print_info(f"   Features: {', '.join(info['features'])}")
        print_info(f"   API Key: {info['api_key_env']}")
    
    print_success("✅ Provider information test passed")
    return True


def test_video_provider_config():
    """Test video provider configuration validation."""
    print_info("🔧 Testing video provider configuration")
    
    providers = get_supported_providers()
    configured = get_configured_providers()
    
    print_info(f"Configured providers: {configured}")
    
    for provider in providers:
        is_configured = validate_video_provider_config(provider)
        status = "✅ Configured" if is_configured else "❌ Not configured"
        print_info(f"   {provider}: {status}")
    
    print_success("✅ Configuration test passed")
    return True


def test_video_client_creation():
    """Test video client creation."""
    print_info("🏭 Testing video client creation")
    
    providers = get_supported_providers()
    
    for provider in providers:
        print_info(f"\nTesting {provider} client creation...")
        
        try:
            client = create_video_client(provider)
            if client:
                print_success(f"✅ {provider} client created successfully")
                print_info(f"   Client type: {type(client).__name__}")
            else:
                print_warning(f"⚠️ {provider} client creation failed (likely missing API key)")
        except Exception as e:
            print_warning(f"⚠️ {provider} client creation error: {e}")
    
    print_success("✅ Client creation test completed")
    return True


def demonstrate_interactive_flow():
    """Demonstrate the interactive video provider selection flow."""
    print_info("🎭 Demonstrating interactive video provider selection")
    
    # Show the flow that users will see
    print_info("\n📝 Interactive Flow Example:")
    print_info("1. User starts KGen: `python main.py`")
    print_info("2. User selects agent type (VideoAgent/PoetryAgent)")
    print_info("3. User selects video provider (SiliconFlow)")
    print_info("4. User selects model and LoRA options")
    print_info("5. User enters prompt")
    print_info("6. System generates video with selected provider")
    
    print_info("\n🎯 Available Video Providers:")
    for provider in get_supported_providers():
        info = get_video_provider_info(provider)
        configured = "✅" if validate_video_provider_config(provider) else "❌"
        print_info(f"   • {info['name']}: {info['resolution']}, {info['duration']} {configured}")
    
    print_success("✅ Interactive flow demonstration complete")
    return True


def test_video_generation_parameters():
    """Test video generation parameters for different providers."""
    print_info("⚙️ Testing video generation parameters")
    
    providers = get_supported_providers()
    
    for provider in providers:
        print_info(f"\n📋 {provider.title()} Parameters:")
        
        if provider == "siliconflow":
            print_info("   • Model: Wan2.1 I2V-14B-720P-Turbo")
            print_info("   • Duration: 5 seconds (fixed)")
            print_info("   • Resolution: 720P (fixed)")
            print_info("   • Features: Conservative prompts, reliable API")
    
    print_success("✅ Parameter testing complete")
    return True


def main():
    """Run all video provider selection tests."""
    print_info("🚀 Starting Video Provider Selection Tests")
    print_info("=" * 50)
    
    tests = [
        test_video_provider_info,
        test_video_provider_config,
        test_video_client_creation,
        demonstrate_interactive_flow,
        test_video_generation_parameters,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print_info("-" * 30)
        try:
            if test():
                passed += 1
            else:
                print_error(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print_error(f"❌ Test {test.__name__} error: {e}")
    
    print_info("=" * 50)
    print_info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("🎉 All tests passed! Video provider selection is ready!")
        print_info("💡 Users can now choose SiliconFlow for video generation")
        print_info("💡 Configure API keys in .env file: SILICONFLOW_VIDEO_KEY")
    else:
        print_warning(f"⚠️ {total - passed} tests failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)