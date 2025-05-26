"""
Lookup tool for the Multi-Agent AI Tutoring System.
"""
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple

from src.utils.adk import BaseTool
from src.utils.errors import ToolError
from src.utils.logging import log_tool_invocation, log_tool_result
from src.config import settings

class LookupTool(BaseTool):
    """
    Tool for looking up physics constants and formulas.
    
    This tool provides access to a read-only database of physics constants,
    formulas, and definitions.
    """
    
    def __init__(self, request_id: Optional[str] = None, trace_id: Optional[str] = None):
        """
        Initialize the lookup tool.
        
        Args:
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        super().__init__("LookupTool", request_id, trace_id)
        
        # Load constants and formulas from settings
        self.constants = settings.PHYSICS_CONSTANTS
        self.formulas = settings.PHYSICS_FORMULAS
    
    def _fuzzy_match(self, key: str, collection: Dict[str, Any]) -> Tuple[Optional[str], float]:
        """
        Perform fuzzy matching on a key.
        
        Args:
            key: The key to match.
            collection: The collection to match against.
            
        Returns:
            A tuple of (matched_key, confidence).
        """
        # First, try exact match
        if key in collection:
            return key, 1.0
        
        # Try case-insensitive match
        key_lower = key.lower()
        for k in collection.keys():
            if k.lower() == key_lower:
                return k, 0.9
        
        # Try partial match
        best_match = None
        best_score = 0.0
        
        for k in collection.keys():
            # Check if key is a substring of k
            if key_lower in k.lower():
                score = len(key_lower) / len(k.lower())
                if score > best_score:
                    best_match = k
                    best_score = score
            
            # Check if k is a substring of key
            elif k.lower() in key_lower:
                score = len(k.lower()) / len(key_lower)
                if score > best_score:
                    best_match = k
                    best_score = score
        
        # Return the best match if it's good enough
        if best_match and best_score > 0.5:
            return best_match, best_score
        
        return None, 0.0
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the lookup tool.
        
        Args:
            inputs: The inputs for the tool.
                key: The key to look up (constant or formula name).
                type: The type of lookup (constant or formula).
            
        Returns:
            The result of the lookup.
                key: The key that was looked up.
                type: The type of lookup (constant or formula).
                value: The value of the constant (for constants).
                unit: The unit of the constant (for constants).
                formula: The formula (for formulas).
                description: Description of the constant or formula.
                variables: Variables in the formula with descriptions (for formulas).
            
        Raises:
            ToolError: If the lookup fails.
        """
        log_tool_invocation(self.logger, self.name, inputs)
        
        # Extract the key and type
        key = inputs.get('key', '')
        lookup_type = inputs.get('type', 'constant')
        
        # Validate the inputs
        if not key:
            self.logger.error("Missing key for lookup")
            raise ToolError(
                message="Missing key for lookup",
                trace_id=self.trace_id
            )
        
        if lookup_type not in ['constant', 'formula']:
            self.logger.error(f"Invalid lookup type: {lookup_type}")
            raise ToolError(
                message=f"Invalid lookup type: {lookup_type}. Must be 'constant' or 'formula'.",
                trace_id=self.trace_id
            )
        
        # Perform the lookup
        collection = self.constants if lookup_type == 'constant' else self.formulas
        matched_key, confidence = self._fuzzy_match(key, collection)
        
        if not matched_key:
            self.logger.error(f"No match found for {lookup_type}: {key}")
            raise ToolError(
                message=f"No match found for {lookup_type}: {key}",
                details={"key": key, "type": lookup_type},
                trace_id=self.trace_id
            )
        
        # Get the result
        result = collection[matched_key]
        
        # Format the result based on the lookup type
        if lookup_type == 'constant':
            tool_result = {
                "key": matched_key,
                "type": "constant",
                "value": result.get('value'),
                "unit": result.get('unit'),
                "description": result.get('description')
            }
        else:  # formula
            tool_result = {
                "key": matched_key,
                "type": "formula",
                "formula": result.get('formula'),
                "description": result.get('description'),
                "variables": result.get('variables')
            }
        
        # Add confidence score if it's a fuzzy match
        if confidence < 1.0:
            tool_result["match_confidence"] = confidence
            tool_result["original_query"] = key
        
        log_tool_result(self.logger, self.name, tool_result)
        return tool_result
