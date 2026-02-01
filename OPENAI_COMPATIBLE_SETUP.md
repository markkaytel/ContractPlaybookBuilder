# Using OpenAI-Compatible APIs with Contract Playbook Builder

This guide explains how to use any OpenAI-compatible API provider with the Contract Playbook Builder, including local models and alternative cloud providers.

---

## Table of Contents

- [Supported Providers](#supported-providers)
- [Configuration Overview](#configuration-overview)
- [LM Studio Setup](#lm-studio-setup)
- [Ollama Setup](#ollama-setup)
- [Other Providers](#other-providers)
- [Troubleshooting](#troubleshooting)
- [Model Recommendations](#model-recommendations)

---

## Supported Providers

Any service that implements the OpenAI API specification will work with this application:

### Local Providers
- **LM Studio** - User-friendly desktop app for running local models
- **Ollama** - Command-line tool for running local models
- **LocalAI** - Self-hosted OpenAI alternative
- **Text Generation WebUI** - Web interface with OpenAI API endpoint
- **Jan** - Desktop app for running local models

### Cloud Providers
- **OpenAI** - Official OpenAI API
- **Azure OpenAI** - Microsoft's OpenAI service
- **Together.ai** - Cloud AI inference
- **Anyscale** - Ray-based AI serving
- **Groq** - Fast inference API
- **DeepInfra** - Multi-model API provider

### Self-Hosted
- **vLLM** - High-performance inference server
- **TGI (Text Generation Inference)** - HuggingFace's inference server
- **FastChat** - Multi-model serving system

---

## Configuration Overview

To use an OpenAI-compatible API, you need to set three environment variables:

```bash
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=http://your-api-endpoint/v1
OPENAI_MODEL=your-model-name
AI_PROVIDER=openai
```

### Configuration File (.env)

Create or edit your `.env` file in the project root:

```bash
# OpenAI-Compatible API Configuration
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=llama-3.1-8b-instruct
AI_PROVIDER=openai

# Optional settings
PORT=3005
MAX_FILE_SIZE=50
```

---

## LM Studio Setup

LM Studio is the easiest way to run local models with an OpenAI-compatible API.

### Step 1: Install LM Studio

1. Download from [lmstudio.ai](https://lmstudio.ai/)
2. Install and launch the application
3. Complete the initial setup

### Step 2: Download a Model

1. Click the **Search** icon (magnifying glass)
2. Search for one of these recommended models:
   - `llama-3.1-8b-instruct` (Good balance)
   - `llama-3.1-70b-instruct` (Best quality, requires powerful GPU)
   - `mistral-7b-instruct` (Fast, good quality)
   - `qwen2.5-14b-instruct` (Good for long contracts)

3. Click **Download** on your chosen model
4. Wait for download to complete

### Step 3: Load the Model

1. Click the **Local Server** tab (plug icon)
2. Select your downloaded model from the dropdown
3. Configure model settings:
   - **Context Length**: 8192 or higher
   - **GPU Offload**: Max for best performance
4. Click **Start Server**
5. Server will start on `http://localhost:1234`

### Step 4: Configure the Application

Edit your `.env` file:

```bash
OPENAI_API_KEY=lm-studio
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=llama-3.1-8b-instruct
AI_PROVIDER=openai
```

### Step 5: Run the Application

```bash
# Make sure your virtual environment is activated
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Start the application
python app.py
```

You should see:
```
============================================================
Contract Playbook Builder
============================================================
Starting server on http://localhost:3005
AI Provider: OpenAI-Compatible API
Base URL: http://localhost:1234/v1
Model: llama-3.1-8b-instruct
============================================================
```

---

## Ollama Setup

Ollama is a command-line tool for running local models with minimal configuration.

### Step 1: Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
- Download installer from [ollama.com](https://ollama.com/)
- Run the installer
- Ollama will start automatically

### Step 2: Pull a Model

```bash
# Recommended models (choose one):
ollama pull llama3.1          # 8B model
ollama pull llama3.1:70b      # 70B model (better quality)
ollama pull qwen2.5:14b       # 14B model (good balance)
ollama pull mistral           # 7B model (faster)

# List downloaded models
ollama list
```

### Step 3: Start Ollama Server

Ollama server usually starts automatically. If not:

```bash
ollama serve
```

Server runs on `http://localhost:11434`

### Step 4: Configure the Application

Edit your `.env` file:

```bash
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1
AI_PROVIDER=openai
```

**Note:** Use the model name exactly as shown in `ollama list`

### Step 5: Run the Application

```bash
python app.py
```

---

## Other Providers

### OpenAI Official API

```bash
OPENAI_API_KEY=sk-your-openai-api-key
# OPENAI_BASE_URL is not needed for official OpenAI
OPENAI_MODEL=gpt-4o
AI_PROVIDER=openai
```

### Azure OpenAI

```bash
OPENAI_API_KEY=your-azure-api-key
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
OPENAI_MODEL=gpt-4
AI_PROVIDER=openai
```

### Together.ai

```bash
OPENAI_API_KEY=your-together-api-key
OPENAI_BASE_URL=https://api.together.xyz/v1
OPENAI_MODEL=meta-llama/Llama-3-70b-chat-hf
AI_PROVIDER=openai
```

### Groq

```bash
OPENAI_API_KEY=your-groq-api-key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.1-70b-versatile
AI_PROVIDER=openai
```

### vLLM (Self-Hosted)

```bash
OPENAI_API_KEY=token-abc123
OPENAI_BASE_URL=http://your-server:8000/v1
OPENAI_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
AI_PROVIDER=openai
```

### LocalAI

```bash
OPENAI_API_KEY=local
OPENAI_BASE_URL=http://localhost:8080/v1
OPENAI_MODEL=llama-3.1-8b-instruct
AI_PROVIDER=openai
```

---

## Troubleshooting

### Connection Refused Error

**Problem:** Can't connect to the API endpoint

**Solutions:**
1. Verify the server is running:
   - LM Studio: Check "Local Server" tab shows "Running"
   - Ollama: Run `ollama list` to verify it's running
2. Check the URL in `.env` matches the server:
   - LM Studio: `http://localhost:1234/v1`
   - Ollama: `http://localhost:11434/v1`
3. Try accessing the API directly:
   ```bash
   curl http://localhost:1234/v1/models
   ```

### Model Not Found Error

**Problem:** API can't find the specified model

**Solutions:**
1. Verify model is loaded:
   - LM Studio: Check the model is selected in "Local Server" tab
   - Ollama: Run `ollama list` to see available models
2. Match the model name exactly:
   - LM Studio: Use the name shown in the dropdown
   - Ollama: Use exact name from `ollama list`
3. Reload the model

### Slow Performance

**Problem:** Generating playbooks takes too long

**Solutions:**
1. Use a smaller model (7B-8B instead of 70B+)
2. Enable GPU acceleration:
   - LM Studio: Set "GPU Offload" to maximum
   - Ollama: Automatically uses GPU if available
3. Reduce context length if needed
4. Ensure sufficient RAM/VRAM:
   - 8B models: ~8GB RAM minimum
   - 70B models: ~40GB RAM or 40GB VRAM

### Out of Memory Error

**Problem:** System runs out of memory

**Solutions:**
1. Use a quantized model (Q4, Q5 versions)
2. Switch to a smaller model
3. Reduce GPU layers (LM Studio)
4. Close other applications
5. Use cloud API instead of local

### API Key Invalid Error

**Problem:** API rejects the key

**Solutions:**
1. For local servers, use any non-empty string:
   ```bash
   OPENAI_API_KEY=local
   ```
2. For cloud providers, verify your API key is correct
3. Check for extra spaces in `.env` file
4. Regenerate API key from provider

### Response Format Errors

**Problem:** Model returns unexpected format

**Solutions:**
1. Use instruction-tuned models (e.g., `-instruct` versions)
2. Verify model supports chat/completion format
3. Try a different model known to work well
4. Check model temperature/parameters in server settings

---

## Model Recommendations

### For Best Quality
- **Llama 3.1 70B Instruct** - Excellent contract analysis
- **Qwen 2.5 72B Instruct** - Great for complex legal text
- **GPT-4** (OpenAI) - Premium cloud option

**Requirements:** 40GB+ VRAM or 80GB+ RAM

### For Good Balance (Recommended)
- **Llama 3.1 8B Instruct** - Fast and capable
- **Qwen 2.5 14B Instruct** - Better quality, still fast
- **Mistral 7B Instruct** - Very efficient

**Requirements:** 8-16GB VRAM or 16-32GB RAM

### For Speed (Lower Quality)
- **Llama 3.2 3B Instruct** - Fastest option
- **Phi-3 Mini** - Compact and efficient

**Requirements:** 4-8GB RAM

### Model Features to Look For
- ✅ Instruction-tuned (has "instruct" or "chat" in name)
- ✅ Long context support (8K+ tokens)
- ✅ Good at structured output (JSON, analysis)
- ✅ Quantized versions available (Q4, Q5, Q8)

### Model Features to Avoid
- ❌ Base models (not instruction-tuned)
- ❌ Short context only (<4K tokens)
- ❌ Code-only or specialized models
- ❌ Very small models (<3B parameters)

---

## Performance Expectations

### Processing Time (Typical Contract)

| Model Size | Hardware | Time Range |
|------------|----------|------------|
| 7-8B | GPU | 3-8 minutes |
| 7-8B | CPU only | 15-30 minutes |
| 13-14B | GPU | 5-12 minutes |
| 13-14B | CPU only | 30-60 minutes |
| 70B+ | GPU | 10-20 minutes |
| 70B+ | CPU only | 60+ minutes |
| Cloud API | N/A | 2-5 minutes |

### Quality Comparison

- **Claude Sonnet** (Cloud): ⭐⭐⭐⭐⭐ - Excellent, comprehensive analysis
- **GPT-4** (Cloud): ⭐⭐⭐⭐⭐ - Excellent, detailed insights
- **Llama 3.1 70B**: ⭐⭐⭐⭐ - Very good, may miss some nuances
- **Qwen 2.5 14B**: ⭐⭐⭐⭐ - Good, reliable analysis
- **Llama 3.1 8B**: ⭐⭐⭐ - Decent, may be less thorough
- **Mistral 7B**: ⭐⭐⭐ - Good for simple contracts
- **Smaller models**: ⭐⭐ - Basic analysis only

---

## Getting Help

If you encounter issues:

1. Check the terminal output for error messages
2. Verify server is running and accessible
3. Test API connection with curl
4. Review this troubleshooting guide
5. Open an issue on [GitHub](https://github.com/Tucuxi-Inc/ContractPlaybookBuilder/issues)

---

## Additional Resources

- [LM Studio Documentation](https://lmstudio.ai/docs)
- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [vLLM Documentation](https://docs.vllm.ai/)
- [HuggingFace Model Hub](https://huggingface.co/models)