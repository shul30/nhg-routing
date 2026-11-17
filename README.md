# NHG Routing – IE 7200 Team 2

## Setup
Put `deliveries.xlsx`, `distances.xlsx`, `Solution_Check.xlsm` in `data/`. Requires Python 3.10+, pandas, openpyxl.

## Commands (run from this folder)
- `PYTHONPATH=. python validate.py` – checker replica vs. Excel macro output (example solution)
- `PYTHONPATH=. python tests/test_route_vs_checker.py` – fast route check vs. full checker, 20,000 random routes
- `PYTHONPATH=. python run_benchmark.py` – Rung 0 brute-force benchmark → `results/rung0_bruteforce.json`

## Modules
- `nhg/data.py` – loads orders and distance matrix
- `nhg/checker.py` – Python replica of Solution_Check.xlsm (whole plan)
- `nhg/route.py` – fast single-route feasibility + miles (used by all algorithms)
- `nhg/brute_force.py` – Rung 0 exhaustive enumeration
