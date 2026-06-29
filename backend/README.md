# LM Studio Clone - Backend

FastAPI backend for LM Studio Clone with multi-engine support for various model formats.

## Features

- Multi-engine architecture (GGUF, SafeTensors, GPTQ, AWQ, EXL2, ONNX)
- SQLite database for model registry, chat sessions, and API keys
- Download queue with resume support
- OpenAI-compatible API
- Rate limiting and API key management
- Real-time monitoring
- Caching layer

## Installation

### Basic Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Install Inference Engines

Choose engines based on your needs:

#### GGUF (llama.cpp)
```bash
# CPU only
pip install llama-cpp-python

# With CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# With Metal support (Mac)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

#### SafeTensors/PyTorch
```bash
pip install transformers accelerate
```

#### GPTQ
```bash
pip install auto-gptq
```

#### AWQ
```bash
pip install autoawq
```

#### EXL2
```bash
pip install exllamav2
```

#### ONNX
```bash
pip install onnxruntime-gpu  # or onnxruntime for CPU
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings.

## Running

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8078

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8078 --workers 4
```

Or use the main script:

```bash
python -m app.main
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8078/docs
- ReDoc: http://localhost:8078/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── core/                # Core utilities
│   │   ├── config.py        # Settings
│   │   └── auth.py          # Authentication
│   ├── database/            # Database layer
│   │   ├── database.py      # DB connection
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   └── services/            # Business logic
│       └── inference/       # Inference engines
└── requirements.txt
```

## Database Schema

- **models**: Model registry
- **chat_sessions**: Chat sessions
- **chat_messages**: Chat messages
- **api_keys**: API key management
- **api_key_usage**: Usage tracking
- **usage_stats**: Model usage statistics
- **download_queue**: Download queue

## Next Steps

1. Implement Base Engine Interface
2. Implement GGUF Engine
3. Implement other engines
4. Add API endpoints
5. Add monitoring service

