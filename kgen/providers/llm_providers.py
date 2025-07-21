"""LLM provider configuration for KGen.

This module handles the configuration and initialization of the
Large Language Model provider."""

from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI

from kgen.config.config import config


def get_llm(params: Optional[Dict[str, Any]] = None) -> ChatOpenAI:
    """
    Get an LLM instance configured from environment variables.

    Args:
        params: Optional parameters for the LLM

    Returns:
        ChatOpenAI: Configured LLM instance

    Raises:
        ValueError: If required API key is missing
    """
    api_key = config.LLM_API_KEY
    if not api_key:
        raise ValueError(
            "LLM_API_KEY environment variable is required"
        )

    return ChatOpenAI(
        api_key=api_key,
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
        timeout=1000000,
    )
