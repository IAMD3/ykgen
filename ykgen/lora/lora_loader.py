"""
LoRA Configuration Loader

This module provides functions to load and manage LoRA model configurations
from the lora_config.json file.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


def get_lora_config_path() -> str:
    """Get the path to the LoRA configuration file."""
    # Look for the config file in the same directory as this module
    current_dir = Path(__file__).parent.parent
    config_path = current_dir /"config/lora_config.json"
    return str(config_path)


def get_lora_key_for_model_type(model_type: str) -> str:
    """Map model type to LoRA configuration key.
    
    Args:
        model_type: Model type from CLI (e.g., 'flux-schnell', 'illustrious-vpred')
                   or from image config (e.g., 'simple', 'vpred')
    
    Returns:
        str: The corresponding LoRA configuration key
    """
    # Load the mapping from lora_config.json
    try:
        config = load_lora_config()
        mapping = config.get("_model_mapping", {})
        
        # If it's already a valid LoRA key, return as-is
        if model_type in config and model_type != "_model_mapping":
            return model_type
        
        # Try to map from image config key to LoRA key
        if model_type in mapping:
            return mapping[model_type]
        
        # Fallback to flux-schnell for unknown types
        return "flux-schnell"
    except Exception:
        # Fallback if config loading fails
        return "flux-schnell"

def load_lora_config() -> Dict[str, Any]:
    """
    Load the LoRA configuration from the JSON file.
    
    Returns:
        Dictionary containing the LoRA configuration for all models
    """
    config_path = get_lora_config_path()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"LoRA configuration file not found at: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in LoRA configuration file: {e}")


def get_lora_options(model_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Get the available LoRA options for a specific model type.
    
    Args:
        model_type: The model type (e.g., "flux-schnell", "illustrious-vpred", "simple", "vpred")
        
    Returns:
        Dictionary of LoRA options for the specified model type
    """
    config = load_lora_config()
    lora_key = get_lora_key_for_model_type(model_type)
    
    if lora_key not in config:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return config[lora_key]["loras"]


def get_model_description(model_type: str) -> str:
    """
    Get the description for a specific model type.
    
    Args:
        model_type: The model type (e.g., "flux-schnell", "illustrious-vpred", "simple", "vpred")
        
    Returns:
        Description string for the model type
    """
    config = load_lora_config()
    lora_key = get_lora_key_for_model_type(model_type)
    
    if lora_key not in config:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return config[lora_key]["description"]


def get_lora_by_choice(model_type: str, choice: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific LoRA configuration by user choice.
    
    Args:
        model_type: The model type (e.g., "flux-schnell", "illustrious-vpred", "simple", "vpred")
        choice: The user's choice (e.g., "1", "2", etc.)
        
    Returns:
        LoRA configuration dictionary or None if choice is invalid
    """
    lora_key = get_lora_key_for_model_type(model_type)
    lora_options = get_lora_options(lora_key)
    
    if choice in lora_options:
        lora_config = lora_options[choice].copy()
        # Add model_type to the config for compatibility
        lora_config["model_type"] = lora_key
        return lora_config
    
    return None


def get_multiple_loras_by_choices(model_type: str, choices: List[str]) -> List[Dict[str, Any]]:
    """
    Get multiple LoRA configurations by user choices.
    
    Args:
        model_type: The model type (e.g., "flux-schnell", "illustrious-vpred", "simple", "vpred")
        choices: List of user choices (e.g., ["1", "3", "5"])
        
    Returns:
        List of LoRA configuration dictionaries
    """
    selected_loras = []
    lora_key = get_lora_key_for_model_type(model_type)
    lora_options = get_lora_options(lora_key)
    
    for choice in choices:
        if choice in lora_options:
            lora_config = lora_options[choice].copy()
            lora_config["model_type"] = lora_key
            selected_loras.append(lora_config)
    
    return selected_loras


def validate_strength_value(strength: float) -> bool:
    """
    Validate that a strength value is within acceptable range.
    
    Args:
        strength: The strength value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0.1 <= strength <= 1.0


def parse_strength_input(input_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse user input for strength values.
    
    Args:
        input_str: User input string (e.g., "0.8" or "0.8,0.9" or "model:0.8,clip:0.9")
        
    Returns:
        Tuple of (strength_model, strength_clip) or (None, None) if invalid
    """
    if not input_str.strip():
        return 1.0, 1.0  # Default values
    
    input_str = input_str.strip()
    
    try:
        # Handle different input formats
        if ',' in input_str:
            # Format: "0.8,0.9" or "model:0.8,clip:0.9"
            parts = input_str.split(',')
            if len(parts) == 2:
                # Try to parse as "model:value,clip:value"
                if ':' in parts[0] and ':' in parts[1]:
                    model_part = parts[0].split(':')[1].strip()
                    clip_part = parts[1].split(':')[1].strip()
                    strength_model = float(model_part)
                    strength_clip = float(clip_part)
                else:
                    # Parse as "value1,value2"
                    strength_model = float(parts[0].strip())
                    strength_clip = float(parts[1].strip())
                
                if validate_strength_value(strength_model) and validate_strength_value(strength_clip):
                    return strength_model, strength_clip
        else:
            # Single value for both model and clip
            strength = float(input_str)
            if validate_strength_value(strength):
                return strength, strength
    
    except ValueError:
        pass
    
    return None, None


def build_trigger_words(lora_config: Dict[str, Any], include_optional: bool = False) -> str:
    """
    Build the trigger words string from a LoRA configuration.
    
    Args:
        lora_config: LoRA configuration dictionary
        include_optional: Whether to include optional trigger words
        
    Returns:
        Comma-separated string of trigger words
    """
    if not lora_config or not lora_config.get("trigger_words"):
        return ""
    
    trigger_words = lora_config["trigger_words"]
    required = trigger_words.get("required", [])
    
    if include_optional:
        optional = trigger_words.get("optional", [])
        all_words = required + optional
    else:
        all_words = required
    
    return ", ".join(all_words)


def build_combined_trigger_words(lora_configs: List[Dict[str, Any]], include_optional: bool = False) -> str:
    """
    Build combined trigger words from multiple LoRA configurations.
    
    Args:
        lora_configs: List of LoRA configuration dictionaries
        include_optional: Whether to include optional trigger words
        
    Returns:
        Comma-separated string of combined trigger words
    """
    all_trigger_words = []
    
    for lora_config in lora_configs:
        trigger_words = build_trigger_words(lora_config, include_optional)
        if trigger_words:
            all_trigger_words.append(trigger_words)
    
    return ", ".join(all_trigger_words)


def get_essential_traits(lora_config: Dict[str, Any]) -> List[str]:
    """
    Get essential traits for character LoRAs (like Elena Kimberlite).
    
    Args:
        lora_config: LoRA configuration dictionary
        
    Returns:
        List of essential traits
    """
    return lora_config.get("essential_traits", [])


def prepare_lora_for_agent(lora_config: Dict[str, Any], model_type: str = "") -> Dict[str, Any]:
    """
    Prepare LoRA configuration for use with agents.
    
    Args:
        lora_config: Raw LoRA configuration from JSON
        model_type: Model type to use if not present in lora_config
        
    Returns:
        LoRA configuration formatted for agent use
    """
    if not lora_config:
        return {"name": "No LoRA", "file": None, "trigger": "", "model_type": model_type}
    
    # Build the trigger string (required words only for basic trigger)
    trigger = build_trigger_words(lora_config, include_optional=False)
    
    return {
        "name": lora_config.get("name", "Unknown LoRA"),
        "file": lora_config.get("file"),
        "trigger": trigger,
        "model_type": lora_config.get("model_type", model_type),
        "trigger_words": lora_config.get("trigger_words", {}),
        "essential_traits": lora_config.get("essential_traits", []),
        "description": lora_config.get("description", ""),
        "strength_model": lora_config.get("strength_model", 1.0),
        "strength_clip": lora_config.get("strength_clip", 1.0)
    }


def prepare_multiple_loras_for_agent(lora_configs: List[Dict[str, Any]], model_type: str = "") -> Dict[str, Any]:
    """
    Prepare multiple LoRA configurations for use with agents.
    
    Args:
        lora_configs: List of raw LoRA configurations from JSON
        model_type: Model type to use if not present in lora_configs
        
    Returns:
        Combined LoRA configuration formatted for agent use
    """
    if not lora_configs:
        return {"name": "No LoRA", "file": None, "trigger": "", "loras": [], "model_type": model_type}
    
    # Prepare individual LoRAs
    prepared_loras = [prepare_lora_for_agent(config, model_type) for config in lora_configs]
    
    # Build combined trigger words
    combined_trigger = build_combined_trigger_words(lora_configs, include_optional=False)
    
    # Create combined name
    lora_names = [lora["name"] for lora in prepared_loras if lora["name"] != "No LoRA"]
    combined_name = " + ".join(lora_names) if lora_names else "No LoRA"
    
    return {
        "name": combined_name,
        "file": None,  # Multiple files handled in loras list
        "trigger": combined_trigger,
        "model_type": lora_configs[0].get("model_type", model_type),
        "loras": prepared_loras,  # List of individual LoRA configs
        "is_multiple": True
    }


def get_available_model_types() -> List[str]:
    """
    Get all available model types from the configuration.
    
    Returns:
        List of available model type strings
    """
    config = load_lora_config()
    # Filter out special configuration keys
    return [key for key in config.keys() if not key.startswith("_")]


def validate_lora_config() -> bool:
    """
    Validate the LoRA configuration file structure.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        config = load_lora_config()
        
        # Check if we have at least one model type
        if not config:
            return False
        
        # Check each model type (skip special keys like _model_mapping)
        for model_type, model_config in config.items():
            # Skip special configuration keys
            if model_type.startswith("_"):
                continue
                
            if "description" not in model_config:
                return False
            
            if "loras" not in model_config:
                return False
            
            # Check each LoRA in the model
            for lora_id, lora_config in model_config["loras"].items():
                required_fields = ["name", "description", "file", "trigger_words", "display_trigger", "strength_model", "strength_clip"]
                for field in required_fields:
                    if field not in lora_config:
                        return False
                
                # Check trigger_words structure
                trigger_words = lora_config["trigger_words"]
                if not isinstance(trigger_words, dict):
                    return False
                
                if "required" not in trigger_words or "optional" not in trigger_words:
                    return False
                
                if not isinstance(trigger_words["required"], list):
                    return False
                
                if not isinstance(trigger_words["optional"], list):
                    return False
                
                # Check strength values
                strength_model = lora_config.get("strength_model", 1.0)
                strength_clip = lora_config.get("strength_clip", 1.0)
                
                if not isinstance(strength_model, (int, float)) or not isinstance(strength_clip, (int, float)):
                    return False
                
                if not (0.1 <= strength_model <= 1.0) or not (0.1 <= strength_clip <= 1.0):
                    return False
        
        return True
    
    except Exception:
        return False