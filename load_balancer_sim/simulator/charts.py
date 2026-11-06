"""Chart helpers (matplotlib). Each function returns a Figure.

The Streamlit dashboard shows them with st.pyplot(fig); the experiment runner
saves them as PNG files.
"""
from __future__ import annotations

from typing import Dict

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .algorithms import ALGORITHM_LABELS  # noqa: E402
from .metrics import server_utilisation  # noqa: E402


def traffic_chart(traffic) -> Figure:
    fig = Figure(figsize=(8, 3))
    ax = fig.subplots()
    ax.plot(traffic.counts(), color="#4C78A8", lw=1, label="Arrivals per second")
    ax.plot(traffic.rate_profile, color="#E45756", lw=1.5, ls="--", label="Expected rate")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Requests")
    ax.set_title(f"Traffic pattern: {traffic.pattern}")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def metric_bar(summary: pd.DataFrame, column: str, title: str, ylabel: str) -> Figure:
    fig = Figure(figsize=(7, 3.5))
    ax = fig.subplots()
    values = summary[column]
    bars = ax.bar(range(len(values)), values, color="#4C78A8")
    best = int(np.nanargmin(values.to_numpy()))
    bars[best].set_color("#54A24B")
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels([str(i).replace(" ", "\n", 1) for i in values.index], fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    for rect, v in zip(bars, values):
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height(),
                f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    return fig


def utilisation_chart(results: Dict[str, object]) -> Figure:
    """Grouped bars: utilisation of every server under every algorithm."""
    names = list(results)
    n_servers = len(next(iter(results.values())).capacities)
    fig = Figure(figsize=(8, 3.8))
    ax = fig.subplots()
    width = 0.8 / n_servers
    x = np.arange(len(names))
    for s in range(n_servers):
        vals = [100 * server_utilisation(results[n])[s] for n in names]
        ax.bar(x + s * width - 0.4 + width / 2, vals, width,
               label=f"Server {s + 1} (cap {results[names[0]].capacities[s]:g})")
    ax.set_xticks(x)
    ax.set_xticklabels([ALGORITHM_LABELS[n].replace(" ", "\n", 1) for n in names], fontsize=8)
    ax.set_ylabel("Utilisation (%)")
    ax.set_title("Load spread across servers")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def queue_timeline_chart(result) -> Figure:
    fig = Figure(figsize=(8, 3.2))
    ax = fig.subplots()
    tl = result.timeline
    for i in range(len(result.capacities)):
        ax.plot(tl["tick"], tl[f"queue_{i}"], lw=1.2,
                label=f"Server {i + 1} (cap {result.capacities[i]:g})")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Requests waiting")
    ax.set_title(f"Queue length over time - {ALGORITHM_LABELS[result.algorithm]}")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def response_cdf_chart(results: Dict[str, object]) -> Figure:
    fig = Figure(figsize=(8, 3.5))
    ax = fig.subplots()
    for name, res in results.items():
        r = np.sort(res.completed["response"].to_numpy())
        if r.size:
            ax.plot(r, np.arange(1, r.size + 1) / r.size * 100, lw=1.5,
                    label=ALGORITHM_LABELS[name])
    ax.set_xlabel("Response time (seconds)")
    ax.set_ylabel("% of requests finished")
    ax.set_title("Response time distribution (closer to the top-left is better)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig
