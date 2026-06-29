# LM Studio Clone

یک کلون قدرتمند از LM Studio با پشتیبانی از چندین فرمت مدل و قابلیت‌های پیشرفته.

## ویژگی‌ها

### Backend
- ✅ **Multi-Engine Architecture**: پشتیبانی از GGUF, SafeTensors, GPTQ, AWQ, EXL2, ONNX
- ✅ **Model Management**: لود، آنلود و مدیریت مدل‌های متعدد همزمان
- ✅ **Streaming Inference**: تولید متن با streaming real-time
- ✅ **Download Queue**: دانلود همزمان چندین مدل با قابلیت Resume
- ✅ **OpenAI-Compatible API**: سازگار با API استاندارد OpenAI
- ✅ **API Key Management**: مدیریت کلیدها و Rate Limiting
- ✅ **Session Management**: ذخیره و بازیابی چت‌ها
- ✅ **Database Integration**: SQLite برای ذخیره‌سازی داده
- ✅ **GPU Support**: پشتیبانی از CUDA و Metal

### Frontend
- ✅ **Modern UI**: طراحی مدرن با TailwindCSS
- ✅ **Dark/Light Theme**: تم تیره و روشن
- ✅ **Model Browser**: مرور و مدیریت مدل‌ها
- ✅ **Chat Interface**: رابط چت با streaming
- ✅ **Real-time Updates**: به‌روزرسانی زنده
- ✅ **Responsive Design**: طراحی واکنش‌گرا

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.10+
- Node.js 18+
- (اختیاری) CUDA برای GPU support

### 1. Backend Setup

```bash
cd backend

# ایجاد محیط مجازی
python -m venv venv

# فعال‌سازی محیط مجازی
# در Windows:
venv\Scripts\activate
# در Linux/Mac:
source venv/bin/activate

# نصب بسته‌های اصلی
pip install -r requirements.txt

# نصب Engine مورد نظر (انتخابی)
# GGUF (با CPU)
pip install llama-cpp-python

# GGUF (با CUDA)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# SafeTensors/PyTorch
pip install transformers accelerate

# GPTQ
pip install auto-gptq

# AWQ
pip install autoawq

# EXL2
pip install exllamav2

# ONNX
pip install onnxruntime-gpu

# اجرای سرور
python -m app.main
```

Backend در `http://localhost:8078` در دسترس خواهد بود.

### 2. Frontend Setup

```bash
cd frontend

# نصب dependencies
npm install

# اجرا در حالت development
npm run dev
```

Frontend در `http://localhost:3032` در دسترس خواهد بود.

## استفاده

### 1. اضافه کردن مدل

#### از HuggingFace:
```bash
curl -X POST "http://localhost:8078/api/downloads" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://huggingface.co/model-path/model.gguf",
    "model_name": "My Model",
    "model_format": "GGUF"
  }'
```

#### مدل Local:
```bash
curl -X POST "http://localhost:8078/api/models" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Local Model",
    "path": "/path/to/model.gguf",
    "format": "GGUF",
    "source": "Local"
  }'
```

### 2. لود کردن مدل

```bash
curl -X POST "http://localhost:8078/api/models/1/load" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "gpu_layers": -1,
    "context_length": 2048
  }'
```

### 3. چت با مدل

#### ایجاد Session:
```bash
curl -X POST "http://localhost:8078/api/chat/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "name": "My Chat",
    "temperature": 0.7
  }'
```

#### ارسال پیام:
```bash
curl -X POST "http://localhost:8078/api/chat/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "message": "Hello!",
    "stream": true
  }'
```

### 4. استفاده از OpenAI-Compatible API

```python
import openai

openai.api_base = "http://localhost:8078/v1"
openai.api_key = "your-api-key"  # اگر فعال باشد

response = openai.ChatCompletion.create(
    model="My Model",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

## ساختار پروژه

```
modelServing/
├── backend/               # FastAPI Backend
│   ├── app/
│   │   ├── main.py       # Entry point
│   │   ├── api/          # API routes
│   │   ├── services/     # Business logic
│   │   ├── database/     # Database models
│   │   └── schemas/      # Pydantic schemas
│   └── requirements.txt
├── frontend/             # React Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
└── models/              # Downloaded models
```

## API Documentation

بعد از اجرای backend، مستندات API در آدرس‌های زیر در دسترس است:
- Swagger UI: `http://localhost:8078/docs`
- ReDoc: `http://localhost:8078/redoc`

## Endpoints اصلی

### Models
- `GET /api/models` - لیست مدل‌ها
- `POST /api/models` - ایجاد مدل
- `POST /api/models/{id}/load` - لود کردن مدل
- `POST /api/models/{id}/unload` - آنلود کردن مدل
- `DELETE /api/models/{id}` - حذف مدل

### Chat
- `POST /api/chat/sessions` - ایجاد session
- `GET /api/chat/sessions` - لیست session‌ها
- `POST /api/chat/generate` - تولید پاسخ

### Downloads
- `POST /api/downloads` - شروع دانلود
- `GET /api/downloads` - لیست دانلودها
- `POST /api/downloads/{id}/cancel` - لغو دانلود

### OpenAI-Compatible
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions
- `GET /v1/models` - لیست مدل‌ها

## تنظیمات

فایل `.env` را در پوشه `backend` ایجاد کنید:

```env
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Model Settings
MAX_CONCURRENT_MODELS=3
DEFAULT_GPU_LAYERS=0

# Download Settings
MAX_CONCURRENT_DOWNLOADS=3

# API Keys
API_KEY_ENABLED=False
SECRET_KEY=your-secret-key-here
```

## توسعه

### اضافه کردن Engine جدید

1. کلاس engine جدید را در `backend/app/services/inference/` بسازید:

```python
from app.services.inference.base_engine import InferenceEngine, EngineRegistry

@EngineRegistry.register
class MyEngine(InferenceEngine):
    @staticmethod
    def supports_format(format: str) -> bool:
        return format.upper() == "MYFORMAT"
    
    @staticmethod
    def get_engine_name() -> str:
        return "MyEngine"
    
    # Implement abstract methods...
```

2. Engine به صورت خودکار register می‌شود.

## مشارکت

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## تشکر

- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [HuggingFace Transformers](https://github.com/huggingface/transformers)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)

## پشتیبانی

برای گزارش مشکلات یا پیشنهادات، لطفاً یک Issue ایجاد کنید.

