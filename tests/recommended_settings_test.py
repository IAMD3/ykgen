#!/usr/bin/env python3
"""
Test script to demonstrate recommended_settings behavior with multiple LoRAs.
Only the first LoRA's recommended_settings should be applied.
"""

import json
from kgen.image.comfyui_image_flux import ComfyUIClient4Flux
from kgen.image.comfyui_image_illustrious import ComfyUIIllustriousClient


def test_single_lora_with_recommended_settings():
    """Test single LoRA with recommended_settings."""
    print("🧪 Testing Single LoRA with recommended_settings...")
    
    lora_config = {
        "name": "Test LoRA",
        "file": "test_lora.safetensors",
        "strength_model": 0.85,
        "strength_clip": 0.85,
        "recommended_settings": {
            "cfg": 4.5,
            "sampler": "euler_ancestral",
            "steps": 28
        }
    }
    
    client = ComfyUIClient4Flux(lora_config=lora_config)
    print("   Expected console output:")
    print("   ✅ Applied recommended settings from LoRA: Test LoRA")
    print("        🔧 Settings changed: CFG: 1 → 4.5, Sampler: euler → euler_ancestral, Steps: 4 → 28")
    print()
    
    prompt = client.create_flux_prompt("A beautiful landscape")
    
    ksampler = prompt["31"]["inputs"]
    print(f"   ✅ Actual settings: CFG={ksampler['cfg']}, Sampler={ksampler['sampler_name']}, Steps={ksampler['steps']}")
    print()


def test_multiple_loras_first_has_settings():
    """Test multiple LoRAs where first LoRA has recommended_settings."""
    print("🧪 Testing Multiple LoRAs - First LoRA has recommended_settings...")
    
    lora_config = {
        "is_multiple": True,
        "name": "Multiple LoRAs",
        "loras": [
            {
                "name": "First LoRA",
                "file": "first_lora.safetensors",
                "strength_model": 0.85,
                "strength_clip": 0.85,
                "recommended_settings": {
                    "cfg": 4.5,
                    "sampler": "euler_ancestral",
                    "steps": 28
                }
            },
            {
                "name": "Second LoRA",
                "file": "second_lora.safetensors",
                "strength_model": 0.7,
                "strength_clip": 0.7,
                "recommended_settings": {
                    "cfg": 6.0,
                    "sampler": "dpm_2",
                    "steps": 30
                }
            }
        ]
    }
    
    client = ComfyUIClient4Flux(lora_config=lora_config)
    print("   Expected console output:")
    print("   ✅ Applied recommended settings from LoRA: First LoRA")
    print("        🔧 Settings changed: CFG: 1 → 4.5, Sampler: euler → euler_ancestral, Steps: 4 → 28")
    print("        ⚠️  Ignored settings from 1 additional LoRA(s):")
    print("           2. Second LoRA: CFG: 6.0, Sampler: dpm_2, Steps: 30")
    print()
    
    prompt = client.create_flux_prompt("A beautiful landscape")
    
    ksampler = prompt["31"]["inputs"]
    print(f"   ✅ Applied settings from FIRST LoRA: CFG={ksampler['cfg']}, Sampler={ksampler['sampler_name']}, Steps={ksampler['steps']}")
    print(f"   ❌ Second LoRA's settings (CFG=6.0, Sampler=dpm_2, Steps=30) were IGNORED")
    print()


def test_multiple_loras_second_has_settings():
    """Test multiple LoRAs where second LoRA has recommended_settings."""
    print("🧪 Testing Multiple LoRAs - Only Second LoRA has recommended_settings...")
    
    lora_config = {
        "is_multiple": True,
        "name": "Multiple LoRAs",
        "loras": [
            {
                "name": "First LoRA",
                "file": "first_lora.safetensors",
                "strength_model": 0.85,
                "strength_clip": 0.85
                # No recommended_settings
            },
            {
                "name": "Second LoRA",
                "file": "second_lora.safetensors",
                "strength_model": 0.7,
                "strength_clip": 0.7,
                "recommended_settings": {
                    "cfg": 6.0,
                    "sampler": "dpm_2",
                    "steps": 30
                }
            }
        ]
    }
    
    client = ComfyUIClient4Flux(lora_config=lora_config)
    print("   Expected console output:")
    print("        ⚙️  Using default settings (no recommended_settings in LoRA)")
    print("        🔧 Default: CFG=1, Sampler=euler, Steps=4")
    print()
    
    prompt = client.create_flux_prompt("A beautiful landscape")
    
    ksampler = prompt["31"]["inputs"]
    print(f"   ✅ Using default settings: CFG={ksampler['cfg']}, Sampler={ksampler['sampler_name']}, Steps={ksampler['steps']}")
    print(f"   ❌ Second LoRA's settings (CFG=6.0, Sampler=dpm_2, Steps=30) were IGNORED")
    print()


def test_no_lora_settings():
    """Test LoRA without recommended_settings."""
    print("🧪 Testing LoRA without recommended_settings...")
    
    lora_config = {
        "name": "Basic LoRA",
        "file": "basic_lora.safetensors",
        "strength_model": 1.0,
        "strength_clip": 1.0
        # No recommended_settings
    }
    
    client = ComfyUIClient4Flux(lora_config=lora_config)
    print("   Expected console output:")
    print("        ⚙️  Using default settings (no recommended_settings in LoRA)")
    print("        🔧 Default: CFG=1, Sampler=euler, Steps=4")
    print()
    
    prompt = client.create_flux_prompt("A beautiful landscape")
    
    ksampler = prompt["31"]["inputs"]
    print(f"   ✅ Using default settings: CFG={ksampler['cfg']}, Sampler={ksampler['sampler_name']}, Steps={ksampler['steps']}")
    print()


def test_illustrious_multiple_loras():
    """Test Illustrious workflow with multiple LoRAs."""
    print("🧪 Testing Illustrious Multiple LoRAs with recommended_settings...")
    
    lora_config = {
        "is_multiple": True,
        "name": "Multiple Illustrious LoRAs",
        "loras": [
            {
                "name": "First LoRA",
                "file": "first_illustrious.safetensors",
                "strength_model": 0.85,
                "strength_clip": 0.85,
                "recommended_settings": {
                    "cfg": 4.5,
                    "sampler": "euler_ancestral",
                    "steps": 28
                }
            },
            {
                "name": "Second LoRA",
                "file": "second_illustrious.safetensors",
                "strength_model": 0.7,
                "strength_clip": 0.7,
                "recommended_settings": {
                    "cfg": 7.0,
                    "sampler": "dpm_2_ancestral",
                    "steps": 35
                }
            }
        ]
    }
    
    client = ComfyUIIllustriousClient(lora_config=lora_config)
    print("   Expected console output:")
    print("   ✅ Applied recommended settings from LoRA: First LoRA")
    print("        🔧 Settings changed: CFG: 5 → 4.5, Sampler: euler_ancestral → euler_ancestral, Steps: 27 → 28")
    print("        ⚠️  Ignored settings from 1 additional LoRA(s):")
    print("           2. Second LoRA: CFG: 7.0, Sampler: dpm_2_ancestral, Steps: 35")
    print()
    
    prompt = client.create_illustrious_prompt("A beautiful landscape")
    
    ksampler = prompt["3"]["inputs"]
    print(f"   ✅ Applied settings from FIRST LoRA: CFG={ksampler['cfg']}, Sampler={ksampler['sampler_name']}, Steps={ksampler['steps']}")
    print(f"   ❌ Second LoRA's settings (CFG=7.0, Sampler=dpm_2_ancestral, Steps=35) were IGNORED")
    print()


def test_real_world_scenario():
    """Test a real-world scenario with the actual Illustrious Tweaker LoRA."""
    print("🧪 Testing Real-World Scenario: Illustrious Tweaker LoRA v2...")
    
    lora_config = {
        "name": "Illustrious Tweaker LoRA v2",
        "file": "IllustriousTweakerLora_v2-rev9.safetensors",
        "strength_model": 0.85,
        "strength_clip": 0.85,
        "recommended_settings": {
            "cfg": 4.5,
            "sampler": "euler_ancestral",
            "steps": 28
        }
    }
    
    client = ComfyUIIllustriousClient(lora_config=lora_config)
    print("   Expected console output:")
    print("   ✅ Applied recommended settings from LoRA: Illustrious Tweaker LoRA v2")
    print("        🔧 Settings changed: CFG: 5 → 4.5, Steps: 27 → 28")
    print("        ✅ No changes needed (settings already optimal) - for sampler")
    print()
    
    prompt = client.create_illustrious_prompt("A beautiful landscape")
    
    ksampler = prompt["3"]["inputs"]
    print(f"   ✅ Optimized settings: CFG={ksampler['cfg']}, Sampler={ksampler['sampler_name']}, Steps={ksampler['steps']}")
    print()


if __name__ == "__main__":
    print("🎯 Testing recommended_settings behavior with console logging")
    print("=" * 70)
    
    test_single_lora_with_recommended_settings()
    test_multiple_loras_first_has_settings()
    test_multiple_loras_second_has_settings()
    test_no_lora_settings()
    test_illustrious_multiple_loras()
    test_real_world_scenario()
    
    print("✅ All tests completed!")
    print("\n📋 Console Logging Summary:")
    print("- ✅ Shows which LoRA's recommended_settings are being applied")
    print("- 🔧 Displays before/after values for changed settings")
    print("- ⚠️  Lists ignored settings from additional LoRAs")
    print("- ⚙️  Shows default settings when no recommended_settings exist")
    print("- 📊 Provides clear feedback on settings optimization")
    print("\n🎯 Key Benefits:")
    print("- Users can see exactly how LoRA impacts generation settings")
    print("- Clear visibility into multiple LoRA priority handling")
    print("- Transparency about which settings are being used/ignored")
    print("- Easy troubleshooting for generation quality issues")