# Contract Playbook Builder

A web application that automatically generates professional contract playbooks from any template agreement. Upload a PDF, Word document, or Excel file, and receive a comprehensive negotiation playbook following industry best practices.

**Powered by Claude AI** - Uses Anthropic's Claude for intelligent contract analysis.

---

## Table of Contents

- [What is a Contract Playbook?](#what-is-a-contract-playbook)
- [Features](#features)
- [Quick Start](#quick-start)
- [Detailed Setup Guide](#detailed-setup-guide)
- [Configuration](#configuration)
- [How to Use](#how-to-use)
- [Understanding Your Playbook](#understanding-your-playbook)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## What is a Contract Playbook?

A contract playbook is a strategic guide that documents your organization's negotiation positions, risk tolerance, and standard terms for contract negotiations. It helps legal teams, procurement professionals, and business stakeholders:

- **Negotiate consistently** across all deals
- **Save time** by providing pre-approved language and positions
- **Reduce risk** by identifying deal-breakers and acceptable alternatives
- **Empower non-lawyers** to handle routine negotiations
- **Preserve institutional knowledge** about preferred terms

---

## Features

- **Multi-format Upload**: Supports PDF, Word (.docx), and Excel (.xlsx) files
- **Claude AI Analysis**: Uses Anthropic's Claude for deep contract understanding
- **Web Research Integration**: Search and select relevant legal articles, checklists, and guides to enhance AI analysis
- **Topic-Based Organization**: Separate sheets for each contract area (Indemnification, Liability, IP, etc.)
- **Professional Output**: Excel playbooks matching industry standards
- **Dual Perspective**: Analysis from both customer and provider viewpoints
- **Actionable Guidance**: Ready-to-use fallback language and hard limits
- **Quick Reference**: Executive summary with deal-breakers and approval requirements

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Tucuxi-Inc/ContractPlaybookBuilder.git
cd ContractPlaybookBuilder

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key (choose one method)

# Option A: Create .env file (recommended)
cp .env.example .env
# Edit .env and add your Anthropic API key

# Option B: Export environment variable
export ANTHROPIC_API_KEY="your-api-key-here"

# 5. Run the application
python app.py

# 6. Open http://localhost:3005 in your browser
```

---

## Detailed Setup Guide

### Prerequisites

- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **Anthropic API Key** - [Get one here](https://console.anthropic.com/)

### Step 1: Get the Code

```bash
git clone https://github.com/Tucuxi-Inc/ContractPlaybookBuilder.git
cd ContractPlaybookBuilder
```

Or download the ZIP from GitHub and extract it.

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows CMD
.\venv\Scripts\Activate.ps1   # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

```

### Step 3: Configure API Key

**Option A: Using .env file (Recommended)**

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your favorite editor
nano .env   # or: code .env, vim .env, etc.
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

**Option B: Environment Variable**

```bash
# Mac/Linux
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
```

### Step 4: Run the Application

```bash
python app.py
```

You should see:
```
============================================================
Contract Playbook Builder
============================================================
Starting server on http://localhost:3005
AI Provider: Anthropic Claude (claude-sonnet-4-20250514)
============================================================
```

Open **http://localhost:3005** in your browser.

---

## Configuration

All configuration can be done via the `.env` file or environment variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `ANTHROPIC_MODEL` | claude-sonnet-4-20250514 | Claude model to use |
| `PORT` | 3005 | Server port |
| `MAX_FILE_SIZE` | 50 | Max upload size in MB |
| `FLASK_DEBUG` | 0 | Set to 1 for debug mode |

### Alternative: OpenAI

If you prefer OpenAI, set these instead:
```
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
AI_PROVIDER=openai
```

The app will automatically use OpenAI if no Anthropic key is configured.

### OpenAI-Compatible APIs

You can use **any OpenAI-compatible API** by setting a custom base URL. This includes:

- **Local Models**: LM Studio, Ollama, LocalAI, Jan
- **Cloud Providers**: OpenAI, Azure OpenAI, Together.ai, Groq, DeepInfra
- **Self-Hosted**: vLLM, Text Generation Inference, FastChat

**Quick Example (LM Studio):**
```bash
OPENAI_API_KEY=lm-studio
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=llama-3.1-8b-instruct
AI_PROVIDER=openai
```

**Quick Example (Ollama):**
```bash
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1
AI_PROVIDER=openai
```

**📖 For detailed setup instructions, model recommendations, and troubleshooting, see [OPENAI_COMPATIBLE_SETUP.md](OPENAI_COMPATIBLE_SETUP.md)**

This comprehensive guide includes:
- Step-by-step setup for LM Studio, Ollama, and other providers
- Model recommendations and quality comparisons
- Performance expectations and hardware requirements
- Troubleshooting common issues
- Configuration examples for 10+ different providers

### Google Search Setup (Optional)

The web research feature allows you to search for and include relevant legal resources in your playbook generation. This is **optional** but can significantly enhance the quality of the output.

**Step 1: Get a Google API Key**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Custom Search API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Custom Search API"
   - Click "Enable"
4. Create API credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy your API key

**Step 2: Create a Custom Search Engine**

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Configure:
   - **Sites to search**: Leave empty to search the entire web
   - **Name**: "Contract Legal Resources" (or your choice)
   - **Search the entire web**: Toggle ON
4. Click "Create"
5. Copy your **Search Engine ID** (cx parameter)

**Step 3: Add to .env file**

```bash
# Add to your .env file
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**Testing the Setup:**

After adding these credentials, restart the application. The "Search for Legal Resources" button should now work. If not configured, you'll see an error message when clicking the button.

**API Costs:**

- Google Custom Search API: 100 free queries/day
- After that: $5 per 1,000 queries
- Typical usage: 1-2 queries per playbook (if you use the search feature)

---

## How to Use

### 1. Upload Your Agreement

- Click **"Choose File"** or drag and drop
- Supported: PDF, Word (.docx), Excel (.xlsx)
- Max size: 50 MB

### 2. Configure Options

- **Agreement Type**: SaaS, MSA, NDA, etc. (helps AI understand context)
- **Your Role**: Customer or Provider (tailors the analysis)
- **Risk Tolerance**: Low, Moderate, or High

### 3. (Optional) Search for Legal Resources

Click **"Search for Legal Resources"** to enhance your playbook with external research:

- Automatically searches for relevant checklists, legal articles, and best practices
- Review search results and select relevant resources by clicking checkboxes
- Click **"Save Selected Resources"** to include them in the AI analysis
- Selected resources will be fetched and included as context for the playbook generation

**Search Engines:**
- **DuckDuckGo** (free, no API key required) - used by default
- **Google Custom Search** (optional, requires API key) - for better results (see [Google Search Setup](#google-search-setup-optional))

### 4. Generate & Download

- Click **"Generate Playbook"**
- Wait 2-5 minutes (progress shown)
- Download the Excel file when complete

---

## Understanding Your Playbook

The generated Excel workbook contains multiple sheets organized by topic:

### Overview Sheet
- Agreement title, parties, governing law
- Key principles and executive summary
- How to use the playbook

### Topic Sheets (Definitions, Indemnification, Liability, etc.)

Each topic sheet contains:

| Column | Description |
|--------|-------------|
| **Section** | Reference to original agreement section |
| **Issue** | Specific contractual issue |
| **Current Language** | Exact text from the agreement |
| **Purpose/Rationale** | Why this clause matters |
| **Customer Concerns** | What buyers worry about |
| **Customer Edits to Watch** | Edits customers typically request |
| **Provider Position** | What vendors need to protect |
| **Acceptable Modifications** | Negotiable changes |
| **Fallback Language** | Ready-to-use alternative text |
| **Do Not Accept** | Hard limits requiring approval |

### Quick Reference Sheet
- Hard limits by topic
- Items requiring executive approval

---

## Troubleshooting

### "API key not configured"

Make sure your `.env` file exists and contains:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Or export the environment variable before running.

### "Port already in use"

```bash
# Use a different port
PORT=3006 python app.py
```

### "ModuleNotFoundError"

```bash
# Make sure venv is activated and dependencies installed
source venv/bin/activate
pip install -r requirements.txt
```

### Large files timing out

- Files over 50 pages may take 5-10 minutes
- Ensure stable internet connection
- Check terminal for error messages

### PDF not parsing correctly

- Must be text-based (not scanned images)
- Use OCR software for scanned documents
- Remove password protection

---

## Project Structure

```
ContractPlaybookBuilder/
├── app.py                    # Flask application
├── config.py                 # Configuration (loads .env)
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment file
├── .env                      # Your local config (not in git)
├── README.md                 # This file
├── templates/
│   └── index.html            # Web interface
├── static/
│   ├── css/style.css
│   └── js/main.js
├── utils/
│   ├── document_parser.py    # PDF/Word/Excel extraction
│   ├── playbook_generator.py # Claude AI analysis
│   └── excel_writer.py       # Excel output generation
├── uploads/                  # Temporary uploads (auto-cleaned)
└── output/                   # Generated playbooks
```

---

## API Costs

Typical cost per playbook using Claude:
- Short contracts (1-10 pages): ~$0.05-0.15
- Medium contracts (10-30 pages): ~$0.15-0.40
- Long contracts (30-100 pages): ~$0.40-1.00

---

## Security Notes

- **API Keys**: Stored in `.env` which is gitignored - never committed
- **Uploaded Files**: Temporarily stored, auto-deleted after processing
- **Local Only**: Runs on localhost by default
- **Data Privacy**: Contract text is sent to Anthropic's API for analysis

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues or questions:
- Open an issue on [GitHub](https://github.com/Tucuxi-Inc/ContractPlaybookBuilder/issues)