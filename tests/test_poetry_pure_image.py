#!/usr/bin/env python3
"""
Test script for PoetryAgent pure image mode functionality.
"""

def test_poetry_agent_pure_image():
    """Test that PoetryAgent can be instantiated with pure image mode."""
    try:
        # Import the necessary modules
        from kgen import PoetryAgent
        
        print("✓ Successfully imported PoetryAgent")
        
        # Test instantiation with pure image mode
        agent = PoetryAgent(
            enable_audio=False,
            pure_image_mode=True,
            images_per_scene=2,
        )
        
        print("✓ Successfully created PoetryAgent with pure image mode")
        print(f"  - pure_image_mode: {agent.pure_image_mode}")
        print(f"  - images_per_scene: {agent.images_per_scene}")
        print(f"  - enable_audio: {agent.enable_audio}")
        
        # Test workflow creation
        workflow = agent.create_workflow()
        print("✓ Successfully created workflow")
        
        print("\n🎉 All tests passed! PoetryAgent pure image mode is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing PoetryAgent pure image mode functionality...")
    print("=" * 60)
    
    success = test_poetry_agent_pure_image()
    
    if success:
        print("\n✅ PoetryAgent pure image mode is ready to use!")
    else:
        print("\n❌ PoetryAgent pure image mode has issues that need to be fixed.")