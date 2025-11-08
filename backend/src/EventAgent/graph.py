from typing import Dict, Any, List
import json
import logging
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

logger = logging.getLogger(__name__)

from EventAgent.state import (
    EventAgentState,
    EventDetectionState,
    SignalGenerationState,
    PortfolioAnalysisState,
)
from EventAgent.configuration import EventAgentConfiguration
from EventAgent.prompts import (
    EVENT_DETECTION_PROMPT,
    SIGNAL_GENERATION_PROMPT,
    PORTFOLIO_ANALYSIS_PROMPT,
    INVESTMENT_REASONING_PROMPT,
    get_current_date,
)
from EventAgent.tools_and_schemas import FINANCIAL_TOOLS


def create_event_agent_graph():
    """Create the EventAgent LangGraph workflow."""
    
    # Create tool node
    tool_node = ToolNode(FINANCIAL_TOOLS)
    
    # Define the graph
    graph = StateGraph(EventAgentState)
    
    # Add nodes
    graph.add_node("detect_events", detect_market_events)
    graph.add_node("analyze_portfolio", analyze_portfolio_state)
    graph.add_node("evaluate_formulas", evaluate_formula_strategies)
    graph.add_node("generate_signals", generate_trading_signals)
    graph.add_node("investment_reasoning", provide_investment_reasoning)
    graph.add_node("tools", tool_node)
    
    # Add edges
    graph.add_edge(START, "detect_events")
    graph.add_edge("detect_events", "analyze_portfolio")
    graph.add_edge("analyze_portfolio", "evaluate_formulas")
    graph.add_edge("evaluate_formulas", "generate_signals")
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
            "continue": "evaluate_formulas"
        }
    )
    
    graph.add_edge("tools", "evaluate_formulas")
    
    return graph.compile()


def evaluate_formula_strategies(state: EventAgentState, config: Dict[str, Any]) -> EventAgentState:
    """Evaluate formula-based trading strategies."""
    from EventAgent.formula_handler import get_formula_handler
    from EventAgent.strategy_manager import get_strategy_manager
    
    try:
        formula_handler = get_formula_handler()
        strategy_manager = get_strategy_manager()
        
        # Get market data from state
        market_data = {
            "prices": {},
            "indicators": {},
            "events": state.get("market_events", [])
        }
        
        # Extract portfolio context
        portfolio_context = state.get("current_portfolio", {})
        
        # Get active strategies
        active_strategies = strategy_manager.get_active_strategies()
        
        if not active_strategies:
            logger.info("No active formula strategies found")
            return state
        
        # Evaluate all active formulas
        formula_signals = []
        formula_evaluations = []
        
        for strategy in active_strategies:
            try:
                signals = formula_handler.evaluate_formula_strategy(
                    strategy.formula_model_name,
                    market_data,
                    portfolio_context,
                    strategy.symbols
                )
                
                # Record evaluation
                evaluation_record = {
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.name,
                    "formula_name": strategy.formula_model_name,
                    "signals_generated": len(signals),
                    "timestamp": datetime.now().isoformat()
                }
                formula_evaluations.append(evaluation_record)
                
                # Record signals with strategy manager
                for signal in signals:
                    strategy_manager.record_signal(
                        strategy.strategy_id,
                        signal.to_dict()
                    )
                    formula_signals.append(signal.to_dict())
                
                logger.info(f"Strategy {strategy.name} generated {len(signals)} signals")
                
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy.name}: {e}")
                strategy_manager.record_error(strategy.strategy_id, str(e))
        
        # Update state with formula signals
        state["formula_signals"].extend(formula_signals)
        state["formula_evaluations"].extend(formula_evaluations)
        
        logger.info(f"Total formula signals generated: {len(formula_signals)}")
        
    except Exception as e:
        logger.error(f"Error in evaluate_formula_strategies: {e}")
    
    return state


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
    
    # Get formula signals from state
    formula_signals = state.get("formula_signals", [])
    
    # Prepare signal generation prompt
    prompt = SIGNAL_GENERATION_PROMPT.format(
        event_analysis=json.dumps(state.get("market_events", [])),
        market_data="Current market data placeholder",
        technical_indicators="Technical indicators placeholder",
        portfolio_context=json.dumps(state.get("current_portfolio", {})),
        risk_tolerance=state.get("risk_tolerance", "moderate")
    )
    
    # Add formula signals context to prompt
    if formula_signals:
        formula_context = f"\n\nFormula-Based Signals ({len(formula_signals)} signals):\n"
        formula_context += json.dumps(formula_signals, indent=2)
        prompt += formula_context
    
    # Generate trading signals
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Parse and store signals
    try:
        signal_data = json.loads(response.content)
        llm_signals = signal_data.get("signals", [])
    except json.JSONDecodeError:
        llm_signals = []
    
    # Combine formula signals with LLM signals
    all_signals = formula_signals + llm_signals
    
    # Mark signal sources
    for signal in all_signals:
        if "formula_name" in signal:
            signal["source"] = "formula_engine"
        elif signal not in formula_signals:
            signal["source"] = "llm_analysis"
    
    state["financial_signals"].extend(all_signals)
    
    logger.info(f"Generated {len(llm_signals)} LLM signals, {len(formula_signals)} formula signals")
    
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
# Utility functions for integration
def initialize_event_agent_state(
    user_message: str,
    portfolio_data: Dict[str, Any] = None,
    risk_tolerance: str = "moderate",
    investment_horizon: str = "medium",
    active_formulas: List[str] = None
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
        "formula_signals": [],
        "formula_evaluations": [],
        "active_formulas": active_formulas or [],
        "event_loop_count": 0,
        "max_event_loops": 3,
        "reasoning_model": "gemini-2.5-pro-preview-05-06",
        "current_portfolio": portfolio_data or {},
        "risk_tolerance": risk_tolerance,
        "investment_horizon": investment_horizon
    }
