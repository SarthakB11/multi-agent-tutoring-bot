"""
ADK (Agent Development Kit) implementation for the Multi-Agent AI Tutoring System.
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, List, AsyncGenerator, Union, Type
from abc import ABC, abstractmethod

from src.models.adk import (
    InvocationContext, 
    Event, 
    EventType,
    DelegationEvent,
    ClarificationEvent,
    GeneralResponseEvent,
    ToolInvocationEvent,
    ToolResultEvent,
    FinalResponseEvent,
    ErrorEvent
)
from src.utils.logging import get_logger

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, request_id: Optional[str] = None, trace_id: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            name: The name of the agent.
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        self.name = name
        self.request_id = request_id or str(uuid.uuid4())
        self.trace_id = trace_id or str(uuid.uuid4())
        
        # Set up logging
        log_context = {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "agent": self.name
        }
        self.logger = get_logger(f"agent.{self.name.lower()}", log_context)
        
    @abstractmethod
    async def run(self, context: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Run the agent with the given context.
        
        Args:
            context: The invocation context.
            
        Yields:
            Events produced by the agent.
        """
        pass

class BaseTool(ABC):
    """Base class for all tools in the system."""
    
    def __init__(self, name: str, request_id: Optional[str] = None, trace_id: Optional[str] = None):
        """
        Initialize the tool.
        
        Args:
            name: The name of the tool.
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        self.name = name
        self.request_id = request_id or str(uuid.uuid4())
        self.trace_id = trace_id or str(uuid.uuid4())
        
        # Set up logging
        log_context = {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "tool": self.name
        }
        self.logger = get_logger(f"tool.{self.name.lower()}", log_context)
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given inputs.
        
        Args:
            inputs: The inputs for the tool.
            
        Returns:
            The result of the tool execution.
            
        Raises:
            Exception: If the tool execution fails.
        """
        pass

class Runner:
    """Runner for executing agents and tools."""
    
    def __init__(
        self, 
        agents: Dict[str, BaseAgent],
        tools: Dict[str, BaseTool],
        session_service: Optional['SessionService'] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """
        Initialize the runner.
        
        Args:
            agents: Dictionary of agent name to agent instance.
            tools: Dictionary of tool name to tool instance.
            session_service: Optional session service for managing session state.
            request_id: The request ID for tracing.
            trace_id: The trace ID for internal correlation.
        """
        self.agents = agents
        self.tools = tools
        self.session_service = session_service
        self.request_id = request_id or str(uuid.uuid4())
        self.trace_id = trace_id or str(uuid.uuid4())
        
        # Set up logging
        log_context = {
            "request_id": self.request_id,
            "trace_id": self.trace_id
        }
        self.logger = get_logger("runner", log_context)
    
    async def run_agent(
        self, 
        agent_name: str, 
        context: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Run an agent with the given context.
        
        Args:
            agent_name: The name of the agent to run.
            context: The invocation context.
            
        Yields:
            Events produced by the agent.
            
        Raises:
            ValueError: If the agent is not found.
        """
        if agent_name not in self.agents:
            self.logger.error(f"Agent not found: {agent_name}")
            yield ErrorEvent(
                error_code="AGENT_NOT_FOUND",
                error_message=f"Agent not found: {agent_name}",
                request_id=self.request_id,
                trace_id=self.trace_id
            )
            return
        
        agent = self.agents[agent_name]
        self.logger.info(f"Running agent: {agent_name}")
        
        try:
            async for event in agent.run(context):
                self.logger.info(f"Agent {agent_name} produced event: {event.event_type}")
                
                # Handle delegation events
                if event.event_type == EventType.DELEGATION:
                    delegation_event = event
                    target_agent = delegation_event.target_agent
                    
                    # Update context with extracted context from the delegating agent
                    new_context = InvocationContext(
                        query=context.query,
                        request_id=context.request_id,
                        session_id=context.session_id,
                        trace_id=context.trace_id,
                        session_state=context.session_state,
                        metadata=context.metadata,
                        extracted_context=delegation_event.context
                    )
                    
                    # Run the target agent
                    self.logger.info(f"Delegating to agent: {target_agent}")
                    async for sub_event in self.run_agent(target_agent, new_context):
                        yield sub_event
                    
                # Handle tool invocation events
                elif event.event_type == EventType.TOOL_INVOCATION:
                    tool_event = event
                    tool_name = tool_event.tool_name
                    
                    # Execute the tool
                    try:
                        if tool_name not in self.tools:
                            self.logger.error(f"Tool not found: {tool_name}")
                            yield ErrorEvent(
                                error_code="TOOL_NOT_FOUND",
                                error_message=f"Tool not found: {tool_name}",
                                request_id=self.request_id,
                                trace_id=self.trace_id
                            )
                            continue
                        
                        tool = self.tools[tool_name]
                        self.logger.info(f"Executing tool: {tool_name}")
                        result = await tool.execute(tool_event.inputs)
                        
                        # Return the result
                        yield ToolResultEvent(
                            tool_name=tool_name,
                            result=result,
                            request_id=self.request_id,
                            trace_id=self.trace_id
                        )
                    except Exception as e:
                        self.logger.error(f"Tool execution failed: {str(e)}")
                        yield ToolResultEvent(
                            tool_name=tool_name,
                            result={},
                            error=str(e),
                            request_id=self.request_id,
                            trace_id=self.trace_id
                        )
                
                # Pass through other events
                else:
                    yield event
        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}")
            yield ErrorEvent(
                error_code="AGENT_EXECUTION_ERROR",
                error_message=f"Agent execution failed: {str(e)}",
                request_id=self.request_id,
                trace_id=self.trace_id
            )
    
    async def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user query.
        
        Args:
            query: The user query.
            session_id: Optional session ID for context preservation.
            
        Returns:
            The final response.
            
        Raises:
            Exception: If query processing fails.
        """
        # Get session state if available
        session_state = {}
        if self.session_service and session_id:
            session_state = await self.session_service.get_session_state(session_id)
        
        # Create invocation context
        context = InvocationContext(
            query=query,
            request_id=self.request_id,
            session_id=session_id,
            trace_id=self.trace_id,
            session_state=session_state,
            metadata={},
            extracted_context={}
        )
        
        # Start with the Tutor Agent
        final_response = None
        agent_used = "TutorAgent"
        tool_used = None
        tool_results = None
        
        try:
            async for event in self.run_agent("TutorAgent", context):
                if event.event_type == EventType.FINAL_RESPONSE:
                    final_response = event.response
                    agent_used = event.agent_used
                    tool_used = event.tool_used
                    tool_results = event.tool_results
                    break
                elif event.event_type == EventType.ERROR:
                    raise Exception(f"{event.error_code}: {event.error_message}")
            
            # Update session state if available
            if self.session_service and session_id:
                await self.session_service.update_session_state(
                    session_id, 
                    {
                        "last_query": query,
                        "last_response": final_response,
                        "last_agent_used": agent_used
                    }
                )
            
            if not final_response:
                raise Exception("No final response was generated")
            
            return {
                "answer": final_response,
                "agent_details": {
                    "agent_used": agent_used,
                    "tool_used": tool_used,
                    "tool_results": tool_results
                }
            }
        except Exception as e:
            self.logger.error(f"Query processing failed: {str(e)}")
            raise

class SessionService:
    """Service for managing session state."""
    
    def __init__(self):
        """Initialize the session service."""
        self.sessions = {}
        self.logger = get_logger("session_service")
    
    async def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get the state for a session.
        
        Args:
            session_id: The session ID.
            
        Returns:
            The session state.
        """
        return self.sessions.get(session_id, {})
    
    async def update_session_state(self, session_id: str, updates: Dict[str, Any]) -> None:
        """
        Update the state for a session.
        
        Args:
            session_id: The session ID.
            updates: The updates to apply to the session state.
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {}
        
        self.sessions[session_id].update(updates)
    
    async def clear_session(self, session_id: str) -> None:
        """
        Clear a session.
        
        Args:
            session_id: The session ID.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
