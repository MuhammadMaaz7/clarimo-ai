import json
from typing import Tuple, Optional
from app.services.shared.llm_service import UnifiedLLMService
from app.core.logging import logger

class RelevanceChecker:
    """
    Utility service to validate if user inputs are relevant to startup/product development.
    Rejects gibberish, non-business queries, or nonsensical text.
    """
    
    def __init__(self):
        # Use Groq for ultra-fast validation
        self.llm = UnifiedLLMService(provider_order=["groq", "openrouter"])
        self.temperature = 0.0 # Strict validation
        
    async def validate_relevance(self, input_text: str, context_type: str = "startup idea") -> Tuple[bool, str]:
        """
        Validates the input text.
        Returns: (is_relevant, error_message)
        """
        if not input_text or len(input_text.strip()) < 10:
            return False, "Input is too short to be a valid business description."
            
        prompt = f"""You are a startup validation bot. Your job is to detect if a given text is a legitimate description of a startup, product, business idea, or market problem.
        
        REJECT:
        - Random characters or single-word gibberish (e.g., 'asdfghj', 'cscaskjcs', 'asdf').
        - Non-business queries (e.g., 'what is the weather', 'tell me a joke', 'who is the president').
        - General information tasks (e.g., 'how to bake a cake', 'what is the capital of France').
        - Unrelated finance tasks (e.g., 'stock price of Apple', 'crypto news').
        - Personal requests or pure nonsense.
        
        ACCEPT:
        - Vague but legitimate business ideas (e.g., 'Uber for laundry').
        - Local physical businesses (e.g., 'Noodle shop in my street', 'Barber shop').
        - Hardware/IoT products (e.g., 'Smart collar for dogs').
        - Market problems (e.g., 'people struggle to find parking').
        - Technical product descriptions.
        
        INPUT TEXT: "{input_text}"
        CONTEXT: "{context_type}"
        
        Respond ONLY in the following JSON format:
        {{
            "is_relevant": true/false,
            "reason": "Clear explanation if rejected (e.g., 'This appears to be gibberish' or 'This is an unrelated general knowledge query'), or 'valid' if accepted"
        }}"""
        
        try:
            response = await self.llm.call_llm(
                prompt=prompt,
                response_format="json",
                temperature=self.temperature,
                max_tokens=150
            )
            result = json.loads(response)
            return result.get("is_relevant", True), result.get("reason", "Invalid input.")
        except Exception as e:
            logger.error(f"Relevance validation failed: {e}")
            # Fallback to true to avoid blocking users on API failure, 
            # but we could also do basic regex/length checks as a secondary fallback.
            return True, "Validation skipped."

relevance_checker = RelevanceChecker()
