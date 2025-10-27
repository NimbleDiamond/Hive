# 🧠 Submind Discussion System

A multi-agent discussion system where five specialized AI personas collaborate to explore ideas, questions, and problems from different perspectives.

## Overview

Submind simulates a group chat environment where specialized LLM instances discuss and critique user prompts. Each "submind" brings a unique perspective:

- **Doctrinal** 🔵 - Traditional wisdom and proven methods
- **Analytical** 🔷 - Data-driven and empirical analysis
- **Strategic** 🟢 - Practical implementation and feasibility
- **Creative** 🟣 - Innovative and unconventional thinking
- **Skeptic** 🔴 - Critical analysis and devil's advocate

## Features

- ✅ Five specialized AI personas with distinct perspectives
- ✅ Sequential conversation flow with full context awareness
- ✅ Hybrid termination (smart detection + max rounds fallback)
- ✅ Easy model configuration (use free or paid models)
- ✅ Conversation export (JSON & Markdown)
- ✅ Color-coded CLI interface
- ✅ Configurable per-submind settings

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

### Setup

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**

   On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```

6. **Configure models (optional)**

   Edit `config.yaml` to choose which models to use. See "Finding Free Models" section below.

## Usage

Submind offers two interfaces: a **web interface** (recommended) and a **CLI**.

### Web Interface (Recommended)

The web interface provides a Discord/WhatsApp-style chat with real-time streaming!

1. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Run the web server**:
   ```bash
   python app.py
   ```

3. **Open your browser** to: `http://localhost:5000`

**Features:**
- 🎨 Discord-style chat interface
- ⚡ Real-time streaming (see responses as they're generated)
- 🎨 Color-coded subminds with avatars
- 📥 Export conversations to JSON
- 📱 Responsive design (works on mobile)

### CLI Interface

For a terminal-based experience:

1. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Run the CLI**:
   ```bash
   python main.py
   ```

Enter your question or prompt when asked, and watch the subminds discuss!

### Example Prompts

Try asking questions like:
- "Should I start a business or get a job?"
- "How can I improve my productivity?"
- "What's the best way to learn programming?"
- "Analyze the pros and cons of remote work"
- "Help me decide between two career paths"

### Output

Conversations are automatically exported to the `exports/` directory in two formats:
- **JSON**: Structured data with full metadata
- **Markdown**: Human-readable conversation transcript

## Configuration

### Model Configuration

The `config.yaml` file controls all system behavior. To change models:

1. **Change the default model for all subminds:**
   ```yaml
   default_model: "meta-llama/llama-3.2-3b-instruct:free"
   ```

2. **Use different models for specific subminds:**
   ```yaml
   subminds:
     - name: "Doctrinal"
       role: "traditional"
       model: "openai/gpt-4-turbo"  # Override default
   ```

3. **Use the default model for a submind:**
   ```yaml
   subminds:
     - name: "Doctrinal"
       role: "traditional"
       model: null  # Uses default_model
   ```

### Finding Free Models

OpenRouter offers several free models. Visit [OpenRouter Models](https://openrouter.ai/models) and filter by "Free".

Popular free models (as of 2024):
- `meta-llama/llama-3.2-3b-instruct:free`
- `google/gemini-flash-1.5`
- `nousresearch/hermes-3-llama-3.1-405b:free`
- `mistralai/mistral-7b-instruct:free`

### Other Configuration Options

```yaml
conversation:
  max_rounds: 3              # Maximum discussion rounds
  detect_consensus: true     # Enable smart termination
  consensus_threshold: 0.7   # Similarity threshold for repetition

export:
  format: ["json", "markdown"]
  directory: "exports"
  include_metadata: true
```

## Project Structure

```
submind/
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── requirements.txt         # Python dependencies
├── config.yaml              # System configuration
├── main.py                  # CLI entry point
├── app.py                   # Web interface entry point
├── templates/
│   └── index.html          # Discord-style chat interface
├── static/
│   ├── app.js              # Frontend JavaScript (SSE handling)
│   └── style.css           # Custom CSS styling
├── src/
│   ├── api_client.py       # OpenRouter API wrapper
│   ├── submind.py          # Individual submind class
│   ├── conversation.py     # CLI conversation orchestration
│   ├── conversation_stream.py  # Web streaming conversation
│   ├── termination.py      # Termination detection logic
│   └── exporter.py         # Export functionality
├── subminds/
│   └── prompts.py          # System prompts for each persona
└── exports/                # Saved conversations (auto-created)
```

## How It Works

1. **User submits a prompt** - Your question or idea
2. **Initial round** - Each submind responds to your prompt in sequence
3. **Discussion rounds** - Subminds respond to each other's points
4. **Smart termination** - System detects when discussion reaches conclusion
5. **Export** - Conversation saved to JSON and Markdown

### Termination Logic

Conversations end when:
- Maximum rounds reached (configurable, default: 3)
- Consensus detected (subminds agreeing)
- Completion signals detected (summary language)
- Repetition detected (circular discussion)

## Customization

### Adding New Subminds

1. Add system prompt in `subminds/prompts.py`:
   ```python
   SYSTEM_PROMPTS["your_role"] = """Your system prompt here..."""
   ```

2. Add configuration in `config.yaml`:
   ```yaml
   subminds:
     - name: "YourSubmind"
       role: "your_role"
       model: null
       temperature: 0.7
       max_tokens: 500
       color: "yellow"
   ```

### Adjusting Submind Personalities

Edit the system prompts in `subminds/prompts.py` to change how subminds behave.

## Troubleshooting

### API Key Issues

```
Error: OpenRouter API key not found
```
**Solution**: Make sure `.env` file exists with valid `OPENROUTER_API_KEY`

### Model Not Found

```
Error: Model not found
```
**Solution**: Check model name at [OpenRouter Models](https://openrouter.ai/models). Model names must match exactly.

### Rate Limits

Free models may have rate limits. If you hit limits:
- Wait a few minutes between conversations
- Switch to a different free model
- Consider using a paid model for higher limits

## Cost Considerations

- **Free models**: No cost, but may have rate limits
- **Paid models**: Each submind makes 1 API call per round
  - 5 subminds × 3 rounds = 15 API calls per conversation
  - Check [OpenRouter pricing](https://openrouter.ai/models) for specific model costs

## Contributing

This is a personal project, but feel free to fork and modify for your needs!

## License

MIT License - feel free to use and modify as you wish.

## Acknowledgments

- Built with [OpenRouter](https://openrouter.ai/) for flexible model access
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal output

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review [OpenRouter documentation](https://openrouter.ai/docs)
3. Check your `config.yaml` settings

---

**Happy discussing! 🧠✨**
