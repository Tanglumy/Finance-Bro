# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from typing import Any, Dict, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import fastapi.exceptions

from langchain_core.messages import HumanMessage

from .graph import create_event_agent_graph, initialize_event_agent_state
from .configuration import EventAgentConfiguration


# Request/Response models
class EventAgentRequest(BaseModel):
    message: str
    portfolio_data: Dict[str, Any] = {}
    risk_tolerance: str = "moderate"
    investment_horizon: str = "medium"


class EventAgentResponse(BaseModel):
    analysis: str
    market_events: List[Dict[str, Any]]
    trading_signals: List[Dict[str, Any]]
    portfolio_recommendations: List[Dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Initialize the EventAgent graph
    app.state.event_agent_graph = create_event_agent_graph()
    yield


# Define the FastAPI app
app = FastAPI(
    title="Event Agent API",
    description="API for event-driven financial analysis and trading decisions",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/analyze", response_model=EventAgentResponse)
async def analyze_market_events(request: EventAgentRequest):
    """Analyze market events and generate trading recommendations."""
    try:
        # Initialize state
        initial_state = initialize_event_agent_state(
            user_message=request.message,
            portfolio_data=request.portfolio_data,
            risk_tolerance=request.risk_tolerance,
            investment_horizon=request.investment_horizon
        )
        
        # Run the EventAgent graph
        config = {"configurable": {}}
        final_state = await app.state.event_agent_graph.ainvoke(initial_state, config)
        
        # Extract the final analysis from messages
        analysis = ""
        if final_state.get("messages"):
            last_message = final_state["messages"][-1]
            analysis = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        return EventAgentResponse(
            analysis=analysis,
            market_events=final_state.get("market_events", []),
            trading_signals=final_state.get("financial_signals", []),
            portfolio_recommendations=final_state.get("portfolio_analysis", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/config")
async def get_configuration():
    """Get current EventAgent configuration."""
    config = EventAgentConfiguration()
    return config.model_dump()


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir
    static_files_path = build_path / "assets"  # Vite uses 'assets' subdir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    build_dir = pathlib.Path(build_dir)

    react = FastAPI(openapi_url="")
    react.mount(
        "/assets", StaticFiles(directory=static_files_path), name="static_assets"
    )

    @react.get("/{path:path}")
    async def handle_catch_all(request: Request, path: str):
        fp = build_path / path
        if not fp.exists() or not fp.is_file():
            fp = build_path / "index.html"
        return fastapi.responses.FileResponse(fp)

    return react


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)