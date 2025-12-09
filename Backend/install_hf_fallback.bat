@echo off
echo ========================================
echo HuggingFace Local LLM Setup
echo ========================================
echo.
echo This will install packages for local LLM fallback:
echo - transformers (HuggingFace models)
echo - accelerate (GPU acceleration)
echo - bitsandbytes (8-bit quantization)
echo.
echo Your hardware: i5 10th gen, GTX 1050Ti 4GB, 16GB RAM
echo Recommended model: microsoft/phi-2 (2.7B params)
echo.
pause

echo.
echo Installing packages...
pip install transformers>=4.35.0 accelerate>=0.25.0 bitsandbytes>=0.41.0

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit Backend/.env and set: HF_MODEL=microsoft/phi-2
echo 2. Comment out API keys to test fallback
echo 3. Run: python run.py
echo 4. First run will download ~5.5GB model (one-time)
echo.
echo See HUGGINGFACE_SETUP.md for detailed guide
echo.
pause
