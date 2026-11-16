"""
AI Provider Factory
Centralized discovery and initialization of generative providers.
"""

import os
from python.ai.provider.base import BaseAIProvider
from python.ai.provider.gemini_provider import GeminiProvider
from python.ai.provider.mock_provider import MockAIProvider


def get_ai_provider(provider_type: str = None) -> BaseAIProvider:
    """
    Factory function returning the configured AI provider.
    Defaults to Gemini, falls back to Mock in test mode.
    """
    selected = provider_type or os.environ.get("AI_PROVIDER", "gemini").lower()

    if selected == "mock":
        return MockAIProvider()
    elif selected == "gemini":
        return GeminiProvider()
    elif selected == "openai":
        # Placeholder for OpenAI GPT provider extensibility
        raise NotImplementedError("OpenAI provider module is not yet configured.")
    else:
        # Default to Gemini
        return GeminiProvider()
