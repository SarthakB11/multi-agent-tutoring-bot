"""
Error handling utilities for the Multi-Agent AI Tutoring System.
"""
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status

class BaseError(Exception):
    """Base error class for the application."""
    def __init__(
        self, 
        code: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        retry: bool = False,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.code = code
        self.message = message
        self.details = details
        self.trace_id = trace_id
        self.retry = retry
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary."""
        error_dict = {
            "code": self.code,
            "message": self.message,
            "retry": self.retry
        }
        
        if self.details:
            error_dict["details"] = self.details
            
        if self.trace_id:
            error_dict["trace_id"] = self.trace_id
            
        return error_dict
    
    def to_http_exception(self) -> HTTPException:
        """Convert the error to an HTTP exception."""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )

class ValidationError(BaseError):
    """Error raised when input validation fails."""
    def __init__(
        self, 
        message: str = "Invalid input parameters", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=False,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class AgentRoutingError(BaseError):
    """Error raised when the Tutor Agent cannot determine the appropriate sub-agent."""
    def __init__(
        self, 
        message: str = "Unable to determine appropriate agent for the query", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            code="AGENT_ROUTING_ERROR",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=False,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

class AgentProcessingError(BaseError):
    """Error raised when an agent encounters an error during processing."""
    def __init__(
        self, 
        message: str = "Agent encountered an error during processing", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        retry: bool = True
    ):
        super().__init__(
            code="AGENT_PROCESSING_ERROR",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=retry,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class ToolError(BaseError):
    """Error raised when a tool execution fails."""
    def __init__(
        self, 
        message: str = "Tool execution failed", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        retry: bool = True
    ):
        super().__init__(
            code="TOOL_ERROR",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=retry,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class GeminiAPIError(BaseError):
    """Error raised when there is an issue with the Gemini API."""
    def __init__(
        self, 
        message: str = "Error communicating with Gemini API", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            code="GEMINI_API_ERROR",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=True,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class RateLimitExceededError(BaseError):
    """Error raised when rate limits are exceeded."""
    def __init__(
        self, 
        message: str = "Too many requests", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=True,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class ServiceUnavailableError(BaseError):
    """Error raised when the service is temporarily unavailable."""
    def __init__(
        self, 
        message: str = "Service temporarily unavailable", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=True,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class UnknownError(BaseError):
    """Error raised when an unexpected error occurs."""
    def __init__(
        self, 
        message: str = "Unexpected server error", 
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        super().__init__(
            code="UNKNOWN_ERROR",
            message=message,
            details=details,
            trace_id=trace_id,
            retry=True,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def format_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format validation errors from Pydantic.
    
    Args:
        errors: List of validation errors.
    
    Returns:
        Formatted validation errors.
    """
    formatted_errors = {}
    
    for error in errors:
        loc = error.get("loc", [])
        field = loc[-1] if loc else "unknown"
        msg = error.get("msg", "Unknown validation error")
        
        formatted_errors[field] = msg
        
    return formatted_errors
