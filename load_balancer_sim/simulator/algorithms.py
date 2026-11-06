"""Load balancing algorithms.

Every algorithm implements `choose(servers, rng) -> index of the chosen server`.
`servers` is the list of Server objects from engine.py; each has:
    .capacity        work units processed per tick
    .connections     number of requests currently queued or in service
"""
from __future__ import annotations

from typing import Dict, List, Type


class LoadBalancer:
    name = "base"

    def __init__(self, n_servers: int, capacities: List[float]):
        self.n = n_servers
        self.capacities = list(capacities)

    def choose(self, servers, rng) -> int:
        raise NotImplementedError


class RoundRobin(LoadBalancer):
    """Send requests to servers one after another in a fixed circle."""
    name = "round_robin"

    def __init__(self, n_servers, capacities):
        super().__init__(n_servers, capacities)
        self._next = 0

    def choose(self, servers, rng) -> int:
        idx = self._next
        self._next = (self._next + 1) % self.n
        return idx


class WeightedRoundRobin(LoadBalancer):
    """Round robin where stronger servers get proportionally more requests.

    Uses the 'smooth weighted round robin' method (as in Nginx) so requests
    for a strong server are spread out rather than sent in one long run.
    """
    name = "weighted_round_robin"

    def __init__(self, n_servers, capacities):
        super().__init__(n_servers, capacities)
        self._current = [0.0] * n_servers
        self._total = float(sum(capacities))

    def choose(self, servers, rng) -> int:
        for i, w in enumerate(self.capacities):
            self._current[i] += w
        idx = max(range(self.n), key=lambda i: self._current[i])
        self._current[idx] -= self._total
        return idx


class LeastConnections(LoadBalancer):
    """Send the request to the server with the fewest active requests."""
    name = "least_connections"

    def choose(self, servers, rng) -> int:
        return min(range(self.n), key=lambda i: (servers[i].connections, i))


class WeightedLeastConnections(LoadBalancer):
    """Least connections, but divided by server capacity (strong servers take more)."""
    name = "weighted_least_connections"

    def choose(self, servers, rng) -> int:
        return min(range(self.n),
                   key=lambda i: (servers[i].connections / servers[i].capacity, i))


class RandomChoice(LoadBalancer):
    """Pick any server at random (a simple baseline)."""
    name = "random"

    def choose(self, servers, rng) -> int:
        return int(rng.integers(0, self.n))


ALGORITHMS: Dict[str, Type[LoadBalancer]] = {
    cls.name: cls
    for cls in (RoundRobin, WeightedRoundRobin, LeastConnections,
                WeightedLeastConnections, RandomChoice)
}

ALGORITHM_LABELS = {
    "round_robin": "Round Robin",
    "weighted_round_robin": "Weighted Round Robin",
    "least_connections": "Least Connections",
    "weighted_least_connections": "Weighted Least Connections",
    "random": "Random",
}


def make_balancer(name: str, capacities: List[float]) -> LoadBalancer:
    if name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm {name!r}. Choose from {list(ALGORITHMS)}")
    return ALGORITHMS[name](len(capacities), capacities)
