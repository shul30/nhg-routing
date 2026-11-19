"""One command to reproduce every M1 number.

Usage:  python run.py        (python3 on Mac)

Outputs (results/):
  benchmark_table.csv / .md        one row per method
  schedules/<method>_schedule.csv  driver schedule, every stop
  schedules/<method>_routes.csv    per-route totals (miles, drive/duty hours, overnight rest)
  sequences/<method>.txt           route sequence to paste into Solution_Check.xlsm (column B)
  rung0_bruteforce.json            brute-force benchmark
"""
import json, os, platform, time, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from nhg.data import load_orders, load_distances
from nhg.checker import simulate
from nhg.route import evaluate_route, route_to_sequence
from nhg.brute_force import pick_instance, enumerate_all
from nhg.baseline import repaired_example
from nhg.heuristics import nearest_neighbor_day, savings_day, plan_week, flatten
from nhg.local_search import improve_week, improve_day
from nhg.report import driver_schedule, route_summary, write_csv

orders, dist = load_orders(), load_distances()
cities = pd.read_excel("data/deliveries.xlsx", "LocationTable", dtype={"ZIP": str}) \
           .set_index("ZIP")["CITY"].to_dict()
for d in ("results", "results/schedules", "results/sequences"):
    os.makedirs(d, exist_ok=True)

# ---------------- Rung 0: brute-force calibration ----------------
print("Rung 0: brute force on 9-order instance ...")
inst = pick_instance(orders, dist, size=9, min_depot_miles=130)
bf = enumerate_all(inst, orders, dist)
opt = bf["optimal_miles"]
json.dump(dict(instance=inst, result=bf), open("results/rung0_bruteforce.json", "w"), indent=2)
print(f"  optimum {opt:.0f} mi, {bf['n_permutations']:,} permutations, {bf['runtime_s']:.1f}s\n")


def calib(build):
    routes = build(inst)
    return sum(evaluate_route(r, orders, dist)[1] for r in routes)


# ---------------- Methods ----------------
def m_baseline():
    routes, _, _ = repaired_example(orders, dist)
    return routes

def m_nn():
    return flatten(plan_week(nearest_neighbor_day, orders, dist))

def m_cw():
    return flatten(plan_week(savings_day, orders, dist))

def ls(start_fn, strategy):
    def run():
        plan, _ = improve_week(plan_week(start_fn, orders, dist), orders, dist, strategy=strategy)
        return flatten(plan)
    return run

def ls_calib(start_fn, strategy):
    return lambda ids: improve_day(start_fn(ids, orders, dist), orders, dist, strategy=strategy)[0]

methods = [
    ("baseline_example", "Example solution (+ order 7)", m_baseline, None),
    ("nearest_neighbor", "Nearest Neighbor", m_nn, lambda ids: nearest_neighbor_day(ids, orders, dist)),
    ("clarke_wright", "Clarke-Wright Savings", m_cw, lambda ids: savings_day(ids, orders, dist)),
    ("nn_ls_first", "NN + Local Search (first-improvement)", ls(nearest_neighbor_day, "first"), ls_calib(nearest_neighbor_day, "first")),
    ("nn_ls_best", "NN + Local Search (best-improvement)", ls(nearest_neighbor_day, "best"), ls_calib(nearest_neighbor_day, "best")),
    ("cw_ls_first", "CW + Local Search (first-improvement)", ls(savings_day, "first"), ls_calib(savings_day, "first")),
    ("cw_ls_best", "CW + Local Search (best-improvement)", ls(savings_day, "best"), ls_calib(savings_day, "best")),
]

table = []
base_miles = None
for key, label, build, cal in methods:
    t0 = time.perf_counter()
    routes = build()
    runtime = time.perf_counter() - t0
    seq = route_to_sequence(routes)
    sched, res = driver_schedule(seq, orders, dist, cities)
    rsum = route_summary(res, orders, dist)
    write_csv(f"results/schedules/{key}_schedule.csv", sched)
    write_csv(f"results/schedules/{key}_routes.csv", rsum)
    with open(f"results/sequences/{key}.txt", "w") as f:
        f.write("\n".join(str(x) for x in seq) + "\n")
    if base_miles is None:
        base_miles = res["total_miles"]
    per_day = pd.DataFrame(rsum).groupby("day").size().reindex(["Mon", "Tue", "Wed", "Thu", "Fri"])
    c = cal and calib(cal)
    table.append({
        "method": label,
        "total_miles": round(res["total_miles"]),
        "vs_baseline_pct": round(100 * (res["total_miles"] - base_miles) / base_miles, 1),
        "routes": res["n_routes"],
        "max_routes_per_day": int(per_day.max()),
        "overnight_returns": sum(r["overnight_rest"] for r in rsum),
        "max_drive_h": max(r["drive_h_to_last_stop"] for r in rsum),
        "max_duty_h": max(r["duty_h_to_last_stop"] for r in rsum),
        "runtime_s": round(runtime, 3),
        "rung0_miles": round(c) if c else "",
        "rung0_error_pct": round(100 * (c - opt) / opt, 1) if c else "",
        "feasible": res["feasible"],
    })
    print(f"{label:<40} {res['total_miles']:>7.0f} mi  {res['n_routes']:>3} routes  "
          f"{runtime:6.2f}s  feasible: {res['feasible']}")

df = pd.DataFrame(table)
df.to_csv("results/benchmark_table.csv", index=False)
with open("results/benchmark_table.md", "w") as f:
    f.write(f"Rung 0 optimum on 9-order instance: {opt:.0f} mi. "
            f"Runtimes measured on {platform.platform()}, Python {platform.python_version()}.\n\n")
    try:
        f.write(df.to_markdown(index=False))
    except ImportError:          # to_markdown needs the 'tabulate' package
        f.write(df.to_string(index=False))
    f.write("\n")
print("\nmax_drive_h / max_duty_h: depot departure through the LAST DELIVERY (limits 11 h / 14 h).")
print("overnight_returns: routes where the driver takes the 10-h rest on the way back to the depot.")
print("Saved results/benchmark_table.csv/.md, results/schedules/, results/sequences/")
