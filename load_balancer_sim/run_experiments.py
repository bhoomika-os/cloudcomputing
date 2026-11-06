"""Run every algorithm on every traffic pattern and save tables and charts.

Usage:
    python run_experiments.py                 # default settings
    python run_experiments.py --load 1.0      # heavier load
    python run_experiments.py --servers 6 --duration 600

Output goes to the results/ folder:
    results/summary_all.csv      every number from every run
    results/<cluster>_<pattern>_*.png   charts for the report
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

from simulator import PATTERNS, build_capacities, run_comparison
from simulator.charts import (metric_bar, response_cdf_chart, traffic_chart,
                              utilisation_chart)
from simulator.scenarios import best_algorithm


def main() -> None:
    p = argparse.ArgumentParser(description="Cloud load balancer experiments")
    p.add_argument("--servers", type=int, default=4, help="number of servers")
    p.add_argument("--load", type=float, default=0.85,
                   help="average load as share of capacity (1.0 = full)")
    p.add_argument("--duration", type=int, default=300, help="seconds of traffic")
    p.add_argument("--max-queue", type=int, default=50, help="queue limit per server")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", default="results")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    all_rows = []
    winners = []

    for cluster in ("equal", "mixed"):
        caps = build_capacities(cluster, args.servers)
        for pattern in PATTERNS:
            traffic, results, summary = run_comparison(
                pattern, caps, load_factor=args.load, duration=args.duration,
                max_queue=args.max_queue, seed=args.seed)

            tag = f"{cluster}_{pattern}"
            traffic_chart(traffic).savefig(f"{args.out}/{tag}_traffic.png", dpi=130)
            metric_bar(summary, "avg_response", "Average response time",
                       "seconds").savefig(f"{args.out}/{tag}_response.png", dpi=130)
            utilisation_chart(results).savefig(f"{args.out}/{tag}_utilisation.png", dpi=130)
            response_cdf_chart(results).savefig(f"{args.out}/{tag}_cdf.png", dpi=130)

            tidy = summary.reset_index()
            tidy.insert(0, "pattern", pattern)
            tidy.insert(0, "cluster", cluster)
            all_rows.append(tidy)
            winners.append((cluster, pattern, best_algorithm(summary)))
            print(f"[{cluster:5s} | {pattern:7s}] best algorithm: {winners[-1][2]}")

    full = pd.concat(all_rows, ignore_index=True)
    full.to_csv(f"{args.out}/summary_all.csv", index=False)

    print("\nBest algorithm per scenario")
    print(pd.DataFrame(winners, columns=["cluster", "pattern", "best"]).to_string(index=False))
    print(f"\nSaved tables and charts to ./{args.out}/")


if __name__ == "__main__":
    main()
