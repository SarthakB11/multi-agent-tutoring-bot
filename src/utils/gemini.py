"""
Utilities for interacting with the Google Gemini API.
"""
import logging
import time
from typing import Dict, Any, Optional, List, Tuple

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from src.config import settings
from src.utils.errors import GeminiAPIError
from src.utils.logging import get_logger, log_gemini_request, log_gemini_response

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiClient:
    """Client for interacting with the Google Gemini API."""
    
    def __init__(
        self, 
        model: str = settings.GEMINI_MODEL,
        temperature: float = settings.GEMINI_TEMPERATURE,
        max_tokens: int = settings.GEMINI_MAX_TOKENS,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """
        Initialize the Gemini client.
        
        Args:
            model: The Gemini model to use.
            temperature: The temperature for text generation.
            max_tokens: The maximum number of tokens to generate.
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.request_id = request_id
        self.trace_id = trace_id
        
        # Set up logging
        log_context = {}
        if request_id:
            log_context["request_id"] = request_id
        if trace_id:
            log_context["trace_id"] = trace_id
            
        self.logger = get_logger("gemini_client", log_context)
        
        # Initialize the model
        try:
            self.genai_model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    top_p=0.95,
                    top_k=40,
                )
            )
            self.logger.info(f"Initialized Gemini model: {self.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise GeminiAPIError(
                message=f"Failed to initialize Gemini model: {str(e)}",
                trace_id=self.trace_id
            )
    
    async def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0
    ) -> str:
        """
        Generate text using the Gemini API.
        
        Args:
            prompt: The prompt to send to the model.
            system_instruction: Optional system instruction for the model.
            retry_count: Number of retries for transient errors.
            retry_delay: Delay between retries in seconds.
            
        Returns:
            The generated text.
            
        Raises:
            GeminiAPIError: If there is an error communicating with the Gemini API.
        """
        log_gemini_request(self.logger, prompt)
        
        # Prepare the chat
        chat = self.genai_model.start_chat(
            history=[],
            system_instruction=system_instruction
        )
        
        # Try to generate text with retries for transient errors
        for attempt in range(retry_count + 1):
            try:
                response = await chat.send_message_async(prompt)
                text = response.text
                log_gemini_response(self.logger, len(text))
                return text
            except Exception as e:
                self.logger.warning(f"Gemini API error (attempt {attempt+1}/{retry_count+1}): {str(e)}")
                
                # If this was the last attempt, raise the error
                if attempt == retry_count:
                    self.logger.error(f"Failed to generate text after {retry_count+1} attempts")
                    raise GeminiAPIError(
                        message=f"Failed to generate text: {str(e)}",
                        trace_id=self.trace_id
                    )
                
                # Otherwise, wait and retry
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
    
    async def analyze_query_intent(
        self, 
        query: str,
        available_agents: List[str] = ["MathAgent", "PhysicsAgent"]
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Analyze the intent of a user query to determine the appropriate agent.
        
        Args:
            query: The user query to analyze.
            available_agents: List of available agent names.
            
        Returns:
            A tuple containing:
            - The name of the most appropriate agent
            - The confidence score for that agent
            - A dictionary of confidence scores for all agents
            
        Raises:
            GeminiAPIError: If there is an error communicating with the Gemini API.
        """
        system_instruction = """
        You are an expert query classifier for an educational tutoring system.
        Your task is to analyze the user's query and determine which specialized agent would be best suited to handle it.
        You must assign confidence scores to each available agent based on how well the query matches their domain expertise.
        """
        
        prompt = f"""
        Analyze the following query and determine which specialized agent would be best suited to handle it.
        
        Query: "{query}"
        
        Available agents:
        - MathAgent: Handles mathematical questions, calculations, algebra, calculus, geometry, etc.
        - PhysicsAgent: Handles physics questions, physical laws, mechanics, thermodynamics, electromagnetism, etc.
        
        For each agent, assign a confidence score between 0.0 and 1.0 that represents how well the query matches their domain expertise.
        The sum of all confidence scores should not exceed 1.0.
        
        Provide your analysis in the following JSON format:
        {{
            "best_agent": "AgentName",
            "confidence": 0.X,
            "reasoning": "Brief explanation of your decision",
            "scores": {{
                "MathAgent": 0.X,
                "PhysicsAgent": 0.X
            }}
        }}
        
        Only respond with the JSON object, no other text.
        """
        
        try:
            response_text = await self.generate_text(prompt, system_instruction)
            
            # Extract JSON from response
            import json
            import re
            
            # Find JSON object in the response
            json_match = re.search(r'({.*})', response_text.replace('\n', ''), re.DOTALL)
            if not json_match:
                raise ValueError("Failed to extract JSON from Gemini response")
            
            json_str = json_match.group(1)
            analysis = json.loads(json_str)
            
            best_agent = analysis.get("best_agent")
            confidence = analysis.get("confidence", 0.0)
            scores = analysis.get("scores", {})
            
            if not best_agent or best_agent not in available_agents:
                raise ValueError(f"Invalid agent name: {best_agent}")
            
            self.logger.info(f"Query intent analysis: best_agent={best_agent}, confidence={confidence:.2f}")
            return best_agent, confidence, scores
            
        except Exception as e:
            self.logger.error(f"Failed to analyze query intent: {str(e)}")
            raise GeminiAPIError(
                message=f"Failed to analyze query intent: {str(e)}",
                trace_id=self.trace_id
            )
