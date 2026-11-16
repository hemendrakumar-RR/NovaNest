"""
NovaNest AI Provider Abstraction
Base interface and data models for AI generative providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class ProviderStatus(str, Enum):
    READY = "ready"
    UNCONFIGURED = "unconfigured"
    ERROR = "error"
    MOCK = "mock"


@dataclass
class AIProviderResult:
    text: str
    status: ProviderStatus
    provider_name: str
    model_name: str
    error: Optional[str] = None
    tokens_used: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "status": self.status.value,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "error": self.error,
            "tokens_used": self.tokens_used
        }


class BaseAIProvider(ABC):
    """Abstract base class for generative AI providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> AIProviderResult:
        """Generates a text completion given a prompt and optional context."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider has valid credentials configured."""
        pass
