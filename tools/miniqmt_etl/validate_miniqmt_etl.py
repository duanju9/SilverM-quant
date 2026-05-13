#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 miniqmt ETL：对比 SQLite 与 DuckDB bars_compat 行数（可选按 period），并抽样 OHLCV。
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _default_sqlite() -> Path:
    raw = (os.environ.get("MINIQMT_SQLITE_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (PROJECT_ROOT.parent / "Vnpy_Yue" / "examples" / "miniqmt_research" / "data" / "miniqmt.sqlite").resolve()


def _default_duckdb() -> Path:
    raw = (os.environ.get("SILVERM_DUCKDB") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (PROJECT_ROOT / "data" / "Astock3.duckdb").resolve()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", type=Path, default=None)
    ap.add_argument("--duckdb", type=Path, default=None)
    ap.add_argument("--code", default="000001.SZ")
    ap.add_argument("--periods", default="1d,5m", help="抽样对比的 period 列表")
    args = ap.parse_args()

    sp = (args.sqlite or _default_sqlite()).resolve()
    dp = (args.duckdb or _default_duckdb()).resolve()
    if not sp.is_file():
        print(f"[validate] missing sqlite: {sp}", file=sys.stderr)
        return 2
    if not dp.is_file():
        print(f"[validate] missing duckdb: {dp}", file=sys.stderr)
        return 2

    sq = sqlite3.connect(str(sp))
    dk = duckdb.connect(str(dp), read_only=True)
    try:
        for period in [p.strip() for p in args.periods.split(",") if p.strip()]:
            a = sq.execute("SELECT COUNT(*) FROM bars WHERE period=?", (period,)).fetchone()[0]
            b = dk.execute("SELECT COUNT(*) FROM bars_compat WHERE period=?", [period]).fetchone()[0]
            ok = "OK" if a == b else "MISMATCH"
            print(f"[validate] period={period} sqlite={a} duckdb={b} {ok}")
        code = args.code
        for period in ["1d", "5m"]:
            srows = sq.execute(
                "SELECT ts, open, close, volume FROM bars WHERE code=? AND period=? ORDER BY ts DESC LIMIT 3",
                (code, period),
            ).fetchall()
            drows = dk.execute(
                "SELECT ts, open, close, volume FROM bars_compat WHERE code=? AND period=? ORDER BY ts DESC LIMIT 3",
                [code, period],
            ).fetchall()
            print(f"[validate] sample code={code} period={period}")
            print(f"  sqlite: {srows}")
            print(f"  duckdb: {drows}")
    finally:
        sq.close()
        dk.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
