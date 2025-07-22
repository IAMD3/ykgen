"""Model type enumerations for YKGen.

This module defines the available model types and provides utilities
for model type checking and workflow selection.
"""

from enum import Enum
from typing import Set


class ModelType(Enum):
    """Enumeration of available model types."""
    
    # Simple workflow models
    FLUX_SCHNELL = "flux-schnell"
    WAI_ILLUSTRIOUS = "wai-illustrious"
    
    # vPred workflow models
    ILLUSTRIOUS_VPRED = "illustrious-vpred"


class WorkflowType(Enum):
    """Enumeration of workflow types."""
    
    SIMPLE = "simple"
    VPRED = "vpred"


# Model type to workflow mapping
MODEL_WORKFLOW_MAPPING = {
    ModelType.FLUX_SCHNELL: WorkflowType.SIMPLE,
    ModelType.WAI_ILLUSTRIOUS: WorkflowType.SIMPLE,  # Fixed: WaiNSFW should use simple workflow
    ModelType.ILLUSTRIOUS_VPRED: WorkflowType.VPRED,
}

# Legacy string-based sets for backward compatibility
VPRED_MODELS: Set[str] = {
    ModelType.ILLUSTRIOUS_VPRED.value,
}

SIMPLE_MODELS: Set[str] = {
    ModelType.FLUX_SCHNELL.value,
    ModelType.WAI_ILLUSTRIOUS.value,
}


def is_vpred_model(model_type: str) -> bool:
    """Check if a model type uses the vPred workflow.
    
    Args:
        model_type: The model type string to check
        
    Returns:
        bool: True if the model uses vPred workflow, False otherwise
    """
    return model_type in VPRED_MODELS


def is_simple_model(model_type: str) -> bool:
    """Check if a model type uses the simple workflow.
    
    Args:
        model_type: The model type string to check
        
    Returns:
        bool: True if the model uses simple workflow, False otherwise
    """
    return model_type in SIMPLE_MODELS


def get_workflow_type(model_type: str) -> WorkflowType:
    """Get the workflow type for a given model type.
    
    Args:
        model_type: The model type string
        
    Returns:
        WorkflowType: The workflow type for the model
        
    Raises:
        ValueError: If the model type is not recognized
    """
    try:
        model_enum = ModelType(model_type)
        return MODEL_WORKFLOW_MAPPING[model_enum]
    except ValueError:
        raise ValueError(f"Unknown model type: {model_type}")


def get_model_display_name(model_type: str) -> str:
    """Get a human-readable display name for a model type.
    
    Args:
        model_type: The model type string
        
    Returns:
        str: Human-readable model name
    """
    display_names = {
        ModelType.FLUX_SCHNELL.value: "Flux-Schnell",
        ModelType.WAI_ILLUSTRIOUS.value: "WaiNSFW Illustrious",
        ModelType.ILLUSTRIOUS_VPRED.value: "Illustrious vPred",
    }
    
    return display_names.get(model_type, model_type)