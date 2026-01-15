"""
Azure Model Configuration

Utilities for managing Azure OpenAI model configurations, including
support for multiple model providers hosted on Azure (OpenAI, Anthropic Claude,
xAI Grok, DeepSeek, etc.).

Based on the implementation from tubeOnAI web-app-v2/src/lib/model-manager.ts
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AzureModelConfig:
    """
    Configuration for Azure OpenAI models.

    Attributes:
        api_key: Azure OpenAI API key
        endpoint: Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com)
        deployment_name: Azure deployment name
        api_version: Azure API version (default: 2024-08-01-preview)
        model_name: Actual model name (e.g., gpt-4o, claude-sonnet-4-5, grok-3)
    """

    api_key: str
    endpoint: str
    deployment_name: str
    api_version: str = "2024-08-01-preview"
    model_name: Optional[str] = None


def is_azure_anthropic_model(model_name: str) -> bool:
    """
    Check if a model is an Azure-hosted Anthropic model (Claude).

    Azure supports hosting Claude models via Anthropic's API format.

    Args:
        model_name: The model name to check (e.g., "claude-haiku-4-5", "claude-sonnet-4-5")

    Returns:
        True if the model is an Anthropic/Claude model, False otherwise

    Examples:
        >>> is_azure_anthropic_model("claude-haiku-4-5")
        True
        >>> is_azure_anthropic_model("gpt-4o")
        False
    """
    if not model_name:
        return False

    lower = model_name.lower()

    # Anthropic Claude model patterns
    claude_patterns = [
        "claude-",
        "claude3",
        "claude4",
        "claude-haiku",
        "claude-sonnet",
        "claude-opus",
    ]

    return any(pattern in lower for pattern in claude_patterns)


def is_azure_xai_model(model_name: str) -> bool:
    """
    Check if a model is an Azure-hosted xAI model (Grok).

    Azure hosts Grok models using OpenAI-compatible API format.

    Args:
        model_name: The model name to check (e.g., "grok-3", "grok-4-fast")

    Returns:
        True if the model is an xAI/Grok model, False otherwise

    Examples:
        >>> is_azure_xai_model("grok-3")
        True
        >>> is_azure_xai_model("gpt-4o")
        False
    """
    if not model_name:
        return False

    lower = model_name.lower()

    # xAI Grok model patterns
    grok_patterns = ["grok-", "grok"]

    return any(pattern in lower for pattern in grok_patterns)


def is_azure_deepseek_model(model_name: str) -> bool:
    """
    Check if a model is an Azure-hosted DeepSeek model.

    Azure hosts DeepSeek models using OpenAI-compatible API format.

    Args:
        model_name: The model name to check (e.g., "deepseek-v3", "deepseek-r1")

    Returns:
        True if the model is a DeepSeek model, False otherwise

    Examples:
        >>> is_azure_deepseek_model("deepseek-v3.1")
        True
        >>> is_azure_deepseek_model("gpt-4o")
        False
    """
    if not model_name:
        return False

    lower = model_name.lower()

    # DeepSeek model patterns
    deepseek_patterns = ["deepseek-", "deepseek"]

    return any(pattern in lower for pattern in deepseek_patterns)


def is_azure_dalle_model(model_name: str) -> bool:
    """
    Check if a model is an Azure DALL-E model for image generation.

    Azure OpenAI only supports DALL-E models for image generation.
    Reference: https://go.microsoft.com/fwlink/?linkid=2197993

    Args:
        model_name: The model name to check (e.g., "dall-e-2", "dall-e-3")

    Returns:
        True if the model is a DALL-E model, False otherwise

    Examples:
        >>> is_azure_dalle_model("dall-e-3")
        True
        >>> is_azure_dalle_model("gpt-5")
        False
    """
    if not model_name:
        return False

    lower = model_name.lower()

    # Azure-supported DALL-E patterns
    dalle_patterns = ["dall-e-2", "dall-e-3", "dalle-2", "dalle-3"]

    return any(pattern in lower for pattern in dalle_patterns)


def get_azure_model_type(model_name: str) -> str:
    """
    Detect the model type for Azure-hosted models.

    Args:
        model_name: The model name to check

    Returns:
        One of: "anthropic", "xai", "deepseek", "openai"

    Examples:
        >>> get_azure_model_type("claude-sonnet-4-5")
        'anthropic'
        >>> get_azure_model_type("grok-3")
        'xai'
        >>> get_azure_model_type("gpt-4o")
        'openai'
    """
    if is_azure_anthropic_model(model_name):
        return "anthropic"
    elif is_azure_xai_model(model_name):
        return "xai"
    elif is_azure_deepseek_model(model_name):
        return "deepseek"
    else:
        return "openai"
