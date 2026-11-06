# Cloud Load Balancer Simulator

A software simulation that compares **load balancing algorithms** on identical
traffic and shows which one gives the best response time, the fewest dropped
requests, and the most even use of servers.

No cloud account, no hardware, no cost. Everything runs on your own computer.

---

## 1. Setup (about 5 minutes)

You need **Python 3.9 or newer**. Check with `python --version` (or `python3 --version`).

```bash
# 1. open a terminal inside this folder, then (optional but recommended):
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

# 2. install the libraries
pip install -r requirements.txt
```

## 2. Run it

### Interactive dashboard (use this for your demo)

```bash
streamlit run app.py
```

Your browser opens automatically. Use the sidebar to choose the number and type
of servers, traffic pattern, load level and algorithms. Results update as you
change settings. The tabs show a comparison table, traffic chart, load on each
server, and queue length over time. You can download the results as CSV.

### Batch experiments (use this to get numbers and charts for your report)

```bash
python run_experiments.py
```

Runs every algorithm on every traffic pattern, for both equal and mixed servers,
and saves everything to the `results/` folder (`summary_all.csv` plus PNG charts).
Options: `--servers 6 --load 1.0 --duration 600 --max-queue 50 --seed 1`.

### Tests

```bash
python -m unittest discover -s tests -v
```

24 tests check the traffic generator, every algorithm, and the simulation rules.

---

## 3. Project structure

```
load_balancer_sim/
├── app.py                  Streamlit dashboard
├── run_experiments.py      Command-line experiments, saves CSV and charts
├── requirements.txt
├── simulator/
│   ├── traffic.py          Generates request traffic (4 patterns)
│   ├── algorithms.py       The 5 load balancing algorithms
│   ├── engine.py           The simulation loop (servers, queues, time)
│   ├── metrics.py          Response time, utilisation, fairness
│   ├── scenarios.py        Server presets and "run all algorithms" helper
│   └── charts.py           Matplotlib charts
├── tests/test_simulator.py
├── results/                Sample output from run_experiments.py
└── REPORT_OUTLINE.md       Chapter-by-chapter outline for your project report
```

---

## 4. How the simulation works

Time moves in steps of **1 second (a "tick")**.

1. **Requests arrive.** Each request needs some amount of work (average 1 work
   unit, random size). The load balancer picks a server for each one. If that
   server's queue is full, the request is **dropped**.
2. **Servers work.** Every server processes work units each second equal to its
   **capacity** (for example 20, 10 or 5 units per second), oldest request first.
   Big requests can take several seconds.
3. **We record** queue lengths and how busy each server was.
4. After the traffic ends, the simulation keeps going until all queues are empty,
   so every accepted request gets a **response time** (finish time minus arrival time).

The **same traffic** is replayed for every algorithm, so the comparison is fair.

**Load factor:** average demand as a share of total capacity. 0.5 = half loaded,
1.0 = exactly at capacity, above 1.0 = overloaded.

## 5. The algorithms

| Algorithm | Idea | Strength | Weakness |
|---|---|---|---|
| Round Robin | Servers take turns in a fixed circle | Simple, fair when servers are equal | Ignores server power and current load |
| Weighted Round Robin | Turns in proportion to capacity (smooth method as in Nginx) | Handles unequal servers | Still ignores current queue length |
| Least Connections | Send to the server with the fewest active requests | Adapts to current load | Treats a weak and a strong server as the same |
| Weighted Least Connections | Fewest requests relative to capacity | Adapts to load and server power | Slightly more complex |
| Random | Pick any server | Very simple baseline | Uneven by chance |

## 6. Traffic patterns

- **steady**: the same number of requests every second
- **poisson**: random arrivals around an average rate (typical web traffic)
- **bursty**: quiet periods broken by short, intense spikes (flash crowds)
- **rising**: load grows from light to heavy during the run

## 7. Metrics

- **Average / 95th percentile / maximum response time** (seconds)
- **Dropped requests** and drop rate (%)
- **Utilisation** of each server (share of its capacity actually used)
- **Fairness index** (Jain's index): 1.0 = all servers equally busy relative to
  their capacity; 1/n = one server does everything
- **Peak queue** length

---

## 8. Sample findings (default settings: 4 servers, load 0.85, 300 s, seed 1)

- **Equal servers, random traffic:** Least Connections gave the lowest average
  response time (0.63 s) against Round Robin (0.72 s) and Random (0.93 s).
- **Mixed servers (20, 10, 10, 5):** plain Round Robin and Random overloaded the
  weak server and **dropped over 1,300 requests**, with average response above
  2.4 s. Weighted Round Robin dropped none and averaged about 0.7 s;
  Weighted Least Connections was best at about 0.6 s.
- **Bursty traffic:** every algorithm drops many requests during spikes because
  queues fill up. On mixed servers the weighted algorithms still give clearly lower
  response times than plain Round Robin and Random.
- **Overall lesson:** when servers differ in power, the algorithm must know
  about capacity. When servers are identical, looking at current load (Least
  Connections) helps most.

Your own runs will give the same numbers if you keep the same seed.

---

## 9. Limitations (mention these in your report)

- It is a simulation: it does not model network delay, failures or health checks.
- Request size and server speed are simplified into "work units".
- Servers process requests one at a time in order (first in, first out).
- One load balancer only; no sticky sessions or caching.

## 10. Ideas to extend it

- Add a new algorithm in `simulator/algorithms.py` (for example "power of two
  choices": pick two random servers and use the less busy one), then add it to
  the `ALGORITHMS` and `ALGORITHM_LABELS` dictionaries. It appears in the
  dashboard automatically.
- Add server failures (a server that stops for 30 seconds).
- Add a new traffic pattern in `simulator/traffic.py`.

---

## 11. Likely viva questions

**What is a load balancer and why is it needed?**
It spreads incoming requests over several servers so no server is overloaded,
response times stay low, and the system keeps working if one server is slow.

**Why simulate instead of using a real cloud?**
It is free, repeatable, safe, and lets us test overload and bursts that would be
risky or costly on real servers.

**Why did Round Robin do badly on mixed servers?**
It sends equal numbers of requests to a weak and a strong server, so the weak
server's queue grows and requests get dropped while strong servers sit partly idle.

**What is the difference between Round Robin and Least Connections?**
Round Robin is static: it follows a fixed order. Least Connections is dynamic:
it looks at the current number of active requests on each server.

**What does the fairness index show?**
How evenly servers are used relative to their capacity (1.0 is perfectly even).

**Why use the same traffic for all algorithms?**
So differences in results come from the algorithm only, not from luck.

**What is a dropped request?**
A request that arrived when the chosen server's queue was full, so it was rejected.

**What is the 95th percentile response time?**
95% of requests finished faster than this value. It shows how bad the slow
requests are, which the average can hide.

**What does the seed do?**
It fixes the random numbers, so the same settings always give the same results.

**How could this be improved?**
Add failures and health checks, network delay, sticky sessions, and test with real traffic logs.
