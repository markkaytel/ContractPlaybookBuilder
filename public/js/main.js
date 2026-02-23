/**
 * Contract Playbook Builder - Frontend JavaScript
 *
 * Vercel deployment version: single-request flow.
 * Uploads the file and receives the Excel playbook directly in the response.
 */

// DOM Elements
const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const errorSection = document.getElementById('error-section');
const uploadForm = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const fileInfo = document.getElementById('file-info');
const generateBtn = document.getElementById('generate-btn');
const downloadBtn = document.getElementById('download-btn');
const progressText = document.getElementById('progress-text');
const progressSubstatus = document.getElementById('progress-substatus');
const progressReassurance = document.getElementById('progress-reassurance');
const errorMessage = document.getElementById('error-message');

// State
let reassuranceInterval = null;
let reassuranceIndex = 0;
let simulatedProgressInterval = null;
let simulatedProgress = 0;
let downloadBlobUrl = null;
let downloadFilename = 'Playbook.xlsx';

// Reassurance messages that rotate while processing
const reassuranceMessages = [
    "Your playbook is being generated...",
    "AI is reviewing the document...",
    "Still processing \u2014 this takes a few minutes...",
    "Building your negotiation guide...",
    "Analyzing document structure...",
    "Processing \u2014 thank you for your patience...",
    "Creating comprehensive guidance...",
    "Almost there \u2014 finalizing analysis...",
];

// Simulated progress stages (client-side only, since server can't push updates)
const progressStages = [
    { target: 8,  message: "Uploading document...",      substatus: "Sending file to server" },
    { target: 15, message: "Parsing document...",         substatus: "Extracting text and structure" },
    { target: 30, message: "Analyzing contract...",       substatus: "AI is reviewing contract overview" },
    { target: 50, message: "Analyzing clauses...",        substatus: "Generating negotiation strategies for each topic" },
    { target: 70, message: "Detailed analysis...",        substatus: "Reviewing all contract provisions" },
    { target: 85, message: "Building playbook...",        substatus: "Compiling analysis results" },
    { target: 93, message: "Generating Excel...",         substatus: "Creating your professional playbook" },
];

// File Upload Handling
fileInput.addEventListener('change', handleFileSelect);

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelect();
    }
});

function handleFileSelect() {
    const file = fileInput.files[0];
    if (file) {
        const fileName = file.name;
        const fileSize = formatFileSize(file.size);

        fileInfo.querySelector('.file-name').textContent = `${fileName} (${fileSize})`;
        fileInfo.classList.remove('hidden');
        dropZone.style.display = 'none';
    }
}

function removeFile() {
    fileInput.value = '';
    fileInfo.classList.add('hidden');
    dropZone.style.display = 'block';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Form Submission — Single-request flow
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
        showError('Please select a file to upload.');
        return;
    }

    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('agreement_type', document.getElementById('agreement-type').value);
    formData.append('user_role', document.getElementById('user-role').value);
    formData.append('risk_tolerance', document.getElementById('risk-tolerance').value);

    // Disable button and show progress
    generateBtn.disabled = true;
    generateBtn.textContent = 'Processing...';

    showSection('progress');
    startSimulatedProgress();
    startReassuranceRotation();

    try {
        // Set up abort controller with 5.5 minute timeout
        // (server has 5 min maxDuration, add 30s buffer for network)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 330000);

        // Single request: upload + process + receive Excel
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            // Try to parse error JSON
            let errorMsg = 'Processing failed';
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorMsg;
            } catch {
                errorMsg = `Server error (${response.status})`;
            }
            throw new Error(errorMsg);
        }

        // Response is the Excel file — convert to downloadable blob
        const blob = await response.blob();

        // Extract filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        if (contentDisposition) {
            const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (match) {
                downloadFilename = match[1].replace(/['"]/g, '');
            }
        }

        // Create blob URL for download
        if (downloadBlobUrl) {
            window.URL.revokeObjectURL(downloadBlobUrl);
        }
        downloadBlobUrl = window.URL.createObjectURL(blob);

        // Set up download button
        downloadBtn.onclick = () => {
            const a = document.createElement('a');
            a.href = downloadBlobUrl;
            a.download = downloadFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        };

        // Auto-trigger the download
        downloadBtn.click();

        // Show success
        stopSimulatedProgress();
        stopReassuranceRotation();
        showSection('result');

    } catch (error) {
        stopSimulatedProgress();
        stopReassuranceRotation();

        if (error.name === 'AbortError') {
            showError('Request timed out. The document may be too large or complex. Please try a shorter document.');
        } else {
            showError(error.message || 'An error occurred during processing.');
        }
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Playbook';
    }
});

// Simulated Progress (client-side only)
function startSimulatedProgress() {
    simulatedProgress = 0;
    let stageIndex = 0;

    // Show initial stage
    if (progressStages.length > 0) {
        progressText.textContent = progressStages[0].message;
        progressSubstatus.textContent = progressStages[0].substatus;
    }

    simulatedProgressInterval = setInterval(() => {
        // Advance to next stage when target is reached
        if (stageIndex < progressStages.length - 1 && simulatedProgress >= progressStages[stageIndex].target) {
            stageIndex++;
            progressText.textContent = progressStages[stageIndex].message;
            progressSubstatus.textContent = progressStages[stageIndex].substatus;
        }

        // Slow logarithmic progress that never reaches 100
        simulatedProgress += Math.max(0.1, (100 - simulatedProgress) * 0.004);
    }, 1000);
}

function stopSimulatedProgress() {
    if (simulatedProgressInterval) {
        clearInterval(simulatedProgressInterval);
        simulatedProgressInterval = null;
    }
}

// Reassurance rotation
function startReassuranceRotation() {
    reassuranceInterval = setInterval(() => {
        reassuranceIndex = (reassuranceIndex + 1) % reassuranceMessages.length;
        if (progressReassurance) {
            progressReassurance.textContent = reassuranceMessages[reassuranceIndex];
        }
    }, 8000);
}

function stopReassuranceRotation() {
    if (reassuranceInterval) {
        clearInterval(reassuranceInterval);
        reassuranceInterval = null;
    }
}

// UI State Management
function showSection(section) {
    uploadSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    resultSection.classList.add('hidden');
    errorSection.classList.add('hidden');

    switch (section) {
        case 'upload':
            uploadSection.classList.remove('hidden');
            break;
        case 'progress':
            progressSection.classList.remove('hidden');
            break;
        case 'result':
            resultSection.classList.remove('hidden');
            break;
        case 'error':
            errorSection.classList.remove('hidden');
            break;
    }
}

function showError(message) {
    errorMessage.textContent = message;
    showSection('error');
    stopSimulatedProgress();
    stopReassuranceRotation();
}

function startOver() {
    // Clean up blob URL
    if (downloadBlobUrl) {
        window.URL.revokeObjectURL(downloadBlobUrl);
        downloadBlobUrl = null;
    }

    stopSimulatedProgress();
    stopReassuranceRotation();
    reassuranceIndex = 0;

    // Reset form
    uploadForm.reset();
    removeFile();

    showSection('upload');
}

// Health check on load
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        if (!data.api_key_configured) {
            showError('API key is not configured. Please set the ANTHROPIC_API_KEY (or OPENAI_API_KEY) environment variable and restart the server.');
        }
    } catch (error) {
        console.log('Health check failed:', error);
    }
});
