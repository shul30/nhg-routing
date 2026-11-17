"""Python replica of the Solution_Check.xlsm macro (Module1.Button1_Click).

Input: a flat sequence of order IDs with 0 = depot, e.g. [0, 85, 87, 0, 76, 120, 0].
It reproduces the macro's timeline row by row, so that a plan
that is feasible here is feasible in the Excel tool.
"""
import math

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
SPEED, DRIVE_MAX, DUTY_MAX, REST = 40.0, 11.0, 14.0, 10.0
OPEN, CLOSE = 8.0, 18.0


def _next_day(d):
    return DAYS[(DAYS.index(d) + 1) % 5] if d in DAYS else d


def _tod(h):
    """Time-of-day as Excel stores it after Format(...,'HH:MM:SS'): mod 24, whole seconds."""
    s = round((h % 24) * 3600)
    return (s % 86400) / 3600


def _wait_to_8(t):
    """VBA DateDiff('n', t, 8:00) / 60  (minute-boundary count, can be negative)."""
    return (480 - math.floor(t * 60 + 1e-9)) / 60


def unload_hours(cube, rate=0.03):
    u = cube * rate / 60
    return 0.5 if 0 < u < 0.5 else u


def simulate(seq, orders, dist, depot_zip="01887", capacity=3200, rate=0.03):
    n = len(seq)
    zip_ = [depot_zip if o == 0 else orders[o].zip for o in seq]
    D = ["(Depot)" if o == 0 else orders[o].day for o in seq]
    H = [0 if o == 0 else orders[o].cube for o in seq]
    J = [0.0 if o == 0 else unload_hours(orders[o].cube, rate) for o in seq]
    E = [0.0] + [dist[zip_[k - 1]][zip_[k]] for k in range(1, n)]
    F = [e / SPEED for e in E]
    M, N, O, P, Q = [0.0] * n, [0] * n, [0.0] * n, [0.0] * n, [None] * n

    P[0] = M[0] = _tod(OPEN - (F[1] if n > 1 else 0))
    Q[0] = D[0]
    if n > 1:
        Q[1] = D[1]
    cdrive = cduty = 0.0

    for i in range(1, n):
        dt, prev_dep = F[i], P[i - 1]
        if seq[i] == 0:  # back at depot
            brk = cdrive + dt > DRIVE_MAX or cduty + dt > DUTY_MAX
            N[i] = 10 if brk else 0
            M[i] = _tod(prev_dep + dt + (REST if brk else 0))
            cdrive = cduty = 0.0
            nxt = F[i + 1] if i + 1 < n else 0.0
            P[i] = _tod(OPEN - nxt)
            Q[i] = D[i]
            if i + 1 < n:
                Q[i + 1] = D[i + 1]
        elif cdrive + dt > DRIVE_MAX or cduty + dt > DUTY_MAX:  # rest taken mid-leg
            until = DRIVE_MAX - cdrive if cdrive + dt > DRIVE_MAX else DUTY_MAX - cduty
            after = dt - until
            N[i] = 10
            arr = M[i] = _tod(prev_dep + dt + REST)
            cdrive = after
            if not (OPEN <= arr <= CLOSE):
                w = _wait_to_8(arr)
                O[i] = w
                P[i] = _tod(arr + J[i] + w)
                cduty = after + J[i] + w
            else:
                P[i] = _tod(arr + J[i])
                cduty = after + J[i]
            Q[i] = _next_day(Q[i - 1])
        else:
            arr = M[i] = _tod(prev_dep + dt)
            cdrive += dt
            cduty += dt
            if arr > CLOSE or arr + J[i] > CLOSE:  # too late: sleep at the store
                N[i] = 10
                arr = M[i] = _tod(arr + REST)
                cdrive = 0.0
                if arr < OPEN:
                    w = _wait_to_8(arr)
                    O[i] = w
                    P[i] = _tod(arr + J[i] + w)
                    cduty = J[i] + w
                else:
                    P[i] = _tod(arr + J[i])
                    cduty = J[i]
                Q[i] = _next_day(Q[i - 1])
            else:
                same = Q[i - 1] == D[i] or seq[i - 1] == 0 or N[i - 1] == 10
                if same and cduty + J[i] <= DUTY_MAX:
                    P[i] = _tod(arr + J[i])
                    cduty += J[i]
                    if seq[i - 1] != 0:
                        Q[i] = Q[i - 1]
                else:  # "Line1": burn remaining duty, rest 10 h, roll to next day
                    wl = DUTY_MAX - cduty
                    O[i], N[i] = wl, 10
                    cdrive = 0.0
                    arr2 = _tod(arr + wl + REST)
                    if not (OPEN <= arr2 <= CLOSE):
                        w = _wait_to_8(arr2)
                        O[i] = w + wl
                        P[i] = _tod(arr2 + J[i] + w)
                        cduty = J[i] + w
                    else:
                        P[i] = _tod(arr2 + J[i])
                        cduty = J[i]
                    Q[i] = _next_day(Q[i - 1])

    # ---- route summaries and feasibility flags (as the macro computes them) ----
    routes, start = [], 0
    for i in range(1, n):
        if seq[i] == 0:
            rng = range(start, i + 1)
            stops = [k for k in rng if seq[k] != 0]
            r = dict(
                orders=[seq[k] for k in stops],
                dispatch_day=D[stops[0]] if stops else None,
                dispatch_time=P[start],
                drive=sum(F[k] for k in rng), unload=sum(J[k] for k in rng),
                duty=sum(F[k] + J[k] for k in rng), brk=sum(N[k] for k in rng),
                wait=sum(O[k] for k in rng), miles=sum(E[k] for k in rng),
                cube=sum(H[k] for k in rng),
            )
            r["cap_ok"] = r["cube"] <= capacity
            r["drive_ok"] = not (r["drive"] > DRIVE_MAX and r["brk"] < 10)
            r["day_ok"] = all(Q[k] == D[k] for k in stops)
            routes.append(r)
            start = i + 1
    served = sum(len(r["orders"]) for r in routes)
    result = dict(
        total_miles=sum(r["miles"] for r in routes),
        n_routes=len(routes),
        stops_ok=served == len(orders),
        capacity_ok=all(r["cap_ok"] for r in routes),
        drive_ok=all(r["drive_ok"] for r in routes),
        day_ok=all(r["day_ok"] for r in routes),
        routes=routes,
        rows=dict(M=M, N=N, O=O, P=P, Q=Q, E=E),
    )
    result["feasible"] = all(result[k] for k in ("stops_ok", "capacity_ok", "drive_ok", "day_ok"))
    return result
