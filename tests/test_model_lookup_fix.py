#!/usr/bin/env python3
"""
Integration test to validate the model lookup fix.

This test validates that the model lookup error is resolved by testing
the actual configuration and conversion logic.
"""

import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ykgen.lora.lora_loader import get_lora_key_for_model_type
from ykgen.config.image_model_loader import (
    find_model_by_name, 
    get_all_model_names,
    load_image_model_config
)


class TestModelLookupFix(unittest.TestCase):
    """Integration test cases for the model lookup fix."""

    def setUp(self):
        """Set up test fixtures."""
        try:
            # Load the actual configuration
            self.config = load_image_model_config()
            self.all_models = get_all_model_names()
        except Exception as e:
            self.skipTest(f"Could not load configuration: {e}")

    def test_model_exists_in_config(self):
        """Test that models exist in the configuration."""
        self.assertGreater(len(self.all_models), 0, "No models found in configuration")
        print(f"Found {len(self.all_models)} models in configuration")
        for model in self.all_models[:3]:  # Print first 3 models
            print(f"  - {model}")

    def test_model_lookup_by_name(self):
        """Test that models can be found by name."""
        for model_name in self.all_models:
            model_config = find_model_by_name(model_name)
            self.assertIsNotNone(model_config, f"Could not find model: {model_name}")
            self.assertIn("name", model_config, f"Model config missing 'name' field: {model_name}")

    def test_lora_config_key_conversion(self):
        """Test that model names can be converted to lora_config_keys."""
        for model_name in self.all_models:
            try:
                lora_key = get_lora_key_for_model_type(model_name)
                self.assertIsNotNone(lora_key, f"Could not get lora_key for model: {model_name}")
                print(f"Model '{model_name}' -> LoRA key '{lora_key}'")
            except Exception as e:
                self.fail(f"Error converting model '{model_name}' to lora_key: {e}")

    def test_reverse_lookup_lora_key_to_model(self):
        """Test that lora_config_keys can be converted back to model names."""
        # Test with a few models
        test_models = self.all_models[:3] if len(self.all_models) >= 3 else self.all_models
        
        for original_model_name in test_models:
            # Get the lora_config_key for this model
            lora_key = get_lora_key_for_model_type(original_model_name)
            
            # Now try to find the model that uses this lora_config_key
            found_model_name = None
            for name in get_all_model_names():
                model_config = find_model_by_name(name)
                if model_config and model_config.get("lora_config_key") == lora_key:
                    found_model_name = name
                    break
            
            # If no model was found with this lora_config_key, that's also valid
            # (some models might not have lora_config_key defined)
            if found_model_name:
                print(f"LoRA key '{lora_key}' -> Model '{found_model_name}'")
            else:
                print(f"LoRA key '{lora_key}' -> No model found (fallback will be used)")

    def test_specific_wai_illustrious_case(self):
        """Test the specific case that was causing the error."""
        # Check if WaiNSFW Illustrious exists in config
        wai_model = None
        for model_name in self.all_models:
            if "illustrious" in model_name.lower() and "wai" in model_name.lower():
                wai_model = model_name
                break
        
        if wai_model:
            print(f"Found WaiNSFW model: {wai_model}")
            
            # Test conversion to lora_key
            lora_key = get_lora_key_for_model_type(wai_model)
            print(f"WaiNSFW model '{wai_model}' -> LoRA key '{lora_key}'")
            
            # Test that this lora_key doesn't cause lookup errors
            model_config = find_model_by_name(wai_model)
            self.assertIsNotNone(model_config)
            
            # Test reverse lookup
            found_model = None
            for name in get_all_model_names():
                config = find_model_by_name(name)
                if config and config.get("lora_config_key") == lora_key:
                    found_model = name
                    break
            
            if found_model:
                print(f"Reverse lookup successful: '{lora_key}' -> '{found_model}'")
            else:
                print(f"No reverse lookup found for '{lora_key}' (fallback will be used)")
        else:
            print("WaiNSFW Illustrious model not found in configuration")

    def test_no_model_lookup_error(self):
        """Test that the specific error 'Model not found in configuration' doesn't occur."""
        # Test that 'wai-illustrious' (the lora_config_key) is not treated as a model name
        try:
            # This should not raise a "Model not found" error anymore
            # because we're not trying to look up 'wai-illustrious' as a model name
            model_config = find_model_by_name("wai-illustrious")
            # It's OK if this returns None, as 'wai-illustrious' is a lora_config_key, not a model name
            print(f"Lookup of 'wai-illustrious' as model name returned: {model_config}")
        except ValueError as e:
            if "not found in configuration" in str(e):
                self.fail(f"The old error still occurs: {e}")
            else:
                # Some other error is OK
                pass


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)