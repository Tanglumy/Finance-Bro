from typing import Dict, Any, List
import json
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from .state import (
    EventAgentState,
    EventDetectionState,
    SignalGenerationState,
    PortfolioAnalysisState,
)
from .configuration import EventAgentConfiguration
from .prompts import (
    EVENT_DETECTION_PROMPT,
    SIGNAL_GENERATION_PROMPT,
    PORTFOLIO_ANALYSIS_PROMPT,
    INVESTMENT_REASONING_PROMPT,
    get_current_date,
)
from .tools_and_schemas import FINANCIAL_TOOLS


def create_event_agent_graph():
    """Create the EventAgent LangGraph workflow."""
    
    # Create tool node
    tool_node = ToolNode(FINANCIAL_TOOLS)
    
    # Define the graph
    graph = StateGraph(EventAgentState)
    
    # Add nodes
    graph.add_node("detect_events", detect_market_events)
    graph.add_node("analyze_portfolio", analyze_portfolio_state)
    graph.add_node("generate_signals", generate_trading_signals)
    graph.add_node("investment_reasoning", provide_investment_reasoning)
    graph.add_node("tools", tool_node)
    
    # Add edges
    graph.add_edge(START, "detect_events")
    graph.add_edge("detect_events", "analyze_portfolio")
    graph.add_edge("analyze_portfolio", "generate_signals")
    graph.add_edge("generate_signals", "investment_reasoning")
    graph.add_edge("investment_reasoning", END)
    
    # Add conditional edges for tool usage
    graph.add_conditional_edges(
        "detect_events",
        should_use_tools,
        {
            "tools": "tools",
            "continue": "analyze_portfolio"
        }
    )
    
    graph.add_conditional_edges(
        "analyze_portfolio", 
        should_use_tools,
        {
            "tools": "tools",
            "continue": "generate_signals"
        }
    )
    
    graph.add_edge("tools", "generate_signals")
    
    return graph.compile()


def detect_market_events(state: EventAgentState, config: Dict[str, Any]) -> EventAgentState:
    """Detect significant market events from current data."""
    configuration = EventAgentConfiguration.from_runnable_config(config)
    
    # Initialize LLM for event detection
    llm = ChatGoogleGenerativeAI(
        model=configuration.event_detection_model,
        temperature=0.1
    )
    
    # Gather market data using tools
    market_data = "Current market data placeholder"  # TODO: Integrate with actual tools
    news_data = "Recent news headlines placeholder"
    economic_events = "Economic calendar placeholder"
    
    # Create event detection prompt
    prompt = EVENT_DETECTION_PROMPT.format(
        market_data=market_data,
        news_data=news_data,
        economic_events=economic_events,
        threshold=configuration.event_significance_threshold
    )
    
    # Generate event detection
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse response (assuming JSON format)
    try:
        event_data = json.loads(response.content)
        detected_events = event_data.get("detected_events", [])
    except json.JSONDecodeError:
        detected_events = []
    
    # Update state
    state["market_events"].extend(detected_events)
    state["event_loop_count"] += 1
    
    return state


def analyze_portfolio_state(state: EventAgentState, config: Dict[str, Any]) -> EventAgentState:
    """Analyze current portfolio in context of detected events."""
    configuration = EventAgentConfiguration.from_runnable_config(config)
    
    # Initialize LLM for portfolio analysis
    llm = ChatGoogleGenerativeAI(
        model=configuration.portfolio_analysis_model,
        temperature=0.1
    )
    
    # Prepare portfolio analysis prompt
    prompt = PORTFOLIO_ANALYSIS_PROMPT.format(
        portfolio_data=json.dumps(state.get("current_portfolio", {})),
        market_events=json.dumps(state.get("market_events", [])),
        performance_metrics="Performance metrics placeholder",
        risk_metrics="Risk metrics placeholder"
    )
    
    # Generate portfolio analysis
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse and store analysis
    try:
        analysis_data = json.loads(response.content)
        portfolio_analysis = analysis_data.get("portfolio_analysis", {})
    except json.JSONDecodeError:
        portfolio_analysis = {"error": "Failed to parse portfolio analysis"}
    
    state["portfolio_analysis"].append(portfolio_analysis)
    
    return state


def generate_trading_signals(state: EventAgentState, config: Dict[str, Any]) -> EventAgentState:
    """Generate trading signals based on events and portfolio analysis."""
    configuration = EventAgentConfiguration.from_runnable_config(config)
    
    # Initialize LLM for signal generation
    llm = ChatGoogleGenerativeAI(
        model=configuration.signal_generation_model,
        temperature=0.1
    )
    
    # Prepare signal generation prompt
    prompt = SIGNAL_GENERATION_PROMPT.format(
        event_analysis=json.dumps(state.get("market_events", [])),
        market_data="Current market data placeholder",
        technical_indicators="Technical indicators placeholder",
        portfolio_context=json.dumps(state.get("current_portfolio", {})),
        risk_tolerance=state.get("risk_tolerance", "moderate")
    )
    
    # Generate trading signals
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse and store signals
    try:
        signal_data = json.loads(response.content)
        trading_signals = signal_data.get("signals", [])
    except json.JSONDecodeError:
        trading_signals = []
    
    state["financial_signals"].extend(trading_signals)
    
    return state


def provide_investment_reasoning(state: EventAgentState, config: Dict[str, Any]) -> EventAgentState:
    """Provide comprehensive investment reasoning and recommendations."""
    configuration = EventAgentConfiguration.from_runnable_config(config)
    
    # Initialize LLM for investment reasoning
    llm = ChatGoogleGenerativeAI(
        model=configuration.reasoning_model,
        temperature=0.2
    )
    
    # Get the original question from messages
    user_question = ""
    if state.get("messages"):
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break
    
    # Prepare investment reasoning prompt
    prompt = INVESTMENT_REASONING_PROMPT.format(
        question=user_question,
        market_events=json.dumps(state.get("market_events", [])),
        signal_analysis=json.dumps(state.get("financial_signals", [])),
        portfolio_context=json.dumps(state.get("current_portfolio", {})),
        research_results=json.dumps(state.get("research_results", [])),
        current_date=get_current_date()
    )
    
    # Generate investment reasoning
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Add reasoning to messages
    state["messages"].append(response)
    
    return state


def should_use_tools(state: EventAgentState) -> str:
    """Determine if tools should be used based on current state."""
    # For now, always continue without tools
    # TODO: Implement logic to determine when tools are needed
    return "continue"


def route_to_research_agent(state: EventAgentState) -> bool:
    """Determine if Research Agent should be called for additional information."""
    # Check if we need more research based on detected events
    significant_events = [
        event for event in state.get("market_events", [])
        if event.get("significance_score", 0) > 0.8
    ]
    
    return len(significant_events) > 0 and len(state.get("research_results", [])) == 0


# Utility functions for integration
def initialize_event_agent_state(
    user_message: str,
    portfolio_data: Dict[str, Any] = None,
    risk_tolerance: str = "moderate",
    investment_horizon: str = "medium"
) -> EventAgentState:
    """Initialize the EventAgent state with user input and context."""
    return {
        "messages": [HumanMessage(content=user_message)],
        "market_events": [],
        "financial_signals": [],
        "portfolio_analysis": [],
        "research_queries": [],
        "research_results": [],
        "sources_gathered": [],
        "event_loop_count": 0,
        "max_event_loops": 3,
        "reasoning_model": "gemini-2.5-pro-preview-05-06",
        "current_portfolio": portfolio_data or {},
        "risk_tolerance": risk_tolerance,
        "investment_horizon": investment_horizon
    }