"""
Contract Playbook Builder - Main Flask Application

A web application that generates professional contract playbooks from uploaded agreements.
"""
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

import config
from utils.document_parser import parse_document, allowed_file
from utils.playbook_generator import analyze_contract_chunked
from utils.excel_writer import generate_playbook_excel
from utils.web_search import search_legal_resources, fetch_multiple_urls, format_web_resources_for_ai

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE_MB * 1024 * 1024

# In-memory storage for progress tracking
processing_status = {}


@app.route("/")
def index():
    """Render the main upload page."""
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """
    Handle file upload and start playbook generation.

    Returns JSON with job_id for progress tracking.
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

    # Check for API key (Anthropic or OpenAI)
    if not config.ANTHROPIC_API_KEY and not config.OPENAI_API_KEY:
        return jsonify({
            "error": "API key not configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable."
        }), 500

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_filename = f"{timestamp}_{job_id}_{filename}"
    file_path = os.path.join(config.UPLOAD_FOLDER, saved_filename)
    file.save(file_path)

    # Get options from request
    agreement_type = request.form.get("agreement_type", "General Agreement")
    user_role = request.form.get("user_role", "Customer")
    risk_tolerance = request.form.get("risk_tolerance", "Moderate")

    # Handle guidance documents (multiple files)
    guidance_files = request.files.getlist("guidance_files")
    guidance_file_paths = []
    
    for guidance_file in guidance_files:
        if guidance_file and guidance_file.filename:
            if allowed_file(guidance_file.filename, config.ALLOWED_EXTENSIONS):
                guidance_filename = secure_filename(guidance_file.filename)
                guidance_saved_filename = f"{timestamp}_{job_id}_guidance_{guidance_filename}"
                guidance_path = os.path.join(config.UPLOAD_FOLDER, guidance_saved_filename)
                guidance_file.save(guidance_path)
                guidance_file_paths.append({
                    "path": guidance_path,
                    "filename": guidance_filename
                })

    # Initialize status
    processing_status[job_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Uploading file...",
        "file_path": file_path,
        "original_filename": filename,
        "agreement_type": agreement_type,
        "user_role": user_role,
        "risk_tolerance": risk_tolerance,
        "output_path": None,
        "error": None,
        "web_resources": [],
        "guidance_files": guidance_file_paths
    }

    return jsonify({
        "job_id": job_id,
        "message": "File uploaded successfully. Processing started.",
        "guidance_count": len(guidance_file_paths)
    })


@app.route("/api/process/<job_id>", methods=["POST"])
def process_file(job_id):
    """
    Process the uploaded file and generate the playbook.
    """
    if job_id not in processing_status:
        return jsonify({"error": "Job not found"}), 404

    job = processing_status[job_id]

    if job["status"] == "completed":
        return jsonify({"status": "completed", "message": "Already processed"})

    if job["status"] == "error":
        return jsonify({"status": "error", "error": job["error"]})

    try:
        # Update progress callback
        def update_progress(progress, message):
            processing_status[job_id]["progress"] = progress
            processing_status[job_id]["message"] = message

        # Step 1: Parse document
        update_progress(10, "Parsing document...")
        doc_data = parse_document(job["file_path"])

        if not doc_data.get("text"):
            raise ValueError("Could not extract text from the document. Please ensure it's not a scanned image.")

        # Step 2: Parse guidance documents if provided
        guidance_documents_text = ""
        if job.get("guidance_files"):
            update_progress(15, f"Parsing {len(job['guidance_files'])} guidance document(s)...")
            guidance_texts = []
            for guidance_file in job["guidance_files"]:
                try:
                    guidance_data = parse_document(guidance_file["path"])
                    if guidance_data.get("text"):
                        guidance_texts.append(f"--- Guidance Document: {guidance_file['filename']} ---\n{guidance_data['text']}")
                except Exception as e:
                    print(f"Warning: Could not parse guidance file {guidance_file['filename']}: {e}")
            
            if guidance_texts:
                guidance_documents_text = "\n\n".join(guidance_texts)
        
        # Step 3: Analyze with AI
        update_progress(20, "Analyzing contract with AI...")
        
        # Include web resources if any were selected
        web_resources_text = ""
        if job.get("web_resources"):
            update_progress(20, "Fetching selected web resources...")
            web_resources_data = fetch_multiple_urls(job["web_resources"])
            web_resources_text = format_web_resources_for_ai(web_resources_data)
        
        playbook_data = analyze_contract_chunked(
            contract_text=doc_data["text"],
            agreement_type=job["agreement_type"],
            user_role=job["user_role"],
            risk_tolerance=job["risk_tolerance"],
            progress_callback=lambda p, m: update_progress(20 + int(p * 0.6), m),
            web_resources=web_resources_text,
            guidance_documents=guidance_documents_text
        )

        # Step 3: Generate Excel
        update_progress(85, "Generating Excel playbook...")
        output_filename = f"Playbook_{job['original_filename'].rsplit('.', 1)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = os.path.join(config.OUTPUT_FOLDER, output_filename)
        generate_playbook_excel(playbook_data, output_path)

        # Update status
        processing_status[job_id]["status"] = "completed"
        processing_status[job_id]["progress"] = 100
        processing_status[job_id]["message"] = "Playbook generated successfully!"
        processing_status[job_id]["output_path"] = output_path
        processing_status[job_id]["output_filename"] = output_filename

        # Clean up uploaded file
        try:
            os.remove(job["file_path"])
        except Exception:
            pass

        return jsonify({
            "status": "completed",
            "message": "Playbook generated successfully!",
            "download_url": f"/api/download/{job_id}"
        })

    except Exception as e:
        processing_status[job_id]["status"] = "error"
        processing_status[job_id]["error"] = str(e)
        processing_status[job_id]["message"] = f"Error: {str(e)}"

        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/api/status/<job_id>")
def get_status(job_id):
    """Get the processing status for a job."""
    if job_id not in processing_status:
        return jsonify({"error": "Job not found"}), 404

    job = processing_status[job_id]
    return jsonify({
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "error": job.get("error"),
        "download_url": f"/api/download/{job_id}" if job["status"] == "completed" else None
    })


@app.route("/api/download/<job_id>")
def download_file(job_id):
    """Download the generated playbook."""
    if job_id not in processing_status:
        return jsonify({"error": "Job not found"}), 404

    job = processing_status[job_id]

    if job["status"] != "completed":
        return jsonify({"error": "Playbook not ready"}), 400

    if not job.get("output_path") or not os.path.exists(job["output_path"]):
        return jsonify({"error": "Output file not found"}), 404

    return send_file(
        job["output_path"],
        as_attachment=True,
        download_name=job.get("output_filename", "Playbook.xlsx"),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/api/search", methods=["POST"])
def search_resources():
    """
    Search for legal resources related to an agreement type.
    
    Uses Google Custom Search if configured, otherwise uses DuckDuckGo (free).
    
    Expects JSON: {
        "agreement_type": "SaaS Agreement",
        "search_instructions": "Optional custom search instructions"
    }
    Returns: List of search results
    """
    try:
        data = request.get_json()
        agreement_type = data.get("agreement_type", "General Agreement")
        search_instructions = data.get("search_instructions", "")
        
        results = search_legal_resources(
            agreement_type=agreement_type,
            max_results=12,
            custom_instructions=search_instructions
        )
        
        # Determine which search engine was used
        search_engine = "Google Custom Search" if (config.GOOGLE_API_KEY and config.GOOGLE_SEARCH_ENGINE_ID) else "DuckDuckGo"
        
        return jsonify({
            "results": results,
            "count": len(results),
            "search_engine": search_engine
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Search failed: {str(e)}"
        }), 500


@app.route("/api/resources/save", methods=["POST"])
def save_selected_resources():
    """
    Save selected web resources to a job for later use in playbook generation.
    
    Expects JSON: {
        "job_id": "...",
        "selected_urls": ["url1", "url2", ...]
    }
    """
    try:
        data = request.get_json()
        job_id = data.get("job_id")
        selected_urls = data.get("selected_urls", [])
        
        if not job_id or job_id not in processing_status:
            return jsonify({"error": "Invalid job ID"}), 404
        
        # Store the selected URLs
        processing_status[job_id]["web_resources"] = selected_urls
        
        return jsonify({
            "message": "Resources saved successfully",
            "count": len(selected_urls)
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Failed to save resources: {str(e)}"
        }), 500


@app.route("/api/health")
def health_check():
    """Health check endpoint."""
    # Check for either Anthropic or OpenAI API key
    api_configured = bool(config.ANTHROPIC_API_KEY) or bool(config.OPENAI_API_KEY)
    
    provider_info = {
        "provider": config.AI_PROVIDER,
        "model": config.ANTHROPIC_MODEL if config.AI_PROVIDER == "anthropic" else config.OPENAI_MODEL
    }
    
    if config.AI_PROVIDER == "openai" and config.OPENAI_BASE_URL:
        provider_info["base_url"] = config.OPENAI_BASE_URL
    
    # Check Google Search configuration
    google_search_configured = bool(config.GOOGLE_API_KEY) and bool(config.GOOGLE_SEARCH_ENGINE_ID)
    
    return jsonify({
        "status": "healthy",
        "api_key_configured": api_configured,
        "google_search_configured": google_search_configured,
        **provider_info
    })


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("Contract Playbook Builder")
    print(f"{'='*60}")
    print(f"Starting server on http://localhost:{config.PORT}")

    if config.ANTHROPIC_API_KEY:
        print(f"AI Provider: Anthropic Claude")
        print(f"Model: {config.ANTHROPIC_MODEL}")
    elif config.OPENAI_API_KEY:
        if config.OPENAI_BASE_URL:
            print(f"AI Provider: OpenAI-Compatible API")
            print(f"Base URL: {config.OPENAI_BASE_URL}")
        else:
            print(f"AI Provider: OpenAI")
        print(f"Model: {config.OPENAI_MODEL}")
    else:
        print("AI Provider: NOT CONFIGURED")
    print(f"{'='*60}\n")

    if not config.ANTHROPIC_API_KEY and not config.OPENAI_API_KEY:
        print("WARNING: No API key configured!")
        print("Set with: export ANTHROPIC_API_KEY='your-key-here'")
        print("Or:       export OPENAI_API_KEY='your-key-here'")
        print("Or:       export OPENAI_BASE_URL='http://localhost:1234/v1'\n")

    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)