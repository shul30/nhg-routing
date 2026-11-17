"""Rung 0 benchmark. Usage: python run_benchmark.py"""
import json, math, os, warnings
warnings.filterwarnings("ignore")
from nhg.data import load_orders, load_distances
from nhg.brute_force import pick_instance, enumerate_all

orders, dist = load_orders(), load_distances()
os.makedirs("results", exist_ok=True)

# 1) main instance: 9 stops
stops = pick_instance(orders, dist, size=9, min_depot_miles=130)
res = enumerate_all(stops, orders, dist)
print(f"Instance ({orders[stops[0]].day}, 9 orders):", stops)
for o in stops:
    print(f"  order {o:>3}  zip {orders[o].zip}  cube {orders[o].cube}  {dist['01887'][orders[o].zip]:.0f} mi from depot")
print(f"Total cube: {sum(orders[o].cube for o in stops)} ft3")
import pandas as pd
city = pd.read_excel("data/deliveries.xlsx", "LocationTable", dtype={"ZIP": str}).set_index("ZIP")["CITY"]
print("Cities:", ", ".join(city.get(orders[o].zip, "?") for o in res["optimal_route"]), "(optimal order)")
print(f"Permutations: {res['n_permutations']:,}  feasible: {res['n_feasible']:,}")
print(f"OPTIMAL: {res['optimal_miles']:.0f} miles  route {res['optimal_route']}  "
      f"(ties: {res['n_optimal']})  runtime {res['runtime_s']:.1f}s")

# 2) combinatorial wall: subsets of the same cluster
wall = []
for k in range(5, 10):
    r = enumerate_all(stops[:k], orders, dist)
    wall.append(dict(stops=k, permutations=r["n_permutations"], runtime_s=round(r["runtime_s"], 3)))
per_perm = res["runtime_s"] / res["n_permutations"]
for k in (10, 11, 12, 15):
    wall.append(dict(stops=k, permutations=math.factorial(k),
                     runtime_s=round(math.factorial(k) * per_perm, 1), estimated=True))
print("\nRuntime wall:")
for w in wall:
    est = " (estimated)" if w.get("estimated") else ""
    print(f"  {w['stops']:>2} stops  {w['permutations']:>16,} perms  {w['runtime_s']:>12,.1f}s{est}")

json.dump(dict(instance=stops, result=res, wall=wall), open("results/rung0_bruteforce.json", "w"), indent=2)
print("\nSaved results/rung0_bruteforce.json")
