"""Fast single-day route check, used inside heuristics and brute force.

Encodes how Solution_Check.xlsm treats a route that serves one day's orders:
  - truck reaches the first stop at exactly 8:00 AM (clocks start at depot departure)
  - every delivery must finish by 6:00 PM
  - cumulative drive <= 11 h and on-duty <= 14 h up to the last delivery
  - total cube <= capacity
  - the return leg to the depot is unconstrained (driver may rest on the way back)
Validated against nhg.checker.simulate (see tests/test_route_vs_checker.py).
"""
from nhg.checker import unload_hours, SPEED, DRIVE_MAX, DUTY_MAX, OPEN, CLOSE

EPS = 1e-9


def evaluate_route(route, orders, dist, depot="01887", capacity=3200, rate=0.03):
    """route: list of order IDs (no depot zeros). Returns (feasible, miles, info)."""
    if not route:
        return True, 0.0, {}
    if sum(orders[o].cube for o in route) > capacity:
        return False, None, {"reason": "capacity"}
    day = orders[route[0]].day
    if any(orders[o].day != day for o in route):
        return False, None, {"reason": "mixed days"}

    prev = depot
    miles = 0.0
    t = OPEN
    drive = duty = 0.0
    for k, o in enumerate(route):
        z = orders[o].zip
        d = dist[prev][z]
        miles += d
        h = d / SPEED
        drive += h
        duty += h
        if drive > DRIVE_MAX + EPS or duty > DUTY_MAX + EPS:
            return False, None, {"reason": "hours", "stop": k}
        if k > 0:
            t += h
        u = unload_hours(orders[o].cube, rate)
        if t + u > CLOSE + EPS or duty + u > DUTY_MAX + EPS:
            return False, None, {"reason": "window/duty", "stop": k}
        t += u
        duty += u
        prev = z
    miles += dist[prev][depot]
    return True, miles, {"drive_h": drive, "duty_h": duty, "last_departure": t}


def route_to_sequence(routes):
    """[[85, 87], [76]] -> [0, 85, 87, 0, 76, 0] (format for the Excel tool)."""
    seq = [0]
    for r in routes:
        seq += list(r) + [0]
    return seq
