"""Unit tests. Run from the project folder with:

    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator import (ALGORITHMS, PATTERNS, build_capacities, generate_traffic,  # noqa: E402
                       jain_fairness, make_balancer, run_comparison, simulate)
from simulator.engine import Server  # noqa: E402


def fake_servers(capacities, connections=None):
    servers = [Server(i, c, 50) for i, c in enumerate(capacities)]
    if connections:
        for s, k in zip(servers, connections):
            for _ in range(k):
                s.queue.append([0, 0, 1.0])
    return servers


class TrafficTests(unittest.TestCase):
    def test_same_seed_same_traffic(self):
        a = generate_traffic("poisson", 100, 5, seed=3)
        b = generate_traffic("poisson", 100, 5, seed=3)
        self.assertTrue(np.array_equal(a.counts(), b.counts()))

    def test_different_seed_differs(self):
        a = generate_traffic("poisson", 100, 5, seed=3)
        b = generate_traffic("poisson", 100, 5, seed=4)
        self.assertFalse(np.array_equal(a.counts(), b.counts()))

    def test_average_rate_is_respected(self):
        for pattern in PATTERNS:
            t = generate_traffic(pattern, 2000, 8.0, seed=1)
            self.assertAlmostEqual(t.counts().mean(), 8.0, delta=0.8, msg=pattern)

    def test_steady_is_constant(self):
        t = generate_traffic("steady", 100, 4.0)
        self.assertTrue(np.all(t.counts() == 4))

    def test_bursty_has_spikes(self):
        t = generate_traffic("bursty", 400, 5.0, seed=2)
        self.assertGreater(t.counts().max(), 2 * t.counts().mean())

    def test_rising_increases(self):
        t = generate_traffic("rising", 600, 6.0, seed=2)
        c = t.counts()
        self.assertGreater(c[-100:].mean(), c[:100].mean())

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            generate_traffic("nope", 10, 1)
        with self.assertRaises(ValueError):
            generate_traffic("steady", 0, 1)


class AlgorithmTests(unittest.TestCase):
    def test_round_robin_cycles(self):
        lb = make_balancer("round_robin", [10, 10, 10])
        servers = fake_servers([10, 10, 10])
        picks = [lb.choose(servers, None) for _ in range(6)]
        self.assertEqual(picks, [0, 1, 2, 0, 1, 2])

    def test_weighted_round_robin_matches_weights(self):
        caps = [20, 10, 5]
        lb = make_balancer("weighted_round_robin", caps)
        servers = fake_servers(caps)
        picks = [lb.choose(servers, None) for _ in range(350)]
        counts = [picks.count(i) for i in range(3)]
        self.assertEqual(counts, [200, 100, 50])

    def test_least_connections_picks_emptiest(self):
        lb = make_balancer("least_connections", [10, 10, 10])
        servers = fake_servers([10, 10, 10], connections=[5, 2, 7])
        self.assertEqual(lb.choose(servers, None), 1)

    def test_weighted_least_connections_considers_capacity(self):
        lb = make_balancer("weighted_least_connections", [20, 5])
        # server 0: 6/20 = 0.3, server 1: 2/5 = 0.4  -> server 0 is relatively freer
        servers = fake_servers([20, 5], connections=[6, 2])
        self.assertEqual(lb.choose(servers, None), 0)

    def test_random_stays_in_range(self):
        lb = make_balancer("random", [10, 10, 10])
        rng = np.random.default_rng(0)
        servers = fake_servers([10, 10, 10])
        picks = {lb.choose(servers, rng) for _ in range(200)}
        self.assertEqual(picks, {0, 1, 2})

    def test_unknown_algorithm(self):
        with self.assertRaises(ValueError):
            make_balancer("magic", [10])


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.caps = build_capacities("mixed", 4)
        self.traffic = generate_traffic("poisson", 200, 0.8 * sum(self.caps), seed=5)

    def test_every_request_is_accounted_for(self):
        for name in ALGORITHMS:
            r = simulate(self.traffic, self.caps, name, max_queue=30, seed=1)
            self.assertEqual(len(r.completed) + r.dropped, r.total_requests, name)
            self.assertEqual(r.total_requests, self.traffic.total_requests, name)

    def test_utilisation_never_exceeds_capacity(self):
        for name in ALGORITHMS:
            r = simulate(self.traffic, self.caps, name, seed=1)
            util_cols = [c for c in r.timeline.columns if c.startswith("util_")]
            self.assertLessEqual(r.timeline[util_cols].to_numpy().max(), 1.0 + 1e-9, name)

    def test_response_time_is_positive_and_finish_after_arrival(self):
        r = simulate(self.traffic, self.caps, "round_robin", seed=1)
        self.assertTrue((r.completed["response"] > 0).all())
        self.assertTrue((r.completed["finish"] > r.completed["arrival"]).all())

    def test_simulation_is_deterministic(self):
        a = simulate(self.traffic, self.caps, "random", seed=9).summary
        b = simulate(self.traffic, self.caps, "random", seed=9).summary
        self.assertEqual(a, b)

    def test_light_load_has_no_drops_and_fast_responses(self):
        caps = [10, 10, 10, 10]
        t = generate_traffic("steady", 200, 0.3 * sum(caps), seed=1)
        r = simulate(t, caps, "least_connections", seed=1)
        self.assertEqual(r.dropped, 0)
        self.assertLess(r.summary["avg_response"], 1.0)

    def test_overload_causes_drops(self):
        caps = [10, 10]
        t = generate_traffic("steady", 200, 1.6 * sum(caps), seed=1)
        r = simulate(t, caps, "round_robin", max_queue=20, seed=1)
        self.assertGreater(r.dropped, 0)

    def test_weighted_beats_plain_round_robin_on_mixed_servers(self):
        _, _, summary = run_comparison("poisson", [20, 10, 10, 5], load_factor=0.85,
                                       duration=300, seed=1,
                                       algorithms=["round_robin", "weighted_round_robin"])
        rr = summary.loc["Round Robin"]
        wrr = summary.loc["Weighted Round Robin"]
        self.assertLess(wrr["avg_response"], rr["avg_response"])
        self.assertGreaterEqual(wrr["fairness_index"], rr["fairness_index"])

    def test_least_connections_beats_random_on_equal_servers(self):
        _, _, summary = run_comparison("poisson", [10, 10, 10, 10], load_factor=0.85,
                                       duration=300, seed=1,
                                       algorithms=["least_connections", "random"])
        self.assertLess(summary.loc["Least Connections", "avg_response"],
                        summary.loc["Random", "avg_response"])

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            simulate(self.traffic, [10, 0], "round_robin")


class MetricTests(unittest.TestCase):
    def test_fairness_bounds(self):
        self.assertAlmostEqual(jain_fairness([5, 5, 5, 5]), 1.0)
        self.assertAlmostEqual(jain_fairness([10, 0, 0, 0]), 0.25)
        self.assertTrue(0.25 <= jain_fairness([1, 2, 3, 4]) <= 1.0)

    def test_capacity_presets(self):
        self.assertEqual(build_capacities("equal", 3), [10.0, 10.0, 10.0])
        self.assertEqual(build_capacities("mixed", 4), [20.0, 10.0, 10.0, 5.0])
        self.assertEqual(build_capacities("custom", 0, [3, 4]), [3.0, 4.0])
        with self.assertRaises(ValueError):
            build_capacities("custom", 2)


if __name__ == "__main__":
    unittest.main()
