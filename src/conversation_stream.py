"""
Streaming conversation manager for real-time web interface.
Yields events as they happen for Server-Sent Events.
"""

import time
from typing import List, Dict, Generator
from datetime import datetime
from src.submind import Submind
from src.termination import TerminationDetector


class StreamingConversation:
    """
    Manages a multi-agent discussion with real-time streaming support.
    """

    def __init__(
        self,
        subminds: List[Submind],
        termination_detector: TerminationDetector,
        delay_between_subminds: float = 0.0,
    ):
        """
        Initialize streaming conversation manager.

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

    def stream_conversation(self, user_prompt: str) -> Generator[Dict[str, any], None, None]:
        """
        Start a conversation and yield events as they happen.

        Args:
            user_prompt: The initial prompt/question from the user

        Yields:
            Event dictionaries with 'type' and relevant data
            Event types: 'start', 'user_message', 'submind_start', 'submind_response',
                        'round_complete', 'termination', 'complete'
        """
        self.user_prompt = user_prompt
        self.start_time = datetime.now()

        # Yield start event
        yield {
            "type": "start",
            "timestamp": self.start_time.isoformat(),
        }

        # Add user prompt to history
        user_message = {
            "speaker": "User",
            "content": user_prompt,
            "timestamp": self.start_time.isoformat(),
            "round": 0,
            "role": "user",
        }
        self.history.append(user_message)

        # Yield user message event
        yield {
            "type": "user_message",
            "message": user_message,
        }

        # Run discussion rounds with streaming
        yield from self._stream_discussion()

        self.end_time = datetime.now()

        # Yield complete event with summary
        yield {
            "type": "complete",
            "summary": self.get_summary(),
            "history": self.history,
        }

    def _stream_discussion(self) -> Generator[Dict[str, any], None, None]:
        """
        Execute discussion rounds and yield events for each response.

        Yields:
            Event dictionaries for each submind response
        """
        while True:
            self.current_round += 1

            # Yield round start
            yield {
                "type": "round_start",
                "round": self.current_round,
            }

            # Each submind responds in sequence
            for submind in self.subminds:
                # Yield submind start event
                yield {
                    "type": "submind_start",
                    "submind": submind.name,
                    "round": self.current_round,
                }

                try:
                    # Generate response
                    message = submind.generate_response(self.history)
                    self.history.append(message)

                    # Yield submind response event
                    yield {
                        "type": "submind_response",
                        "message": message,
                    }

                    # Add delay to simulate reading time
                    if self.delay_between_subminds > 0:
                        time.sleep(self.delay_between_subminds)

                except Exception as e:
                    # Yield error event
                    yield {
                        "type": "error",
                        "submind": submind.name,
                        "error": str(e),
                    }

                    # Add delay even after error to maintain pacing
                    if self.delay_between_subminds > 0:
                        time.sleep(self.delay_between_subminds)

            # Yield round complete
            yield {
                "type": "round_complete",
                "round": self.current_round,
            }

            # Check if conversation should terminate
            expected_subminds = [submind.name for submind in self.subminds]
            should_terminate, reason = self.termination_detector.should_terminate(
                self.history, self.current_round, expected_subminds
            )

            if should_terminate:
                # Add termination notice to history
                termination_message = {
                    "speaker": "System",
                    "content": f"Discussion terminated: {reason}",
                    "timestamp": datetime.now().isoformat(),
                    "round": self.current_round,
                    "role": "system",
                }
                self.history.append(termination_message)

                # Yield termination event
                yield {
                    "type": "termination",
                    "message": termination_message,
                    "reason": reason,
                }
                break

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
