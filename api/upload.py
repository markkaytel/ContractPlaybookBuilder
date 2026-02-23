"""
Vercel serverless function: Upload, process, and return playbook.

Single synchronous endpoint that handles the entire pipeline:
1. Receives the uploaded file
2. Saves it to /tmp
3. Parses the document
4. Runs AI analysis (Anthropic Claude)
5. Generates Excel workbook
6. Returns the Excel file as the HTTP response

Requires Vercel Pro plan with maxDuration: 300 (5 minutes).
"""
import os
import sys
import uuid
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Add parent directory to path so utils/ and config can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.document_parser import parse_document, allowed_file
from utils.playbook_generator import analyze_contract_chunked
from utils.excel_writer import generate_playbook_excel

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE_MB * 1024 * 1024


@app.route('/api/upload', methods=['POST'])
def upload_and_process():
    """
    Single endpoint: upload file, process it, return Excel.

    Accepts multipart form data with:
    - file: The agreement file (PDF, DOCX, or XLSX)
    - agreement_type: Type of agreement (optional, default: General Agreement)
    - user_role: User's role (optional, default: Customer)
    - risk_tolerance: Risk tolerance level (optional, default: Moderate)

    Returns: The generated Excel playbook file as an attachment.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, config.ALLOWED_EXTENSIONS):
        return jsonify({
            "error": f"File type not supported. Allowed types: {', '.join(config.ALLOWED_EXTENSIONS)}"
        }), 400

    if not config.ANTHROPIC_API_KEY and not config.OPENAI_API_KEY:
        return jsonify({
            "error": "API key not configured. Set ANTHROPIC_API_KEY environment variable."
        }), 500

    # Save to /tmp (only writable directory on Vercel)
    filename = secure_filename(file.filename)
    tmp_upload = os.path.join(tempfile.gettempdir(), f"upload_{uuid.uuid4()}_{filename}")
    file.save(tmp_upload)

    try:
        # Get configuration options from form
        agreement_type = request.form.get("agreement_type", "General Agreement")
        user_role = request.form.get("user_role", "Customer")
        risk_tolerance = request.form.get("risk_tolerance", "Moderate")

        # Step 1: Parse document
        doc_data = parse_document(tmp_upload)
        if not doc_data.get("text"):
            raise ValueError(
                "Could not extract text from the document. "
                "Please ensure it's not a scanned image."
            )

        # Step 2: AI analysis (takes 1-4 minutes with parallel processing)
        playbook_data = analyze_contract_chunked(
            contract_text=doc_data["text"],
            agreement_type=agreement_type,
            user_role=user_role,
            risk_tolerance=risk_tolerance,
            progress_callback=None
        )

        # Step 3: Generate Excel to /tmp
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        output_filename = f"Playbook_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        tmp_output = os.path.join(tempfile.gettempdir(), output_filename)
        generate_playbook_excel(playbook_data, tmp_output)

        # Step 4: Return the Excel file directly
        return send_file(
            tmp_output,
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up uploaded file
        try:
            os.remove(tmp_upload)
        except OSError:
            pass
