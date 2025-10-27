"""
Conversation manager for orchestrating submind discussions.
"""

import time
from typing import List, Dict, Optional
from datetime import datetime
from src.submind import Submind
from src.termination import TerminationDetector


class Conversation:
    """
    Manages a multi-agent discussion between subminds.
    """

    def __init__(
        self,
        subminds: List[Submind],
        termination_detector: TerminationDetector,
        delay_between_subminds: float = 0.0,
    ):
        """
        Initialize conversation manager.

        Args:
            subminds: List of submind instances to participate
            termination_detector: Termination detector instance
            delay_between_subminds: Seconds to wait between each submind response
        """
        self.subminds = subminds
        self.termination_detector = termination_detector
        self.delay_between_subminds = delay_between_subminds
        self.history: List[Dict[str, any]] = []
        self.current_round = 0
        self.user_prompt = None
        self.start_time = None
        self.end_time = None

    def start(self, user_prompt: str) -> List[Dict[str, any]]:
        """
        Start a new conversation with a user prompt.

        Args:
            user_prompt: The initial prompt/question from the user

        Returns:
            List of all messages in the conversation

        Raises:
            ValueError: If conversation already started
        """
        if self.history:
            raise ValueError("Conversation already started. Use reset() to start new conversation.")

        self.user_prompt = user_prompt
        self.start_time = datetime.now()

        # Add user prompt as first message
        self.history.append({
            "speaker": "User",
            "content": user_prompt,
            "timestamp": self.start_time.isoformat(),
            "round": 0,
            "role": "user",
        })

        # Run discussion rounds
        self._run_discussion()

        self.end_time = datetime.now()

        return self.history

    def _run_discussion(self):
        """
        Execute the discussion rounds with termination logic.
        """
        while True:
            self.current_round += 1

            # Each submind responds in sequence
            for submind in self.subminds:
                message = submind.generate_response(self.history)
                self.history.append(message)

                # Add delay to simulate reading time
                if self.delay_between_subminds > 0:
                    time.sleep(self.delay_between_subminds)

            # Check if conversation should terminate
            expected_subminds = [submind.name for submind in self.subminds]
            should_terminate, reason = self.termination_detector.should_terminate(
                self.history, self.current_round, expected_subminds
            )

            if should_terminate:
                # Add termination notice to history
                self.history.append({
                    "speaker": "System",
                    "content": f"Discussion terminated: {reason}",
                    "timestamp": datetime.now().isoformat(),
                    "round": self.current_round,
                    "role": "system",
                })
                break

    def get_messages_by_round(self, round_num: int) -> List[Dict[str, any]]:
        """
        Get all messages from a specific round.

        Args:
            round_num: Round number (0 = user prompt)

        Returns:
            List of messages from that round
        """
        return [msg for msg in self.history if msg.get("round") == round_num]

    def get_messages_by_speaker(self, speaker: str) -> List[Dict[str, any]]:
        """
        Get all messages from a specific speaker.

        Args:
            speaker: Speaker name

        Returns:
            List of messages from that speaker
        """
        return [msg for msg in self.history if msg.get("speaker") == speaker]

    def get_summary(self) -> Dict[str, any]:
        """
        Get conversation summary statistics.

        Returns:
            Dict with summary information
        """
        if not self.history:
            return {}

        # Count messages by speaker
        speaker_counts = {}
        for msg in self.history:
            speaker = msg.get("speaker", "Unknown")
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1

        # Calculate duration
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            "user_prompt": self.user_prompt,
            "total_messages": len(self.history),
            "total_rounds": self.current_round,
            "speaker_counts": speaker_counts,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "subminds": [submind.name for submind in self.subminds],
        }

    def reset(self):
        """
        Reset conversation state for a new discussion.
        """
        self.history = []
        self.current_round = 0
        self.user_prompt = None
        self.start_time = None
        self.end_time = None

        # Reset all subminds
        for submind in self.subminds:
            submind.reset()

    def get_full_history(self) -> List[Dict[str, any]]:
        """
        Get complete conversation history.

        Returns:
            List of all messages
        """
        return self.history.copy()

    def __repr__(self) -> str:
        submind_names = [s.name for s in self.subminds]
        return f"Conversation(subminds={submind_names}, rounds={self.current_round})"
