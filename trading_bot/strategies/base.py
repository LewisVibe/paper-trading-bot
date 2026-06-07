"""Base types for future research strategy-lab work.

These types are intentionally not wired into existing runtime commands yet.
They provide a small, stable shape for future research strategies without
changing the current bot, backtest, preview, or paper-execution behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class StrategyMetadata:
    """Human-readable details about a research strategy."""

    name: str
    display_name: str
    description: str = ""
    category: str = "research"
    default_timeframe: str = "daily"
    long_only: bool = True
    research_only: bool = True
    version: str = "0.1"
    tags: tuple[str, ...] = field(default_factory=tuple)


class ResearchStrategy(Protocol):
    """Minimal interface for future backtest-only strategy candidates."""

    metadata: StrategyMetadata

    def generate_signals(self, market_data: Any) -> Any:
        """Return strategy signals for supplied research market data."""
        ...


@dataclass(frozen=True)
class StaticResearchStrategy:
    """Small concrete strategy shell useful for registry tests and scaffolding."""

    metadata: StrategyMetadata

    def generate_signals(self, market_data: Any) -> Any:
        raise NotImplementedError("Strategy signal generation is not implemented yet.")
