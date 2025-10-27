#!/usr/bin/env python3
"""
Submind System - Multi-agent discussion CLI
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from src import (
    OpenRouterClient,
    Submind,
    Conversation,
    TerminationDetector,
    ConversationExporter,
)


class SubmindCLI:
    """Command-line interface for Submind system."""

    def __init__(self):
        self.console = Console()
        self.config = None
        self.api_client = None
        self.subminds = []
        self.conversation = None
        self.exporter = None

    def load_config(self, config_path: str = "config.yaml") -> bool:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file

        Returns:
            True if successful
        """
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
            return True
        except Exception as e:
            self.console.print(f"[red]Error loading config: {e}[/red]")
            return False

    def initialize_api_client(self) -> bool:
        """
        Initialize OpenRouter API client.

        Returns:
            True if successful
        """
        try:
            self.api_client = OpenRouterClient()
            self.console.print("[green]✓[/green] API client initialized")
            return True
        except Exception as e:
            self.console.print(f"[red]✗ Error initializing API client: {e}[/red]")
            self.console.print("\n[yellow]Make sure you have set OPENROUTER_API_KEY in your .env file[/yellow]")
            return False

    def initialize_subminds(self) -> bool:
        """
        Initialize all subminds from config.

        Returns:
            True if successful
        """
        try:
            default_model = self.config.get("default_model", "meta-llama/llama-3.2-3b-instruct:free")

            for submind_config in self.config.get("subminds", []):
                name = submind_config["name"]
                role = submind_config["role"]

                # Handle both 'model' (single) and 'models' (list with fallbacks)
                if "models" in submind_config and submind_config["models"]:
                    model = submind_config["models"]  # List of models
                elif "model" in submind_config and submind_config["model"]:
                    model = submind_config["model"]  # Single model
                else:
                    model = default_model  # Fallback to default

                temperature = submind_config.get("temperature", 0.7)
                max_tokens = submind_config.get("max_tokens", 500)
                color = submind_config.get("color", "white")

                submind = Submind(
                    name=name,
                    role=role,
                    api_client=self.api_client,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    color=color,
                )

                self.subminds.append(submind)

            self.console.print(f"[green]✓[/green] Initialized {len(self.subminds)} subminds")
            return True

        except Exception as e:
            self.console.print(f"[red]✗ Error initializing subminds: {e}[/red]")
            return False

    def initialize_components(self) -> bool:
        """
        Initialize conversation and exporter components.

        Returns:
            True if successful
        """
        try:
            # Initialize termination detector
            conv_config = self.config.get("conversation", {})
            termination_detector = TerminationDetector(
                max_rounds=conv_config.get("max_rounds", 3),
                detect_consensus=conv_config.get("detect_consensus", True),
                consensus_threshold=conv_config.get("consensus_threshold", 0.7),
                minimum_responses_per_submind=conv_config.get("minimum_responses_per_submind", 1),
            )

            # Initialize conversation manager
            self.conversation = Conversation(
                subminds=self.subminds,
                termination_detector=termination_detector,
                delay_between_subminds=conv_config.get("delay_between_subminds", 0.0),
            )

            # Initialize exporter
            export_config = self.config.get("export", {})
            self.exporter = ConversationExporter(
                export_dir=export_config.get("directory", "exports"),
                formats=export_config.get("format", ["json", "markdown"]),
                include_metadata=export_config.get("include_metadata", True),
            )

            self.console.print("[green]✓[/green] Components initialized")
            return True

        except Exception as e:
            self.console.print(f"[red]✗ Error initializing components: {e}[/red]")
            return False

    def display_header(self):
        """Display welcome header."""
        header = """
# 🧠 Submind Discussion System

Five specialized AI agents collaborate to explore your questions:
- **Doctrinal**: Traditional wisdom and proven methods
- **Analytical**: Data-driven and empirical analysis
- **Strategic**: Practical implementation and feasibility
- **Creative**: Innovative and unconventional thinking
- **Skeptic**: Critical analysis and devil's advocate
"""
        self.console.print(Panel(Markdown(header), border_style="blue"))

    def display_message(self, message: dict):
        """
        Display a single message with formatting.

        Args:
            message: Message dict
        """
        speaker = message.get("speaker", "Unknown")
        content = message.get("content", "")

        # Get color from submind if available
        color = "white"
        for submind in self.subminds:
            if submind.name == speaker:
                color = submind.color
                break

        if speaker == "User":
            self.console.print(f"\n[bold cyan]{speaker}:[/bold cyan] {content}\n")
        elif speaker == "System":
            self.console.print(f"[dim italic]{content}[/dim italic]\n")
        else:
            # Get model name if available
            model_info = ""
            if "model" in message:
                # Extract short model name (e.g., "llama-3.2" from "meta-llama/llama-3.2-3b-instruct:free")
                model_full = message["model"]
                model_short = model_full.split('/')[-1].split(':')[0]
                model_info = f" [dim]({model_short})[/dim]"

            self.console.print(f"[bold {color}]{speaker}:{model_info}[/bold {color}]")
            self.console.print(f"{content}\n")

    def run_conversation(self, prompt: str):
        """
        Run a conversation with the given prompt.

        Args:
            prompt: User's initial prompt
        """
        self.console.print("\n[bold]Starting discussion...[/bold]\n")

        try:
            # Start conversation
            history = self.conversation.start(prompt)

            # Display conversation
            for message in history:
                self.display_message(message)

            # Get summary
            summary = self.conversation.get_summary()

            # Export if enabled
            if self.config.get("conversation", {}).get("enable_export", True):
                self.console.print("\n[bold]Exporting conversation...[/bold]")
                saved_files = self.exporter.export(history, summary)

                for format_type, filepath in saved_files.items():
                    self.console.print(f"[green]✓[/green] Saved {format_type}: {filepath}")

            # Display summary
            self.console.print(f"\n[dim]Discussion completed in {summary['total_rounds']} rounds[/dim]")

        except Exception as e:
            self.console.print(f"[red]Error during conversation: {e}[/red]")

    def run(self):
        """Main CLI loop."""
        # Load environment variables
        load_dotenv()

        # Display header
        self.display_header()

        # Initialize system
        self.console.print("\n[bold]Initializing system...[/bold]")

        if not self.load_config():
            return

        if not self.initialize_api_client():
            return

        if not self.initialize_subminds():
            return

        if not self.initialize_components():
            return

        self.console.print("\n[green]✓ System ready![/green]\n")

        # Main loop
        while True:
            try:
                # Get user prompt
                prompt = Prompt.ask("\n[bold cyan]Enter your question or prompt[/bold cyan] (or 'quit' to exit)")

                if prompt.lower() in ["quit", "exit", "q"]:
                    self.console.print("\n[yellow]Goodbye![/yellow]")
                    break

                if prompt.strip().lower() == "stop":
                    self.console.print("\n[yellow]Discussion stopped. Enter a new question to continue.[/yellow]")
                    continue

                if not prompt.strip():
                    continue

                # Run conversation
                self.run_conversation(prompt)

                # Reset for next conversation
                self.conversation.reset()

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Interrupted. Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"\n[red]Unexpected error: {e}[/red]")


def main():
    """Entry point."""
    cli = SubmindCLI()
    cli.run()


if __name__ == "__main__":
    main()
