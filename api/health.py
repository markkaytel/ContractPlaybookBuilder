"""
Vercel serverless function: Health check endpoint.
"""
import os
import sys
from flask import Flask, jsonify

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

app = Flask(__name__)


@app.route('/api/health')
def health():
    """Health check endpoint."""
    api_configured = bool(config.ANTHROPIC_API_KEY) or bool(config.OPENAI_API_KEY)
    return jsonify({
        "status": "healthy",
        "api_key_configured": api_configured,
        "provider": "anthropic" if config.ANTHROPIC_API_KEY else "openai"
    })
