"""Cloud Load Balancer Simulator - interactive dashboard.

Run with:   streamlit run app.py
"""
import streamlit as st

from simulator import (ALGORITHM_LABELS, ALGORITHMS, PATTERN_DESCRIPTIONS, PATTERNS,
                       SERVER_PRESETS, build_capacities, run_comparison)
from simulator.charts import (metric_bar, queue_timeline_chart, response_cdf_chart,
                              traffic_chart, utilisation_chart)
from simulator.scenarios import best_algorithm

st.set_page_config(page_title="Cloud Load Balancer Simulator", layout="wide")
st.title("Cloud Load Balancer Simulator")
st.caption("Compare load balancing algorithms on the same traffic and see which one "
           "keeps response times low and servers evenly used.")

# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Settings")

    st.subheader("Servers")
    preset = st.selectbox("Server type", list(SERVER_PRESETS),
                          format_func=lambda k: f"{k} - {SERVER_PRESETS[k]}")
    custom_caps = None
    if preset == "custom":
        text = st.text_input("Capacities (comma separated)", "20, 10, 10, 5")
        try:
            custom_caps = [float(x) for x in text.split(",") if x.strip()]
        except ValueError:
            st.error("Please enter numbers separated by commas, e.g. 20, 10, 5")
            st.stop()
        n_servers = len(custom_caps)
    else:
        n_servers = st.slider("Number of servers", 2, 10, 4)
    base_cap = st.number_input("Base capacity (work units / second)", 1.0, 100.0, 10.0,
                               disabled=(preset != "equal"))

    st.subheader("Traffic")
    pattern = st.selectbox("Pattern", PATTERNS)
    st.caption(PATTERN_DESCRIPTIONS[pattern])
    load = st.slider("Average load (share of total capacity)", 0.2, 1.4, 0.85, 0.05,
                     help="1.0 means demand equals total capacity; above 1.0 is overload.")
    duration = st.slider("Duration (seconds)", 60, 900, 300, 30)
    mean_size = st.slider("Average request size (work units)", 0.2, 3.0, 1.0, 0.1)

    st.subheader("Algorithms")
    chosen = st.multiselect("Compare", list(ALGORITHMS), default=list(ALGORITHMS),
                            format_func=lambda k: ALGORITHM_LABELS[k])
    max_queue = st.slider("Queue limit per server", 5, 200, 50,
                          help="Requests arriving at a full server are dropped.")
    seed = st.number_input("Random seed", 0, 9999, 1, help="Same seed = same traffic.")

    st.caption("Results update automatically when you change a setting.")

if not chosen:
    st.warning("Select at least one algorithm in the sidebar.")
    st.stop()

# ------------------------------------------------------------------ run it
capacities = build_capacities(preset, n_servers, custom_caps, base_cap)


@st.cache_data(show_spinner="Simulating...")
def cached_run(pattern, capacities, load, duration, mean_size, chosen, max_queue, seed):
    traffic, results, summary = run_comparison(
        pattern, list(capacities), load, duration, mean_size, list(chosen), max_queue, seed)
    return traffic, results, summary


# Re-runs automatically whenever a setting changes (results are cached).
traffic, results, summary = cached_run(pattern, tuple(capacities), load, duration,
                                       mean_size, tuple(chosen), max_queue, int(seed))

# ----------------------------------------------------------------- results
winner = best_algorithm(summary)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Servers", n_servers, help=f"Capacities: {capacities}")
c2.metric("Requests generated", f"{traffic.total_requests:,}")
c3.metric("Best algorithm", winner)
c4.metric("Overload?", "Yes" if load > 1.0 else "No")

tab_summary, tab_traffic, tab_servers, tab_queue = st.tabs(
    ["Comparison", "Traffic", "Server load", "Queue timeline"])

with tab_summary:
    st.subheader("Results table")
    show = summary.rename(columns={
        "total_requests": "Total requests", "completed": "Completed",
        "dropped": "Dropped", "drop_rate_pct": "Drop rate (%)",
        "avg_response": "Avg response (s)", "p95_response": "95th pct response (s)",
        "max_response": "Max response (s)", "avg_utilisation_pct": "Avg utilisation (%)",
        "max_utilisation_pct": "Busiest server (%)", "fairness_index": "Fairness (0-1)",
        "peak_queue": "Peak queue"})
    st.dataframe(show.round(3))
    st.caption("Fairness uses Jain's index: 1.0 means every server is equally busy "
               "relative to its capacity. The best algorithm has the fewest dropped "
               "requests, then the lowest average response time.")

    left, right = st.columns(2)
    left.pyplot(metric_bar(summary, "avg_response", "Average response time", "seconds"))
    right.pyplot(metric_bar(summary, "p95_response", "95th percentile response time",
                            "seconds"))
    left.pyplot(metric_bar(summary, "dropped", "Dropped requests", "requests"))
    right.pyplot(response_cdf_chart(results))

with tab_traffic:
    st.pyplot(traffic_chart(traffic))

with tab_servers:
    st.pyplot(utilisation_chart(results))
    st.caption("An ideal algorithm keeps all bars of a group at a similar height.")

with tab_queue:
    pick = st.selectbox("Algorithm", list(results),
                        format_func=lambda k: ALGORITHM_LABELS[k])
    st.pyplot(queue_timeline_chart(results[pick]))

st.download_button("Download results as CSV", summary.to_csv().encode("utf-8"),
                   file_name="load_balancer_results.csv", mime="text/csv")
