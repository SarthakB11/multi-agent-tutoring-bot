"""
API data models for the Multi-Agent AI Tutoring System.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
import uuid

class QueryRequest(BaseModel):
    """
    Request model for the query endpoint.
    """
    question: str = Field(..., min_length=1, max_length=1000, description="The user's question")
    request_id: Optional[str] = Field(None, description="Client-generated ID for traceability")
    session_id: Optional[str] = Field(None, description="Client-generated session ID for maintaining context")
    
    @validator('request_id', 'session_id')
    def validate_ids(cls, v):
        """Validate that IDs are valid UUIDs if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("Must be a valid UUID")
        return v
    
    @validator('question')
    def validate_question(cls, v):
        """Validate that the question is not empty or just whitespace."""
        if not v.strip():
            raise ValueError("Question cannot be empty or just whitespace")
        return v

class AgentDetails(BaseModel):
    """
    Details about the agent used to process a query.
    """
    agent_used: str = Field(..., description="The name of the agent used to process the query")
    tool_used: Optional[str] = Field(None, description="The name of the tool used by the agent")
    tool_results: Optional[Dict[str, Any]] = Field(None, description="Results from tool execution")

class DebugInfo(BaseModel):
    """
    Debug information about query processing.
    """
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    delegation_time_ms: int = Field(..., description="Time spent on delegation in milliseconds")
    agent_processing_time_ms: int = Field(..., description="Time spent on agent processing in milliseconds")
    tool_processing_time_ms: Optional[int] = Field(None, description="Time spent on tool processing in milliseconds")

class QueryResponse(BaseModel):
    """
    Response model for the query endpoint.
    """
    request_id: str = Field(..., description="Echoes client request_id or server-generated one")
    session_id: Optional[str] = Field(None, description="Echoes client session_id or server-generated one")
    answer: str = Field(..., description="The AI agent's generated answer to the question")
    agent_details: AgentDetails = Field(..., description="Details about the agent used")
    debug_info: DebugInfo = Field(..., description="Debug information about query processing")

class ErrorDetails(BaseModel):
    """
    Details about an error.
    """
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="A user-friendly error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional context-specific error details")
    trace_id: Optional[str] = Field(None, description="Internal trace ID for server logs correlation")
    retry: bool = Field(False, description="Indicates if the client should retry the request")

class ErrorResponse(BaseModel):
    """
    Response model for errors.
    """
    request_id: str = Field(..., description="Server-generated or echoed request_id")
    session_id: Optional[str] = Field(None, description="Echoed client session_id if provided")
    error: ErrorDetails = Field(..., description="Error details")
