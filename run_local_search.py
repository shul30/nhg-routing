"""Rung 2: local search (2-Opt, Relocate, Swap) on top of the Rung 1 heuristics.
Usage: python run_local_search.py"""
import json, os, time, warnings
warnings.filterwarnings("ignore")
from nhg.data import load_orders, load_distances
from nhg.heuristics import nearest_neighbor_day, savings_day, plan_week, flatten
from nhg.local_search import improve_week, improve_day
from nhg.route import evaluate_route, route_to_sequence
from nhg.checker import simulate

orders, dist = load_orders(), load_distances()
os.makedirs("results", exist_ok=True)
starts = {"nearest_neighbor": nearest_neighbor_day, "clarke_wright": savings_day}

bf = json.load(open("results/rung0_bruteforce.json"))
inst, opt = bf["instance"], bf["result"]["optimal_miles"]

summary = {}
print(f"{'method':<34}{'calib (414 opt)':>16}{'miles':>8}{'routes':>8}{'runtime':>9}  moves (2opt/reloc/swap)")
for sname, fn in starts.items():
    for strategy in ("first", "best"):
        name = f"{sname}+ls_{strategy}"
        # calibration
        r9, _ = improve_day(fn(inst, orders, dist), orders, dist, strategy=strategy)
        m9 = sum(evaluate_route(r, orders, dist)[1] for r in r9)
        # full week
        t0 = time.perf_counter()
        start_plan = plan_week(fn, orders, dist)
        plan, st = improve_week(start_plan, orders, dist, strategy=strategy)
        runtime = time.perf_counter() - t0
        seq = route_to_sequence(flatten(plan))
        res = simulate(seq, orders, dist)
        summary[name] = dict(total_miles=res["total_miles"], n_routes=res["n_routes"],
                             runtime_s=round(runtime, 2), feasible=res["feasible"], moves=st,
                             calibration=dict(miles=m9, error_pct=100 * (m9 - opt) / opt))
        with open(f"results/{name}_sequence.txt", "w") as f:
            f.write("\n".join(str(x) for x in seq) + "\n")
        print(f"{name:<34}{m9:>9.0f} ({100*(m9-opt)/opt:4.1f}%){res['total_miles']:>8.0f}"
              f"{res['n_routes']:>8}{runtime:>8.1f}s  {st['2opt']}/{st['relocate']}/{st['swap']}"
              f"   feasible: {res['feasible']}")

json.dump(summary, open("results/rung2_local_search.json", "w"), indent=2)
print("\nSaved results/rung2_local_search.json and results/<method>_sequence.txt")
