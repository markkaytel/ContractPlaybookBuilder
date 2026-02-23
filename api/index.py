"""
Vercel serverless function: Serve the main HTML page.
"""
import os
import sys
from flask import Flask, render_template

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    """Serve the main application page."""
    return render_template('index.html')
