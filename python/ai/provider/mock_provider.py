"""
Mock AI Provider Implementation for Automated Testing
Simulates AI responses without calling external paid APIs.
"""

from typing import Optional, List, Dict
from python.ai.provider.base import BaseAIProvider, AIProviderResult, ProviderStatus


class MockAIProvider(BaseAIProvider):
    """
    Mock provider for automated unit testing and offline development.
    Returns deterministic or simulated responses.
    """

    def __init__(self, canned_response: Optional[str] = None):
        self.canned_response = canned_response

    def is_configured(self) -> bool:
        return True

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> AIProviderResult:
        if self.canned_response:
            text = self.canned_response
        else:
            text = f"[Mock AI Business Analyst Analysis]\nBased on the project's verified metrics, the inquiry regarding '{prompt[:50]}' was processed."

        return AIProviderResult(
            text=text,
            status=ProviderStatus.MOCK,
            provider_name="mock",
            model_name="mock-analyst-v1",
            tokens_used=42
        )
