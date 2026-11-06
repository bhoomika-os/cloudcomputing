"""Cloud Load Balancer Simulator - core package."""
from .traffic import generate_traffic, PATTERNS, PATTERN_DESCRIPTIONS, Traffic
from .algorithms import ALGORITHMS, ALGORITHM_LABELS, make_balancer
from .engine import simulate, SimulationResult
from .metrics import summarize, jain_fairness
from .scenarios import SERVER_PRESETS, build_capacities, run_comparison

__all__ = [
    "generate_traffic", "PATTERNS", "PATTERN_DESCRIPTIONS", "Traffic",
    "ALGORITHMS", "ALGORITHM_LABELS", "make_balancer",
    "simulate", "SimulationResult",
    "summarize", "jain_fairness",
    "SERVER_PRESETS", "build_capacities", "run_comparison",
]
