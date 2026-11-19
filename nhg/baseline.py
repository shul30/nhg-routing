"""Baseline: the example solution shipped in Solution_Check.xlsm.

The example serves 260 of 261 orders (order 7 is missing). `repaired_example`
inserts each missing order at the cheapest legal position, so the baseline is a
complete, feasible 261-order plan we can benchmark against.
"""
import openpyxl
from nhg.route import evaluate_route


def load_example_sequence(path="data/Solution_Check.xlsm"):
    """Read the example route sequence (order IDs, 0 = depot) from the workbook."""
    ws = openpyxl.load_workbook(path, data_only=True)["ExampleSolution"]
    seq = [int(v) for (v,) in ws.iter_rows(min_row=5, min_col=3, max_col=3, values_only=True)
           if v is not None]
    return seq


def sequence_to_routes(seq):
    routes, cur = [], []
    for o in seq[1:]:
        if o == 0:
            routes.append(cur)
            cur = []
        else:
            cur.append(o)
    return routes


def repaired_example(orders, dist, path="data/Solution_Check.xlsm"):
    """Return (routes, missing, notes). Each missing order goes to the cheapest
    legal position in an existing route of its day; if none, it gets its own route."""
    routes = sequence_to_routes(load_example_sequence(path))
    served = {o for r in routes for o in r}
    missing = sorted(set(orders) - served)
    notes = []
    for m in missing:
        best = None
        for ri, r in enumerate(routes):
            if not r or orders[r[0]].day != orders[m].day:
                continue
            base = evaluate_route(r, orders, dist)[1]
            for pos in range(len(r) + 1):
                cand = r[:pos] + [m] + r[pos:]
                ok, miles, _ = evaluate_route(cand, orders, dist)
                if ok and (best is None or (miles - base, ri, pos) < best[:3]):
                    best = (miles - base, ri, pos, cand)
        if best:
            added, ri, pos, cand = best
            routes[ri] = cand
            notes.append(f"order {m} inserted into route {ri + 1} at position {pos + 1} ({added:+.0f} mi)")
        else:
            routes.append([m])
            notes.append(f"order {m} given its own route")
    return routes, missing, notes
