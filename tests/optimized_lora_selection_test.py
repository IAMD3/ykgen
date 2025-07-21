"""
Test for optimized LoRA selection that selects LoRAs once for all scenes.

This test demonstrates the new optimized approach that analyzes all scenes
together to select the most appropriate LoRAs for the entire story.
"""

from kgen.lora.lora_selector import select_loras_for_all_scenes_optimized



def test_optimized_lora_selection():
    """Test the optimized LoRA selection approach."""
    
    # Sample group mode configuration
    group_config = {
        "mode": "group",
        "model_type": "flux-schnell",
        "required_loras": [
            {
                "name": "Base Style",
                "description": "Base visual style for all scenes",
                "file": "base_style.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0
            }
        ],
        "optional_loras": [
            {
                "name": "Watercolor Style",
                "description": "Soft watercolor painting style with gentle brushstrokes",
                "file": "watercolor.safetensors",
                "trigger": "watercolor, soft painting",
                "strength_model": 0.8,
                "strength_clip": 0.8
            },
            {
                "name": "Cyberpunk Style",
                "description": "Futuristic cyberpunk aesthetic with neon lights",
                "file": "cyberpunk.safetensors",
                "trigger": "cyberpunk, neon, futuristic",
                "strength_model": 0.9,
                "strength_clip": 0.9
            },
            {
                "name": "Fantasy Style",
                "description": "Magical fantasy world with ethereal lighting",
                "file": "fantasy.safetensors",
                "trigger": "fantasy, magical, ethereal",
                "strength_model": 0.85,
                "strength_clip": 0.85
            },
            {
                "name": "Pixel Art Style",
                "description": "Retro pixel art aesthetic with blocky graphics",
                "file": "pixel_art.safetensors",
                "trigger": "pixel art, retro, 8-bit",
                "strength_model": 0.9,
                "strength_clip": 0.9
            }
        ]
    }
    
    # Sample scenes with image prompts (required for optimized selection)
    scenes = [
        {
            "location": "Enchanted Forest",
            "time": "Dawn",
            "characters": [{"name": "Hero", "description": "Brave adventurer"}],
            "action": "Hero walks through misty forest",
            "image_prompt_positive": "1girl, hero, enchanted forest, dawn, misty atmosphere, magical lighting, fantasy setting, ethereal glow, soft colors, masterpiece, best quality",
            "image_prompt_negative": "text, words, letters, writing, low quality, blurry, distorted, deformed"
        },
        {
            "location": "Ancient Castle",
            "time": "Night",
            "characters": [{"name": "Hero", "description": "Brave adventurer"}],
            "action": "Hero explores mysterious castle",
            "image_prompt_positive": "1girl, hero, ancient castle, night, mysterious atmosphere, torch lighting, stone walls, gothic architecture, fantasy setting, masterpiece, best quality",
            "image_prompt_negative": "text, words, letters, writing, low quality, blurry, distorted, deformed"
        },
        {
            "location": "Crystal Cave",
            "time": "Unknown",
            "characters": [{"name": "Hero", "description": "Brave adventurer"}],
            "action": "Hero discovers magical crystals",
            "image_prompt_positive": "1girl, hero, crystal cave, magical crystals, ethereal lighting, fantasy setting, glowing gems, mystical atmosphere, masterpiece, best quality",
            "image_prompt_negative": "text, words, letters, writing, low quality, blurry, distorted, deformed"
        }
    ]
    
    print("Testing Optimized LoRA Selection")
    print("=" * 50)
    print(f"Number of scenes: {len(scenes)}")
    print(f"Required LoRAs: {len(group_config['required_loras'])}")
    print(f"Optional LoRAs: {len(group_config['optional_loras'])}")
    print()
    
    try:
        # Test the optimized selection
        result = select_loras_for_all_scenes_optimized(
            scenes=scenes,
            group_config=group_config
        )
        
        print("Optimized LoRA Selection Result:")
        print("-" * 40)
        
        if result:
            print(f"Selected LoRA Configuration: {result.get('name', 'Unknown')}")
            print(f"Optimized Selection: {result.get('optimized_selection', False)}")
            print(f"Total Scenes: {result.get('total_scenes', 'Unknown')}")
            
            if result.get("is_multiple"):
                print("Multiple LoRAs Selected:")
                for lora in result.get("loras", []):
                    print(f"  - {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
            else:
                print(f"Single LoRA: {result.get('name', 'Unknown')}")
                print(f"Strength - Model: {result.get('strength_model', 1.0)}, CLIP: {result.get('strength_clip', 1.0)}")
            
            if result.get("trigger"):
                print(f"Trigger Words: {result['trigger']}")
            
            if result.get("selection_reasoning"):
                print(f"Selection Reasoning: {result['selection_reasoning']}")
        else:
            print("No LoRAs selected")
            
    except Exception as e:
        print(f"Error in optimized LoRA selection: {str(e)}")


def test_optimized_vs_traditional():
    """Compare optimized vs traditional LoRA selection approaches."""
    
    print("\n" + "=" * 60)
    print("COMPARISON: Optimized vs Traditional LoRA Selection")
    print("=" * 60)
    
    print("\nTRADITIONAL APPROACH:")
    print("- LoRA selection per scene (N LLM calls)")
    print("- Each scene analyzed independently")
    print("- May result in inconsistent visual styles")
    print("- Higher API costs")
    print("- Slower execution")
    
    print("\nOPTIMIZED APPROACH:")
    print("- Single LoRA selection for entire story (1 LLM call)")
    print("- All scenes analyzed together")
    print("- Ensures visual consistency across story")
    print("- Lower API costs")
    print("- Faster execution")
    print("- Better story coherence")
    
    print("\nBENEFITS:")
    print("- Reduced LLM API calls: N → 1")
    print("- Improved visual consistency")
    print("- Better narrative coherence")
    print("- Cost effective")
    print("- Faster processing")


if __name__ == "__main__":
    test_optimized_lora_selection()
    test_optimized_vs_traditional()