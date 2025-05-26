"""
ADK data models for the Multi-Agent AI Tutoring System.
"""
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from enum import Enum

class EventType(str, Enum):
    """Types of events in the ADK system."""
    DELEGATION = "delegation"
    CLARIFICATION = "clarification"
    GENERAL_RESPONSE = "general_response"
    TOOL_INVOCATION = "tool_invocation"
    TOOL_RESULT = "tool_result"
    FINAL_RESPONSE = "final_response"
    ERROR = "error"

class InvocationContext(BaseModel):
    """
    Context for agent invocation, containing the user query, session state, and metadata.
    """
    query: str = Field(..., description="The user's query")
    request_id: str = Field(..., description="Unique identifier for the request")
    session_id: Optional[str] = Field(None, description="Session identifier for context preservation")
    trace_id: str = Field(..., description="Internal trace ID for correlation")
    session_state: Dict[str, Any] = Field(default_factory=dict, description="Session state for context preservation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    extracted_context: Dict[str, Any] = Field(default_factory=dict, description="Context extracted by previous agents")

class DelegationEvent(BaseModel):
    """
    Event for delegating a query to a sub-agent.
    """
    event_type: str = Field(EventType.DELEGATION, const=True)
    target_agent: str = Field(..., description="The name of the target agent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the delegation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the target agent")
    request_id: str = Field(..., description="Request ID for traceability")
    trace_id: str = Field(..., description="Trace ID for correlation")

class ClarificationEvent(BaseModel):
    """
    Event for requesting clarification from the user.
    """
    event_type: str = Field(EventType.CLARIFICATION, const=True)
    message: str = Field(..., description="Clarification message for the user")
    options: Optional[List[str]] = Field(None, description="Possible options for the user to choose from")
    request_id: str = Field(..., description="Request ID for traceability")
    trace_id: str = Field(..., description="Trace ID for correlation")

class GeneralResponseEvent(BaseModel):
    """
    Event for providing a general response when no delegation is possible.
    """
    event_type: str = Field(EventType.GENERAL_RESPONSE, const=True)
    response: str = Field(..., description="The response text")
    request_id: str = Field(..., description="Request ID for traceability")
    trace_id: str = Field(..., description="Trace ID for correlation")

class ToolInvocationEvent(BaseModel):
    """
    Event for invoking a tool.
    """
    event_type: str = Field(EventType.TOOL_INVOCATION, const=True)
    tool_name: str = Field(..., description="The name of the tool to invoke")
    inputs: Dict[str, Any] = Field(..., description="The inputs for the tool")
    request_id: str = Field(..., description="Request ID for traceability")
    trace_id: str = Field(..., description="Trace ID for correlation")

class ToolResultEvent(BaseModel):
    """
    Event for returning the result of a tool invocation.
    """
    event_type: str = Field(EventType.TOOL_RESULT, const=True)
    tool_name: str = Field(..., description="The name of the tool that was invoked")
    result: Dict[str, Any] = Field(..., description="The result of the tool invocation")
    error: Optional[str] = Field(None, description="Error message if the tool invocation failed")
    request_id: str = Field(..., description="Request ID for traceability")
    trace_id: str = Field(..., description="Trace ID for correlation")

class FinalResponseEvent(BaseModel):
    """
    Event for providing the final response to the user.
    """
    event_type: str = Field(EventType.FINAL_RESPONSE, const=True)
    response: str = Field(..., description="The response text")
    agent_used: str = Field(..., description="The name of the agent that generated the response")
    tool_used: Optional[str] = Field(None, description="The name of the tool used by the agent")
    tool_results: Optional[Dict[str, Any]] = Field(None, description="Results from tool execution")
    request_id: str = Field(..., description="Request ID for traceability")
    trace_id: str = Field(..., description="Trace ID for correlation")

class ErrorEvent(BaseModel):
    """
    Event for reporting an error.
    """
    event_type: str = Field(EventType.ERROR, const=True)
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: str = Field(..., description="Request ID for traceability")
    trace_id: str = Field(..., description="Trace ID for correlation")

# Union type for all event types
Event = Union[
    DelegationEvent,
    ClarificationEvent,
    GeneralResponseEvent,
    ToolInvocationEvent,
    ToolResultEvent,
    FinalResponseEvent,
    ErrorEvent
]

# Tool input/output schemas
class CalculatorInput(BaseModel):
    """
    Input schema for the Calculator tool.
    """
    expression: str = Field(..., description="The mathematical expression to evaluate")

class CalculatorOutput(BaseModel):
    """
    Output schema for the Calculator tool.
    """
    result: float = Field(..., description="The result of the calculation")
    steps: Optional[List[str]] = Field(None, description="Steps taken to arrive at the result")

class LookupInput(BaseModel):
    """
    Input schema for the Lookup tool.
    """
    key: str = Field(..., description="The key to look up (constant or formula name)")
    type: str = Field("constant", description="The type of lookup (constant or formula)")

class LookupOutput(BaseModel):
    """
    Output schema for the Lookup tool.
    """
    key: str = Field(..., description="The key that was looked up")
    type: str = Field(..., description="The type of lookup (constant or formula)")
    value: Optional[float] = Field(None, description="The value of the constant")
    unit: Optional[str] = Field(None, description="The unit of the constant")
    formula: Optional[str] = Field(None, description="The formula")
    description: str = Field(..., description="Description of the constant or formula")
    variables: Optional[Dict[str, str]] = Field(None, description="Variables in the formula with descriptions")
