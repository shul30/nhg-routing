"""Rung 1: Nearest Neighbor vs. Clarke-Wright Savings.
Usage: python run_heuristics.py"""
import json, os, time, warnings
warnings.filterwarnings("ignore")
from nhg.data import load_orders, load_distances
from nhg.heuristics import nearest_neighbor_day, savings_day, plan_week, flatten
from nhg.route import evaluate_route, route_to_sequence
from nhg.checker import simulate

orders, dist = load_orders(), load_distances()
os.makedirs("results", exist_ok=True)
methods = {"nearest_neighbor": nearest_neighbor_day, "clarke_wright": savings_day}

# ---- 1) calibration on the Rung 0 instance ----
bf = json.load(open("results/rung0_bruteforce.json"))
inst, opt = bf["instance"], bf["result"]["optimal_miles"]
print(f"Calibration on Rung 0 instance ({len(inst)} orders, optimum {opt:.0f} mi)")
calib = {}
for name, fn in methods.items():
    routes = fn(inst, orders, dist)
    miles = sum(evaluate_route(r, orders, dist)[1] for r in routes)
    calib[name] = dict(miles=miles, routes=len(routes), error_pct=100 * (miles - opt) / opt)
    print(f"  {name:<17} {miles:>6.0f} mi  {len(routes)} route(s)  error {calib[name]['error_pct']:5.1f}%")

# ---- 2) full week, 261 orders ----
print("\nFull week (261 orders)")
summary = {}
for name, fn in methods.items():
    t0 = time.perf_counter()
    plan = plan_week(fn, orders, dist)
    runtime = time.perf_counter() - t0
    routes = flatten(plan)
    seq = route_to_sequence(routes)
    res = simulate(seq, orders, dist)          # independent check with the Excel replica
    per_day = {d: dict(routes=len(r), miles=sum(evaluate_route(x, orders, dist)[1] for x in r))
               for d, r in plan.items()}
    summary[name] = dict(total_miles=res["total_miles"], n_routes=res["n_routes"],
                         runtime_s=round(runtime, 3), feasible=res["feasible"],
                         per_day=per_day, calibration=calib[name])
    with open(f"results/{name}_sequence.txt", "w") as f:   # paste into column B of Excel
        f.write("\n".join(str(x) for x in seq) + "\n")
    print(f"  {name:<17} {res['total_miles']:>7.0f} mi  {res['n_routes']:>3} routes  "
          f"{runtime:6.2f}s  checker feasible: {res['feasible']}")
    for d, v in per_day.items():
        print(f"      {d}: {v['routes']:>2} routes  {v['miles']:>6.0f} mi")

json.dump(summary, open("results/rung1_heuristics.json", "w"), indent=2)
print("\nSaved results/rung1_heuristics.json and results/<method>_sequence.txt")
