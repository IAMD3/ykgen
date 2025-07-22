"""Image Model Configuration Loader

This module provides functions to load and manage image model configurations
from the image_model_config.json file, replacing hardcoded model definitions.
"""

import json
from typing import Dict, List, Optional, Any, Set
from pathlib import Path



def get_image_model_config_path() -> str:
    """Get the path to the image model configuration file."""
    return str(_get_image_model_config_path())

def _get_image_model_config_path() :
    """Get the path to the image model configuration file."""
    current_dir = Path(__file__).parent.parent.parent
    return  current_dir / "image_model_config.json"



def load_image_model_config() -> Dict[str, Any]:
    """Load the image model configuration from the JSON file.
    
    Returns:
        Dictionary containing the image model configuration
    """
    config_path = get_image_model_config_path()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Image model configuration file not found at: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in image model configuration file: {e}")


def get_all_model_names() -> List[str]:
    """Get all available model names from the configuration.
    
    Returns:
        List of all model names across all categories
    """
    config = load_image_model_config()
    model_names = []
    
    for category_data in config.values():
        if isinstance(category_data, dict) and "models" in category_data:
            for model in category_data["models"]:
                if "name" in model:
                    model_names.append(model["name"])
    
    return model_names


def get_model_categories() -> List[str]:
    """Get all model categories (workflow types) from the configuration.
    
    Returns:
        List of category names (e.g., 'simple', 'vpred')
    """
    config = load_image_model_config()
    return list(config.keys())


def get_models_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all models in a specific category.
    
    Args:
        category: The category name (e.g., 'simple', 'vpred')
        
    Returns:
        List of model configurations in the category
    """
    config = load_image_model_config()
    category_data = config.get(category, {})
    
    if isinstance(category_data, dict) and "models" in category_data:
        return category_data["models"]
    
    return []


def find_model_by_name(model_name: str) -> Optional[Dict[str, Any]]:
    """Find a model configuration by name.
    
    Args:
        model_name: The name of the model to find
        
    Returns:
        Model configuration dict if found, None otherwise
    """
    config = load_image_model_config()
    
    for category_data in config.values():
        if isinstance(category_data, dict) and "models" in category_data:
            for model in category_data["models"]:
                if model.get("name") == model_name:
                    return model
    
    return None


def get_model_category(model_name: str) -> Optional[str]:
    """Get the category (workflow type) for a specific model.
    
    Args:
        model_name: The name of the model
        
    Returns:
        Category name if found, None otherwise
    """
    config = load_image_model_config()
    
    for category, category_data in config.items():
        if isinstance(category_data, dict) and "models" in category_data:
            for model in category_data["models"]:
                if model.get("name") == model_name:
                    return category
    
    return None


def is_vpred_model(model_name: str) -> bool:
    """Check if a model uses vPred workflow.
    
    Args:
        model_name: The name of the model to check
        
    Returns:
        True if the model uses vPred workflow, False otherwise
    """
    category = get_model_category(model_name)
    return category == "vpred"


def is_simple_model(model_name: str) -> bool:
    """Check if a model uses simple workflow.
    
    Args:
        model_name: The name of the model to check
        
    Returns:
        True if the model uses simple workflow, False otherwise
    """
    category = get_model_category(model_name)
    return category == "simple"


def get_workflow_type(model_name: str) -> str:
    """Get the workflow type for a model.
    
    Args:
        model_name: The name of the model
        
    Returns:
        Workflow type string (category name)
    """
    category = get_model_category(model_name)
    if category is None:
        # Fallback to simple for unknown models
        return "simple"
    return category


def get_model_display_name(model_name: str) -> str:
    """Get the display name for a model.
    
    Args:
        model_name: The name of the model
        
    Returns:
        Display name for the model
    """
    model_config = find_model_by_name(model_name)
    if model_config:
        return model_config.get("name", model_name)
    return model_name


def get_default_model_for_category(category: str) -> Optional[str]:
    """Get the default model name for a category.
    
    Args:
        category: The category name
        
    Returns:
        Default model name if found, None otherwise
    """
    models = get_models_by_category(category)
    
    for model in models:
        if model.get("default", False):
            return model.get("name")
    
    # If no default is set, return the first model
    if models:
        return models[0].get("name")
    
    return None


def get_all_default_models() -> Dict[str, str]:
    """Get all default models for each category.
    
    Returns:
        Dictionary mapping category to default model name
    """
    categories = get_model_categories()
    defaults = {}
    
    for category in categories:
        default_model = get_default_model_for_category(category)
        if default_model:
            defaults[category] = default_model
    
    return defaults


# Dynamic enum-like classes for backward compatibility
class ModelType:
    """Dynamic model type class that loads from configuration."""
    
    def __init__(self):
        self._models = None
    
    @property
    def models(self) -> Set[str]:
        """Get all available model names."""
        if self._models is None:
            self._models = set(get_all_model_names())
        return self._models
    
    def __contains__(self, model_name: str) -> bool:
        """Check if a model name exists in the configuration."""
        return model_name in self.models
    
    def __iter__(self):
        """Iterate over all model names."""
        return iter(self.models)


class WorkflowType:
    """Dynamic workflow type class that loads from configuration."""
    
    def __init__(self):
        self._categories = None
    
    @property
    def categories(self) -> Set[str]:
        """Get all available workflow categories."""
        if self._categories is None:
            self._categories = set(get_model_categories())
        return self._categories
    
    def __contains__(self, category: str) -> bool:
        """Check if a workflow category exists in the configuration."""
        return category in self.categories
    
    def __iter__(self):
        """Iterate over all workflow categories."""
        return iter(self.categories)


# Create instances for backward compatibility
model_type = ModelType()
workflow_type = WorkflowType()