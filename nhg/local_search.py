"""Rung 2 local search: 2-Opt, Relocate and Swap on a single day's routes.

Every candidate route is checked with nhg.route.evaluate_route, so the plan stays
legal after every accepted move. Distances are symmetric, but timing is not
(the first stop is reached at 8:00 AM), so reversed segments are re-checked.

strategy="first": apply the first improving move found, then rescan.
strategy="best":  scan every move, apply the single best one, then rescan.
Enumeration order is fixed, so results are deterministic.
"""
from nhg.route import evaluate_route

EPS = 1e-9


def _cost(route, orders, dist, cache, **kw):
    """Miles of a route, or None if illegal. Empty route = 0 miles."""
    if not route:
        return 0.0
    key = tuple(route)
    if key not in cache:
        ok, miles, _ = evaluate_route(route, orders, dist, **kw)
        cache[key] = miles if ok else None
    return cache[key]


def _moves(routes):
    """Yield (name, a, b, new_route_a, new_route_b). b is None for single-route moves."""
    R = len(routes)
    # 2-Opt within a route
    for a in range(R):
        r = routes[a]
        for i in range(len(r) - 1):
            for j in range(i + 1, len(r)):
                yield "2opt", a, None, r[:i] + r[i:j + 1][::-1] + r[j + 1:], None
    # Relocate one order (within the same route or to another route)
    for a in range(R):
        ra = routes[a]
        for i, o in enumerate(ra):
            rest = ra[:i] + ra[i + 1:]
            for b in range(R):
                if b == a:
                    for p in range(len(rest) + 1):
                        if p != i:
                            yield "relocate", a, None, rest[:p] + [o] + rest[p:], None
                else:
                    rb = routes[b]
                    for p in range(len(rb) + 1):
                        yield "relocate", a, b, rest, rb[:p] + [o] + rb[p:]
    # Swap two orders in different routes
    for a in range(R):
        for b in range(a + 1, R):
            ra, rb = routes[a], routes[b]
            for i in range(len(ra)):
                for j in range(len(rb)):
                    na, nb = ra[:], rb[:]
                    na[i], nb[j] = rb[j], ra[i]
                    yield "swap", a, b, na, nb


def improve_day(routes, orders, dist, strategy="first", **kw):
    """Return (improved_routes, stats). Input routes must be legal."""
    routes = [list(r) for r in routes if r]
    cache = {}
    cost = [_cost(r, orders, dist, cache, **kw) for r in routes]
    stats = {"2opt": 0, "relocate": 0, "swap": 0, "passes": 0}
    while True:
        stats["passes"] += 1
        best = None
        for name, a, b, na, nb in _moves(routes):
            ca = _cost(na, orders, dist, cache, **kw)
            if ca is None:
                continue
            if b is None:
                delta = ca - cost[a]
            else:
                cb = _cost(nb, orders, dist, cache, **kw)
                if cb is None:
                    continue
                delta = ca + cb - cost[a] - cost[b]
            if delta < -EPS and (best is None or delta < best[0] - EPS):
                best = (delta, name, a, b, na, nb)
                if strategy == "first":
                    break
        if best is None:
            break
        delta, name, a, b, na, nb = best
        routes[a] = na
        cost[a] = _cost(na, orders, dist, cache, **kw)
        if b is not None:
            routes[b] = nb
            cost[b] = _cost(nb, orders, dist, cache, **kw)
        stats[name] += 1
        keep = [k for k, r in enumerate(routes) if r]          # drop emptied routes
        routes, cost = [routes[k] for k in keep], [cost[k] for k in keep]
    return routes, stats


def improve_week(plan, orders, dist, strategy="first", **kw):
    """plan: {day: [routes]} -> (improved plan, combined stats)."""
    out, total = {}, {"2opt": 0, "relocate": 0, "swap": 0, "passes": 0}
    for day, routes in plan.items():
        out[day], s = improve_day(routes, orders, dist, strategy=strategy, **kw)
        for k in total:
            total[k] += s[k]
    return out, total
