"""Entry point. Behaviour changes per environment via config/<APP_ENV>.json."""
import json
import os
from pathlib import Path

from pipeline.transform import clean, load_rows, orders_by_region, revenue_by_region

ROOT = Path(__file__).resolve().parents[2]


def load_config(env):
    path = ROOT / "config" / f"{env}.json"
    if not path.exists():
        raise SystemExit(f"Unknown environment '{env}' (no {path})")
    return json.loads(path.read_text())


def run():
    env = os.environ.get("APP_ENV", "dev")
    cfg = load_config(env)
    secret_status = "set" if os.environ.get("DB_PASSWORD") else "NOT set"

    print(f"== Running pipeline in [{env}] ==")
    print(f"   target warehouse : {cfg['warehouse']}")
    print(f"   min_amount       : {cfg['min_amount']}")
    print(f"   DB_PASSWORD      : {secret_status}")

    rows = clean(load_rows(ROOT / cfg["input_path"]), cfg["min_amount"])
    result = {
        "revenue_by_region": revenue_by_region(rows),
        "orders_by_region": orders_by_region(rows),
    }

    out_dir = ROOT / "output" / env
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
