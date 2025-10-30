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
- [LM Studio](https://lmstudio.ai/) installed and running
- A model loaded in LM Studio (e.g., mistralai/mistral-7b-instruct-v0.3)

### Setup

1. **Clone or download this repository**

2. **Start LM Studio**
   - Open LM Studio
   - Load a model (e.g., Mistral 7B Instruct)
   - Start the local server (default: port 1234)
   - Ensure the server is accessible at `http://192.168.4.30:1234`

3. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   ```

4. **Activate the virtual environment**

   On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Configure environment variables (optional)**
   ```bash
   cp .env.example .env
   ```

   If your LM Studio server is on a different URL, edit `.env`:
   ```
   LMSTUDIO_BASE_URL=http://your-server-ip:port/v1
   ```

7. **Configure models (optional)**

   Edit `config.yaml` to update the model identifier to match what you have loaded in LM Studio.

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

The `config.yaml` file controls all system behavior. Since LM Studio typically runs one model at a time, all subminds use the same model with different temperatures for varied perspectives.

1. **Change the model identifier:**
   ```yaml
   default_model: "mistralai/mistral-7b-instruct-v0.3"
   ```

2. **Update specific submind settings:**
   ```yaml
   subminds:
     - name: "Doctrinal"
       role: "traditional"
       model: "mistralai/mistral-7b-instruct-v0.3"
       temperature: 0.7  # Different temperatures create varied responses
   ```

### Model Identifier

The model identifier in your config should match the model loaded in LM Studio. You can find this in:
- LM Studio → My Models → Model name
- Or check the LM Studio server endpoint: `http://192.168.4.30:1234/v1/models`

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
│   ├── api_client.py       # LM Studio API client wrapper
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

### LM Studio Connection Issues

```
Error: LM Studio API error / Connection test failed
```
**Solution**:
- Make sure LM Studio is running
- Check that the local server is started in LM Studio
- Verify the server URL is correct (default: `http://192.168.4.30:1234`)
- If using a different IP/port, update `LMSTUDIO_BASE_URL` in `.env`

### Model Not Found

```
Error: Model not found
```
**Solution**:
- Make sure you have a model loaded in LM Studio
- Check that the model identifier in `config.yaml` matches the model in LM Studio
- You can verify the model name at `http://192.168.4.30:1234/v1/models`

### Slow Response Times

LM Studio runs locally, so response speed depends on your hardware:
- **GPU**: Much faster inference
- **CPU only**: Slower, especially for larger models
- Consider using a smaller/quantized model if responses are too slow

## Cost Considerations

- **Completely free!** LM Studio runs entirely on your local machine
- No API costs or rate limits
- Only consideration is hardware performance and electricity

## Contributing

This is a personal project, but feel free to fork and modify for your needs!

## License

MIT License - feel free to use and modify as you wish.

## Acknowledgments

- Built with [LM Studio](https://lmstudio.ai/) for local LLM inference
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Uses OpenAI-compatible API interface

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review [LM Studio documentation](https://lmstudio.ai/docs)
3. Check your `config.yaml` settings
4. Verify LM Studio server is running and accessible

---

**Happy discussing! 🧠✨**
