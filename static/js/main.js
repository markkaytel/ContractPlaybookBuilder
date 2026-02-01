/**
 * Contract Playbook Builder - Frontend JavaScript
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

// Guidance Documents Elements
const guidanceInput = document.getElementById('guidance-input');
const guidanceDropZone = document.getElementById('guidance-drop-zone');
const guidanceFilesList = document.getElementById('guidance-files-list');
const guidanceFilesItems = document.getElementById('guidance-files-items');
const clearGuidanceBtn = document.getElementById('clear-guidance-btn');

// State
let currentJobId = null;
let statusPollInterval = null;
let reassuranceInterval = null;
let reassuranceIndex = 0;
let selectedResources = [];
let searchResults = [];

// Reassurance messages that rotate while processing
const reassuranceMessages = [
    "Your playbook is being generated...",
    "AI is reviewing the document...",
    "Still processing — this takes a few minutes...",
    "Building your negotiation guide...",
    "Analyzing document structure...",
    "Processing — thank you for your patience...",
    "Creating comprehensive guidance...",
    "Almost there — finalizing analysis...",
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

// Guidance Documents Upload Handling
guidanceInput.addEventListener('change', handleGuidanceFilesSelect);

guidanceDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    guidanceDropZone.classList.add('dragover');
});

guidanceDropZone.addEventListener('dragleave', () => {
    guidanceDropZone.classList.remove('dragover');
});

guidanceDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    guidanceDropZone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        // Add to existing files
        const dt = new DataTransfer();
        
        // Add existing files
        for (let i = 0; i < guidanceInput.files.length; i++) {
            dt.items.add(guidanceInput.files[i]);
        }
        
        // Add new files
        for (let i = 0; i < files.length; i++) {
            dt.items.add(files[i]);
        }
        
        guidanceInput.files = dt.files;
        handleGuidanceFilesSelect();
    }
});

function handleGuidanceFilesSelect() {
    const files = guidanceInput.files;
    
    if (files.length === 0) {
        guidanceFilesList.classList.add('hidden');
        return;
    }
    
    guidanceFilesList.classList.remove('hidden');
    
    const countElement = guidanceFilesList.querySelector('.guidance-count');
    countElement.textContent = `${files.length} document${files.length !== 1 ? 's' : ''} selected`;
    
    guidanceFilesItems.innerHTML = '';
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileItem = document.createElement('div');
        fileItem.className = 'guidance-file-item';
        fileItem.innerHTML = `
            <div class="guidance-file-info">
                <span class="guidance-file-name">${escapeHtml(file.name)}</span>
                <span class="guidance-file-size">${formatFileSize(file.size)}</span>
            </div>
            <button type="button" class="remove-guidance-file" data-index="${i}">×</button>
        `;
        
        const removeBtn = fileItem.querySelector('.remove-guidance-file');
        removeBtn.addEventListener('click', () => removeGuidanceFile(i));
        
        guidanceFilesItems.appendChild(fileItem);
    }
}

function removeGuidanceFile(index) {
    const dt = new DataTransfer();
    const files = guidanceInput.files;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }
    
    guidanceInput.files = dt.files;
    handleGuidanceFilesSelect();
}

clearGuidanceBtn.addEventListener('click', () => {
    guidanceInput.value = '';
    handleGuidanceFilesSelect();
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

// Form Submission
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
    
    // Add guidance documents if any
    const guidanceFiles = guidanceInput.files;
    for (let i = 0; i < guidanceFiles.length; i++) {
        formData.append('guidance_files', guidanceFiles[i]);
    }

    // Disable button and show progress
    generateBtn.disabled = true;
    generateBtn.textContent = 'Uploading...';

    try {
        // Upload file
        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const uploadData = await uploadResponse.json();

        if (!uploadResponse.ok) {
            throw new Error(uploadData.error || 'Upload failed');
        }

        currentJobId = uploadData.job_id;

        // Save selected resources if any
        if (selectedResources.length > 0) {
            try {
                await fetch('/api/resources/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        job_id: currentJobId,
                        selected_urls: selectedResources.map(r => r.link)
                    })
                });
            } catch (error) {
                console.warn('Failed to save resources:', error);
                // Continue anyway - not critical
            }
        }

        // Show progress section
        showSection('progress');
        updateProgress(5, 'Starting analysis...');
        startReassuranceRotation();

        // Start polling for status updates - this is the primary completion detection
        startPollingStatus(currentJobId);

        // Start processing in background (don't await - it takes minutes)
        // The polling will detect completion, but we also handle it here as backup
        fetch(`/api/process/${currentJobId}`, {
            method: 'POST'
        }).then(response => response.json()).then(processData => {
            // Processing complete - the polling should have already detected this
            // but handle here as backup in case polling missed it
            if (processData.status === 'completed') {
                if (statusPollInterval) {
                    clearInterval(statusPollInterval);
                }
                stopReassuranceRotation();
                showSection('result');
                downloadBtn.onclick = () => downloadPlaybook(currentJobId);
            } else if (processData.status === 'error') {
                if (statusPollInterval) {
                    clearInterval(statusPollInterval);
                }
                stopReassuranceRotation();
                showError(processData.error || 'Processing failed');
            }
            // If neither completed nor error, let polling continue to handle it
        }).catch(error => {
            // Only show error if we're still in processing state
            // (polling might have already handled completion)
            if (progressSection && !progressSection.classList.contains('hidden')) {
                if (statusPollInterval) {
                    clearInterval(statusPollInterval);
                }
                stopReassuranceRotation();
                showError(error.message || 'Processing failed');
            }
        });

    } catch (error) {
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Playbook';
    }
});

// Progress Updates
function updateProgress(percent, message) {
    progressText.textContent = message;

    // Update substatus based on progress
    if (percent < 20) {
        progressSubstatus.textContent = "Parsing document and preparing for analysis";
    } else if (percent < 50) {
        progressSubstatus.textContent = "AI is reviewing contract provisions";
    } else if (percent < 80) {
        progressSubstatus.textContent = "Generating negotiation strategies";
    } else {
        progressSubstatus.textContent = "Finalizing your playbook";
    }
}

function startReassuranceRotation() {
    // Rotate reassurance messages every 8 seconds
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

function startPollingStatus(jobId) {
    statusPollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            const data = await response.json();

            updateProgress(data.progress, data.message);

            if (data.status === 'completed') {
                clearInterval(statusPollInterval);
                showSection('result');
                downloadBtn.onclick = () => downloadPlaybook(jobId);
            } else if (data.status === 'error') {
                clearInterval(statusPollInterval);
                showError(data.error || 'An error occurred');
            }
        } catch (error) {
            clearInterval(statusPollInterval);
            showError('Lost connection to server');
        }
    }, 1000);
}

// Download
async function downloadPlaybook(jobId) {
    window.location.href = `/api/download/${jobId}`;
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

    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }
    stopReassuranceRotation();
}

function startOver() {
    currentJobId = null;
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }
    stopReassuranceRotation();
    reassuranceIndex = 0;

    // Reset form
    uploadForm.reset();
    removeFile();
    updateProgress(0, 'Starting analysis...');

    showSection('upload');
}

// Web Search Functionality
const searchModal = document.getElementById('search-modal');
const searchResourcesBtn = document.getElementById('search-resources-btn');
const closeSearchModal = document.getElementById('close-search-modal');
const cancelSearchBtn = document.getElementById('cancel-search-btn');
const saveResourcesBtn = document.getElementById('save-resources-btn');
const searchLoading = document.getElementById('search-loading');
const searchError = document.getElementById('search-error');
const searchErrorMessage = document.getElementById('search-error-message');
const searchResultsDiv = document.getElementById('search-results');
const searchResultsList = document.getElementById('search-results-list');
const selectedResourcesDisplay = document.getElementById('selected-resources-display');
const selectedResourcesList = document.getElementById('selected-resources-list');
const clearResourcesBtn = document.getElementById('clear-resources-btn');

// Search button click
searchResourcesBtn.addEventListener('click', async () => {
    const agreementType = document.getElementById('agreement-type').value;
    const searchInstructions = document.getElementById('search-instructions').value.trim();
    
    // Show modal
    searchModal.classList.remove('hidden');
    
    // Show loading state
    searchLoading.classList.remove('hidden');
    searchError.classList.add('hidden');
    searchResultsDiv.classList.add('hidden');
    
    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                agreement_type: agreementType,
                search_instructions: searchInstructions
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Search failed');
        }
        
        searchResults = data.results;
        displaySearchResults(searchResults);
        
    } catch (error) {
        searchLoading.classList.add('hidden');
        searchError.classList.remove('hidden');
        searchErrorMessage.textContent = error.message;
    }
});

// Display search results
function displaySearchResults(results) {
    searchLoading.classList.add('hidden');
    searchError.classList.add('hidden');
    searchResultsDiv.classList.remove('hidden');
    
    searchResultsList.innerHTML = '';
    
    if (results.length === 0) {
        searchResultsList.innerHTML = '<p style="text-align: center; color: var(--text-muted);">No results found. Try a different agreement type.</p>';
        return;
    }
    
    results.forEach((result, index) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'search-result-item';
        resultItem.dataset.index = index;
        
        // Check if already selected
        const isSelected = selectedResources.some(r => r.link === result.link);
        if (isSelected) {
            resultItem.classList.add('selected');
        }
        
        resultItem.innerHTML = `
            <div class="search-result-header">
                <input type="checkbox" class="search-result-checkbox" ${isSelected ? 'checked' : ''} data-index="${index}">
                <div class="search-result-content">
                    <div class="search-result-title">${escapeHtml(result.title)}</div>
                    <div class="search-result-url">${escapeHtml(result.display_link)}</div>
                    <div class="search-result-snippet">${escapeHtml(result.snippet)}</div>
                </div>
            </div>
        `;
        
        // Click handler for the whole item
        resultItem.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT') {
                const checkbox = resultItem.querySelector('.search-result-checkbox');
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
        
        // Checkbox change handler
        const checkbox = resultItem.querySelector('.search-result-checkbox');
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            toggleResourceSelection(index, resultItem);
        });
        
        searchResultsList.appendChild(resultItem);
    });
}

// Toggle resource selection
function toggleResourceSelection(index, itemElement) {
    const result = searchResults[index];
    const existingIndex = selectedResources.findIndex(r => r.link === result.link);
    
    if (existingIndex >= 0) {
        // Remove from selection
        selectedResources.splice(existingIndex, 1);
        itemElement.classList.remove('selected');
    } else {
        // Add to selection
        selectedResources.push(result);
        itemElement.classList.add('selected');
    }
    
    updateSelectedResourcesDisplay();
}

// Update selected resources display
function updateSelectedResourcesDisplay() {
    const count = selectedResources.length;
    const countElement = document.querySelector('.selected-count');
    
    if (count === 0) {
        selectedResourcesDisplay.classList.add('hidden');
        return;
    }
    
    selectedResourcesDisplay.classList.remove('hidden');
    countElement.textContent = `${count} resource${count !== 1 ? 's' : ''} selected`;
    
    selectedResourcesList.innerHTML = '';
    
    selectedResources.forEach((resource, index) => {
        const item = document.createElement('div');
        item.className = 'selected-resource-item';
        item.innerHTML = `
            <div class="selected-resource-info">
                <div class="selected-resource-title">${escapeHtml(resource.title)}</div>
                <div class="selected-resource-url">${escapeHtml(resource.link)}</div>
            </div>
            <button type="button" class="remove-resource" data-index="${index}">×</button>
        `;
        
        const removeBtn = item.querySelector('.remove-resource');
        removeBtn.addEventListener('click', () => {
            selectedResources.splice(index, 1);
            updateSelectedResourcesDisplay();
            
            // Update search results display if modal is open
            if (!searchModal.classList.contains('hidden')) {
                displaySearchResults(searchResults);
            }
        });
        
        selectedResourcesList.appendChild(item);
    });
}

// Save selected resources
saveResourcesBtn.addEventListener('click', async () => {
    if (!currentJobId) {
        // No job yet - just close modal and keep selections
        closeSearchModalHandler();
        return;
    }
    
    // Save to backend
    try {
        const response = await fetch('/api/resources/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_id: currentJobId,
                selected_urls: selectedResources.map(r => r.link)
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save resources');
        }
        
        closeSearchModalHandler();
        
    } catch (error) {
        alert('Failed to save resources: ' + error.message);
    }
});

// Clear all resources
clearResourcesBtn.addEventListener('click', () => {
    selectedResources = [];
    updateSelectedResourcesDisplay();
    
    // Update search results if modal is open
    if (!searchModal.classList.contains('hidden')) {
        displaySearchResults(searchResults);
    }
});

// Close modal handlers
function closeSearchModalHandler() {
    searchModal.classList.add('hidden');
}

closeSearchModal.addEventListener('click', closeSearchModalHandler);
cancelSearchBtn.addEventListener('click', closeSearchModalHandler);

// Close modal on backdrop click
searchModal.addEventListener('click', (e) => {
    if (e.target === searchModal) {
        closeSearchModalHandler();
    }
});

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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