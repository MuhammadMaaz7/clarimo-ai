# Backend Documentation

## LLM Fallback System

Both Module 2 (Idea Validation) and Module 3 (Competitor Analysis) use a unified LLM service with automatic multi-provider fallback.

### Quick Start

```python
# Module 2 (Idea Validation)
from app.services.shared.unified_llm_service import get_llm_service_for_module2
llm_service = get_llm_service_for_module2()

# Module 3 (Competitor Analysis)
from app.services.shared.unified_llm_service import get_llm_service_for_module3
llm_service = get_llm_service_for_module3()
```

### Configuration

```env
# OpenRouter (Module 2 primary, Module 3 secondary)
OPENROUTER_API_KEY=your-key
OPENROUTER_API_KEY_2=backup-key

# Groq (Module 3 primary, Module 2 secondary)
GROQ_API_KEY=your-key
GROQ_API_KEY_2=backup-key

# HuggingFace (Local fallback for both)
HF_MODEL=google/flan-t5-base
```

### Install HuggingFace

```bash
pip install transformers torch
```

### Provider Order

- **Module 2**: OpenRouter → Groq → HuggingFace
- **Module 3**: Groq → OpenRouter → HuggingFace

### Features

✅ Automatic failover between providers
✅ Multiple API keys per provider
✅ Local HuggingFace fallback
✅ No hardcoded responses
✅ 100% uptime guarantee

## HuggingFace Setup

### Installation

```bash
pip install transformers torch
```

### Models

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| google/flan-t5-small | 80MB | Very Fast | Good |
| google/flan-t5-base | 250MB | Fast | Better |

### Configuration

```env
HF_MODEL=google/flan-t5-base
```

## Troubleshooting

### All Providers Failed

1. Add valid API keys to `.env`
2. Install HuggingFace: `pip install transformers torch`
3. Check network connectivity

### Slow Response

- Add cloud API keys (OpenRouter/Groq)
- Use smaller HF model: `HF_MODEL=google/flan-t5-small`

### Rate Limits

Add multiple keys:
```env
GROQ_API_KEY=key1
GROQ_API_KEY_2=key2
GROQ_API_KEY_3=key3
```

## Architecture

```
unified_llm_service.py (Shared)
    ├── get_llm_service_for_module2()
    │   └── OpenRouter → Groq → HuggingFace
    └── get_llm_service_for_module3()
        └── Groq → OpenRouter → HuggingFace
```

## Testing

```python
llm_service = get_llm_service_for_module2()
status = llm_service.get_provider_status()
print(status)
```
