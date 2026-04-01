/**
 * Simulated backend for AI Chatbot to demonstrate loading, streaming, and guardrails.
 */

const CLARIMO_RESPONSES = [
  "Clarimo AI accelerates your startup journey by offering real-time problem discovery, AI validation, and complete Go-to-Market strategies.",
  "Our platform is divided into core modules: Problem Discovery, AI Validation, Competitor Intelligence, and Go-to-Market Planner. Which one would you like to explore?",
  "With Clarimo AI, you can validate ideas at 10x speed compared to traditional market research methods.",
  "The Competitor Radar module helps you instantly dive deep into your competitors' offerings and feature gaps.",
  "Hello there! I'm the Clarimo AI assistant. I can guide you through our startup acceleration tools, modules, and validation systems. How can I assist you today?"
];

const OFF_TOPIC_REFUSAL = "I am an specialized assistant for Clarimo AI. I can only answer queries related to our startup acceleration tools, platform features, and entrepreneurial guidance. Please try asking about your startup idea or our platform modules!";

const isOffTopic = (message: string) => {
  const offTopicKeywords = ["capital", "sports", "python code", "weather", "recipe", "cook", "poem", "joke", "movie", "president", "buy", "sell"];
  return offTopicKeywords.some(keyword => message.toLowerCase().includes(keyword));
};

export class MockChatService {
  /**
   * Simulates a streaming response from the AI backend.
   * @param message User message
   * @param onContent Callback fired for each chunk of text
   */
  static async streamResponse(
    message: string,
    onContent: (chunk: string) => void
  ): Promise<void> {
    // 1) Simulate network connection / "Thinking" time
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Force an API failure demonstration
    if (message.toLowerCase().includes("fail") || message.toLowerCase().includes("error")) {
      throw new Error("Network connection lost or API timeout.");
    }

    let responseText = "";

    // 2) Guardrails logic
    if (isOffTopic(message)) {
      responseText = OFF_TOPIC_REFUSAL;
    } else if (message.toLowerCase().includes("modules") || message.toLowerCase().includes("features")) {
       responseText = CLARIMO_RESPONSES[1];
    } else if (message.toLowerCase().includes("hello") || message.toLowerCase().includes("hi")) {
       responseText = CLARIMO_RESPONSES[4];
    } else {
      // Pick a smart random response about Clarimo AI
      const idx = Math.floor(Math.random() * (CLARIMO_RESPONSES.length - 1));
      responseText = CLARIMO_RESPONSES[idx];
    }

    // 3) Streaming simulation
    const words = responseText.split(" ");
    for (let i = 0; i < words.length; i++) {
      // simulate realistic text generation speed (50-100ms per word)
      await new Promise((resolve) => setTimeout(resolve, Math.random() * 50 + 50));
      onContent(words[i] + (i === words.length - 1 ? "" : " "));
    }
  }
}
