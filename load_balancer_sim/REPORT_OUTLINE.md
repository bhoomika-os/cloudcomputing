# Project Report Outline: Cloud Load Balancer Simulator

Use this as the skeleton of your report. Put your own name, guide, college and
date on the title page. Charts and tables come from `run_experiments.py`
(the `results/` folder) and from screenshots of the dashboard.

## Title page, certificate, acknowledgement, abstract

**Abstract (about 150 words):** state the problem (uneven load on cloud servers),
what you built (a simulator comparing five algorithms on four traffic patterns),
and the main result (weighted algorithms win when servers differ; Least
Connections wins when servers are equal).

## Chapter 1: Introduction
- 1.1 Cloud computing and scalability in brief
- 1.2 What a load balancer is
- 1.3 Problem statement
- 1.4 Objectives
- 1.5 Scope and limitations (see README section 9)

## Chapter 2: Literature Review / Background
- Static vs dynamic load balancing
- Round robin, weighted round robin, least connections, random (describe each)
- Performance metrics used in cloud systems (response time, throughput, fairness)
- Existing simulators (for example CloudSim) and why a lightweight custom one was built

## Chapter 3: System Design
- 3.1 Architecture (traffic generator -> load balancer -> servers -> metrics -> dashboard)
- 3.2 Server model (capacity, queue, drop rule)
- 3.3 Traffic model (four patterns; exponential request sizes)
- 3.4 Algorithms (flowchart or pseudocode for each; see `simulator/algorithms.py`)
- 3.5 Simulation loop (the four tick steps in README section 4)
- 3.6 Metrics and how each is calculated (include the Jain fairness formula)

Suggested diagrams: block diagram of the architecture; flowchart of one simulation tick.

## Chapter 4: Implementation
- 4.1 Technology stack: Python, NumPy, Pandas, Matplotlib, Streamlit
- 4.2 Module-by-module description (use the structure table in README)
- 4.3 Dashboard screenshots (settings sidebar, comparison table, server load tab, queue tab)
- 4.4 How to run (short version of README sections 1 and 2)

## Chapter 5: Testing
- 5.1 Unit tests: list the test groups (traffic, algorithms, simulation, metrics) and that all 24 pass
- 5.2 Sanity checks: every request is either completed or dropped; utilisation never exceeds 100%; same seed gives same results
- 5.3 Expected-behaviour tests: weighted beats plain round robin on mixed servers; least connections beats random on equal servers

## Chapter 6: Experiments and Results
- 6.1 Experiment setup: 4 servers, load 0.85, 300 seconds, seed 1, queue limit 50
- 6.2 Equal servers: table and charts for the four traffic patterns
- 6.3 Mixed servers (20, 10, 10, 5): table and charts for the four patterns
- 6.4 Effect of load level: rerun with `--load 0.5`, `0.85` and `1.1` and compare
- 6.5 Discussion: why weighted algorithms help, why Round Robin overloads the weak server, what bursts do to queues
- 6.6 Summary table: best algorithm per scenario (printed at the end of `run_experiments.py`)

## Chapter 7: Conclusion and Future Work
- Conclusions (one per finding)
- Future work: server failures and health checks, network delay, sticky sessions, more algorithms (power of two choices), replaying real web server logs

## References
Add the sources you actually read, such as textbook chapters on cloud computing,
the Nginx documentation on upstream load balancing, and R. Jain's paper on the
fairness index.

## Appendix
- A: Full source code listing (or link to the folder)
- B: Complete results table (`results/summary_all.csv`)
- C: Dashboard screenshots
