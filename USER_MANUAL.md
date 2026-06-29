# User Manual
# LM Studio Clone - AI Model Serving Platform

**Version:** 1.0.0  
**Last Updated:** December 2025  
**For:** End Users and Administrators

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Dashboard Overview](#3-dashboard-overview)
4. [Managing Models](#4-managing-models)
5. [Using the Chat Interface](#5-using-the-chat-interface)
6. [Advanced Features](#6-advanced-features)
7. [API Keys & Security](#7-api-keys--security)
8. [System Monitoring](#8-system-monitoring)
9. [Troubleshooting](#9-troubleshooting)
10. [FAQs](#10-faqs)

---

## 1. Introduction

### 1.1 What is LM Studio Clone?

LM Studio Clone is a powerful, self-hosted AI model serving platform that allows you to run Large Language Models (LLMs) locally on your own hardware. This gives you:

- **Privacy:** Your data never leaves your machine
- **Cost Savings:** No recurring cloud API fees
- **Control:** Full control over your AI infrastructure
- **Flexibility:** Support for multiple model formats and sizes

### 1.2 Key Features

- **Multi-Format Support:** Works with GGUF, SafeTensors, GPTQ, AWQ, EXL2, and ONNX models
- **Chat Interface:** Interactive conversations with AI models
- **Model Management:** Easy download, registration, and management of models
- **RAG (Retrieval-Augmented Generation):** Enhance responses with your own documents
- **Function Calling:** Models can execute functions like calculations
- **Batch Processing:** Process multiple prompts efficiently
- **System Monitoring:** Real-time resource usage tracking
- **OpenAI-Compatible API:** Use with existing OpenAI-based applications

### 1.3 Who Should Use This Manual?

This manual is designed for:
- **End Users:** People who want to chat with AI models and use the web interface
- **Administrators:** Users who manage models, API keys, and system settings
- **Developers:** Those integrating the platform via API

---

## 2. Getting Started

### 2.1 Accessing the Platform

1. **Start the Backend Server:**
   - The backend should be running on `http://localhost:8078`
   - If not running, start it using the provided startup script or command

2. **Open the Web Interface:**
   - Navigate to `http://localhost:3032` in your web browser
   - You should see the login or dashboard page

3. **First-Time Setup:**
   - If this is your first time, you may need to create an API key (see Section 7)

### 2.2 System Requirements

**Minimum (CPU-Only):**
- 4 CPU cores, 2.5 GHz+
- 8 GB RAM
- 20 GB free storage
- Suitable for small models (< 3B parameters)

**Recommended (GPU-Accelerated):**
- 8+ CPU cores
- 16-32 GB RAM
- NVIDIA GPU with 12GB+ VRAM (RTX 3060 or better)
- 100 GB+ SSD storage
- Suitable for models up to 13B parameters

**Enterprise:**
- 16+ CPU cores
- 64 GB+ RAM
- NVIDIA A100 (40GB+) or RTX 4090 (24GB)
- 500 GB+ NVMe SSD
- Suitable for large models (up to 70B parameters)

### 2.3 Browser Compatibility

The platform works best with:
- **Chrome** 90+ (Recommended)
- **Firefox** 88+
- **Edge** 90+
- **Safari** 14+

---

## 3. Dashboard Overview

### 3.1 Main Dashboard

When you first log in, you'll see the **Dashboard** page with:

- **System Status:** CPU, RAM, and GPU usage
- **Quick Actions:** Shortcuts to common tasks
- **Recent Activity:** Your latest model loads and chat sessions
- **Model Statistics:** Number of registered models, loaded models, etc.

### 3.2 Navigation

The left sidebar provides access to all features:

- **Dashboard** - Overview and quick actions
- **Models** - Manage your AI models
- **Chat** - Basic chat interface
- **Enhanced Chat** - Advanced chat with more features
- **HuggingFace** - Browse and download models
- **Downloads** - Monitor download progress
- **Function Tester** - Test function calling
- **RAG Manager** - Manage document collections
- **Batch Processor** - Process multiple prompts
- **API Keys** - Manage API access keys
- **Monitoring** - System metrics and performance
- **Settings** - Application settings
- **Admin Dashboard** - Administrative tools (if available)

---

## 4. Managing Models

### 4.1 Viewing Your Models

1. Navigate to **Models** from the sidebar
2. You'll see a list of all registered models with:
   - Model name
   - Format (GGUF, SafeTensors, etc.)
   - Size
   - Parameters (e.g., 7B, 13B)
   - Status (Loaded/Not Loaded)
   - Actions (Load, Unload, Delete)

### 4.2 Registering a Local Model

If you have a model file on your computer:

1. Click **"Register Model"** or **"Add Model"** button
2. Enter the model details:
   - **Name:** A descriptive name (e.g., "Llama-2-7B-Chat")
   - **Path:** Full path to the model file
   - **Format:** Select the format (GGUF, SafeTensors, etc.)
   - **Parameters:** Model size (e.g., "7B", "13B")
   - **Quantization:** If applicable (e.g., "Q4_K_M")
3. Click **"Register"**
4. The model will appear in your models list

### 4.3 Downloading Models from HuggingFace

1. Navigate to **HuggingFace** from the sidebar
2. **Search for Models:**
   - Enter keywords in the search box (e.g., "llama", "mistral")
   - Filter by task, library, or language
   - Browse popular models
3. **Select a Model:**
   - Click on a model to view details
   - Check model size and requirements
4. **Download:**
   - Click **"Download"** button
   - Select the specific file if multiple options are available
   - The download will appear in the **Downloads** page
5. **Monitor Progress:**
   - Go to **Downloads** to see download status
   - Large models may take 30 minutes to several hours
6. **After Download:**
   - The model will be automatically registered
   - You can find it in the **Models** page

### 4.4 Loading a Model

Before you can use a model for chat or inference, you need to load it into memory:

1. Go to **Models** page
2. Find the model you want to use
3. Click **"Load"** button
4. Configure loading options (if prompted):
   - **Context Length:** How many tokens the model can remember (default: 2048)
   - **GPU Layers:** Number of layers to offload to GPU (0 = CPU only)
5. Wait for loading to complete (may take 1-5 minutes depending on model size)
6. The status will change to **"Loaded"**

**Note:** Loading a model consumes RAM/VRAM. Make sure you have enough memory before loading large models.

### 4.5 Unloading a Model

To free up memory:

1. Go to **Models** page
2. Find the loaded model
3. Click **"Unload"** button
4. The model will be removed from memory but remain registered

### 4.6 Deleting a Model

To permanently remove a model:

1. Go to **Models** page
2. Find the model you want to delete
3. Click **"Delete"** button
4. Confirm the deletion
5. **Warning:** This will delete the model file from your system!

---

## 5. Using the Chat Interface

### 5.1 Basic Chat

1. Navigate to **Chat** from the sidebar
2. **Create a New Session:**
   - Click **"New Session"** or **"+"** button
   - Select a loaded model
   - Enter a session name (e.g., "Python Help")
   - Optionally set a system prompt
   - Click **"Create"**
3. **Start Chatting:**
   - Type your message in the input box
   - Press **Enter** or click **"Send"**
   - The model will generate a response (streaming in real-time)
4. **Continue Conversation:**
   - The model remembers previous messages in the session
   - You can have multi-turn conversations
5. **Switch Sessions:**
   - Use the sidebar to switch between different chat sessions
   - Each session maintains its own conversation history

### 5.2 Enhanced Chat Features

The **Enhanced Chat** page offers additional features:

- **Model Presets:** Pre-configured settings for different use cases
- **Temperature Control:** Adjust creativity (0.0 = focused, 1.0 = creative)
- **Max Tokens:** Limit response length
- **Top P / Top K:** Advanced generation parameters
- **System Prompt:** Customize the model's behavior
- **Export Conversations:** Save chats as JSON or Markdown
- **Regenerate Response:** Get a new response to the same prompt

### 5.3 Chat Tips

- **Be Specific:** Clear, specific prompts get better results
- **Use System Prompts:** Guide the model's behavior (e.g., "You are a helpful Python tutor")
- **Adjust Temperature:** Lower (0.3-0.5) for factual tasks, higher (0.7-0.9) for creative writing
- **Manage Context:** Very long conversations may exceed context limits
- **Save Important Sessions:** Export conversations you want to keep

---

## 6. Advanced Features

### 6.1 RAG (Retrieval-Augmented Generation)

RAG allows you to enhance model responses with information from your own documents.

**Creating a RAG Collection:**

1. Navigate to **RAG Manager**
2. Click **"Create Collection"**
3. Enter a collection name (e.g., "Company Docs")
4. Select an embedding model (default: "all-MiniLM-L6-v2")
5. Click **"Create"**

**Adding Documents:**

1. Select your collection
2. Click **"Add Documents"**
3. Upload files (TXT, PDF, JSON supported) or paste text
4. Documents will be automatically chunked and embedded
5. Wait for processing to complete

**Using RAG in Chat:**

1. When creating a chat session, enable **"Use RAG"**
2. Select a collection
3. The model will automatically retrieve relevant context from your documents
4. Responses will be enhanced with information from your collection

**Querying Collections:**

1. In RAG Manager, select a collection
2. Enter a query in the search box
3. View retrieved documents and their relevance scores
4. Use this to test your collection before using it in chat

### 6.2 Function Calling

Function calling allows models to execute real functions (like calculations) during conversations.

**Available Functions:**

- **Calculator:** Perform mathematical operations
- **Get Current Time:** Retrieve current date and time
- **Web Search:** Search the web (mock implementation)

**Using Function Calling:**

1. Navigate to **Function Tester**
2. Select a function from the list
3. Enter parameters
4. Click **"Execute"** to test
5. In chat, the model will automatically use functions when appropriate

**Note:** Function calling requires models that support this feature. Not all models support function calling.

### 6.3 Batch Processing

Process multiple prompts efficiently:

1. Navigate to **Batch Processor**
2. Click **"Create Batch Job"**
3. Select a model
4. Enter multiple prompts (one per line or as a list)
5. Configure generation parameters
6. Click **"Submit"**
7. Monitor progress in the job list
8. Download results when complete (JSON or CSV format)

**Use Cases:**
- Dataset labeling
- Bulk content generation
- Model evaluation
- A/B testing

### 6.4 HuggingFace Integration

Browse and download from HuggingFace's model library:

1. Navigate to **HuggingFace**
2. **Search Models:**
   - Use the search bar to find models
   - Filter by task (text-generation, etc.)
   - Filter by library (transformers, etc.)
3. **Browse Popular Models:**
   - Click "Popular Models" to see trending models
4. **View Model Details:**
   - Click on any model to see:
     - Model description
     - File sizes
     - Download links
     - Usage examples
5. **Download:**
   - Click "Download" on the model or specific file
   - Monitor progress in **Downloads** page

### 6.5 Download Management

Monitor and manage model downloads:

1. Navigate to **Downloads**
2. View all active and completed downloads
3. **Download Status:**
   - **Pending:** Waiting to start
   - **Downloading:** In progress (with progress bar)
   - **Completed:** Successfully downloaded
   - **Failed:** Error occurred
4. **Actions:**
   - **Cancel:** Stop an active download
   - **Retry:** Restart a failed download
   - **Clear:** Remove completed downloads from the list

**Note:** Downloads support resume - if interrupted, you can resume from where it stopped.

---

## 7. API Keys & Security

### 7.1 Creating API Keys

To use the platform programmatically or integrate with other applications:

1. Navigate to **API Keys**
2. Click **"Create API Key"**
3. Enter a descriptive name (e.g., "My App Integration")
4. Set rate limit (requests per minute)
5. Optionally set an expiration date
6. Click **"Create"**
7. **Important:** Copy the API key immediately - it's only shown once!
8. Store it securely (password manager, environment variable, etc.)

### 7.2 Managing API Keys

- **View Keys:** See all your API keys with their status
- **Revoke:** Deactivate a key (click "Revoke")
- **Reactivate:** Re-enable a revoked key
- **Delete:** Permanently remove a key
- **Usage Stats:** View how many requests each key has made

### 7.3 Using API Keys

**In API Requests:**

Include the API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY_HERE
```

**Example with curl:**

```bash
curl -X GET "http://localhost:8078/api/models" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE"
```

**Example with Python:**

```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_KEY_HERE"
}

response = requests.get(
    "http://localhost:8078/api/models",
    headers=headers
)
```

### 7.4 Security Best Practices

- **Never share API keys:** Treat them like passwords
- **Use different keys:** Create separate keys for different applications
- **Set expiration dates:** For temporary integrations
- **Monitor usage:** Regularly check usage statistics
- **Revoke compromised keys:** If a key is exposed, revoke it immediately
- **Use HTTPS in production:** Always use encrypted connections

---

## 8. System Monitoring

### 8.1 Monitoring Dashboard

View real-time system metrics:

1. Navigate to **Monitoring**
2. View key metrics:
   - **CPU Usage:** Per-core and aggregate
   - **RAM Usage:** Used, available, percentage
   - **GPU Metrics:** Utilization, memory, temperature (if available)
   - **VRAM Usage:** GPU memory consumption
   - **Inference Performance:** Tokens per second, latency

### 8.2 Understanding Metrics

**CPU Usage:**
- Normal: 20-50% during inference
- High: >80% may indicate bottleneck
- Action: Consider GPU acceleration or smaller models

**RAM Usage:**
- Model loading: 4-16 GB per model (depending on size)
- High: >90% may cause slowdowns
- Action: Unload unused models

**GPU Usage:**
- Normal: 50-90% during inference
- Low: <30% may indicate CPU bottleneck
- High: >95% is optimal for throughput

**VRAM:**
- Each model consumes VRAM when loaded
- Check model requirements before loading
- Action: Unload models to free VRAM

### 8.3 Performance Optimization Tips

- **Use GPU:** Dramatically faster than CPU-only
- **Quantized Models:** Use Q4 or Q5 quantized models for better performance
- **Context Length:** Smaller context = faster inference
- **Batch Size:** Process multiple requests together when possible
- **Model Selection:** Smaller models are faster but less capable

---

## 9. Troubleshooting

### 9.1 Common Issues

#### Model Won't Load

**Symptoms:** Model stays in "Not Loaded" status or shows error

**Solutions:**
- Check available RAM/VRAM (see Monitoring page)
- Verify model file exists and is not corrupted
- Try unloading other models first
- Check model format compatibility
- Review error message in browser console

#### Slow Response Times

**Symptoms:** Chat responses take very long

**Solutions:**
- Check CPU/GPU usage in Monitoring
- Use GPU acceleration if available
- Reduce context length
- Use a smaller or quantized model
- Close other applications using GPU

#### Download Fails

**Symptoms:** Model download stops or shows error

**Solutions:**
- Check internet connection
- Verify sufficient disk space
- Try canceling and restarting download
- Check HuggingFace service status
- Try downloading a different file

#### Out of Memory Errors

**Symptoms:** "Out of memory" or "CUDA out of memory" errors

**Solutions:**
- Unload other loaded models
- Use a smaller model
- Use quantized models (Q4, Q5)
- Reduce context length
- Close other GPU applications
- Restart the backend server

#### API Key Not Working

**Symptoms:** API requests return 401 Unauthorized

**Solutions:**
- Verify API key is correct (no extra spaces)
- Check key is active (not revoked)
- Verify key hasn't expired
- Check Authorization header format: `Bearer YOUR_KEY`
- Create a new key if needed

### 9.2 Getting Help

**Check Logs:**
- Backend logs show detailed error messages
- Browser console (F12) shows frontend errors

**Common Error Messages:**

- **"Model not found":** Model file path is incorrect
- **"Engine not available":** Required engine library not installed
- **"Rate limit exceeded":** Too many requests, wait or increase limit
- **"Invalid format":** Model format not supported

**Reset Options:**
- Restart backend server
- Clear browser cache
- Reload the page (F5)

---

## 10. FAQs

### 10.1 General Questions

**Q: What models work best?**  
A: Popular choices include Llama 2, Mistral, Phi-2, and CodeLlama. Start with 7B parameter models for good balance of quality and speed.

**Q: Can I use this offline?**  
A: Yes! Once models are downloaded, the platform works completely offline. Only model downloads require internet.

**Q: How much storage do I need?**  
A: Models range from 2GB (small quantized) to 40GB+ (large unquantized). Plan for 50-100GB for a small collection.

**Q: Is my data private?**  
A: Yes! All processing happens locally. No data is sent to external servers (except HuggingFace for downloads).

**Q: Can multiple users use it?**  
A: Yes, via API keys. Each user can have their own keys with separate rate limits and usage tracking.

### 10.2 Technical Questions

**Q: What's the difference between model formats?**  
A:
- **GGUF:** Best for CPU, very efficient
- **SafeTensors:** Standard HuggingFace format, GPU-friendly
- **GPTQ/AWQ/EXL2:** Quantized formats, smaller and faster
- **ONNX:** Cross-platform, production-ready

**Q: Do I need a GPU?**  
A: No, but GPU is highly recommended. CPU-only works but is 10-50x slower.

**Q: Can I fine-tune models?**  
A: Fine-tuning is not included in this version. Use external tools and import the fine-tuned model.

**Q: How do I update the platform?**  
A: Pull latest code, update dependencies (`pip install -r requirements.txt`), and restart the server.

**Q: Can I use OpenAI's API with this?**  
A: Yes! The platform provides OpenAI-compatible endpoints. Point your OpenAI SDK to `http://localhost:8078/v1`.

### 10.3 Usage Questions

**Q: How do I get better responses?**  
A:
- Use better system prompts
- Adjust temperature (lower for facts, higher for creativity)
- Provide more context in your messages
- Use RAG with relevant documents

**Q: Can I save my chat history?**  
A: Yes! Use the export feature in Enhanced Chat to save as JSON or Markdown.

**Q: How many models can I load at once?**  
A: Depends on your RAM/VRAM. Typically 1-3 large models or 5-10 small models.

**Q: What's the difference between Chat and Enhanced Chat?**  
A: Enhanced Chat has more controls (temperature, presets, export) and advanced features.

**Q: Can I use this for production?**  
A: Yes, but ensure proper security (HTTPS, firewall, API key management) and monitoring.

---

## Appendix A: Keyboard Shortcuts

- **Ctrl/Cmd + K:** Quick search (if implemented)
- **Ctrl/Cmd + Enter:** Send message in chat
- **Esc:** Close dialogs/modals
- **F5:** Refresh page

---

## Appendix B: Model Recommendations

### For Beginners:
- **Phi-2** (2.7B) - Fast, good quality
- **Llama-2-7B-Chat** (GGUF Q4) - Balanced

### For Quality:
- **Mistral-7B-Instruct** - Excellent instruction following
- **Llama-2-13B-Chat** - More capable but slower

### For Speed:
- **Phi-2** (smallest)
- **TinyLlama-1.1B** (very fast, lower quality)

### For Code:
- **CodeLlama-7B-Instruct** - Specialized for coding
- **StarCoder** - Code generation

---

## Appendix C: Quick Reference

### Model Loading Checklist:
- [ ] Model file exists and is accessible
- [ ] Sufficient RAM/VRAM available
- [ ] Model format is supported
- [ ] Backend server is running

### Chat Best Practices:
- [ ] Model is loaded
- [ ] Session is created
- [ ] System prompt is set (optional)
- [ ] Temperature is appropriate for task

### API Integration Checklist:
- [ ] API key is created and copied
- [ ] Key is included in Authorization header
- [ ] Base URL is correct (`http://localhost:8078`)
- [ ] Model is loaded before making requests

---

## Support & Resources

- **API Documentation:** Available at `http://localhost:8078/docs` (Swagger UI)
- **Project Documentation:** See `PROJECT_DOCUMENTATION.md` for technical details
- **Error Logs:** Check backend console output for detailed errors

---

**End of User Manual**

*For technical implementation details, please refer to PROJECT_DOCUMENTATION.md*
