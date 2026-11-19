# AI Usage Log

AI tools are used under Section 5 of the project guidelines. Every AI-generated
component is verified before use; the verification is recorded below.

| Date | Component | Tool | What AI generated | How we verified it |
|---|---|---|---|---|
| 2026-11-16 | `nhg/checker.py` | Claude | Extracted the VBA macro from Solution_Check.xlsm and rewrote its logic in Python | `validate.py`: matches the Excel macro's output on all 1,560 cells of the example solution (12,303 mi, 51 routes) |
| 2026-11-16 | `nhg/data.py` | Claude | Loader for deliveries.xlsx and distances.xlsx | Used by all checks in this log; order count (261) and matrix size (123×123) confirmed |
| 2026-11-16 | `nhg/route.py` | Claude | Fast single-route feasibility and mileage check | `tests/test_route_vs_checker.py`: agrees with checker.py on 20,000 random routes (9,164 feasible, 10,836 infeasible) |
| 2026-11-16 | `nhg/brute_force.py`, `run_benchmark.py` | Claude | Rung 0 enumeration and instance-selection rule | All 362,880 permutations evaluated; optimum 414 mi reproduced on two machines |
| 2026-11-16 | Repo setup, README | Claude | Folder structure, README, .gitignore | All three checks run on macOS (Anaconda Python 3.13); .gitignore confirmed to exclude data/ in the published repo. README run commands to be corrected for Windows |
| 2026-11-16 | `nhg/heuristics.py`, `run_heuristics.py` | Claude | Nearest Neighbor and Clarke-Wright Savings (per day, deterministic tie-breaking) | Both full-week plans pass checker.py on all flags (261 stops); calibration vs. Rung 0 optimum; equivalence test extended to 30,000 routes of 1–20 stops |
| 2026-11-16 | `nhg/baseline.py`, `run_baseline.py` | Claude | Reads the example solution from Solution_Check.xlsm and inserts missing order 7 at its cheapest legal position | Original reproduces 12,303 mi / 51 routes; repaired plan passes checker.py on all flags (12,301 mi). The −2 mi insertion traced to a triangle-inequality violation in the distance matrix (21,344 such triples found) |
| 2026-11-18 | `nhg/local_search.py`, `run_local_search.py` | Claude | 2-Opt, Relocate and Swap local search with first- and best-improvement strategies | All four plans pass checker.py on all flags (261 stops); every start reaches the 414-mi optimum on the Rung 0 instance |
| 2026-11-18 | `run.py`, `nhg/report.py` | Claude | One-command reproduction: benchmark table, driver schedules, route summaries, Excel sequences | All 7 methods reproduce prior results exactly; schedules generated from checker.py's timeline (matches Excel); all plans feasible |

## Findings from verification
- The example solution in Solution_Check.xlsm serves 260 of 261 orders (order 7 is missing), so it fails the stop-count check.
- The macro's "Operating Hours" and "On-duty Hours" flags always return Feasible due to how they are coded; time windows and duty limits are enforced only indirectly through the day-of-delivery check.


