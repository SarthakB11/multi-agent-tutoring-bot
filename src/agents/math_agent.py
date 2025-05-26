"""
Math Agent for the Multi-Agent AI Tutoring System.
"""
import asyncio
import re
from typing import Dict, Any, Optional, List, AsyncGenerator, Tuple

from src.utils.adk import BaseAgent
from src.models.adk import (
    InvocationContext,
    Event,
    ToolInvocationEvent,
    FinalResponseEvent,
    ErrorEvent
)
from src.utils.gemini import GeminiClient
from src.utils.logging import log_agent_decision

class MathAgent(BaseAgent):
    """
    Specialized agent for handling mathematical queries.
    
    The Math Agent can identify calculation needs in user queries and use the Calculator Tool
    to perform calculations. It then generates educational responses that explain the concepts
    and show step-by-step solutions.
    """
    
    def __init__(self, request_id: Optional[str] = None, trace_id: Optional[str] = None):
        """
        Initialize the Math Agent.
        
        Args:
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        super().__init__("MathAgent", request_id, trace_id)
        
        # Initialize Gemini client for response generation
        self.gemini_client = GeminiClient(
            request_id=request_id,
            trace_id=trace_id
        )
        
        # Define patterns for identifying calculation needs
        self.calculation_patterns = [
            r'\d+\s*[\+\-\*\/\^]\s*\d+',  # Basic arithmetic: 2 + 3, 5*6
            r'calculate\s+(.+)',  # Explicit calculation requests
            r'compute\s+(.+)',  # Explicit computation requests
            r'evaluate\s+(.+)',  # Explicit evaluation requests
            r'solve\s+(.+)',  # Solve requests
            r'simplify\s+(.+)',  # Simplify requests
            r'what\s+is\s+(.+)',  # What is questions
            r'find\s+the\s+value\s+of\s+(.+)',  # Find the value questions
            r'derivative\s+of\s+(.+)',  # Derivative questions
            r'integral\s+of\s+(.+)'  # Integral questions
        ]
    
    def _extract_calculation_expression(self, query: str) -> Optional[str]:
        """
        Extract a mathematical expression from a query.
        
        Args:
            query: The user query.
            
        Returns:
            The extracted expression, or None if no expression is found.
        """
        query_lower = query.lower()
        
        # Check for explicit calculation patterns
        for pattern in self.calculation_patterns:
            match = re.search(pattern, query_lower)
            if match:
                # If the pattern has a capture group, use it
                if match.groups():
                    return match.group(1).strip()
                # Otherwise, use the whole match
                return match.group(0).strip()
        
        # Check for standalone expressions
        # This is a simple heuristic and might need refinement
        if re.match(r'^[\d\s\+\-\*\/\^\(\)\.]+$', query.strip()):
            return query.strip()
        
        return None
    
    def _needs_calculation(self, query: str) -> bool:
        """
        Determine if a query needs calculation.
        
        Args:
            query: The user query.
            
        Returns:
            True if the query needs calculation, False otherwise.
        """
        return self._extract_calculation_expression(query) is not None
    
    def _format_calculation_for_tool(self, expression: str) -> str:
        """
        Format a calculation expression for the Calculator Tool.
        
        Args:
            expression: The expression to format.
            
        Returns:
            The formatted expression.
        """
        # Remove natural language elements
        expression = re.sub(r'calculate\s+', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'compute\s+', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'evaluate\s+', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'what\s+is\s+', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'find\s+the\s+value\s+of\s+', '', expression, flags=re.IGNORECASE)
        
        # Replace common words with symbols
        expression = re.sub(r'plus', '+', expression, flags=re.IGNORECASE)
        expression = re.sub(r'minus', '-', expression, flags=re.IGNORECASE)
        expression = re.sub(r'times', '*', expression, flags=re.IGNORECASE)
        expression = re.sub(r'multiplied\s+by', '*', expression, flags=re.IGNORECASE)
        expression = re.sub(r'divided\s+by', '/', expression, flags=re.IGNORECASE)
        expression = re.sub(r'squared', '^2', expression, flags=re.IGNORECASE)
        expression = re.sub(r'cubed', '^3', expression, flags=re.IGNORECASE)
        
        # Remove any remaining non-mathematical characters
        expression = re.sub(r'[^0-9\+\-\*\/\^\(\)\.\s]', '', expression)
        
        return expression.strip()
    
    async def _generate_response(
        self, 
        query: str, 
        calculation_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response to a mathematical query.
        
        Args:
            query: The user query.
            calculation_result: The result of a calculation, if any.
            
        Returns:
            The generated response.
        """
        system_instruction = """
        You are an expert math tutor. Your goal is to provide clear, educational responses to mathematical questions.
        Explain concepts thoroughly and show step-by-step solutions when appropriate.
        Use proper mathematical notation and provide context for your explanations.
        If calculation results are provided, incorporate them into your explanation and verify they are correct.
        """
        
        prompt = f"""
        Question: {query}
        
        """
        
        if calculation_result:
            prompt += f"""
            Calculation Result: {calculation_result.get('result')}
            
            Calculation Steps:
            {chr(10).join(calculation_result.get('steps', []))}
            
            Please provide a thorough explanation of this mathematical problem, incorporating the calculation result and steps.
            Verify the calculation is correct and explain the mathematical concepts involved.
            """
        else:
            prompt += """
            Please provide a thorough explanation of this mathematical concept or problem.
            If appropriate, show how to solve the problem step-by-step.
            """
        
        return await self.gemini_client.generate_text(prompt, system_instruction)
    
    async def run(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Run the Math Agent with the given context.
        
        Args:
            context: The invocation context.
            
        Yields:
            Events produced by the agent.
        """
        query = context.query
        request_id = context.request_id
        trace_id = context.trace_id
        
        self.logger.info(f"Processing math query: {query}")
        
        try:
            # Check if the query needs calculation
            if self._needs_calculation(query):
                self.logger.info("Query requires calculation")
                
                # Extract the calculation expression
                expression = self._extract_calculation_expression(query)
                formatted_expression = self._format_calculation_for_tool(expression)
                
                self.logger.info(f"Extracted expression: {formatted_expression}")
                
                # Invoke the Calculator Tool
                yield ToolInvocationEvent(
                    tool_name="CalculatorTool",
                    inputs={"expression": formatted_expression},
                    request_id=request_id,
                    trace_id=trace_id
                )
                
                # Wait for the tool result
                tool_result = yield
                
                if tool_result.event_type == "tool_result":
                    if tool_result.error:
                        self.logger.error(f"Calculator Tool error: {tool_result.error}")
                        
                        # Generate a response without calculation
                        response = await self._generate_response(query)
                        
                        yield FinalResponseEvent(
                            response=response,
                            agent_used=self.name,
                            request_id=request_id,
                            trace_id=trace_id
                        )
                    else:
                        self.logger.info(f"Calculator Tool result: {tool_result.result}")
                        
                        # Generate a response with the calculation result
                        response = await self._generate_response(query, tool_result.result)
                        
                        yield FinalResponseEvent(
                            response=response,
                            agent_used=self.name,
                            tool_used="CalculatorTool",
                            tool_results=tool_result.result,
                            request_id=request_id,
                            trace_id=trace_id
                        )
                else:
                    self.logger.error(f"Unexpected event type: {tool_result.event_type}")
                    
                    # Generate a response without calculation
                    response = await self._generate_response(query)
                    
                    yield FinalResponseEvent(
                        response=response,
                        agent_used=self.name,
                        request_id=request_id,
                        trace_id=trace_id
                    )
            else:
                self.logger.info("Query does not require calculation")
                
                # Generate a response without calculation
                response = await self._generate_response(query)
                
                yield FinalResponseEvent(
                    response=response,
                    agent_used=self.name,
                    request_id=request_id,
                    trace_id=trace_id
                )
        
        except Exception as e:
            self.logger.error(f"Error in Math Agent: {str(e)}")
            yield ErrorEvent(
                error_code="MATH_AGENT_ERROR",
                error_message=f"Error in Math Agent: {str(e)}",
                request_id=request_id,
                trace_id=trace_id
            )
