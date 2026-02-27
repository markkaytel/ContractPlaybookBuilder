# CLAUDE.md - Contract Playbook Builder

## Project Overview

A web application that allows users to upload any type of template agreement (PDF, Word, Excel) and automatically generates a professional contract playbook in Excel format. The playbook follows industry best practices with clause-by-clause analysis, negotiation guidance, and risk classification.

**Primary AI Provider:** Anthropic Claude (claude-sonnet-4-20250514)
**Fallback AI Provider:** OpenAI GPT-4o
**Deployment Targets:** Local development (Flask) and Vercel (serverless)

---

## Repository Structure

```
ContractPlaybookBuilder/
├── app.py                    # Main Flask app (local development, job queue)
├── config.py                 # Configuration (port, API keys, file limits)
├── requirements.txt          # Python dependencies
├── vercel.json               # Vercel serverless deployment config
├── .env.example              # Environment variable template
├── CLAUDE.md                 # This file
├── README.md                 # User-facing documentation
├── LOCAL_AI_GUIDE.md         # Guide for Ollama/local AI integration
│
├── api/                      # Vercel serverless functions
│   ├── index.py              # Route handler (serves index.html)
│   ├── upload.py             # Single synchronous upload+process endpoint
│   └── health.py             # Health check (verifies API key)
│
├── utils/                    # Core application logic
│   ├── __init__.py
│   ├── document_parser.py    # PDF/DOCX/XLSX text extraction
│   ├── playbook_generator.py # AI-powered contract analysis (Anthropic Claude)
│   └── excel_writer.py       # Excel workbook generation (openpyxl)
│
├── templates/
│   └── index.html            # Main web UI (single-page)
│
├── static/                   # Assets for local development
│   ├── css/style.css
│   └── js/main.js
│
├── public/                   # Assets for Vercel deployment
│   ├── css/style.css
│   └── js/main.js
│
├── uploads/                  # Temp upload storage (local only, gitignored)
├── output/                   # Generated playbooks (local only, gitignored)
└── BackgroundDocs/           # Reference materials (not in git)
```

---

## Quick Start (Local Development)

```bash
# Clone and enter project
git clone https://github.com/Tucuxi-Inc/ContractPlaybookBuilder
cd ContractPlaybookBuilder

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy template, then edit)
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env (primary) or OPENAI_API_KEY (fallback)

# Run the application
python app.py

# Access the web interface
open http://localhost:3005
```

**Note:** The default port is **3005** (not 8005).

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | — | Anthropic API key (primary AI provider) |
| `OPENAI_API_KEY` | Yes* | — | OpenAI API key (fallback if Anthropic not set) |
| `PORT` | No | `3005` | Server port for local development |
| `DEBUG` | No | `False` | Flask debug mode |
| `MAX_FILE_SIZE_MB` | No | `50` | Maximum upload file size in MB |

*At least one of `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` must be set.

---

## Architecture

### Dual Deployment Model

**Local Development** (`app.py`):
```
POST /api/upload  →  job created (in-memory)
POST /api/process/<job_id>  →  async background processing
GET  /api/status/<job_id>   →  polling (1s intervals from frontend)
GET  /api/download/<job_id> →  stream Excel file
```

**Vercel Serverless** (`api/upload.py`):
```
POST /api/upload  →  synchronous pipeline (5 min timeout, 1GB memory)
                  →  returns Excel file directly
```

### Processing Pipeline

```
User uploads agreement (PDF/DOCX/XLSX)
    ↓
document_parser.py  →  extract text, metadata, sections
    ↓
playbook_generator.py  →  parallel AI analysis (13 topics, 5 threads)
    ↓
excel_writer.py  →  generate professional Excel workbook
    ↓
User downloads completed playbook
```

---

## Key Modules

### `utils/document_parser.py`
Extracts text and structure from uploaded documents.

- `parse_document(file_path)` — auto-detects format, calls appropriate parser
- `parse_pdf(file_path)` — uses PyPDF2; returns text, page count, metadata
- `parse_docx(file_path)` — uses python-docx; extracts paragraphs and tables
- `parse_xlsx(file_path)` — uses openpyxl; extracts sheets and cell content
- `extract_sections(text)` — heuristic section identification using regex

Returns a dict with keys: `text`, `metadata`, `sections`, `page_count`, `format`

### `utils/playbook_generator.py`
AI-powered contract analysis using Anthropic Claude API.

- `analyze_contract_chunked(document_data, progress_callback)` — main entry point
- `analyze_contract_with_claude(text, topics, progress_callback)` — parallel analysis
- Uses `ThreadPoolExecutor(max_workers=5)` to analyze 13 topics concurrently
- Falls back from Anthropic to OpenAI if Anthropic key not configured

**13 Contract Topics Analyzed:**
1. Definitions
2. Solution/Services Description
3. Intellectual Property
4. Financial Terms
5. Confidentiality
6. Security & Data Protection
7. Warranties & Representations
8. Indemnification
9. Limitation of Liability
10. Term & Termination
11. General Provisions
12. Exhibits & Schedules
13. Dispute Resolution

**System prompt persona:** Expert contract attorney with 25+ years of experience. JSON responses extracted from Claude output with regex fallback.

### `utils/excel_writer.py`
Generates professional Excel workbooks using openpyxl.

- `generate_playbook_excel(playbook_data, output_path)` — main function
- `create_overview_sheet(wb, data)` — agreement summary, principles, how-to guide
- `create_topic_sheet(wb, topic_name, clauses)` — per-topic analysis sheet
- `create_quick_reference_sheet(wb, data)` — hard limits requiring exec approval

**12 Columns Per Topic Sheet:**
| Column | Description |
|--------|-------------|
| Section | Contract section number/name |
| Subsection | Specific subsection reference |
| Issue | Issue or clause being analyzed |
| Current Language | Actual text from agreement |
| Purpose/Rationale | Business context explanation |
| Customer Concerns | Customer perspective and risks |
| Customer Edits to Watch | Language customers typically try to insert |
| Provider Position | Preferred provider stance |
| Acceptable Modifications | Modifications you can live with |
| Fallback Language | Alternative acceptable language |
| Do Not Accept | Deal-breaker language to reject |
| Notes | Additional guidance |

Styling: professional headers, alternating row colors, text wrapping, frozen panes, optimized column widths.

---

## Frontend

### `templates/index.html`
Single-page interface with sections:
- **Upload**: drag-drop + file input (PDF, DOCX, XLSX)
- **Configuration**: Agreement Type (12 options), User Role (Customer/Provider/Neutral), Risk Tolerance (Low/Moderate/High)
- **Progress**: spinner, status messages, rotating reassurance messages (every 8s)
- **Result**: download button, generate another option
- **Error**: display with retry

### `static/js/main.js` and `public/js/main.js`
Frontend logic (identical files for local vs. Vercel):
- File validation and upload via FormData
- Two-phase for local: upload → poll `/api/status/<job_id>` every 1 second
- Single-phase for Vercel: wait for synchronous response
- Health check on page load (`/api/health`)

**Note:** `static/` is used by local Flask (`app.py`); `public/` is served by Vercel. Keep these files in sync when making frontend changes.

---

## Vercel Deployment

The `vercel.json` configures:
- Python 3.12 runtime for all `api/*.py` functions
- Upload function: **300s timeout**, **1GB memory** (required for large documents)
- Static routing: `/css/*` and `/js/*` → `public/`
- API routing: `/api/upload` → `api/upload.py`, etc.

Vercel uses `/tmp` for all file storage (its only writable directory). Files are cleaned up after each request.

---

## Development Conventions

### Adding New Contract Topics
1. Add topic name to the topics list in `playbook_generator.py`
2. Update the system prompt if needed
3. The Excel writer auto-generates a sheet per topic — no changes needed there

### AI Provider Selection
The app checks `ANTHROPIC_API_KEY` first, then `OPENAI_API_KEY`. To force a specific provider, only set that provider's key. The model names are configured in `config.py`:
- Anthropic: `claude-sonnet-4-20250514`
- OpenAI: `gpt-4o`

### Local vs. Vercel Code Paths
- `IS_VERCEL` flag in `config.py` detects Vercel environment
- `app.py` is **not** used on Vercel — only `api/*.py` functions run
- Job queue and polling in `app.py` have no Vercel equivalent (synchronous only)

### Frontend Changes
Always update **both** `static/` and `public/` when changing CSS or JS, since they serve different deployment targets.

---

## Common Commands

```bash
# Run development server
python app.py

# Run with debug mode
FLASK_DEBUG=1 python app.py

# Check code style
flake8 .

# Verify API key is set
echo $ANTHROPIC_API_KEY

# Kill process on port 3005
lsof -i :3005 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

---

## Troubleshooting

**Port 3005 already in use:**
```bash
lsof -i :3005
kill -9 <PID>
```

**Import errors:**
```bash
pip install -r requirements.txt
```

**API key errors:**
```bash
# Check which key is set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
# Or check .env file
cat .env
```

**Vercel timeout (document too large):**
- The upload function has a 5-minute limit; very large documents may exceed this
- Consider chunking the document in `document_parser.py` before analysis

**Large documents slow to process:**
- Parallel analysis (5 workers) is already enabled
- Reduce the number of topics or increase `max_workers` in `playbook_generator.py`

---

## Do Not Modify

- `BackgroundDocs/` — Reference materials (not in git)
- `vercel.json` timeouts/memory — Required for large document processing
- The 12-column schema in `excel_writer.py` — Changing breaks existing playbook format

## Safe to Adjust

- `config.py` — Ports, model names, file size limits
- `templates/index.html` — UI layout and copy
- `static/` and `public/` — Styling and frontend behavior
- Contract topics list in `playbook_generator.py` — Extend as needed
- System prompt in `playbook_generator.py` — Tune AI analysis style

---

## Remote Repository

https://github.com/Tucuxi-Inc/ContractPlaybookBuilder
