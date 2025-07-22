"""Model type definitions and utilities for YKGen.

This module provides dynamic model type definitions that load from
image_model_config.json, replacing hardcoded enums for better configurability."""

from typing import Dict, Optional
from .image_model_loader import (
    is_vpred_model as _is_vpred_model,
    is_simple_model as _is_simple_model,
    get_workflow_type as _get_workflow_type,
    get_model_display_name as _get_model_display_name,
    get_all_model_names,
    get_model_categories,
    find_model_by_name,
    get_model_category,
    model_type as ModelType,
    workflow_type as WorkflowType,
)


# Re-export functions for backward compatibility
def is_vpred_model(model_name: str) -> bool:
    """Check if a model uses vPred workflow.
    
    Args:
        model_name: The name of the model to check
        
    Returns:
        True if the model uses vPred workflow, False otherwise
    """
    return _is_vpred_model(model_name)


def is_simple_model(model_name: str) -> bool:
    """Check if a model uses simple workflow.
    
    Args:
        model_name: The name of the model to check
        
    Returns:
        True if the model uses simple workflow, False otherwise
    """
    return _is_simple_model(model_name)


def get_workflow_type(model_name: str) -> str:
    """Get the workflow type for a model.
    
    Args:
        model_name: The name of the model
        
    Returns:
        Workflow type string
    """
    return _get_workflow_type(model_name)


def get_model_display_name(model_name: str) -> str:
    """Get the display name for a model.
    
    Args:
        model_name: The name of the model
        
    Returns:
        Display name for the model
    """
    return _get_model_display_name(model_name)


# Additional utility functions
def get_all_models() -> list[str]:
    """Get all available model names.
    
    Returns:
        List of all model names
    """
    return get_all_model_names()


def get_all_workflows() -> list[str]:
    """Get all available workflow types.
    
    Returns:
        List of all workflow categories
    """
    return get_model_categories()


def model_exists(model_name: str) -> bool:
    """Check if a model exists in the configuration.
    
    Args:
        model_name: The name of the model to check
        
    Returns:
        True if the model exists, False otherwise
    """
    return find_model_by_name(model_name) is not None


def get_model_config(model_name: str) -> Optional[Dict]:
    """Get the full configuration for a model.
    
    Args:
        model_name: The name of the model
        
    Returns:
        Model configuration dict if found, None otherwise
    """
    return find_model_by_name(model_name)