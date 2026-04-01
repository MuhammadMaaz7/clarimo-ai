import json
import os
import asyncio
import aiohttp
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

SYSTEM_PROMPT = """You are Clarimo AI, an advanced AI Assistant for the Clarimo Startup Accelerator.
Your goal is to provide elite, ultra-professional, and extremely concise guidance to startup founders.

**STRICT OPERATIONAL GUIDELINES:**
1. **BREVITY IS MANDATORY:** Keep individual responses under 3-4 short sentences or a very concise list. NEVER provide long paragraphs unless explicitly asked for a 'deep dive'. 
2. **FORMATTING:** Use clean Markdown. Use bolding for key terms. Use bullet points for steps. Avoid excessive noise.
3. **ONLY STARTUPS:** Only answer queries related to Clarimo AI modules (Problem Discovery, Idea Validation, Competitor Intelligence, GTM), startup building, or entrepreneurship.
4. **OFF-TOPIC REFUSAL:** If the prompt is off-topic (cooking, coding unrelated to business, sports, etc.), refuse with: 
"I am a specialized assistant for Clarimo AI. I can only assist with queries related to startup acceleration, business tools, and our platform. Please try asking about your business idea or our modules!"
5. **TONE:** High-tech, premium, encouraging, and razor-sharp intelligence.
"""

async def stream_groq(messages_input: list):
    """
    Stream chat response using Groq API
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        yield "data: [ERROR] Configuration error: GROQ_API_KEY is not set.\n\n"
        return

    # To rate limit safely inside the async generator (simple best practice anti-abuse delay logic not needed explicitly on API level for standard use unless highly scaled)
    # The application can be rate limited at the Nginx level, or using slowapi. We simply implement the streaming.

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant") # using standard fast Groq model
    api_url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Inject system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages_input:
        messages.append({"role": msg.role, "content": msg.content})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 1024,
        "stream": True
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=payload, timeout=30) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Groq API Error: {response.status} {error_text}")
                    yield "data: [API_ERROR]\n\n"
                    return

                async for line in response.content:
                    if line:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                json_data = json.loads(data)
                                chunk = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if chunk:
                                    # Output chunk using raw bytes or string (SSE format)
                                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                            except Exception as e:
                                pass
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        yield "data: [API_ERROR]\n\n"

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Standard SSE endpoint for the AI Chatbot streaming
    """
    # Rate limit mock: Can add real logic here if needed via redis rate-limiter
    return StreamingResponse(
        stream_groq(request.messages), 
        media_type="text/event-stream"
    )
