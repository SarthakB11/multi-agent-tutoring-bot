"""
Logging utilities for the Multi-Agent AI Tutoring System.
"""
import logging
import sys
import json
from typing import Dict, Any, Optional

from src.config import settings

# Configure the root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class ContextAdapter(logging.LoggerAdapter):
    """
    A logger adapter that adds context information to log messages.
    """
    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # Add context from adapter to extra
        for key, value in self.extra.items():
            if key not in kwargs['extra']:
                kwargs['extra'][key] = value
        
        # Format message with request_id if available
        if 'request_id' in self.extra:
            msg = f"[{self.extra['request_id']}] {msg}"
        
        # Add trace_id if available
        if 'trace_id' in self.extra:
            msg = f"[{self.extra['trace_id']}] {msg}"
            
        return msg, kwargs

def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.LoggerAdapter:
    """
    Get a logger with the given name and context.
    
    Args:
        name: The name of the logger.
        context: Optional context information to add to log messages.
    
    Returns:
        A logger adapter with the given context.
    """
    logger = logging.getLogger(name)
    return ContextAdapter(logger, context or {})

def log_event(logger: logging.LoggerAdapter, event_type: str, data: Dict[str, Any]) -> None:
    """
    Log an event with structured data.
    
    Args:
        logger: The logger to use.
        event_type: The type of event.
        data: The event data.
    """
    logger.info(f"EVENT: {event_type} - {json.dumps(data)}")

def log_api_request(logger: logging.LoggerAdapter, method: str, path: str, params: Dict[str, Any]) -> None:
    """
    Log an API request.
    
    Args:
        logger: The logger to use.
        method: The HTTP method.
        path: The request path.
        params: The request parameters.
    """
    logger.info(f"API REQUEST: {method} {path} - {json.dumps(params)}")

def log_api_response(logger: logging.LoggerAdapter, status_code: int, response_data: Dict[str, Any]) -> None:
    """
    Log an API response.
    
    Args:
        logger: The logger to use.
        status_code: The HTTP status code.
        response_data: The response data.
    """
    logger.info(f"API RESPONSE: {status_code} - {json.dumps(response_data)}")

def log_tool_invocation(logger: logging.LoggerAdapter, tool_name: str, inputs: Dict[str, Any]) -> None:
    """
    Log a tool invocation.
    
    Args:
        logger: The logger to use.
        tool_name: The name of the tool.
        inputs: The tool inputs.
    """
    logger.info(f"TOOL INVOCATION: {tool_name} - {json.dumps(inputs)}")

def log_tool_result(logger: logging.LoggerAdapter, tool_name: str, result: Dict[str, Any]) -> None:
    """
    Log a tool result.
    
    Args:
        logger: The logger to use.
        tool_name: The name of the tool.
        result: The tool result.
    """
    logger.info(f"TOOL RESULT: {tool_name} - {json.dumps(result)}")

def log_agent_decision(logger: logging.LoggerAdapter, agent_name: str, decision: str, confidence: float) -> None:
    """
    Log an agent decision.
    
    Args:
        logger: The logger to use.
        agent_name: The name of the agent.
        decision: The decision made.
        confidence: The confidence score.
    """
    logger.info(f"AGENT DECISION: {agent_name} - {decision} (confidence: {confidence:.2f})")

def log_gemini_request(logger: logging.LoggerAdapter, prompt: str) -> None:
    """
    Log a Gemini API request.
    
    Args:
        logger: The logger to use.
        prompt: The prompt sent to Gemini.
    """
    # Truncate prompt for logging
    truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
    logger.info(f"GEMINI REQUEST: {truncated_prompt}")

def log_gemini_response(logger: logging.LoggerAdapter, response_length: int) -> None:
    """
    Log a Gemini API response.
    
    Args:
        logger: The logger to use.
        response_length: The length of the response.
    """
    logger.info(f"GEMINI RESPONSE: {response_length} characters")
