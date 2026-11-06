"""Discrete-time simulation engine.

How one tick works
------------------
1. Requests that arrive in this tick are handed one by one to the load balancer.
   If the chosen server's queue is already full, the request is dropped.
2. Every server then spends its capacity (work units per tick) on the requests
   in its queue, oldest first. Large requests may take several ticks.
3. We record queue lengths and utilisation for the dashboard.

After the arrival period ends the simulation keeps running ("draining") until
all queues are empty, so every accepted request gets a response time.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd

from .algorithms import make_balancer
from .metrics import summarize
from .traffic import Traffic


class Server:
    def __init__(self, server_id: int, capacity: float, max_queue: int):
        if capacity <= 0:
            raise ValueError("Server capacity must be positive")
        self.id = server_id
        self.capacity = float(capacity)
        self.max_queue = max_queue
        self.queue: deque = deque()     # items: [request_id, arrival_tick, remaining_work]
        self.busy_work = 0.0            # total work done (for utilisation)
        self.handled = 0                # requests completed

    @property
    def connections(self) -> int:
        return len(self.queue)

    @property
    def is_full(self) -> bool:
        return len(self.queue) >= self.max_queue


@dataclass
class SimulationResult:
    algorithm: str
    capacities: List[float]
    traffic_pattern: str
    duration: int
    total_requests: int
    dropped: int
    completed: pd.DataFrame            # request_id, arrival, finish, response, server
    timeline: pd.DataFrame             # tick, queue_i..., util_i...
    busy_work: List[float]
    total_ticks: int
    summary: Dict[str, float] = field(default_factory=dict)


def simulate(traffic: Traffic, capacities: List[float], algorithm: str,
             max_queue: int = 50, seed: int = 0, drain: bool = True) -> SimulationResult:
    """Run one algorithm on one traffic trace and return all recorded data."""
    rng = np.random.default_rng(seed)
    balancer = make_balancer(algorithm, capacities)
    servers = [Server(i, c, max_queue) for i, c in enumerate(capacities)]
    n = len(servers)

    completed_rows = []
    timeline_rows = []
    dropped = 0
    request_id = 0

    t = 0
    safety_limit = traffic.duration * 20 + 1000
    while True:
        in_arrival_period = t < traffic.duration
        if not in_arrival_period:
            if not drain or all(len(s.queue) == 0 for s in servers) or t > safety_limit:
                break

        # 1. dispatch arrivals
        if in_arrival_period:
            for size in traffic.arrivals[t]:
                idx = balancer.choose(servers, rng)
                server = servers[idx]
                if server.is_full:
                    dropped += 1
                else:
                    server.queue.append([request_id, t, float(size)])
                request_id += 1

        # 2. process work
        row = {"tick": t}
        for s in servers:
            budget = s.capacity
            while budget > 1e-12 and s.queue:
                head = s.queue[0]
                work = min(budget, head[2])
                head[2] -= work
                budget -= work
                s.busy_work += work
                if head[2] <= 1e-9:
                    s.queue.popleft()
                    finish = t + (s.capacity - budget) / s.capacity
                    completed_rows.append((head[0], head[1], finish,
                                           finish - head[1], s.id))
                    s.handled += 1
            row[f"queue_{s.id}"] = len(s.queue)
            row[f"util_{s.id}"] = (s.capacity - budget) / s.capacity
        timeline_rows.append(row)
        t += 1

    completed = pd.DataFrame(completed_rows,
                             columns=["request_id", "arrival", "finish", "response", "server"])
    timeline = pd.DataFrame(timeline_rows)
    result = SimulationResult(
        algorithm=algorithm,
        capacities=list(capacities),
        traffic_pattern=traffic.pattern,
        duration=traffic.duration,
        total_requests=request_id,
        dropped=dropped,
        completed=completed,
        timeline=timeline,
        busy_work=[s.busy_work for s in servers],
        total_ticks=t,
    )
    result.summary = summarize(result)
    return result
