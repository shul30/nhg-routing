"""Rung 1 construction heuristics: Nearest Neighbor and Clarke-Wright Savings.

Both plan each delivery day independently (M1: fixed delivery days) and use
nhg.route.evaluate_route as the only feasibility test, so every route they
return is legal under the Solution_Check.xlsm rules.

Tie-breaking is deterministic (lowest order ID wins), so repeated runs give
identical plans.
"""
from nhg.data import DAYS
from nhg.route import evaluate_route


def _miles(route, orders, dist, **kw):
    return evaluate_route(route, orders, dist, **kw)[1]


# --------------------------------------------------------------------------
# Nearest Neighbor
# --------------------------------------------------------------------------
def nearest_neighbor_day(order_ids, orders, dist, depot="01887", **kw):
    """Start at the depot; repeatedly drive to the closest unserved order that
    keeps the route legal. When nothing fits, close the route and start a new one."""
    unserved = sorted(order_ids)
    routes = []
    while unserved:
        route, here = [], depot
        while True:
            # candidates nearest-first; ties -> lowest order ID
            for o in sorted(unserved, key=lambda k: (dist[here][orders[k].zip], k)):
                if evaluate_route(route + [o], orders, dist, depot=depot, **kw)[0]:
                    route.append(o)
                    unserved.remove(o)
                    here = orders[o].zip
                    break
            else:
                break  # nothing fits: close this route
        routes.append(route)
    return routes


# --------------------------------------------------------------------------
# Clarke-Wright Savings (parallel version)
# --------------------------------------------------------------------------
def savings_day(order_ids, orders, dist, depot="01887", **kw):
    """Start with one route per order. For every pair (i, j) compute
    s(i,j) = d(depot,i) + d(depot,j) - d(i,j). Process pairs from largest saving
    to smallest; merge the routes containing i and j if i and j are at the ends
    of different routes and the merged route is legal."""
    ids = sorted(order_ids)
    route_of = {o: i for i, o in enumerate(ids)}       # order -> route index
    routes = {i: [o] for i, o in enumerate(ids)}
    z = {o: orders[o].zip for o in ids}

    pairs = []
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, j = ids[a], ids[b]
            s = dist[depot][z[i]] + dist[depot][z[j]] - dist[z[i]][z[j]]
            pairs.append((-s, i, j))                   # sort: biggest saving first, then IDs
    pairs.sort()

    for neg_s, i, j in pairs:
        ri, rj = route_of[i], route_of[j]
        if ri == rj:
            continue
        A, B = routes[ri], routes[rj]
        # i and j must be at an end of their routes (interior stops can't be linked)
        if i not in (A[0], A[-1]) or j not in (B[0], B[-1]):
            continue
        # orient so that i is last in A and j is first in B; with symmetric distances
        # reversing a route keeps its mileage but changes its timing, so test all
        # orientations that place i next to j and keep the best legal one
        cands = []
        for a_rev in (False, True):
            AA = A[::-1] if a_rev else A
            if AA[-1] != i:
                continue
            for b_rev in (False, True):
                BB = B[::-1] if b_rev else B
                if BB[0] != j:
                    continue
                for merged in (AA + BB, (AA + BB)[::-1]):
                    ok, miles, _ = evaluate_route(merged, orders, dist, depot=depot, **kw)
                    if ok:
                        cands.append((miles, merged))
        if not cands:
            continue
        miles, merged = min(cands, key=lambda c: (c[0], c[1]))
        routes[ri] = merged
        del routes[rj]
        for o in merged:
            route_of[o] = ri
    return [routes[k] for k in sorted(routes)]


# --------------------------------------------------------------------------
# Weekly wrappers
# --------------------------------------------------------------------------
def plan_week(method, orders, dist, depot="01887", **kw):
    """Run a single-day heuristic for each day. Returns {day: [route, ...]}."""
    plan = {}
    for day in DAYS:
        ids = [o for o in orders if orders[o].day == day]
        plan[day] = method(ids, orders, dist, depot=depot, **kw)
    return plan


def flatten(plan):
    return [r for day in DAYS for r in plan.get(day, [])]
