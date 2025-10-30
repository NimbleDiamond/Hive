"""
LM Studio API client for submind system.
Uses OpenAI-compatible interface for LM Studio local server.
"""

import os
from typing import List, Dict, Optional
from openai import OpenAI


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""
    pass


class LMStudioClient:
    """Client for interacting with LM Studio local API server."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize LM Studio client.

        Args:
            base_url: LM Studio server URL. If None, reads from LMSTUDIO_BASE_URL env var.
                     Defaults to http://192.168.4.30:1234/v1

        Note:
            LM Studio doesn't require API authentication for local usage.
        """
        self.base_url = base_url or os.getenv("LMSTUDIO_BASE_URL", "http://192.168.4.30:1234/v1")

        # Initialize OpenAI client with LM Studio base URL
        # LM Studio doesn't require an API key for local usage
        self.client = OpenAI(
            base_url=self.base_url,
            api_key="lm-studio",  # Dummy key required by OpenAI client but not validated by LM Studio
        )

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
            model: The model identifier (e.g., "mistralai/mistral-7b-instruct-v0.3")
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            The generated response text

        Raises:
            Exception: If API call fails
        """
        try:
            # Make API call to LM Studio
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
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
            # Check if this is a rate limit error (less common with local LM Studio)
            error_msg = str(e).lower()
            if any(indicator in error_msg for indicator in [
                'rate limit', 'rate_limit', 'ratelimit',
                'quota', 'too many requests', '429'
            ]):
                raise RateLimitError(f"Rate limit exceeded for model {model}: {str(e)}") from e

            # Not a rate limit error, raise generic exception
            raise Exception(f"LM Studio API error: {str(e)}") from e

    def list_models(self) -> List[str]:
        """
        List available models from LM Studio.

        Returns:
            List of model identifiers available on the LM Studio server
        """
        try:
            # LM Studio supports the /v1/models endpoint
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            # Fallback to known model if API call fails
            print(f"Could not fetch models from LM Studio: {e}")
            return ["mistralai/mistral-7b-instruct-v0.3"]

    def validate_connection(self) -> bool:
        """
        Test the API connection with a minimal request.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get the list of available models as a lightweight test
            models = self.client.models.list()
            return len(models.data) > 0
        except Exception as e:
            print(f"Connection test failed: {e}")
            print(f"Make sure LM Studio is running at {self.base_url}")
            return False
