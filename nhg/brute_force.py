"""Rung 0: exhaustive enumeration on a tiny single-van, single-day instance."""
import itertools, math, time
from nhg.route import evaluate_route
from nhg.data import DAYS


def pick_instance(orders, dist, size=9, min_depot_miles=130, depot="01887", capacity=3200, days=DAYS):
    """Deterministic rule: consider stores at least `min_depot_miles` from the depot
    (long-haul routes, where the hours-of-service and time-window rules bind).
    For each day and each such store, form a group of that store plus its size-1
    nearest same-day stores (distinct zips). Return the most compact group
    (smallest sum of seed-to-member miles) that fits in one van."""
    best = None
    for day in days:
        pool = {}
        for o in sorted(orders):
            od = orders[o]
            if od.day == day and od.zip not in pool and dist[depot][od.zip] >= min_depot_miles:
                pool[od.zip] = o
        for z in pool:
            near = sorted(pool, key=lambda y: (dist[z][y], y))[:size]
            grp = sorted(pool[y] for y in near)
            if len(grp) < size or sum(orders[g].cube for g in grp) > capacity:
                continue
            spread = sum(dist[z][y] for y in near)
            if best is None or spread < best[0]:
                best = (spread, day, grp)
    return best[2]


def enumerate_all(stops, orders, dist):
    t0 = time.perf_counter()
    best_miles, best_routes, n_feasible = math.inf, [], 0
    for perm in itertools.permutations(stops):
        ok, miles, _ = evaluate_route(list(perm), orders, dist)
        if not ok:
            continue
        n_feasible += 1
        if miles < best_miles - 1e-9:
            best_miles, best_routes = miles, [list(perm)]
        elif abs(miles - best_miles) < 1e-9:
            best_routes.append(list(perm))
    return dict(optimal_miles=best_miles, optimal_route=best_routes[0],
                n_optimal=len(best_routes), n_permutations=math.factorial(len(stops)),
                n_feasible=n_feasible, runtime_s=time.perf_counter() - t0)
