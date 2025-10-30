#!/usr/bin/env python3
"""
Submind System - Web Interface
Flask application with Server-Sent Events for real-time chat
"""

import os
import json
import yaml
from flask import Flask, render_template, request, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

from src import LMStudioClient, Submind, TerminationDetector, ConversationExporter
from src.conversation_stream import StreamingConversation


# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
config = None
api_client = None
subminds = []
exporter = None


def load_config(config_path: str = "config.yaml"):
    """Load configuration from YAML file."""
    global config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)


def initialize_system():
    """Initialize API client, subminds, and exporter."""
    global api_client, subminds, exporter

    # Initialize API client
    api_client = LMStudioClient()

    # Initialize subminds
    default_model = config.get("default_model", "mistralai/mistral-7b-instruct-v0.3")

    for submind_config in config.get("subminds", []):
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
            api_client=api_client,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            color=color,
        )

        subminds.append(submind)

    # Initialize exporter
    export_config = config.get("export", {})
    exporter = ConversationExporter(
        export_dir=export_config.get("directory", "exports"),
        formats=export_config.get("format", ["json", "markdown"]),
        include_metadata=export_config.get("include_metadata", True),
    )


@app.route("/")
def index():
    """Render the main chat interface."""
    submind_info = [
        {
            "name": s.name,
            "color": s.color,
            "role": s.role,
        }
        for s in subminds
    ]
    return render_template("index.html", subminds=submind_info)


@app.route("/chat", methods=["POST"])
def chat():
    """
    Stream conversation using Server-Sent Events.
    Receives user prompt and streams submind responses in real-time.
    """
    user_prompt = request.json.get("prompt", "")
    enabled_subminds = request.json.get("enabled_subminds", None)
    auto_terminate = request.json.get("auto_terminate", True)

    if not user_prompt:
        return {"error": "No prompt provided"}, 400

    # Check for stop command
    if user_prompt.strip().lower() == "stop":
        return {"message": "Discussion stopped"}, 200

    # Filter subminds if enabled_subminds is provided
    active_subminds = subminds
    if enabled_subminds is not None:
        # Validate: minimum 2 subminds
        if len(enabled_subminds) < 2:
            return {"error": "Minimum 2 subminds required"}, 400

        # Filter to only enabled subminds
        active_subminds = [s for s in subminds if s.name in enabled_subminds]

        # Validate: all provided names are valid
        if len(active_subminds) != len(enabled_subminds):
            return {"error": "Invalid submind names provided"}, 400

    def generate():
        """Generator function for SSE."""
        # Reset subminds for new conversation
        for submind in active_subminds:
            submind.reset()

        # Create conversation manager
        conv_config = config.get("conversation", {})

        # Use auto_terminate to override detect_consensus setting
        detect_consensus = conv_config.get("detect_consensus", True) if auto_terminate else False

        termination_detector = TerminationDetector(
            max_rounds=conv_config.get("max_rounds", 3),
            detect_consensus=detect_consensus,
            consensus_threshold=conv_config.get("consensus_threshold", 0.7),
            minimum_responses_per_submind=conv_config.get("minimum_responses_per_submind", 1),
        )

        streaming_conversation = StreamingConversation(
            subminds=active_subminds,
            termination_detector=termination_detector,
            delay_between_subminds=conv_config.get("delay_between_subminds", 0.0),
        )

        # Stream conversation events
        try:
            for event in streaming_conversation.stream_conversation(user_prompt):
                # Format as SSE
                event_data = json.dumps(event)
                yield f"data: {event_data}\n\n"

        except Exception as e:
            # Send error event
            error_event = {
                "type": "error",
                "error": str(e),
            }
            yield f"data: {json.dumps(error_event)}\n\n"

        finally:
            # Export conversation if enabled and there's history (even if errors occurred)
            if conv_config.get("enable_export", True):
                history = streaming_conversation.get_full_history()

                # Only export if there's actual conversation data
                if history:
                    try:
                        summary = streaming_conversation.get_summary()
                        saved_files = exporter.export(history, summary)

                        # Send export complete event
                        export_event = {
                            "type": "export_complete",
                            "files": saved_files,
                        }
                        yield f"data: {json.dumps(export_event)}\n\n"
                    except Exception as export_error:
                        # If export fails, log it but don't crash
                        print(f"Warning: Export failed: {export_error}")

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/config")
def get_config():
    """Get current configuration."""
    return {
        "subminds": [
            {
                "name": s.name,
                "color": s.color,
                "role": s.role,
                "models": s.models,
            }
            for s in subminds
        ],
        "max_rounds": config.get("conversation", {}).get("max_rounds", 3),
        "presets": config.get("submind_presets", {}),
    }


def main():
    """Run the Flask development server."""
    # Load configuration and initialize system
    load_config()
    initialize_system()

    # Run Flask app
    print("\n🧠 Submind Web Interface Starting...")
    print("📱 Open your browser to: http://localhost:5000")
    print("Press CTRL+C to stop\n")

    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)


if __name__ == "__main__":
    main()
