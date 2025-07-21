#!/usr/bin/env python3
"""
Test script to demonstrate conservative video prompt generation.
This shows how video prompts are made very conservative to avoid too much character movement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kgen.console import print_banner, print_info, print_success, print_warning


def test_conservative_video_prompts():
    """Test the conservative video prompt generation logic."""
    print_banner()
    print_info("🎬 Testing Conservative Video Prompt Generation 🎬", "")
    print()
    
    # Test scenarios with different types of scene actions
    test_scenarios = [
        {
            "name": "High Action Scene",
            "scene": {
                "location": "Ancient battlefield",
                "time": "Dawn",
                "action": "The warrior charges forward with sword raised, leaping over fallen enemies in dramatic combat",
                "image_prompt_negative": "low quality, worst quality, blurry"
            }
        },
        {
            "name": "Environmental Scene",
            "scene": {
                "location": "Mystical forest",
                "time": "Sunset",
                "action": "Wind gently blows through the trees as magical light sparkles between the leaves",
                "image_prompt_negative": "text, signature, poor quality"
            }
        },
        {
            "name": "Character Interaction",
            "scene": {
                "location": "Royal throne room",
                "time": "Midday",
                "action": "The princess dramatically gestures while speaking passionately to the assembled court",
                "image_prompt_negative": "jpeg artifacts, bad anatomy"
            }
        },
        {
            "name": "Simple Scene",
            "scene": {
                "location": "Peaceful garden",
                "time": "Morning",
                "action": "A character sits quietly reading a book",
                "image_prompt_negative": ""
            }
        }
    ]
    
    print_info("🔍 Testing Conservative Video Prompt Logic:", "")
    print()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print_info(f"Scenario {i}: {scenario['name']}", "")
        scene = scenario["scene"]
        
        # Simulate the conservative video prompt generation logic
        scene_location = scene.get("location", "")
        scene_time = scene.get("time", "")
        scene_action = scene.get("action", "")
        
        print(f"  📍 Location: {scene_location}")
        print(f"  ⏰ Time: {scene_time}")
        print(f"  🎬 Original Action: {scene_action}")
        print()
        
        # Build a very conservative, minimal movement video prompt
        video_prompt_parts = []
        
        # Start with static atmospheric elements only
        if scene_location:
            video_prompt_parts.append(f"static scene at {scene_location}")
        if scene_time:
            video_prompt_parts.append(f"during {scene_time}")
            
        # Minimize character movement - focus on environment instead of actions
        if scene_action:
            # Extract environmental elements and avoid character actions
            action_lower = scene_action.lower()
            
            # Only add very minimal, environmental movements
            if any(word in action_lower for word in ["wind", "breeze", "flowing", "rippling", "ripples"]):
                video_prompt_parts.append("gentle environmental movement")
                movement_type = "Environmental"
            elif any(word in action_lower for word in ["light", "glow", "shine", "sparkle", "glowing"]):
                video_prompt_parts.append("subtle lighting effects")
                movement_type = "Lighting"
            else:
                # For any other action, just add minimal movement
                video_prompt_parts.append("minimal movement")
                movement_type = "Minimal"
        
        # Add very conservative atmospheric qualities that emphasize stillness
        video_prompt_parts.extend([
            "stable composition",
            "minimal character movement", 
            "environmental ambience",
            "subtle lighting changes only",
            "camera remains still"
        ])
        
        video_prompt = ", ".join(video_prompt_parts)
        
        # Create conservative negative prompt for video to avoid excessive movement
        base_negative = scene.get("image_prompt_negative", "")
        video_negative_parts = [
            "too much movement",
            "excessive motion", 
            "fast movement",
            "rapid action",
            "dramatic gestures",
            "sudden changes",
            "camera shake",
            "blurry motion",
            "distorted movement"
        ]
        
        if base_negative:
            video_negative_prompt = f"{base_negative}, {', '.join(video_negative_parts)}"
        else:
            video_negative_prompt = ", ".join(video_negative_parts)
        
        print(f"  🎯 Movement Analysis: {movement_type}")
        print(f"  ✅ Conservative Video Prompt:")
        print(f"     {video_prompt}")
        print()
        print(f"  ❌ Movement-Control Negative:")
        print(f"     {video_negative_prompt}")
        print()
        
        # Analyze the transformation
        print(f"  📊 Transformation Analysis:")
        original_action_words = len([word for word in ["charges", "leaping", "dramatic", "gestures", "passionately"] if word in scene_action.lower()])
        conservative_words = len([word for word in ["static", "minimal", "stable", "subtle"] if word in video_prompt.lower()])
        
        print(f"     • Original action words: {original_action_words}")
        print(f"     • Conservative descriptors: {conservative_words}")
        print(f"     • Movement minimization: {'✅ Effective' if conservative_words > original_action_words else '⚠️ Needs review'}")
        
        print("-" * 80)
        print()


def compare_old_vs_new_prompts():
    """Compare old vs new video prompt generation approaches."""
    print_info("📊 Comparison: Old vs New Video Prompt Generation", "")
    print()
    
    test_scene = {
        "location": "Medieval castle courtyard",
        "time": "Dawn",
        "action": "The knight draws his sword and charges dramatically toward the approaching dragon",
        "image_prompt_negative": "low quality, blurry"
    }
    
    print_info("🎬 Test Scene:", "")
    print(f"  Location: {test_scene['location']}")
    print(f"  Time: {test_scene['time']}")
    print(f"  Action: {test_scene['action']}")
    print()
    
    # Old approach (too action-focused)
    print_info("❌ OLD Approach (Too Action-Focused):", "")
    old_prompt_parts = []
    old_prompt_parts.append(f"peaceful scene at {test_scene['location']}")
    old_prompt_parts.append(f"during {test_scene['time']}")
    
    # Old approach would transform but still include the action
    gentle_action = test_scene['action'].replace("dramatically", "gently").replace("charges", "moves")
    old_prompt_parts.append(f"with {gentle_action}")
    old_prompt_parts.extend(["soft lighting", "subtle movement", "cinematic atmosphere"])
    
    old_prompt = ", ".join(old_prompt_parts)
    print(f"  Result: {old_prompt}")
    print(f"  ⚠️  Problem: Still includes character action that causes too much movement")
    print()
    
    # New approach (very conservative)
    print_info("✅ NEW Approach (Very Conservative):", "")
    new_prompt_parts = []
    new_prompt_parts.append(f"static scene at {test_scene['location']}")
    new_prompt_parts.append(f"during {test_scene['time']}")
    new_prompt_parts.append("minimal movement")  # No character action mentioned
    new_prompt_parts.extend([
        "stable composition",
        "minimal character movement", 
        "environmental ambience",
        "subtle lighting changes only",
        "camera remains still"
    ])
    
    new_prompt = ", ".join(new_prompt_parts)
    print(f"  Result: {new_prompt}")
    print(f"  ✅ Benefit: Focuses on stillness and minimal movement")
    print()
    
    # Negative prompt comparison
    print_info("🚫 Enhanced Negative Prompts:", "")
    old_negative = test_scene['image_prompt_negative']
    new_negative = f"{old_negative}, too much movement, excessive motion, fast movement, rapid action, dramatic gestures, sudden changes, camera shake, blurry motion, distorted movement"
    
    print(f"  Old: {old_negative}")
    print(f"  New: {new_negative}")
    print(f"  ✅ Benefit: Explicitly prevents excessive movement")
    print()


def demonstrate_movement_types():
    """Demonstrate how different movement types are handled."""
    print_info("🎯 Movement Type Classification", "")
    print()
    
    movement_examples = [
        {
            "action": "Wind blows through the character's hair as they stand on a cliff",
            "expected_type": "Environmental",
            "keywords": ["wind", "breeze"]
        },
        {
            "action": "Magical light glows softly around the enchanted sword",
            "expected_type": "Lighting",
            "keywords": ["light", "glow", "shine", "sparkle"]
        },
        {
            "action": "The warrior charges into battle with sword raised high",
            "expected_type": "Minimal",
            "keywords": []
        },
        {
            "action": "Gentle ripples spread across the mystical pond's surface",
            "expected_type": "Environmental", 
            "keywords": ["flowing", "rippling", "ripples"]
        }
    ]
    
    for i, example in enumerate(movement_examples, 1):
        action = example["action"]
        expected = example["expected_type"]
        keywords = example["keywords"]
        
        print(f"Example {i}: {action}")
        
        # Apply the classification logic
        action_lower = action.lower()
        if any(word in action_lower for word in ["wind", "breeze", "flowing", "rippling", "ripples"]):
            movement_type = "Environmental"
            result = "gentle environmental movement"
        elif any(word in action_lower for word in ["light", "glow", "shine", "sparkle", "glowing"]):
            movement_type = "Lighting"
            result = "subtle lighting effects"
        else:
            movement_type = "Minimal"
            result = "minimal movement"
        
        status = "✅ Correct" if movement_type == expected else "❌ Unexpected"
        print(f"  Classification: {movement_type} ({status})")
        print(f"  Video Prompt Addition: '{result}'")
        print(f"  Keywords detected: {[word for word in keywords if word in action_lower] if keywords else 'None'}")
        print()


if __name__ == "__main__":
    print("🎬 Testing Conservative Video Prompt Generation System")
    print("=" * 80)
    
    test_conservative_video_prompts()
    compare_old_vs_new_prompts()
    demonstrate_movement_types()
    
    print_success("✅ All tests completed!")
    print("\n🎯 Conservative Video Prompt Generation Summary:")
    print("- 🎬 Dramatically reduced character movement in video prompts")
    print("- 🔒 Focus on static scenes and environmental elements")
    print("- 🚫 Enhanced negative prompts to prevent excessive motion")
    print("- 📊 Clear logging shows transformation from action to stillness")
    print("- ⚡ Should result in clearer, less blurry video generation")
    print("- 🎯 Maintains atmospheric quality while minimizing movement artifacts") 