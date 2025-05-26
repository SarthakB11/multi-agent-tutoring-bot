"""
Main API module for the Multi-Agent AI Tutoring System.
"""
import time
import uuid
import asyncio
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.models.api import QueryRequest, QueryResponse, ErrorResponse, AgentDetails, DebugInfo
from src.utils.adk import Runner, SessionService
from src.utils.mongodb import get_database, close_mongodb_connection
from src.utils.errors import BaseError, ValidationError as AppValidationError, format_validation_errors
from src.utils.logging import get_logger
from src.agents.tutor_agent import TutorAgent
from src.agents.math_agent import MathAgent
from src.agents.physics_agent import PhysicsAgent
from src.tools.calculator import CalculatorTool
from src.tools.lookup import LookupTool
from src.config import settings

# Create the FastAPI application
app = FastAPI(
    title="Multi-Agent AI Tutoring System",
    description="A multi-agent AI tutoring system based on Google's Agent Development Kit (ADK) principles",
    version="1.0.0"
)

# Add startup and shutdown events for MongoDB connection
@app.on_event("startup")
async def startup_db_client():
    # The database connection will be initialized when needed
    logger.info("Setting up MongoDB connection")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Closing MongoDB connection")
    await close_mongodb_connection()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logger = get_logger("api")

# Create session service
session_service = SessionService()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add process time header and handle exceptions.
    """
    start_time = time.time()
    
    # Generate request ID if not provided
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Generate trace ID for internal correlation
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    
    # Set up request-specific logger
    request_logger = get_logger(
        "api.request",
        {"request_id": request_id, "trace_id": trace_id}
    )
    
    request_logger.info(f"Request started: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Add process time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        request_logger.info(f"Request completed: {response.status_code} in {process_time:.4f}s")
        
        return response
    
    except ValidationError as e:
        request_logger.error(f"Validation error: {str(e)}")
        
        # Format validation errors
        errors = format_validation_errors(e.errors())
        
        # Create error response
        error_response = ErrorResponse(
            request_id=request_id,
            session_id=None,
            error={
                "code": "VALIDATION_ERROR",
                "message": "Invalid input parameters",
                "details": errors,
                "trace_id": trace_id,
                "retry": False
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.dict()
        )
    
    except BaseError as e:
        request_logger.error(f"Application error: {str(e)}")
        
        # Create error response
        error_response = ErrorResponse(
            request_id=request_id,
            session_id=None,
            error={
                "code": e.code,
                "message": e.message,
                "details": e.details,
                "trace_id": trace_id,
                "retry": e.retry
            }
        )
        
        return JSONResponse(
            status_code=e.status_code,
            content=error_response.dict()
        )
    
    except Exception as e:
        request_logger.error(f"Unhandled exception: {str(e)}")
        
        # Create error response
        error_response = ErrorResponse(
            request_id=request_id,
            session_id=None,
            error={
                "code": "UNKNOWN_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(e)} if settings.DEBUG else None,
                "trace_id": trace_id,
                "retry": True
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict()
        )

async def get_runner(request: Request) -> Runner:
    """
    Dependency to create a Runner instance for the request.
    """
    request_id = request.state.request_id
    trace_id = request.state.trace_id
    
    # Create agents
    tutor_agent = TutorAgent(request_id, trace_id)
    math_agent = MathAgent(request_id, trace_id)
    physics_agent = PhysicsAgent(request_id, trace_id)
    
    # Create tools
    calculator_tool = CalculatorTool(request_id, trace_id)
    lookup_tool = LookupTool(request_id, trace_id)
    
    # Create runner
    runner = Runner(
        agents={
            "TutorAgent": tutor_agent,
            "MathAgent": math_agent,
            "PhysicsAgent": physics_agent
        },
        tools={
            "CalculatorTool": calculator_tool,
            "LookupTool": lookup_tool
        },
        session_service=session_service,
        request_id=request_id,
        trace_id=trace_id
    )
    
    return runner

@app.post("/api/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    req: Request,
    runner: Runner = Depends(get_runner)
) -> QueryResponse:
    """
    Process a user query and return the response.
    """
    request_id = req.state.request_id
    trace_id = req.state.trace_id
    
    # Override request_id if provided in the request
    if request.request_id:
        request_id = request.request_id
        
    # Get MongoDB database connection
    async with get_database() as db:
        from src.utils.mongodb import ChatMessage, UserSession
        
        # Store the user message
        user_message = ChatMessage(
            user_id=request.user_id,
            content=request.question,  # Use question field
            role="user",
            timestamp=time.time()
        )
        await user_message.insert()
        
        # Get or create user session
        session = None
        if request.session_id:
            session = await UserSession.find_one({"session_id": request.session_id})
        
        if not session:
            session = UserSession(
                user_id=request.user_id,
                session_id=str(uuid.uuid4()),
                messages=[str(user_message.id)]
            )
            await session.insert()
        else:
            # Update session with new message
            session.messages.append(str(user_message.id))
            await session.save()
    
    # Use the session_id from MongoDB
    session_id = session.session_id
    
    # Set up request-specific logger
    request_logger = get_logger(
        "api.query",
        {"request_id": request_id, "trace_id": trace_id}
    )
    
    request_logger.info(f"Processing query: {request.question}")
    
    # Record start time
    start_time = time.time()
    delegation_start_time = time.time()
    
    try:
        # Process the query
        result = await runner.process_query(request.question, session_id)
        
        # Record end time
        end_time = time.time()
        
        # Calculate processing times
        total_time_ms = int((end_time - start_time) * 1000)
        delegation_time_ms = int((delegation_start_time - start_time) * 1000)
        agent_time_ms = total_time_ms - delegation_time_ms
        
        # Create debug info
        debug_info = DebugInfo(
            processing_time_ms=total_time_ms,
            delegation_time_ms=delegation_time_ms,
            agent_processing_time_ms=agent_time_ms,
            tool_processing_time_ms=None  # We don't have this information yet
        )
        
        # Create agent details
        agent_details = AgentDetails(
            agent_used=result["agent_details"]["agent_used"],
            tool_used=result["agent_details"]["tool_used"],
            tool_results=result["agent_details"]["tool_results"]
        )
        
        # Create response
        response = result["answer"]
        
        # Store the assistant's response in MongoDB
        async with get_database() as db:
            from src.utils.mongodb import ChatMessage, AgentInteraction
            
            # Store the assistant message
            assistant_message = ChatMessage(
                user_id=request.user_id,
                content=response,
                role="assistant",
                timestamp=time.time()
            )
            await assistant_message.insert()
            
            # Update session with assistant message
            session.messages.append(str(assistant_message.id))
            await session.save()
            
            # Store agent interaction details
            agent_interaction = AgentInteraction(
                session_id=session_id,
                agent_name=agent_details.agent_used,
                query=request.query,
                response=response,
                confidence=None,  # We don't have this information yet
                tools_used=[tool for tool in agent_details.tool_used] if agent_details.tool_used else []
            )
            await agent_interaction.insert()
        
        # Create the response object
        response_obj = QueryResponse(
            request_id=request_id,
            session_id=session_id,
            query=request.question,
            answer=response,
            agent_details=agent_details,
            debug_info=debug_info if settings.DEBUG else None
        )
        
        request_logger.info(f"Query processed successfully in {total_time_ms}ms")
        
        return response_obj
    
    except Exception as e:
        request_logger.error(f"Error processing query: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "name": "Multi-Agent AI Tutoring System",
        "version": "1.0.0",
        "description": "A multi-agent AI tutoring system based on Google's Agent Development Kit (ADK) principles",
        "endpoints": {
            "query": "/api/query",
            "health": "/health"
        }
    }
