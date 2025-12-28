# CU-CLA

An AI coding assistant that helps you write and modify code.

## What is this?

CU-CLA is a web-based coding assistant powered by AI (Claude, ChatGPT, Gemini, or local LLMs). You open a file, tell it what you want to do, and it helps you modify your code intelligently.

**Key feature:** When you open a file, it automatically loads all related files (imports, dependencies) so the AI has full context.

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Run

```bash
cd /tmp/cucla
python -m uvicorn main:app --reload
```

### 3. Open Browser

Go to: `http://localhost:8000`

## How to Use

1. **Select LLM Provider**: Choose Demo Mode (no API key) or select Claude/ChatGPT/Gemini/LLM Studio
2. **Enter API Key**: Only if using Claude/ChatGPT/Gemini (skip for Demo or LLM Studio)
3. **Browse Files**: Click folders and files in the left panel to navigate your project
4. **Open a File**: Click any file to open it in the editor
5. **Write Your Task**: Tell the AI what you want to do (e.g., "Add error handling to the login function")
6. **Click "Run Agent"**: Watch the agent analyze and modify your code
7. **Save Changes**: Click "Save File" when you're happy with the changes

## Supported LLMs

- **Demo Mode** - No API key needed, simulated responses for testing
- **Claude** - Anthropic's Claude API (recommended)
- **ChatGPT** - OpenAI's GPT models
- **Gemini** - Google's Gemini Pro
- **LLM Studio** - Run models locally on `http://localhost:1234`

## Features

- 📂 File browser to navigate your project
- ✏️ Code editor with syntax highlighting
- 🤖 AI agent that understands your code structure
- 🔗 Automatically loads related files (imports/dependencies)
- 🔧 Can read, analyze, and modify any file in your project
- 📊 Shows you what the agent is doing in real-time

## Example Tasks

- "Fix the bug in the authentication function"
- "Add input validation to all API endpoints"
- "Refactor this function to be more readable"
- "Add error handling to database queries"
- "Update the imports to use the new module structure"

## Project Structure

```
/tmp/cucla/
├── main.py                 # FastAPI server
├── static/                 # Frontend files
│   ├── css/style.css      # Styles
│   └── js/script.js       # JavaScript
├── templates/
│   └── index.html         # Web interface
└── tools/                 # Agent logic
    ├── agent_controller.py
    ├── tool_executor.py
    ├── dependency_graph.py
    └── ...
```

## Configuration

### Using LLM Studio (Local Models)

1. Install and run [LLM Studio](https://lmstudio.ai/)
2. Start a local server on port 1234
3. Select "LLM Studio (localhost:1234)" in the dropdown
4. No API key needed!

### Using Claude/ChatGPT/Gemini

1. Get an API key from [Anthropic](https://console.anthropic.com/), [OpenAI](https://platform.openai.com/), or [Google AI](https://makersuite.google.com/)
2. Enter your API key in the interface
3. Start using!

## How It Works

1. You open a file (e.g., `main.py`)
2. The agent automatically loads all related files:
   - Files that `main.py` imports
   - Files that import `main.py`
   - Dependencies up to 2 levels deep
3. All files are sent to the AI as context
4. The AI can read, analyze, and modify any of these files
5. Changes are shown in real-time

## Troubleshooting

**Agent says "Error: Please provide an API key"**
- Make sure you entered your API key
- Or switch to Demo Mode

**Files not loading**
- Make sure you're in the correct directory when running `uvicorn`
- Check console output for `[DEP_GRAPH]` messages

**Agent can't modify imported files**
- Check the console for `[INIT] Loaded X files` to see what was loaded
- Files should be automatically loaded - no action needed

## Contributing

This is a project by EAFIT's AI Research Group (Semillero de Inteligencia Artificial).

Repository: https://github.com/Semillero-Inteligencia-Artificial-EAFIT/CuCla



**Made with ❤️ by Semillero de Inteligencia Artificial EAFIT**
