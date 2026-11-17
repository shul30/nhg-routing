import openpyxl, datetime, warnings
warnings.filterwarnings("ignore")
from nhg.data import load_orders, load_distances
from nhg.checker import simulate
orders, dist = load_orders(), load_distances()
ws = openpyxl.load_workbook('data/Solution_Check.xlsm', data_only=True)['SolutionCheck']
seq = [int(ws.cell(r, 2).value) for r in range(2, 314)]
res = simulate(seq, orders, dist)
def h(v):
    if isinstance(v, datetime.time): return v.hour + v.minute/60 + v.second/3600
    if isinstance(v, datetime.datetime): return v.hour + v.minute/60 + v.second/3600
    return float(v or 0)
bad = 0
for k in range(len(seq)):
    r = k + 2
    for col, key in (("M","M"),("N","N"),("O","O"),("P","P"),("Q","Q")):
        exp = ws[f"{col}{r}"].value; got = res["rows"][key][k]
        ok = (exp == got) if col == "Q" else abs(h(exp) - got) < 1/120
        if not ok:
            bad += 1
            if bad < 15: print("row", r, col, "excel:", exp, "python:", got)
print("mismatched cells:", bad, "of", 5*len(seq))
print("total miles: python", res["total_miles"], "excel", ws["Z13"].value)
print("routes: python", res["n_routes"], "excel", ws["Z14"].value)
print({k: res[k] for k in ("stops_ok","capacity_ok","drive_ok","day_ok","feasible")})
print("orders in example:", sum(len(r['orders']) for r in res['routes']))
