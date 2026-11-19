"""Baseline: example solution from Solution_Check.xlsm, repaired to serve all 261 orders.
Usage: python run_baseline.py"""
import json, os, warnings
warnings.filterwarnings("ignore")
from nhg.data import load_orders, load_distances
from nhg.baseline import load_example_sequence, repaired_example
from nhg.route import route_to_sequence
from nhg.checker import simulate

orders, dist = load_orders(), load_distances()
os.makedirs("results", exist_ok=True)

orig = simulate(load_example_sequence(), orders, dist)
print(f"Example as shipped:  {orig['total_miles']:.0f} mi  {orig['n_routes']} routes  "
      f"feasible: {orig['feasible']}  (stops ok: {orig['stops_ok']})")

routes, missing, notes = repaired_example(orders, dist)
seq = route_to_sequence(routes)
res = simulate(seq, orders, dist)
print(f"Missing orders: {missing}")
for n in notes:
    print("  " + n)
print(f"Repaired baseline:   {res['total_miles']:.0f} mi  {res['n_routes']} routes  "
      f"feasible: {res['feasible']}")

with open("results/baseline_sequence.txt", "w") as f:
    f.write("\n".join(str(x) for x in seq) + "\n")
json.dump(dict(total_miles=res["total_miles"], n_routes=res["n_routes"], feasible=res["feasible"],
               missing_orders=missing, repair=notes),
          open("results/baseline.json", "w"), indent=2)
print("Saved results/baseline.json and results/baseline_sequence.txt")
