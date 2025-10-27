"""
Conversation exporter for saving discussions to various formats.
"""

import json
import os
from typing import List, Dict
from datetime import datetime
from pathlib import Path


class ConversationExporter:
    """
    Exports conversations to JSON and Markdown formats.
    """

    def __init__(
        self,
        export_dir: str = "exports",
        formats: List[str] = None,
        include_metadata: bool = True,
    ):
        """
        Initialize exporter.

        Args:
            export_dir: Directory to save exports
            formats: List of formats to export ("json", "markdown")
            include_metadata: Include metadata in exports
        """
        self.export_dir = export_dir
        self.formats = formats or ["json", "markdown"]
        self.include_metadata = include_metadata

        # Create export directory if it doesn't exist
        Path(export_dir).mkdir(parents=True, exist_ok=True)

    def export(
        self,
        conversation_history: List[Dict[str, any]],
        summary: Dict[str, any],
        filename_prefix: str = None,
    ) -> Dict[str, str]:
        """
        Export conversation to configured formats.

        Args:
            conversation_history: List of conversation messages
            summary: Conversation summary dict
            filename_prefix: Optional prefix for filename (defaults to timestamp)

        Returns:
            Dict mapping format to saved filepath
        """
        if not filename_prefix:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_prefix = f"conversation_{timestamp}"

        saved_files = {}

        if "json" in self.formats:
            json_path = self._export_json(conversation_history, summary, filename_prefix)
            saved_files["json"] = json_path

        if "markdown" in self.formats:
            md_path = self._export_markdown(conversation_history, summary, filename_prefix)
            saved_files["markdown"] = md_path

        return saved_files

    def _export_json(
        self,
        history: List[Dict[str, any]],
        summary: Dict[str, any],
        filename_prefix: str,
    ) -> str:
        """
        Export conversation to JSON format.

        Args:
            history: Conversation history
            summary: Conversation summary
            filename_prefix: Filename prefix

        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.export_dir, f"{filename_prefix}.json")

        export_data = {
            "messages": history,
        }

        if self.include_metadata:
            export_data["metadata"] = summary

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return filepath

    def _export_markdown(
        self,
        history: List[Dict[str, any]],
        summary: Dict[str, any],
        filename_prefix: str,
    ) -> str:
        """
        Export conversation to Markdown format.

        Args:
            history: Conversation history
            summary: Conversation summary
            filename_prefix: Filename prefix

        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.export_dir, f"{filename_prefix}.md")

        lines = []

        # Title
        lines.append("# Submind Discussion\n")

        # Metadata section
        if self.include_metadata and summary:
            lines.append("## Metadata\n")
            lines.append(f"- **User Prompt**: {summary.get('user_prompt', 'N/A')}")
            lines.append(f"- **Total Messages**: {summary.get('total_messages', 0)}")
            lines.append(f"- **Total Rounds**: {summary.get('total_rounds', 0)}")
            lines.append(f"- **Start Time**: {summary.get('start_time', 'N/A')}")
            lines.append(f"- **End Time**: {summary.get('end_time', 'N/A')}")

            duration = summary.get('duration_seconds')
            if duration:
                lines.append(f"- **Duration**: {duration:.2f} seconds")

            lines.append(f"- **Subminds**: {', '.join(summary.get('subminds', []))}")
            lines.append("")

        # Conversation section
        lines.append("## Conversation\n")

        current_round = -1
        for msg in history:
            msg_round = msg.get("round", 0)

            # Add round header if new round
            if msg_round != current_round:
                current_round = msg_round
                if current_round == 0:
                    lines.append("### Initial Prompt\n")
                else:
                    lines.append(f"### Round {current_round}\n")

            speaker = msg.get("speaker", "Unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")

            # Format message
            if speaker == "System":
                lines.append(f"*{content}*\n")
            elif speaker == "User":
                lines.append(f"**{speaker}**: {content}\n")
            else:
                lines.append(f"**{speaker}**: {content}\n")

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath

    def export_summary_only(
        self,
        summary: Dict[str, any],
        filename: str = "summary.json",
    ) -> str:
        """
        Export only the conversation summary.

        Args:
            summary: Conversation summary dict
            filename: Output filename

        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.export_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return filepath
