"""
Physics Agent for the Multi-Agent AI Tutoring System.
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

class PhysicsAgent(BaseAgent):
    """
    Specialized agent for handling physics-related queries.
    
    The Physics Agent can identify references to physical constants or formulas in user queries
    and use the Lookup Tool to retrieve them. It can also use the Calculator Tool for physics
    calculations. It then generates educational responses that explain the concepts with
    real-world examples.
    """
    
    def __init__(self, request_id: Optional[str] = None, trace_id: Optional[str] = None):
        """
        Initialize the Physics Agent.
        
        Args:
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        super().__init__("PhysicsAgent", request_id, trace_id)
        
        # Initialize Gemini client for response generation
        self.gemini_client = GeminiClient(
            request_id=request_id,
            trace_id=trace_id
        )
        
        # Define patterns for identifying constant/formula needs
        self.constant_patterns = [
            r'value\s+of\s+([a-zA-Z0-9\s]+)',  # Value of X
            r'what\s+is\s+([a-zA-Z0-9\s]+)',  # What is X
            r'constant\s+([a-zA-Z0-9\s]+)',  # Constant X
            r'acceleration\s+due\s+to\s+gravity',  # g
            r'speed\s+of\s+light',  # c
            r'gravitational\s+constant',  # G
            r'planck\'s\s+constant',  # h
            r'elementary\s+charge',  # e
            r'electron\s+mass',  # me
            r'proton\s+mass',  # mp
            r'boltzmann\s+constant',  # k
            r'avogadro\'s\s+number',  # NA
            r'gas\s+constant'  # R
        ]
        
        self.formula_patterns = [
            r'formula\s+for\s+([a-zA-Z0-9\s]+)',  # Formula for X
            r'equation\s+for\s+([a-zA-Z0-9\s]+)',  # Equation for X
            r'newton\'s\s+second\s+law',  # F = ma
            r'kinetic\s+energy',  # KE = 0.5mv²
            r'potential\s+energy',  # PE = mgh
            r'momentum',  # p = mv
            r'uniform\s+acceleration',  # v = v₀ + at
            r'distance\s+with\s+acceleration',  # d = v₀t + 0.5at²
            r'work',  # W = Fd
            r'power',  # P = W/t
            r'ohm\'s\s+law',  # V = IR
            r'universal\s+gravitation'  # F = G(m₁m₂)/r²
        ]
        
        # Define patterns for identifying calculation needs
        self.calculation_patterns = [
            r'calculate\s+([a-zA-Z0-9\s]+)',  # Calculate X
            r'compute\s+([a-zA-Z0-9\s]+)',  # Compute X
            r'find\s+([a-zA-Z0-9\s]+)',  # Find X
            r'determine\s+([a-zA-Z0-9\s]+)',  # Determine X
            r'what\s+is\s+the\s+([a-zA-Z0-9\s]+)',  # What is the X
            r'\d+\s*[\+\-\*\/\^]\s*\d+'  # Basic arithmetic
        ]
    
    def _extract_constant_key(self, query: str) -> Optional[str]:
        """
        Extract a constant key from a query.
        
        Args:
            query: The user query.
            
        Returns:
            The extracted constant key, or None if no key is found.
        """
        query_lower = query.lower()
        
        # Check for specific constants
        if re.search(r'acceleration\s+due\s+to\s+gravity', query_lower):
            return "g"
        elif re.search(r'speed\s+of\s+light', query_lower):
            return "c"
        elif re.search(r'gravitational\s+constant', query_lower):
            return "G"
        elif re.search(r'planck\'s\s+constant', query_lower):
            return "h"
        elif re.search(r'elementary\s+charge', query_lower):
            return "e"
        elif re.search(r'electron\s+mass', query_lower):
            return "me"
        elif re.search(r'proton\s+mass', query_lower):
            return "mp"
        elif re.search(r'boltzmann\s+constant', query_lower):
            return "k"
        elif re.search(r'avogadro\'s\s+number', query_lower) or re.search(r'avogadro\s+constant', query_lower):
            return "NA"
        elif re.search(r'gas\s+constant', query_lower):
            return "R"
        
        # Check for general patterns
        for pattern in self.constant_patterns:
            match = re.search(pattern, query_lower)
            if match and match.groups():
                return match.group(1).strip()
        
        return None
    
    def _extract_formula_key(self, query: str) -> Optional[str]:
        """
        Extract a formula key from a query.
        
        Args:
            query: The user query.
            
        Returns:
            The extracted formula key, or None if no key is found.
        """
        query_lower = query.lower()
        
        # Check for specific formulas
        if re.search(r'newton\'s\s+second\s+law', query_lower):
            return "newton_second_law"
        elif re.search(r'kinetic\s+energy', query_lower):
            return "kinetic_energy"
        elif re.search(r'potential\s+energy', query_lower) or re.search(r'gravitational\s+potential\s+energy', query_lower):
            return "potential_energy_gravitational"
        elif re.search(r'momentum', query_lower):
            return "momentum"
        elif re.search(r'uniform\s+acceleration', query_lower) and not re.search(r'distance', query_lower):
            return "uniform_acceleration"
        elif re.search(r'distance\s+with\s+acceleration', query_lower) or re.search(r'distance\s+under\s+acceleration', query_lower):
            return "uniform_acceleration_distance"
        elif re.search(r'work', query_lower) and not re.search(r'power', query_lower):
            return "work"
        elif re.search(r'power', query_lower):
            return "power"
        elif re.search(r'ohm\'s\s+law', query_lower):
            return "ohms_law"
        elif re.search(r'universal\s+gravitation', query_lower) or re.search(r'gravitational\s+force', query_lower):
            return "universal_gravitation"
        
        # Check for general patterns
        for pattern in self.formula_patterns:
            match = re.search(pattern, query_lower)
            if match and match.groups():
                return match.group(1).strip()
        
        return None
    
    def _extract_calculation_expression(self, query: str) -> Optional[str]:
        """
        Extract a calculation expression from a query.
        
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
        if re.match(r'^[\d\s\+\-\*\/\^\(\)\.]+$', query.strip()):
            return query.strip()
        
        return None
    
    def _needs_constant_lookup(self, query: str) -> bool:
        """
        Determine if a query needs constant lookup.
        
        Args:
            query: The user query.
            
        Returns:
            True if the query needs constant lookup, False otherwise.
        """
        return self._extract_constant_key(query) is not None
    
    def _needs_formula_lookup(self, query: str) -> bool:
        """
        Determine if a query needs formula lookup.
        
        Args:
            query: The user query.
            
        Returns:
            True if the query needs formula lookup, False otherwise.
        """
        return self._extract_formula_key(query) is not None
    
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
        expression = re.sub(r'find\s+', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'determine\s+', '', expression, flags=re.IGNORECASE)
        expression = re.sub(r'what\s+is\s+the\s+', '', expression, flags=re.IGNORECASE)
        
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
        constant_result: Optional[Dict[str, Any]] = None,
        formula_result: Optional[Dict[str, Any]] = None,
        calculation_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response to a physics query.
        
        Args:
            query: The user query.
            constant_result: The result of a constant lookup, if any.
            formula_result: The result of a formula lookup, if any.
            calculation_result: The result of a calculation, if any.
            
        Returns:
            The generated response.
        """
        system_instruction = """
        You are an expert physics tutor. Your goal is to provide clear, educational responses to physics questions.
        Explain concepts thoroughly and show step-by-step solutions when appropriate.
        Use proper physics notation, include units, and provide real-world examples to illustrate concepts.
        If constants, formulas, or calculation results are provided, incorporate them into your explanation and verify they are correct.
        """
        
        prompt = f"""
        Question: {query}
        
        """
        
        if constant_result:
            prompt += f"""
            Constant Information:
            - Name: {constant_result.get('key')}
            - Value: {constant_result.get('value')} {constant_result.get('unit')}
            - Description: {constant_result.get('description')}
            
            """
        
        if formula_result:
            prompt += f"""
            Formula Information:
            - Name: {formula_result.get('key')}
            - Formula: {formula_result.get('formula')}
            - Description: {formula_result.get('description')}
            """
            
            if formula_result.get('variables'):
                prompt += """
                - Variables:
                """
                for var, desc in formula_result.get('variables', {}).items():
                    prompt += f"  * {var}: {desc}\n"
            
            prompt += "\n"
        
        if calculation_result:
            prompt += f"""
            Calculation Result: {calculation_result.get('result')}
            
            Calculation Steps:
            {chr(10).join(calculation_result.get('steps', []))}
            
            """
        
        prompt += """
        Please provide a thorough explanation of this physics concept or problem, incorporating any provided constants, formulas, or calculation results.
        Verify that any calculations are correct and explain the physical principles involved.
        Include real-world examples to illustrate the concepts and ensure proper units are used throughout.
        """
        
        return await self.gemini_client.generate_text(prompt, system_instruction)
    
    async def run(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Run the Physics Agent with the given context.
        
        Args:
            context: The invocation context.
            
        Yields:
            Events produced by the agent.
        """
        query = context.query
        request_id = context.request_id
        trace_id = context.trace_id
        
        self.logger.info(f"Processing physics query: {query}")
        
        try:
            constant_result = None
            formula_result = None
            calculation_result = None
            tools_used = []
            
            # Check if the query needs constant lookup
            if self._needs_constant_lookup(query):
                self.logger.info("Query requires constant lookup")
                
                # Extract the constant key
                constant_key = self._extract_constant_key(query)
                
                self.logger.info(f"Extracted constant key: {constant_key}")
                
                # Invoke the Lookup Tool for constant
                yield ToolInvocationEvent(
                    tool_name="LookupTool",
                    inputs={"key": constant_key, "type": "constant"},
                    request_id=request_id,
                    trace_id=trace_id
                )
                
                # Wait for the tool result
                tool_result = yield
                
                if tool_result.event_type == "tool_result":
                    if tool_result.error:
                        self.logger.error(f"Lookup Tool error: {tool_result.error}")
                    else:
                        self.logger.info(f"Lookup Tool result: {tool_result.result}")
                        constant_result = tool_result.result
                        tools_used.append(("LookupTool", tool_result.result))
                else:
                    self.logger.error(f"Unexpected event type: {tool_result.event_type}")
            
            # Check if the query needs formula lookup
            if self._needs_formula_lookup(query):
                self.logger.info("Query requires formula lookup")
                
                # Extract the formula key
                formula_key = self._extract_formula_key(query)
                
                self.logger.info(f"Extracted formula key: {formula_key}")
                
                # Invoke the Lookup Tool for formula
                yield ToolInvocationEvent(
                    tool_name="LookupTool",
                    inputs={"key": formula_key, "type": "formula"},
                    request_id=request_id,
                    trace_id=trace_id
                )
                
                # Wait for the tool result
                tool_result = yield
                
                if tool_result.event_type == "tool_result":
                    if tool_result.error:
                        self.logger.error(f"Lookup Tool error: {tool_result.error}")
                    else:
                        self.logger.info(f"Lookup Tool result: {tool_result.result}")
                        formula_result = tool_result.result
                        tools_used.append(("LookupTool", tool_result.result))
                else:
                    self.logger.error(f"Unexpected event type: {tool_result.event_type}")
            
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
                    else:
                        self.logger.info(f"Calculator Tool result: {tool_result.result}")
                        calculation_result = tool_result.result
                        tools_used.append(("CalculatorTool", tool_result.result))
                else:
                    self.logger.error(f"Unexpected event type: {tool_result.event_type}")
            
            # Generate the response
            response = await self._generate_response(
                query,
                constant_result,
                formula_result,
                calculation_result
            )
            
            # Determine which tools were used
            tool_used = None
            tool_results = None
            
            if len(tools_used) == 1:
                tool_used = tools_used[0][0]
                tool_results = tools_used[0][1]
            elif len(tools_used) > 1:
                # If multiple tools were used, combine their results
                tool_used = ", ".join(tool[0] for tool in tools_used)
                tool_results = {
                    "constant_result": constant_result,
                    "formula_result": formula_result,
                    "calculation_result": calculation_result
                }
            
            yield FinalResponseEvent(
                response=response,
                agent_used=self.name,
                tool_used=tool_used,
                tool_results=tool_results,
                request_id=request_id,
                trace_id=trace_id
            )
        
        except Exception as e:
            self.logger.error(f"Error in Physics Agent: {str(e)}")
            yield ErrorEvent(
                error_code="PHYSICS_AGENT_ERROR",
                error_message=f"Error in Physics Agent: {str(e)}",
                request_id=request_id,
                trace_id=trace_id
            )
