"""Load NHG order and distance data into plain Python structures."""
from dataclasses import dataclass
import pandas as pd

DEPOT_ZIP = "01887"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]


@dataclass(frozen=True)
class Order:
    id: int
    zip: str
    cube: int
    day: str
    st_required: bool


def _z(x) -> str:
    return str(int(x)).zfill(5)


def load_orders(path="data/deliveries.xlsx"):
    df = pd.read_excel(path, sheet_name="OrderTable")
    orders = {}
    for r in df.itertuples(index=False):
        if int(r.ORDERID) == 0:
            continue
        st = str(getattr(r, "_5", "")).strip().lower() == "yes"
        orders[int(r.ORDERID)] = Order(int(r.ORDERID), _z(r.TOZIP), int(r.CUBE), r.DayOfWeek, st)
    return orders


def load_distances(path="data/distances.xlsx"):
    """Return dict-of-dicts: dist[zip_a][zip_b] -> road miles."""
    raw = pd.read_excel(path, header=None)
    cols = [_z(z) for z in raw.iloc[0, 2:]]
    rows = [_z(z) for z in raw.iloc[2:, 0]]
    vals = raw.iloc[2:, 2:].astype(float).values
    return {a: {b: vals[i][j] for j, b in enumerate(cols)} for i, a in enumerate(rows)}
