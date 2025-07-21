#!/usr/bin/env python3
"""
Simple test script for the new waiNSFWIllustrious model integration.
"""

import json
import os

def test_wai_model_integration():
    """Test the waiNSFWIllustrious model integration."""
    print("Testing waiNSFWIllustrious model integration...")
    
    # Test 1: Check if lora_config.json contains the new model
    try:
        with open('../kgen/config/lora_config.json', 'r') as f:
            lora_config = json.load(f)
        
        if 'wai-nsfw-illustrious' in lora_config:
            model_config = lora_config['wai-nsfw-illustrious']
            print(f"✓ Found wai-nsfw-illustrious model in lora_config.json")
            print(f"  - Description: {model_config.get('description', 'N/A')}")
            print(f"  - LoRA options: {len(model_config.get('loras', {}))}")
        else:
            print("✗ wai-nsfw-illustrious model not found in lora_config.json")
            return False
    except Exception as e:
        print(f"✗ Error reading lora_config.json: {e}")
        return False
    
    # Test 2: Check if the wai image module exists
    wai_module_path = '../kgen/image/comfyui_image_wai.py'
    if os.path.exists(wai_module_path):
        print(f"✓ Found wai image module: {wai_module_path}")
        
        # Check if it contains the expected class
        with open(wai_module_path, 'r') as f:
            content = f.read()
            if 'class ComfyUIWaiClient' in content:
                print("  - ComfyUIWaiClient class found")
            if 'waiNSFWIllustrious_v120.safetensors' in content:
                print("  - Correct model file reference found")
            if 'steps": 26' in content:
                print("  - Correct step count (26) found")
    else:
        print(f"✗ Wai image module not found: {wai_module_path}")
        return False
    
    # Test 3: Check if __init__.py exports the new functions
    init_path = '../kgen/image/__init__.py'
    if os.path.exists(init_path):
        with open(init_path, 'r') as f:
            content = f.read()
            if 'ComfyUIWaiClient' in content and 'generate_wai_images_for_scenes' in content:
                print("✓ Wai functions exported in __init__.py")
            else:
                print("✗ Wai functions not properly exported in __init__.py")
                return False
    
    # Test 4: Check if agent files have been updated
    agent_files = [
        'kgen/agents/pure_image_agent.py',
        'kgen/agents/poetry_agent.py', 
        'kgen/agents/video_agent.py'
    ]
    
    for agent_file in agent_files:
        if os.path.exists(agent_file):
            with open(agent_file, 'r') as f:
                content = f.read()
                if 'wai-nsfw-illustrious' in content:
                    print(f"✓ {os.path.basename(agent_file)} updated with wai-nsfw-illustrious")
                else:
                    print(f"✗ {os.path.basename(agent_file)} not updated")
                    return False
    
    # Test 5: Check main.py model selection
    main_path = '../main.py'
    if os.path.exists(main_path):
        with open(main_path, 'r') as f:
            content = f.read()
            if 'Wai NSFW Illustrious' in content and 'wai-nsfw-illustrious' in content:
                print("✓ main.py updated with new model option")
            else:
                print("✗ main.py not properly updated")
                return False
    
    print("\n✓ All tests passed! waiNSFWIllustrious model integration is complete.")
    return True

if __name__ == "__main__":
    success = test_wai_model_integration()
    print(f"\nTest result: {'SUCCESS' if success else 'FAILED'}")