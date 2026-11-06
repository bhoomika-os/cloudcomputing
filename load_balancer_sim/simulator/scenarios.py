"""Helpers that glue traffic, servers and algorithms together.

Used by both the Streamlit dashboard and the command-line experiment runner.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from .algorithms import ALGORITHMS, ALGORITHM_LABELS
from .engine import SimulationResult, simulate
from .traffic import Traffic, generate_traffic

SERVER_PRESETS = {
    "equal": "All servers have the same capacity",
    "mixed": "Servers of different power (strong, medium and weak)",
    "custom": "Type your own capacities",
}

_MIXED_PATTERN = [20.0, 10.0, 10.0, 5.0]


def build_capacities(preset: str, n_servers: int,
                     custom: Optional[Sequence[float]] = None,
                     base_capacity: float = 10.0) -> List[float]:
    """Return a list of server capacities (work units processed per tick)."""
    if preset == "equal":
        return [float(base_capacity)] * n_servers
    if preset == "mixed":
        return [_MIXED_PATTERN[i % len(_MIXED_PATTERN)] for i in range(n_servers)]
    if preset == "custom":
        if not custom:
            raise ValueError("Custom preset needs a list of capacities")
        return [float(c) for c in custom]
    raise ValueError(f"Unknown preset {preset!r}")


def run_comparison(pattern: str, capacities: List[float], load_factor: float = 0.8,
                   duration: int = 300, mean_size: float = 1.0,
                   algorithms: Optional[Sequence[str]] = None,
                   max_queue: int = 50, seed: int = 0
                   ) -> Tuple[Traffic, Dict[str, SimulationResult], pd.DataFrame]:
    """Run several algorithms on identical traffic.

    load_factor is the average demand as a share of total capacity:
    0.5 = half loaded, 1.0 = exactly at capacity, 1.2 = overloaded.
    """
    algorithms = list(algorithms) if algorithms else list(ALGORITHMS)
    mean_rate = load_factor * sum(capacities) / mean_size
    traffic = generate_traffic(pattern, duration, mean_rate, mean_size, seed)

    results: Dict[str, SimulationResult] = {}
    rows = []
    for name in algorithms:
        res = simulate(traffic, capacities, name, max_queue=max_queue, seed=seed)
        results[name] = res
        rows.append({"algorithm": ALGORITHM_LABELS[name], **res.summary})
    summary = pd.DataFrame(rows).set_index("algorithm")
    return traffic, results, summary


def best_algorithm(summary: pd.DataFrame) -> str:
    """Pick the algorithm with the lowest average response time (ties: fewest drops)."""
    ranked = summary.sort_values(["dropped", "avg_response"])
    return str(ranked.index[0])
