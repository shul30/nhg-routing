"""Random routes: the fast check must agree with the full checker replica."""
import random, warnings
warnings.filterwarnings("ignore")
from nhg.data import load_orders, load_distances, DAYS
from nhg.checker import simulate
from nhg.route import evaluate_route


def test_agreement(n_routes=30000, seed=7):
    orders, dist = load_orders(), load_distances()
    by_day = {d: [o for o in orders if orders[o].day == d] for d in DAYS}
    rng = random.Random(seed)
    disagree = feas = 0
    for _ in range(n_routes):
        day = rng.choice(DAYS)
        r = rng.sample(by_day[day], rng.randint(1, 20))
        ok, miles, _ = evaluate_route(r, orders, dist)
        res = simulate([0] + r + [0], orders, dist)
        ok2 = res["capacity_ok"] and res["drive_ok"] and res["day_ok"]
        feas += ok
        if ok != ok2 or (ok and abs(miles - res["total_miles"]) > 1e-6):
            disagree += 1
    assert disagree == 0, f"{disagree} disagreements"
    return feas, n_routes


if __name__ == "__main__":
    f, n = test_agreement()
    print(f"fast check == full checker on {n} random routes ({f} feasible, {n-f} infeasible)")
