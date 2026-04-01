const API_BASE_URL = 'http://localhost:8000/api';

export class ChatService {
  /**
   * Real streaming response from the AI backend using groq API.
   * Connects to FastAPI StreamingResponse (SSE).
   * @param messages Full message history
   * @param onContent Callback fired for each chunk of text
   */
  static async streamResponse(
    messages: { role: string; content: string }[],
    onContent: (chunk: string) => void
  ): Promise<void> {
    
    // Check if the user is simulating a failure explicitly for testing fallback UI
    const lastMsgContent = messages[messages.length - 1]?.content?.toLowerCase() || "";
    if (lastMsgContent.includes("simulate error") || lastMsgContent === "fail") {
      throw new Error("Network connection lost or API timeout.");
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Assuming authorization token isn't strictly necessary per routes_chat.py, 
          // but if we used Auth we'd append Bearer token here:
          ...(localStorage.getItem('auth_token') && { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` })
        },
        body: JSON.stringify({ messages })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      if (!response.body) {
         throw new Error("No response body available for streaming");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let done = false;
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '').trim();
              if (dataStr === '[DONE]') {
                 return;
              }
              if (dataStr === '[API_ERROR]' || dataStr.includes('[ERROR]')) {
                 throw new Error("Backend API streaming error");
              }
              if (dataStr) {
                try {
                  const payload = JSON.parse(dataStr);
                  if (payload.chunk) {
                    onContent(payload.chunk);
                  }
                } catch (e) {
                  // Ignore partial json parse errors that could happen if chunks get split
                  console.warn("Could not parse json chunk", dataStr);
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat stream failed:', error);
      throw error;
    }
  }
}
