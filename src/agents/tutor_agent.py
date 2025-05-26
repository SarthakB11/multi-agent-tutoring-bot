"""
Tutor Agent for the Multi-Agent AI Tutoring System.
"""
import asyncio
import re
from typing import Dict, Any, Optional, List, AsyncGenerator, Tuple

from src.utils.adk import BaseAgent
from src.models.adk import (
    InvocationContext,
    Event,
    DelegationEvent,
    ClarificationEvent,
    GeneralResponseEvent,
    ErrorEvent
)
from src.utils.gemini import GeminiClient
from src.config import settings
from src.utils.logging import log_agent_decision

class TutorAgent(BaseAgent):
    """
    Central orchestrating agent that receives user queries and delegates to specialized sub-agents.
    
    The Tutor Agent analyzes the query's content and intent to determine which specialized
    sub-agent is best suited to handle it, then delegates the query to that agent.
    """
    
    def __init__(self, request_id: Optional[str] = None, trace_id: Optional[str] = None):
        """
        Initialize the Tutor Agent.
        
        Args:
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        super().__init__("TutorAgent", request_id, trace_id)
        
        # Initialize Gemini client for intent analysis
        self.gemini_client = GeminiClient(
            request_id=request_id,
            trace_id=trace_id
        )
        
        # Define confidence thresholds
        self.high_confidence = settings.HIGH_CONFIDENCE_THRESHOLD
        self.default_confidence = settings.DEFAULT_CONFIDENCE_THRESHOLD
        self.low_confidence = settings.LOW_CONFIDENCE_THRESHOLD
        
        # Define available sub-agents
        self.available_agents = ["MathAgent", "PhysicsAgent"]
        
        # Define subject-specific keywords for pattern matching
        self.math_keywords = [
            "math", "mathematics", "algebra", "calculus", "geometry", "trigonometry",
            "equation", "solve", "simplify", "factor", "expand", "derivative", "integral",
            "function", "graph", "polynomial", "matrix", "vector", "logarithm", "exponent",
            "sin", "cos", "tan", "calculate", "computation", "arithmetic", "number",
            "theorem", "proof", "formula", "expression", "variable", "coefficient",
            "quadratic", "linear", "inequality", "fraction", "decimal", "percentage"
        ]
        
        self.physics_keywords = [
            "physics", "mechanics", "dynamics", "kinematics", "force", "energy", "momentum",
            "gravity", "acceleration", "velocity", "displacement", "motion", "newton",
            "thermodynamics", "heat", "temperature", "pressure", "volume", "gas",
            "electromagnetism", "electric", "magnetic", "field", "charge", "current",
            "voltage", "resistance", "circuit", "wave", "optics", "light", "reflection",
            "refraction", "quantum", "relativity", "nuclear", "atom", "particle",
            "conservation", "friction", "fluid", "density", "pressure", "oscillation"
        ]
    
    async def _analyze_query_intent(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Analyze the intent of a user query to determine the appropriate agent.
        
        Args:
            query: The user query to analyze.
            
        Returns:
            A tuple containing:
            - The name of the most appropriate agent
            - The confidence score for that agent
            - A dictionary of confidence scores for all agents
        """
        # First, try pattern matching for obvious subject indicators
        query_lower = query.lower()
        
        # Count occurrences of subject-specific keywords
        math_count = sum(1 for keyword in self.math_keywords if keyword in query_lower)
        physics_count = sum(1 for keyword in self.physics_keywords if keyword in query_lower)
        
        # If there's a clear winner based on keyword count, return it with high confidence
        if math_count > 0 and math_count > 2 * physics_count:
            confidence = min(0.7 + 0.1 * math_count, 0.95)  # Cap at 0.95
            self.logger.info(f"Pattern matching: MathAgent (confidence: {confidence:.2f})")
            return "MathAgent", confidence, {"MathAgent": confidence, "PhysicsAgent": 1 - confidence}
        
        if physics_count > 0 and physics_count > 2 * math_count:
            confidence = min(0.7 + 0.1 * physics_count, 0.95)  # Cap at 0.95
            self.logger.info(f"Pattern matching: PhysicsAgent (confidence: {confidence:.2f})")
            return "PhysicsAgent", confidence, {"PhysicsAgent": confidence, "MathAgent": 1 - confidence}
        
        # If pattern matching is inconclusive, use Gemini API for more sophisticated analysis
        self.logger.info("Pattern matching inconclusive, using Gemini API for intent analysis")
        return await self.gemini_client.analyze_query_intent(query, self.available_agents)
    
    async def run(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Run the Tutor Agent with the given context.
        
        Args:
            context: The invocation context.
            
        Yields:
            Events produced by the agent.
        """
        query = context.query
        request_id = context.request_id
        trace_id = context.trace_id
        
        self.logger.info(f"Processing query: {query}")
        
        # Validate the query
        if not query or not query.strip():
            self.logger.error("Empty query received")
            yield ErrorEvent(
                error_code="EMPTY_QUERY",
                error_message="Query cannot be empty",
                request_id=request_id,
                trace_id=trace_id
            )
            return
        
        try:
            # Analyze the query intent
            best_agent, confidence, scores = await self._analyze_query_intent(query)
            
            # Log the decision
            log_agent_decision(self.logger, self.name, f"Delegate to {best_agent}", confidence)
            
            # Apply confidence thresholds
            if confidence >= self.high_confidence:
                # High confidence: Direct delegation
                self.logger.info(f"High confidence delegation to {best_agent} ({confidence:.2f})")
                yield DelegationEvent(
                    target_agent=best_agent,
                    confidence=confidence,
                    context={"scores": scores},
                    request_id=request_id,
                    trace_id=trace_id
                )
            
            elif confidence >= self.default_confidence:
                # Medium confidence: Delegation with a note about potential ambiguity
                self.logger.info(f"Medium confidence delegation to {best_agent} ({confidence:.2f})")
                
                # Add a note about ambiguity to the context
                context = {
                    "scores": scores,
                    "ambiguity_note": f"This query has elements of multiple subjects. Confidence: {confidence:.2f}"
                }
                
                yield DelegationEvent(
                    target_agent=best_agent,
                    confidence=confidence,
                    context=context,
                    request_id=request_id,
                    trace_id=trace_id
                )
            
            elif confidence >= self.low_confidence:
                # Low confidence: Request clarification
                self.logger.info(f"Low confidence, requesting clarification ({confidence:.2f})")
                
                # Generate clarification message based on scores
                message = "I'm not sure which subject your question is about. Could you please clarify if you're asking about:"
                options = []
                
                for agent, score in scores.items():
                    if agent == "MathAgent":
                        options.append("Mathematics")
                    elif agent == "PhysicsAgent":
                        options.append("Physics")
                
                yield ClarificationEvent(
                    message=message,
                    options=options,
                    request_id=request_id,
                    trace_id=trace_id
                )
            
            else:
                # Very low confidence: Provide a general response
                self.logger.info(f"Very low confidence, providing general response ({confidence:.2f})")
                
                response = (
                    "I'm sorry, but I'm not able to determine which subject your question is about. "
                    "Currently, I can help with Mathematics and Physics questions. "
                    "Could you please rephrase your question to be more specific about the subject?"
                )
                
                yield GeneralResponseEvent(
                    response=response,
                    request_id=request_id,
                    trace_id=trace_id
                )
        
        except Exception as e:
            self.logger.error(f"Error in Tutor Agent: {str(e)}")
            yield ErrorEvent(
                error_code="TUTOR_AGENT_ERROR",
                error_message=f"Error in Tutor Agent: {str(e)}",
                request_id=request_id,
                trace_id=trace_id
            )
