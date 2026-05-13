#!/usr/bin/env python3
"""SilverM DuckDB 冒烟：确认 dwd_daily_price / bars_compat 可读（不依赖 pytest / 策略文件）。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
DB = Path(os.environ.get("SILVERM_DUCKDB") or ROOT / "data" / "Astock3.duckdb").resolve()


def main() -> int:
    if not DB.is_file():
        print(f"[smoke] missing {DB}", file=sys.stderr)
        return 2
    con = duckdb.connect(str(DB), read_only=True)
    try:
        n = con.execute("SELECT COUNT(*) FROM bars_compat").fetchone()[0]
        d = con.execute("SELECT COUNT(*) FROM dwd_daily_price WHERE ts_code='000001.SZ'").fetchone()[0]
        m = con.execute("SELECT COUNT(*) FROM dwd_daily_price WHERE data_source='miniqmt_sqlite'").fetchone()[0]
        print(f"[smoke] bars_compat={n} dwd_000001.SZ={d} dwd_miniqmt={m}")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
