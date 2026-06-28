# Mythos AI

**Autonomous AI Agent with CLI and Desktop Interface**

Mythos is a powerful AI agent that can code, execute shell commands, search the web, process PDFs, and analyze images. Built with Python, it provides both CLI and desktop interfaces.

## Features

- **Code Generation**: Write, edit, and debug code
- **Shell Execution**: Run CMD and PowerShell commands
- **Web Search**: Search the web and fetch content
- **PDF Processing**: Read, create, merge, split PDFs
- **Vision**: Analyze images with AI
- **Memory**: Persistent conversation history
- **Auto-Update**: Automatic updates on launch

## Quick Install

### Windows

```bash
# Clone the repository
git clone https://github.com/mythos-ai/mythos.git
cd mythos

# Run installer
python install.py

# Or install globally (adds to PATH)
python install_global.py
```

### Manual Install

```bash
# Install dependencies
pip install -r requirements.txt

# Run Mythos
python mythos.py
```

## Usage

```bash
# Interactive REPL
python mythos.py

# One-shot mode
python mythos.py "write a hello world program"

# Launch with security lock
python mythos.py --lock

# Show version
python mythos.py --version

# Force update
python mythos.py --update
```

## Global Install (Windows)

After running `python install_global.py`, you can use Mythos from anywhere:

```bash
Mythos
Mythos "create a web server"
Mythos --lock
```

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/status` | Show system status |
| `/model <name>` | Switch AI model |
| `/cd <path>` | Change directory |
| `/clear` | Clear screen |
| `/history` | Show conversation history |
| `/shell` | Interactive shell |
| `/image <path>` | Analyze image |
| `/pdf <path>` | Read PDF |
| `/exit` | Exit Mythos |

## Models

| Model | Use Case |
|-------|----------|
| `mythos-code` | Coding and shell tasks |
| `mythos-ultra` | Complex reasoning |
| `mythos-vision` | Image analysis |

## Skills

Mythos includes 17 skills for various tasks:

- **tdd**: Test-driven development
- **systematic-debugging**: Debug issues
- **pdf**: PDF processing
- **docx**: Word documents
- **xlsx**: Excel spreadsheets
- **frontend-design**: UI design
- And more...

## Configuration

Edit `config.json` to customize:

- API keys
- Model selection
- System settings
- Optimization options

## Requirements

- Python 3.9+
- Windows 10/11 (primary support)

## License

MIT License

## Author

Mythos AI Team
