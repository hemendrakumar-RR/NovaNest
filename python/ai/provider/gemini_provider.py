"""
Google Gemini AI Provider Implementation
Calls Google Gemini REST API v1beta using official endpoints with robust error handling.
"""

import os
import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

from python.ai.provider.base import BaseAIProvider, AIProviderResult, ProviderStatus

# Ensure .env is loaded safely
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini API provider using official REST endpoint.
    Supports current Gemini models: gemini-2.5-flash, gemini-1.5-flash, gemini-2.0-flash.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 15
    ):
        raw_key = api_key or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        self.api_key = raw_key.strip() if raw_key else ""
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def get_status(self) -> Dict[str, str]:
        if not self.is_configured():
            return {
                "status": "unconfigured",
                "message": "Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment"
            }
        return {
            "status": "ready",
            "message": f"Gemini provider configured ({self.model})"
        }

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> AIProviderResult:
        if not self.is_configured():
            return AIProviderResult(
                text="Google Gemini API key is not configured in your environment. Set GEMINI_API_KEY in your .env file to enable live AI responses.",
                status=ProviderStatus.UNCONFIGURED,
                provider_name="gemini",
                model_name=self.model,
                error="GEMINI_API_KEY not found in environment."
            )

        endpoint = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        # Construct request payload with strict role validation for Gemini v1beta
        contents = []

        # Multi-turn history if provided
        if history:
            normalized_history = []
            for turn in history[-8:]:  # Keep recent turns
                raw_role = turn.get("role", "user")
                role = "user" if raw_role in ["user", "human"] else "model"
                text = turn.get("content", "").strip()
                if text:
                    normalized_history.append((role, text))

            # Ensure roles alternate and first turn is 'user'
            # Discard any leading 'model' turns
            while normalized_history and normalized_history[0][0] != "user":
                normalized_history.pop(0)

            # Build alternating sequence
            last_role = None
            for role, text in normalized_history:
                if role != last_role:
                    contents.append({
                        "role": role,
                        "parts": [{"text": text}]
                    })
                    last_role = role
                else:
                    # Append to previous parts if consecutive same role
                    if contents:
                        contents[-1]["parts"].append({"text": text})

        # Append current user prompt
        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"].append({"text": prompt})
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)

            # Fallback to gemini-1.5-flash if 2.5-flash returns 404
            if resp.status_code == 404 and self.model != "gemini-1.5-flash":
                fallback_model = "gemini-1.5-flash"
                fallback_endpoint = f"{self.base_url}/{fallback_model}:generateContent?key={self.api_key}"
                resp = requests.post(fallback_endpoint, json=payload, headers=headers, timeout=self.timeout)

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        text = parts[0]["text"]
                        usage = data.get("usageMetadata", {})
                        tokens = usage.get("totalTokenCount")
                        return AIProviderResult(
                            text=text,
                            status=ProviderStatus.READY,
                            provider_name="gemini",
                            model_name=self.model,
                            tokens_used=tokens
                        )
                return AIProviderResult(
                    text="No response text generated by Gemini.",
                    status=ProviderStatus.ERROR,
                    provider_name="gemini",
                    model_name=self.model,
                    error="Empty candidate content"
                )

            elif resp.status_code == 429:
                err_msg = "Gemini API rate limit exceeded. Please wait a moment before trying again."
                logger.warning(err_msg)
                return AIProviderResult(
                    text=err_msg,
                    status=ProviderStatus.ERROR,
                    provider_name="gemini",
                    model_name=self.model,
                    error="Rate limit (HTTP 429)"
                )

            elif resp.status_code in [400, 401, 403]:
                err_msg = "Gemini API authentication failed. Please verify that your GEMINI_API_KEY is valid."
                logger.error(f"Gemini Auth Error ({resp.status_code}): {resp.text}")
                return AIProviderResult(
                    text=err_msg,
                    status=ProviderStatus.ERROR,
                    provider_name="gemini",
                    model_name=self.model,
                    error=f"Auth error ({resp.status_code})"
                )

            else:
                err_msg = f"Gemini API returned status {resp.status_code}."
                logger.error(f"{err_msg}: {resp.text}")
                return AIProviderResult(
                    text=err_msg,
                    status=ProviderStatus.ERROR,
                    provider_name="gemini",
                    model_name=self.model,
                    error=f"HTTP {resp.status_code}"
                )

        except requests.Timeout:
            err_msg = "Gemini API request timed out after 15 seconds. Please try again."
            logger.warning(err_msg)
            return AIProviderResult(
                text=err_msg,
                status=ProviderStatus.ERROR,
                provider_name="gemini",
                model_name=self.model,
                error="Timeout"
            )

        except Exception as e:
            err_msg = f"Network or provider error communicating with Gemini: {str(e)}"
            logger.error(err_msg)
            return AIProviderResult(
                text=err_msg,
                status=ProviderStatus.ERROR,
                provider_name="gemini",
                model_name=self.model,
                error=str(e)
            )


# Compatibility alias
GeminiAIProvider = GeminiProvider
