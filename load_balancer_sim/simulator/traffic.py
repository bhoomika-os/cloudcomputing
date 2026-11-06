"""Traffic generation.

Time is divided into ticks (1 tick = 1 second). For every tick we produce the
list of request sizes (in "work units") that arrive during that tick.

Four patterns are available:
    steady  - the same number of requests every tick (no randomness in counts)
    poisson - random arrivals, Poisson distributed around a constant rate
    bursty  - quiet periods interrupted by short, intense spikes
    rising  - load grows steadily from light to heavy over the run

The same Traffic object can be replayed against every algorithm, so every
algorithm is compared on exactly the same requests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

PATTERNS = ["steady", "poisson", "bursty", "rising"]

PATTERN_DESCRIPTIONS = {
    "steady": "Constant request rate with no randomness in how many requests arrive.",
    "poisson": "Random arrivals around a constant average rate (typical web traffic).",
    "bursty": "Calm periods interrupted by short, intense traffic spikes (flash crowds).",
    "rising": "Load increases gradually from light to heavy during the run.",
}


@dataclass
class Traffic:
    pattern: str
    duration: int
    arrivals: List[np.ndarray]      # arrivals[t] = array of request sizes at tick t
    rate_profile: np.ndarray        # expected arrivals per tick (for plotting)

    @property
    def total_requests(self) -> int:
        return int(sum(len(a) for a in self.arrivals))

    def counts(self) -> np.ndarray:
        return np.array([len(a) for a in self.arrivals])


def _rate_profile(pattern: str, duration: int, mean_rate: float,
                  rng: np.random.Generator) -> np.ndarray:
    if pattern in ("steady", "poisson"):
        profile = np.full(duration, mean_rate, dtype=float)
    elif pattern == "rising":
        profile = np.linspace(0.3, 1.7, duration) * mean_rate
    elif pattern == "bursty":
        profile = np.full(duration, 0.5, dtype=float)
        pos = int(rng.integers(5, 20))
        while pos < duration:
            length = int(rng.integers(8, 20))
            profile[pos:pos + length] = 3.0
            pos += length + int(rng.integers(30, 60))
        profile = profile / profile.mean() * mean_rate   # keep the average equal
    else:
        raise ValueError(f"Unknown traffic pattern: {pattern!r}")
    return profile


def generate_traffic(pattern: str, duration: int, mean_rate: float,
                     mean_size: float = 1.0, seed: int = 0) -> Traffic:
    """Create a reproducible traffic trace.

    Parameters
    ----------
    pattern    : one of PATTERNS
    duration   : number of ticks (seconds) during which requests arrive
    mean_rate  : average number of requests arriving per tick
    mean_size  : average work units a request needs (exponentially distributed)
    seed       : random seed, same seed gives the same traffic
    """
    if duration <= 0:
        raise ValueError("duration must be positive")
    if mean_rate < 0:
        raise ValueError("mean_rate cannot be negative")
    rng = np.random.default_rng(seed)
    profile = _rate_profile(pattern, duration, mean_rate, rng)

    arrivals: List[np.ndarray] = []
    carry = 0.0
    for t in range(duration):
        if pattern == "steady":
            carry += profile[t]
            n = int(carry)
            carry -= n
        else:
            n = int(rng.poisson(profile[t]))
        sizes = np.clip(rng.exponential(mean_size, size=n), 0.05, None)
        arrivals.append(sizes)
    return Traffic(pattern, duration, arrivals, profile)
