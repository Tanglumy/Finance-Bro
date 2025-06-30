from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, List, Dict, Any
from datetime import datetime

from langgraph.graph import add_messages
from typing_extensions import Annotated

import operator
from dataclasses import dataclass, field
from typing_extensions import Annotated


class EventAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    market_events: Annotated[list, operator.add]
    financial_signals: Annotated[list, operator.add]
    portfolio_analysis: Annotated[list, operator.add]
    research_queries: Annotated[list, operator.add]
    research_results: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    event_loop_count: int
    max_event_loops: int
    reasoning_model: str
    current_portfolio: Dict[str, Any]
    risk_tolerance: str
    investment_horizon: str


class EventDetectionState(TypedDict):
    detected_events: List[Dict[str, Any]]
    event_significance: str
    event_type: str
    affected_assets: List[str]
    confidence_score: float


class SignalGenerationState(TypedDict):
    signal_type: str  # "BUY", "SELL", "HOLD"
    asset_symbol: str
    signal_strength: float
    rationale: str
    risk_assessment: str
    entry_price: float
    target_price: float
    stop_loss: float


class PortfolioAnalysisState(TypedDict):
    current_positions: Dict[str, Any]
    portfolio_value: float
    daily_pnl: float
    risk_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    rebalancing_needed: bool


class MarketEvent(TypedDict):
    event_id: str
    timestamp: datetime
    event_type: str
    description: str
    affected_markets: List[str]
    severity: str
    source: str


class FinancialSignal(TypedDict):
    signal_id: str
    timestamp: datetime
    asset: str
    signal_type: str
    strength: float
    rationale: str
    generated_by: str


@dataclass(kw_only=True)
class EventAnalysisOutput:
    event_summary: str = field(default=None)
    investment_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    risk_analysis: str = field(default=None)
    market_outlook: str = field(default=None)


@dataclass(kw_only=True)
class TradingRecommendation:
    action: str  # BUY, SELL, HOLD
    asset: str
    quantity: float
    rationale: str
    confidence: float
    risk_level: str
    time_horizon: str