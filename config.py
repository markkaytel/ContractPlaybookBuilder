"""
Configuration settings for Contract Playbook Builder
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Server settings
PORT = int(os.environ.get("PORT", 3005))
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

# Detect Vercel environment (Vercel automatically sets VERCEL=1)
IS_VERCEL = os.environ.get("VERCEL", "") == "1"

# File upload settings - use /tmp on Vercel (read-only filesystem except /tmp)
if IS_VERCEL:
    UPLOAD_FOLDER = "/tmp/uploads"
    OUTPUT_FOLDER = "/tmp/output"
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "output")

MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE", 50))
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx"}

# AI Provider settings
# Primary: Anthropic Claude (preferred)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# OpenAI or OpenAI-compatible API
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")  # Custom API endpoint (optional)

# Which provider to use (anthropic or openai)
AI_PROVIDER = os.environ.get("AI_PROVIDER", "anthropic" if ANTHROPIC_API_KEY else "openai")

# Google Custom Search API (for web research)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID", "")

# Ensure directories exist (skip on Vercel where filesystem is read-only)
if not IS_VERCEL:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
