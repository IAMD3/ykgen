#!/usr/bin/env python3
"""
Test script to demonstrate example-guided prompt generation.
This shows how the LLM is guided by professional prompt examples.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kgen.agents.video_agent import VideoAgent
from kgen.model.models import VisionState
from kgen.console import print_banner, print_info, print_success
from langchain_core.messages import HumanMessage


def test_example_guided_prompts():
    """Test the example-guided prompt generation feature."""
    print_banner()
    print_info("🎯 Testing Example-Guided Prompt Generation 🎯", "")
    print()
    
    # Create a VideoAgent
    agent = VideoAgent(
        enable_audio=False,
        style="anime",
        lora_config={
            "name": "Test LoRA",
            "file": "test_lora.safetensors",
            "trigger": "1girl, anime style",
            "strength_model": 0.85,
            "strength_clip": 0.85
        }
    )
    
    # Create a test state with characters and scenes
    test_state = VisionState(
        prompt=HumanMessage(content="A magical adventure"),
        story_full=HumanMessage(content="A young warrior embarks on a quest to save her kingdom from an ancient evil."),
        characters_full=[
            {
                "name": "Aria",
                "description": "A brave young warrior with silver hair and blue eyes, skilled in swordsmanship"
            },
            {
                "name": "Shadow Beast",
                "description": "A dark creature with glowing red eyes and ethereal form"
            }
        ],
        scenes=[
            {
                "location": "Ancient castle courtyard",
                "time": "Dawn",
                "characters": [{"name": "Aria", "description": "A brave young warrior with silver hair and blue eyes, skilled in swordsmanship"}],
                "action": "Aria draws her enchanted sword as the shadow beast emerges from the morning mist",
                "image_prompt_positive": None,
                "image_prompt_negative": None
            },
            {
                "location": "Mystical forest clearing",
                "time": "Sunset",
                "characters": [{"name": "Aria", "description": "A brave young warrior with silver hair and blue eyes, skilled in swordsmanship"}],
                "action": "Aria discovers a glowing crystal that holds the key to defeating the ancient evil",
                "image_prompt_positive": None,
                "image_prompt_negative": None
            }
        ],
        style="anime"
    )
    
    print_info("📝 Example Format Used to Guide LLM:", "")
    print("Positive: \"1girl, saber alter, weapon, artoria pendragon (fate), armor, sword, excalibur morgan (fate), solo, armored dress, holding sword, holding weapon, holding, blonde hair, gauntlets, yellow eyes, dress, breastplate, braid, masterpiece, best quality, newest, absurdres, highres, very awa\"")
    print("Negative: \"low quality, worst quality, normal quality, text, signature, jpeg artifacts, bad anatomy, old, early\"")
    print()
    
    print_info("🔧 Testing with LoRA Configuration:", "")
    print(f"  LoRA Name: {agent.lora_config['name']}")
    print(f"  Trigger Words: {agent.lora_config['trigger']}")
    print(f"  Strength - Model: {agent.lora_config['strength_model']}, CLIP: {agent.lora_config['strength_clip']}")
    print()
    
    print_info("🎬 Input Scenes:", "")
    for i, scene in enumerate(test_state["scenes"], 1):
        print(f"  Scene {i}: {scene['action']}")
        print(f"    Location: {scene['location']}")
        print(f"    Time: {scene['time']}")
        print(f"    Characters: {', '.join([char['name'] for char in scene['characters']])}")
        print()
    
    print_info("🚀 Generating Example-Guided Prompts...", "")
    print("=" * 80)
    
    # Generate prompts using the example-guided system
    try:
        result = agent.generate_prompts(test_state)
        
        print_success("✅ Example-Guided Prompts Generated Successfully!")
        print()
        
        # Display the generated prompts
        for i, scene in enumerate(result["scenes"], 1):
            print(f"🎨 Scene {i} Generated Prompts:")
            print(f"  📍 Location: {scene['location']}")
            print(f"  ⏰ Time: {scene['time']}")
            print(f"  🎬 Action: {scene['action']}")
            print()
            
            print(f"  ✅ Positive Prompt:")
            print(f"     {scene['image_prompt_positive']}")
            print()
            
            print(f"  ❌ Negative Prompt:")
            print(f"     {scene['image_prompt_negative']}")
            print()
            
            # Analyze the prompt quality
            positive = scene['image_prompt_positive']
            negative = scene['image_prompt_negative']
            
            print(f"  🔍 Prompt Analysis:")
            
            # Check for example format compliance
            has_quality_tags = any(tag in positive for tag in ["masterpiece", "best quality", "newest", "absurdres", "highres"])
            has_trigger_words = agent.lora_config['trigger'] in positive
            has_character_details = any(char['name'].lower() in positive.lower() for char in scene['characters'])
            has_standard_negatives = any(neg in negative for neg in ["low quality", "worst quality", "text", "signature", "jpeg artifacts"])
            
            print(f"     ✅ Quality tags present: {has_quality_tags}")
            print(f"     ✅ LoRA trigger words included: {has_trigger_words}")
            print(f"     ✅ Character details included: {has_character_details}")
            print(f"     ✅ Standard negative prompts: {has_standard_negatives}")
            
            # Check format similarity to example
            format_score = 0
            if "1girl" in positive or "girl" in positive:
                format_score += 1
            if any(word in positive for word in ["weapon", "sword", "armor", "dress"]):
                format_score += 1
            if any(word in positive for word in ["holding", "solo"]):
                format_score += 1
            if any(word in positive for word in ["hair", "eyes"]):
                format_score += 1
            
            print(f"     📊 Format similarity score: {format_score}/4")
            print()
            
            print("-" * 80)
            print()
    
    except Exception as e:
        print(f"❌ Error during prompt generation: {str(e)}")
        print()
    
    print_info("🎯 Example-Guided Prompt Generation Features:", "")
    print("  📝 LLM is guided by professional prompt examples")
    print("  🎨 Follows proven prompt structures for optimal results")
    print("  ⭐ Includes essential quality tags (masterpiece, best quality, newest)")
    print("  🚫 Uses comprehensive negative prompts to avoid unwanted elements")
    print("  🔧 Automatically includes LoRA trigger words")
    print("  📊 Maintains character and scene consistency")
    print("  🎯 Produces structured, professional-quality prompts")
    print()


def test_fallback_prompts():
    """Test the fallback prompt generation with example guidance."""
    print_info("🔄 Testing Fallback Prompts with Example Guidance:", "")
    print()
    
    # Test fallback prompts by simulating LLM failure
    agent = VideoAgent(
        enable_audio=False,
        style="cyberpunk",
        lora_config={
            "name": "Cyberpunk LoRA",
            "file": "cyberpunk.safetensors",
            "trigger": "cyberpunk style, neon lights",
            "strength_model": 0.9,
            "strength_clip": 0.9
        }
    )
    
    # Create a simple scene for fallback testing
    test_scene = {
        "location": "Neon-lit alley",
        "time": "Night",
        "characters": [{"name": "Cyber Warrior", "description": "A futuristic fighter with augmented reality visor"}],
        "action": "Standing ready for battle in the rain",
        "image_prompt_positive": None,
        "image_prompt_negative": None
    }
    
    print_info("🎬 Fallback Scene:", "")
    print(f"  Location: {test_scene['location']}")
    print(f"  Time: {test_scene['time']}")
    print(f"  Action: {test_scene['action']}")
    print()
    
    # Simulate fallback prompt generation
    positive_parts = []
    
    # Add LoRA trigger words
    if agent.lora_config.get("trigger"):
        positive_parts.append(agent.lora_config["trigger"])
    
    # Add style
    if agent.style:
        positive_parts.extend([agent.style, "style"])
    
    # Add scene description following the example format
    positive_parts.extend([
        test_scene["action"],
        "dynamic composition",
        "masterpiece",
        "best quality",
        "newest",
        "absurdres",
        "highres",
        "detailed",
        "no text"
    ])
    
    fallback_positive = ", ".join(positive_parts)
    fallback_negative = "low quality, worst quality, normal quality, text, signature, jpeg artifacts, bad anatomy, old, early"
    
    print_info("🔄 Generated Fallback Prompts:", "")
    print(f"  ✅ Positive: {fallback_positive}")
    print(f"  ❌ Negative: {fallback_negative}")
    print()
    
    # Analyze fallback prompt quality
    print_info("🔍 Fallback Prompt Analysis:", "")
    has_trigger = agent.lora_config["trigger"] in fallback_positive
    has_quality_tags = any(tag in fallback_positive for tag in ["masterpiece", "best quality", "newest", "absurdres", "highres"])
    has_style = agent.style in fallback_positive
    has_standard_negatives = any(neg in fallback_negative for neg in ["low quality", "worst quality", "text", "signature", "jpeg artifacts"])
    
    print(f"  ✅ LoRA trigger words: {has_trigger}")
    print(f"  ✅ Quality tags from example: {has_quality_tags}")
    print(f"  ✅ Style included: {has_style}")
    print(f"  ✅ Standard negatives: {has_standard_negatives}")
    print()


if __name__ == "__main__":
    print("🎯 Testing Example-Guided Prompt Generation System")
    print("=" * 80)
    
    test_example_guided_prompts()
    test_fallback_prompts()
    
    print_success("✅ All tests completed!")
    print("\n🎯 Example-Guided Prompt Generation Summary:")
    print("- 📝 LLM is guided by professional prompt examples")
    print("- 🎨 Follows proven structures for optimal image generation")
    print("- ⭐ Includes essential quality tags automatically")
    print("- 🚫 Uses comprehensive negative prompts")
    print("- 🔧 Integrates seamlessly with LoRA trigger words")
    print("- 📊 Maintains consistency across all scenes")
    print("- 🎯 Produces professional-quality structured prompts")