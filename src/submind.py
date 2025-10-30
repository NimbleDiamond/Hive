"""
Individual submind class representing one persona in the discussion.
"""

from typing import List, Dict, Optional, Union
from datetime import datetime
from subminds import get_system_prompt
from src.api_client import LMStudioClient, RateLimitError


class Submind:
    """
    Represents an individual submind with a specific role and personality.
    """

    def __init__(
        self,
        name: str,
        role: str,
        api_client: LMStudioClient,
        model: Union[str, List[str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        color: str = "white",
    ):
        """
        Initialize a submind.

        Args:
            name: Display name (e.g., "Doctrinal", "Analytical")
            role: Role identifier for system prompt (e.g., "traditional", "analytical")
            api_client: LM Studio API client instance
            model: Model identifier(s) to use - string for single model, list for fallbacks
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            color: Color for CLI display
        """
        self.name = name
        self.role = role
        self.api_client = api_client

        # Convert single model to list for uniform handling
        if isinstance(model, str):
            self.models = [model]
        else:
            self.models = model

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.color = color

        # Track which model is currently being used
        self.current_model = self.models[0]

        # Get system prompt for this role
        try:
            self.system_prompt = get_system_prompt(role)
        except KeyError as e:
            raise ValueError(f"Invalid role '{role}' for submind '{name}': {e}")

        # Track response count
        self.response_count = 0

    def generate_response(
        self,
        conversation_history: List[Dict[str, any]],
    ) -> Dict[str, any]:
        """
        Generate a response based on conversation history.

        Args:
            conversation_history: List of previous messages in the conversation
                Each message has: {speaker, content, timestamp, round}

        Returns:
            Message dict with: {speaker, content, timestamp, round}

        Raises:
            Exception: If response generation fails
        """
        # Build messages for API call
        # Note: LM Studio doesn't support "system" role, so we prepend it as a user message
        messages = []
        system_message_added = False

        # Add conversation history
        for msg in conversation_history:
            # Format previous messages for context
            speaker = msg.get("speaker", "Unknown")
            content = msg.get("content", "")

            if speaker == self.name:
                # This submind's previous messages
                messages.append({"role": "assistant", "content": content})
            elif speaker == "User":
                # Actual user messages
                # Prepend system prompt to the first user message (LM Studio compatibility)
                if not system_message_added:
                    content = f"{self.system_prompt}\n\n{content}"
                    system_message_added = True
                messages.append({"role": "user", "content": content})
            else:
                # Other subminds' messages - add speaker prefix for clarity
                formatted_content = f"[{speaker}]: {content}"
                # Prepend system prompt to first message if not added yet
                if not system_message_added:
                    formatted_content = f"{self.system_prompt}\n\n{formatted_content}"
                    system_message_added = True
                messages.append({"role": "user", "content": formatted_content})

        # If we didn't add the system prompt yet (empty history), add it now as first message
        if not system_message_added:
            messages.insert(0, {"role": "user", "content": self.system_prompt})

        # Try each model in order until one succeeds
        last_error = None
        for model in self.models:
            try:
                # Generate response
                response_content = self.api_client.generate_response(
                    model=model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                # Success! Update current model and increment count
                self.current_model = model
                self.response_count += 1

                # Create message object
                message = {
                    "speaker": self.name,
                    "content": response_content,
                    "timestamp": datetime.now().isoformat(),
                    "round": self.response_count,
                    "model": model,
                    "role": self.role,
                }

                return message

            except RateLimitError as e:
                # Rate limit hit - try next model if available
                last_error = e
                if model != self.models[-1]:  # Not the last model
                    print(f"  Rate limit on {model}, trying fallback...")
                    continue
                # Was the last model, will raise below

            except Exception as e:
                # Non-rate-limit error - don't try fallbacks
                raise Exception(f"Failed to generate response for {self.name}: {str(e)}") from e

        # All models failed due to rate limits
        raise Exception(
            f"All models exhausted for {self.name}. "
            f"Last error: {str(last_error)}"
        ) from last_error

    def reset(self):
        """Reset the submind's state (response count)."""
        self.response_count = 0

    def __repr__(self) -> str:
        models_str = ', '.join(self.models) if len(self.models) > 1 else self.models[0]
        return f"Submind(name='{self.name}', role='{self.role}', models='{models_str}')"
