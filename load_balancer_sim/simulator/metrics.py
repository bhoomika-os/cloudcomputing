"""Performance metrics for a finished simulation."""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def jain_fairness(values: Sequence[float]) -> float:
    """Jain's fairness index: 1.0 = perfectly even, 1/n = one server does everything."""
    x = np.asarray(values, dtype=float)
    if x.size == 0 or np.allclose(x, 0):
        return 1.0
    return float(x.sum() ** 2 / (x.size * np.sum(x ** 2)))


def server_utilisation(result) -> np.ndarray:
    """Share of each server's capacity that was actually used over the whole run."""
    caps = np.asarray(result.capacities, dtype=float)
    busy = np.asarray(result.busy_work, dtype=float)
    return busy / (caps * max(result.total_ticks, 1))


def summarize(result) -> Dict[str, float]:
    """Return the headline numbers for one simulation result."""
    resp = result.completed["response"].to_numpy()
    util = server_utilisation(result)
    queue_cols = [c for c in result.timeline.columns if c.startswith("queue_")]
    peak_queue = float(result.timeline[queue_cols].to_numpy().max()) if queue_cols else 0.0

    if resp.size:
        avg, p95, mx = float(resp.mean()), float(np.percentile(resp, 95)), float(resp.max())
    else:
        avg = p95 = mx = float("nan")

    return {
        "total_requests": int(result.total_requests),
        "completed": int(resp.size),
        "dropped": int(result.dropped),
        "drop_rate_pct": 100.0 * result.dropped / result.total_requests
        if result.total_requests else 0.0,
        "avg_response": avg,
        "p95_response": p95,
        "max_response": mx,
        "avg_utilisation_pct": 100.0 * float(util.mean()),
        "max_utilisation_pct": 100.0 * float(util.max()),
        "fairness_index": jain_fairness(util),
        "peak_queue": peak_queue,
    }
