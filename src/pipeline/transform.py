"""Tiny transform layer: load raw sales, clean them, aggregate revenue."""
import csv
from collections import defaultdict


def load_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def clean(rows, min_amount=0.0):
    """Drop malformed rows and rows below min_amount; normalise region names."""
    out = []
    for r in rows:
        try:
            amount = float(r["amount"])
            region = r["region"].strip().title()
        except (KeyError, ValueError, AttributeError):
            continue
        if not region or amount < min_amount:
            continue
        out.append({"region": region, "amount": amount})
    return out


def revenue_by_region(rows):
    totals = defaultdict(float)
    for r in rows:
        totals[r["region"]] += r["amount"]
    return {k: round(v, 2) for k, v in sorted(totals.items())}


def orders_by_region(rows):
    """Count orders per region, sorted by region name."""
    counts = defaultdict(int)
    for r in rows:
        counts[r["region"]] += 1
    return dict(sorted(counts.items()))

