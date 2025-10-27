"""
OpenRouter API client for submind system.
Uses OpenAI-compatible interface for OpenRouter.
"""

import os
from typing import List, Dict, Optional
from openai import OpenAI


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key. If None, reads from OPENROUTER_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. "
                "Set OPENROUTER_API_KEY environment variable or pass api_key parameter."
            )

        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        # Optional: Set app identification
        self.app_name = os.getenv("OPENROUTER_APP_NAME", "Submind")
        self.app_url = os.getenv("OPENROUTER_APP_URL", "")

    def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate a response from the specified model.

        Args:
            model: The model identifier (e.g., "openai/gpt-3.5-turbo")
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            The generated response text

        Raises:
            Exception: If API call fails
        """
        try:
            # Build extra headers
            extra_headers = {}
            if self.app_name:
                extra_headers["X-Title"] = self.app_name
            if self.app_url:
                extra_headers["HTTP-Referer"] = self.app_url

            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers=extra_headers if extra_headers else None,
            )

            # Extract response text
            content = response.choices[0].message.content

            # Clean up the response:
            # 1. Strip leading/trailing whitespace
            content = content.strip()

            # 2. Truncate at first [/INST] token to prevent multi-turn responses
            # Some instruct models (like Mistral) try to continue the conversation
            # themselves, playing multiple roles. Stop at the first instruction end token.
            import re
            if '[/INST]' in content:
                content = content.split('[/INST]')[0].strip()

            # 3. Remove any remaining instruction tokens ([INST], [/INST])
            content = re.sub(r'\[/?INST\]', '', content).strip()

            # 4. Remove any speaker prefixes the LLM might have added
            # (e.g., "[Analytical]: " or "Analytical: ")
            content = re.sub(r'^\[?\w+\]?:\s*', '', content)

            return content

        except Exception as e:
            # Check if this is a rate limit error
            error_msg = str(e).lower()
            if any(indicator in error_msg for indicator in [
                'rate limit', 'rate_limit', 'ratelimit',
                'quota', 'too many requests', '429'
            ]):
                raise RateLimitError(f"Rate limit exceeded for model {model}: {str(e)}") from e

            # Not a rate limit error, raise generic exception
            raise Exception(f"OpenRouter API error: {str(e)}") from e

    def list_models(self) -> List[str]:
        """
        List available models (placeholder - OpenRouter doesn't have a direct API for this).

        Returns:
            List of common model identifiers
        """
        # Common free and paid models on OpenRouter
        return [
            # Free models
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemini-flash-1.5",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "mistralai/mistral-7b-instruct:free",
            # Paid models
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-pro-1.5",
        ]

    def validate_connection(self) -> bool:
        """
        Test the API connection with a minimal request.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Make a minimal test call
            response = self.client.chat.completions.create(
                model="meta-llama/llama-3.2-3b-instruct:free",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
