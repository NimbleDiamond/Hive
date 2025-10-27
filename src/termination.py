"""
Termination logic for submind conversations.
Implements hybrid approach: smart detection + max rounds fallback.
"""

from typing import List, Dict
from difflib import SequenceMatcher


class TerminationDetector:
    """
    Detects when a conversation should terminate based on various criteria.
    """

    def __init__(
        self,
        max_rounds: int = 3,
        detect_consensus: bool = True,
        consensus_threshold: float = 0.7,
        minimum_responses_per_submind: int = 1,
    ):
        """
        Initialize termination detector.

        Args:
            max_rounds: Maximum number of discussion rounds before forced termination
            detect_consensus: Enable smart consensus/completion detection
            consensus_threshold: Similarity threshold (0-1) for detecting repetition
            minimum_responses_per_submind: Minimum number of responses each submind must make
        """
        self.max_rounds = max_rounds
        self.detect_consensus = detect_consensus
        self.consensus_threshold = consensus_threshold
        self.minimum_responses_per_submind = minimum_responses_per_submind

        # Keywords that indicate completion
        self.completion_keywords = [
            "in conclusion",
            "to summarize",
            "in summary",
            "overall",
            "final thoughts",
            "to wrap up",
            "all things considered",
            "taking everything into account",
        ]

        # Consensus indicators
        self.consensus_keywords = [
            "i agree",
            "agreed",
            "consensus",
            "we all",
            "everyone agrees",
            "we're aligned",
            "common ground",
            "same page",
        ]

    def should_terminate(
        self,
        conversation_history: List[Dict[str, any]],
        current_round: int,
        expected_subminds: List[str] = None,
    ) -> tuple[bool, str]:
        """
        Determine if conversation should terminate.

        Args:
            conversation_history: List of all messages in the conversation
            current_round: Current discussion round number
            expected_subminds: List of submind names that should participate (optional)

        Returns:
            Tuple of (should_terminate, reason)
        """
        # First, check if minimum response requirement is met
        if not self._check_minimum_responses(conversation_history, expected_subminds):
            # Continue discussion until minimum responses met
            return False, ""

        # Check max rounds (hard limit)
        if current_round >= self.max_rounds:
            return True, f"Maximum rounds ({self.max_rounds}) reached"

        # If smart detection disabled, only use max rounds
        if not self.detect_consensus:
            return False, ""

        # Check for completion signals
        if self._detect_completion_signals(conversation_history):
            return True, "Completion signals detected in discussion"

        # Check for consensus
        if self._detect_consensus(conversation_history):
            return True, "Consensus reached among subminds"

        # Check for repetition/circular discussion
        if current_round > 1 and self._detect_repetition(conversation_history):
            return True, "Discussion becoming repetitive"

        return False, ""

    def _check_minimum_responses(
        self,
        history: List[Dict[str, any]],
        expected_subminds: List[str] = None
    ) -> bool:
        """
        Check if all subminds have met the minimum response requirement.

        Args:
            history: Conversation history
            expected_subminds: List of submind names that should participate (optional)

        Returns:
            True if all subminds have responded at least minimum_responses_per_submind times
        """
        # Count responses per speaker (excluding User and System)
        response_counts = {}
        for msg in history:
            speaker = msg.get("speaker", "Unknown")

            # Skip User and System messages
            if speaker in ["User", "System", "Unknown"]:
                continue

            response_counts[speaker] = response_counts.get(speaker, 0) + 1

        # Check if all speakers have met minimum requirement
        if not response_counts:
            # No submind responses yet
            return False

        # If expected_subminds is provided, check that ALL expected subminds have responded
        if expected_subminds:
            for expected_submind in expected_subminds:
                if expected_submind not in response_counts:
                    # This submind hasn't responded at all yet
                    return False
                if response_counts[expected_submind] < self.minimum_responses_per_submind:
                    # This submind hasn't met minimum responses
                    return False
            return True

        # Fallback: check all subminds that have responded meet minimum
        # (This is the old behavior for backwards compatibility)
        for count in response_counts.values():
            if count < self.minimum_responses_per_submind:
                return False

        return True

    def _detect_completion_signals(self, history: List[Dict[str, any]]) -> bool:
        """
        Detect if subminds are signaling completion.

        Args:
            history: Conversation history

        Returns:
            True if completion signals detected
        """
        if not history:
            return False

        # Check last few messages
        recent_messages = history[-min(5, len(history)):]

        for msg in recent_messages:
            content = msg.get("content", "").lower()

            # Check for completion keywords
            for keyword in self.completion_keywords:
                if keyword in content:
                    return True

        return False

    def _detect_consensus(self, history: List[Dict[str, any]]) -> bool:
        """
        Detect if subminds are reaching consensus.

        Args:
            history: Conversation history

        Returns:
            True if consensus detected
        """
        if len(history) < 3:
            return False

        # Check recent messages for consensus language
        recent_messages = history[-min(5, len(history)):]
        consensus_count = 0

        for msg in recent_messages:
            content = msg.get("content", "").lower()

            for keyword in self.consensus_keywords:
                if keyword in content:
                    consensus_count += 1
                    break

        # If multiple subminds express agreement
        return consensus_count >= 2

    def _detect_repetition(self, history: List[Dict[str, any]]) -> bool:
        """
        Detect if discussion is becoming circular/repetitive.

        Args:
            history: Conversation history

        Returns:
            True if significant repetition detected
        """
        if len(history) < 6:
            return False

        # Group messages by speaker
        messages_by_speaker = {}
        for msg in history:
            speaker = msg.get("speaker", "Unknown")
            content = msg.get("content", "")

            if speaker not in messages_by_speaker:
                messages_by_speaker[speaker] = []

            messages_by_speaker[speaker].append(content)

        # Check if each speaker is repeating themselves
        repetitive_speakers = 0

        for speaker, messages in messages_by_speaker.items():
            if len(messages) < 2:
                continue

            # Compare last message with previous messages
            last_message = messages[-1]

            for prev_message in messages[:-1]:
                similarity = self._text_similarity(last_message, prev_message)

                if similarity >= self.consensus_threshold:
                    repetitive_speakers += 1
                    break

        # If multiple speakers are repeating
        return repetitive_speakers >= 2

    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def get_status(self, current_round: int) -> str:
        """
        Get human-readable status message.

        Args:
            current_round: Current round number

        Returns:
            Status string
        """
        rounds_remaining = self.max_rounds - current_round
        return f"Round {current_round}/{self.max_rounds} ({rounds_remaining} remaining)"
