"""Driver schedules and benchmark tables, built from the Excel-replica checker."""
import csv
from nhg.checker import simulate


def _hhmm(h):
    h = h % 24
    m = int(round(h * 60)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def driver_schedule(seq, orders, dist, cities=None, depot="01887"):
    """One row per stop, using the same timeline as Solution_Check.xlsm."""
    res = simulate(seq, orders, dist, depot_zip=depot)
    rows, R = [], res["rows"]
    route_no, stop_no = 0, 0
    for k, o in enumerate(seq):
        if o == 0:
            if k > 0:  # end of a route: return to depot
                rows.append(dict(route=route_no, stop="return", order="", zip=depot,
                                 city=(cities or {}).get(depot, ""), day="",
                                 arrive=_hhmm(R["M"][k]), depart="", miles_from_prev=R["E"][k],
                                 rest_h=R["N"][k], wait_h=round(R["O"][k], 2)))
            if k < len(seq) - 1:  # start of next route
                route_no += 1
                stop_no = 0
                rows.append(dict(route=route_no, stop="dispatch", order="", zip=depot,
                                 city=(cities or {}).get(depot, ""), day=R["Q"][k + 1],
                                 arrive="", depart=_hhmm(R["P"][k]), miles_from_prev=0,
                                 rest_h=0, wait_h=0))
        else:
            stop_no += 1
            z = orders[o].zip
            rows.append(dict(route=route_no, stop=stop_no, order=o, zip=z,
                             city=(cities or {}).get(z, ""), day=R["Q"][k],
                             arrive=_hhmm(R["M"][k]), depart=_hhmm(R["P"][k]),
                             miles_from_prev=R["E"][k], rest_h=R["N"][k],
                             wait_h=round(R["O"][k], 2)))
    return rows, res


def route_summary(res, orders, dist):
    """Per-route totals. Drive/duty hours are reported two ways:
    *_to_last_stop: from depot departure through the last delivery (the limits that bind:
                    11 h drive / 14 h duty), and total_drive_h including the return leg,
                    on which the driver may take a 10-hour rest (overnight_rest)."""
    from nhg.route import evaluate_route
    out = []
    for i, r in enumerate(res["routes"], 1):
        _, _, info = evaluate_route(r["orders"], orders, dist)
        out.append(dict(route=i, day=r["dispatch_day"], stops=len(r["orders"]),
                        cube=r["cube"], miles=r["miles"],
                        drive_h_to_last_stop=round(info["drive_h"], 2),
                        duty_h_to_last_stop=round(info["duty_h"], 2),
                        total_drive_h=round(r["drive"], 2),
                        overnight_rest=r["brk"] >= 10))
    return out


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
