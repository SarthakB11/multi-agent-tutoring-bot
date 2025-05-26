"""
Calculator tool for the Multi-Agent AI Tutoring System.
"""
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple
import sympy
import numpy as np

from src.utils.adk import BaseTool
from src.utils.errors import ToolError
from src.utils.logging import log_tool_invocation, log_tool_result
from src.config import settings

class CalculatorTool(BaseTool):
    """
    Tool for performing mathematical calculations.
    
    This tool uses sympy for safe expression evaluation and provides
    step-by-step solutions for basic operations.
    """
    
    def __init__(self, request_id: Optional[str] = None, trace_id: Optional[str] = None):
        """
        Initialize the calculator tool.
        
        Args:
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        super().__init__("CalculatorTool", request_id, trace_id)
        
        # Define allowed operations and functions
        self.allowed_symbols = {
            # Basic arithmetic
            '+': 'addition',
            '-': 'subtraction',
            '*': 'multiplication',
            '/': 'division',
            '**': 'exponentiation',
            '^': 'exponentiation',
            # Common functions
            'sqrt': 'square root',
            'exp': 'exponential',
            'log': 'logarithm',
            'sin': 'sine',
            'cos': 'cosine',
            'tan': 'tangent',
            'asin': 'arcsine',
            'acos': 'arccosine',
            'atan': 'arctangent',
            # Constants
            'pi': 'pi constant',
            'e': 'euler constant',
            # Parentheses
            '(': 'opening parenthesis',
            ')': 'closing parenthesis',
            # Numbers and variables
            r'\d+': 'numbers',
            r'\d+\.\d+': 'decimal numbers',
            r'[a-zA-Z]': 'variables'
        }
    
    def _validate_expression(self, expression: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a mathematical expression.
        
        Args:
            expression: The expression to validate.
            
        Returns:
            A tuple of (is_valid, error_message).
        """
        # Check for empty expression
        if not expression or not expression.strip():
            return False, "Expression cannot be empty"
        
        # Check for disallowed symbols
        allowed_pattern = '|'.join(self.allowed_symbols.keys())
        tokens = re.findall(r'[+\-*/^()]|\d+\.\d+|\d+|[a-zA-Z]+', expression)
        
        for token in tokens:
            is_allowed = False
            
            # Check if token is a number
            if re.match(r'^\d+$', token) or re.match(r'^\d+\.\d+$', token):
                is_allowed = True
                continue
                
            # Check if token is an allowed symbol or function
            for pattern in self.allowed_symbols.keys():
                if re.match(f'^{pattern}$', token):
                    is_allowed = True
                    break
            
            if not is_allowed:
                return False, f"Disallowed symbol or function: {token}"
        
        # Check for balanced parentheses
        if expression.count('(') != expression.count(')'):
            return False, "Unbalanced parentheses"
        
        # Check for division by zero (basic check)
        if re.search(r'/\s*0(?![.\d])', expression):
            return False, "Division by zero"
        
        return True, None
    
    def _preprocess_expression(self, expression: str) -> str:
        """
        Preprocess a mathematical expression.
        
        Args:
            expression: The expression to preprocess.
            
        Returns:
            The preprocessed expression.
        """
        # Replace ^ with ** for exponentiation
        expression = expression.replace('^', '**')
        
        # Remove whitespace
        expression = expression.strip()
        
        return expression
    
    def _generate_steps(self, expression: str, result: float) -> List[str]:
        """
        Generate steps for a calculation.
        
        Args:
            expression: The original expression.
            result: The calculation result.
            
        Returns:
            A list of steps.
        """
        steps = []
        
        # For basic arithmetic, we can show the steps
        if '+' in expression or '-' in expression or '*' in expression or '/' in expression:
            # Parse the expression using sympy
            try:
                expr = sympy.sympify(expression)
                
                # For addition and subtraction
                if isinstance(expr, sympy.Add):
                    steps.append(f"Start with the expression: {expression}")
                    for i, term in enumerate(expr.args):
                        if i == 0:
                            steps.append(f"Take the first term: {term}")
                        else:
                            op = '+' if term.is_positive else '-'
                            steps.append(f"{op} {abs(term)}")
                    steps.append(f"Result: {result}")
                
                # For multiplication and division
                elif isinstance(expr, sympy.Mul):
                    steps.append(f"Start with the expression: {expression}")
                    for i, factor in enumerate(expr.args):
                        if i == 0:
                            steps.append(f"Take the first factor: {factor}")
                        else:
                            steps.append(f"Multiply by: {factor}")
                    steps.append(f"Result: {result}")
                
                # For exponentiation
                elif isinstance(expr, sympy.Pow):
                    base, exp = expr.args
                    steps.append(f"Start with the expression: {expression}")
                    steps.append(f"Raise {base} to the power of {exp}")
                    steps.append(f"Result: {result}")
                
                # For functions
                elif isinstance(expr, sympy.Function):
                    func_name = expr.func.__name__
                    args = expr.args
                    steps.append(f"Start with the expression: {expression}")
                    steps.append(f"Apply the {func_name} function to {args}")
                    steps.append(f"Result: {result}")
                
                else:
                    steps.append(f"Calculate: {expression}")
                    steps.append(f"Result: {result}")
            
            except Exception:
                # If parsing fails, just provide a simple step
                steps.append(f"Calculate: {expression}")
                steps.append(f"Result: {result}")
        
        else:
            # For complex expressions, just provide the result
            steps.append(f"Calculate: {expression}")
            steps.append(f"Result: {result}")
        
        return steps
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the calculator tool.
        
        Args:
            inputs: The inputs for the tool.
                expression: The mathematical expression to evaluate.
            
        Returns:
            The result of the calculation.
                result: The numerical result.
                steps: Steps taken to arrive at the result.
            
        Raises:
            ToolError: If the calculation fails.
        """
        log_tool_invocation(self.logger, self.name, inputs)
        
        # Extract the expression
        expression = inputs.get('expression', '')
        
        # Validate the expression
        is_valid, error_message = self._validate_expression(expression)
        if not is_valid:
            self.logger.error(f"Invalid expression: {error_message}")
            raise ToolError(
                message=f"Invalid expression: {error_message}",
                details={"expression": expression},
                trace_id=self.trace_id
            )
        
        # Preprocess the expression
        processed_expression = self._preprocess_expression(expression)
        
        # Evaluate the expression
        try:
            # Use sympy for safe evaluation
            result = float(sympy.sympify(processed_expression).evalf())
            
            # Generate steps
            steps = self._generate_steps(expression, result)
            
            # Create the result
            tool_result = {
                "result": result,
                "steps": steps
            }
            
            log_tool_result(self.logger, self.name, tool_result)
            return tool_result
        
        except Exception as e:
            self.logger.error(f"Calculation failed: {str(e)}")
            raise ToolError(
                message=f"Calculation failed: {str(e)}",
                details={"expression": expression},
                trace_id=self.trace_id
            )
