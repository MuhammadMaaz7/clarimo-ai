# Quick Start: HuggingFace Local LLM Fallback

## 🚀 3-Step Setup

### Step 1: Install Packages (2 minutes)
```bash
cd Backend
pip install transformers>=4.35.0 accelerate>=0.25.0 bitsandbytes>=0.41.0
```

Or run the installer:
```bash
install_hf_fallback.bat
```

### Step 2: Configure Model (30 seconds)
Edit `Backend/.env`:
```env
HF_MODEL=microsoft/phi-2
```

### Step 3: Test (First run: 2-3 minutes for download, then 30-40 seconds per validation)
```bash
# Comment out API keys in .env to test fallback
python run.py
```

## ✅ That's It!

The system will now:
1. Try OpenRouter API (if key available)
2. Try Groq API (if key available)
3. Fall back to local Phi-2 model (always works)

## 📊 What to Expect

### First Run
- Downloads Phi-2 model (~5.5GB) - **one-time only**
- Takes 2-3 minutes
- Model cached for future use

### Subsequent Runs
- Model loads in 10-15 seconds
- Each metric takes 5-10 seconds
- Total validation: 20-40 seconds

### With API Keys (Recommended)
- Each metric takes 1-3 seconds
- Total validation: 4-12 seconds
- Much faster!

## 🎯 Recommended Setup

**For Development:**
```env
# Use local model for testing
HF_MODEL=microsoft/phi-2
# Comment out API keys
```

**For Production:**
```env
# Use API keys as primary
OPENROUTER_API_KEY=your-key-here
GROQ_API_KEY=your-key-here
# Keep local model as fallback
HF_MODEL=microsoft/phi-2
```

## 🔧 Alternative Models

If Phi-2 is too slow or uses too much VRAM:

```env
# Lighter, faster, but less reliable
HF_MODEL=google/flan-t5-large
```

## 📝 Notes

- **First validation**: Slow (model download)
- **Subsequent validations**: Much faster (cached model)
- **API keys**: 5-10x faster than local model
- **Offline mode**: Works without internet (after first download)

## 🆘 Troubleshooting

**Out of memory?**
```env
HF_MODEL=google/flan-t5-large
```

**Still errors?**
- Check logs for details
- Try with API keys
- See `HUGGINGFACE_SETUP.md` for full guide

## 🎉 Done!

Your system now has a reliable local LLM fallback that works on your GTX 1050Ti!
