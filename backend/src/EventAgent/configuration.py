import os
from pydantic import BaseModel, Field
from typing import Any, Optional, List

from langchain_core.runnables import RunnableConfig


class EventAgentConfiguration(BaseModel):
    """The configuration for the Event Agent."""

    event_detection_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the language model to use for event detection."
        },
    )

    signal_generation_model: str = Field(
        default="gemini-2.5-flash-preview-04-17",
        metadata={
            "description": "The name of the language model to use for signal generation."
        },
    )

    portfolio_analysis_model: str = Field(
        default="gemini-2.5-pro-preview-05-06",
        metadata={
            "description": "The name of the language model to use for portfolio analysis."
        },
    )

    reasoning_model: str = Field(
        default="gemini-2.5-pro-preview-05-06",
        metadata={
            "description": "The name of the language model to use for investment reasoning."
        },
    )

    max_event_loops: int = Field(
        default=3,
        metadata={"description": "The maximum number of event processing loops to perform."},
    )

    event_significance_threshold: float = Field(
        default=0.7,
        metadata={"description": "Minimum significance score for events to trigger actions."},
    )

    risk_tolerance: str = Field(
        default="moderate",
        metadata={"description": "Default risk tolerance level (conservative, moderate, aggressive)."},
    )

    investment_horizon: str = Field(
        default="medium",
        metadata={"description": "Default investment horizon (short, medium, long)."},
    )

    monitored_assets: List[str] = Field(
        default=["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        metadata={"description": "List of assets to monitor for events and signals."},
    )

    update_frequency_minutes: int = Field(
        default=15,
        metadata={"description": "How often to check for new events (in minutes)."},
    )

    enable_paper_trading: bool = Field(
        default=True,
        metadata={"description": "Whether to enable paper trading mode."},
    )

    max_position_size_pct: float = Field(
        default=0.1,
        metadata={"description": "Maximum position size as percentage of portfolio."},
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "EventAgentConfiguration":
        """Create an EventAgentConfiguration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values and handle list types
        values = {}
        for k, v in raw_values.items():
            if v is not None:
                if k == "monitored_assets" and isinstance(v, str):
                    # Parse comma-separated string to list
                    values[k] = [asset.strip() for asset in v.split(",")]
                else:
                    values[k] = v

        return cls(**values)