#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4 入场规则探针：从 DuckDB bars_compat 读 5m/60m，调用 Vnpy_Yue strategy_v4 的 entry_ok_sqlite。

需已 ETL bars_compat；需能 import Vnpy_Yue 下 strategy_v4（默认路径见代码）。

用法::
  set VNPY_YUE_STRATEGY_V4=d:\\Vnpy\\Vnpy_Yue\\examples\\miniqmt_live\\strategy_v4
  python tools/miniqmt_etl/v4_entry_probe.py --code 000001.SZ
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _v4_pkg() -> Path:
    raw = (os.environ.get("VNPY_YUE_STRATEGY_V4") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (PROJECT_ROOT.parent / "Vnpy_Yue" / "examples" / "miniqmt_live" / "strategy_v4").resolve()


def _default_duckdb() -> Path:
    raw = (os.environ.get("SILVERM_DUCKDB") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (PROJECT_ROOT / "data" / "Astock3.duckdb").resolve()


def load_range(con: duckdb.DuckDBPyConnection, code: str, period: str, limit: int) -> pd.DataFrame:
    df = con.execute(
        """
        SELECT ts AS dt, open, high, low, close, volume
        FROM bars_compat
        WHERE code = ? AND period = ?
        ORDER BY ts
        """,
        [code, period],
    ).fetchdf()
    if df.empty:
        return df
    if limit > 0 and len(df) > limit:
        df = df.iloc[-limit:].copy()
    df["dt"] = pd.to_datetime(df["dt"], errors="coerce")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["dt"]).reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duckdb", type=Path, default=None)
    ap.add_argument("--code", default="000001.SZ")
    ap.add_argument("--tail-5m", type=int, default=200)
    ap.add_argument("--tail-60m", type=int, default=120)
    ap.add_argument("--support", type=float, default=0.0, help="入场支撑价探针；0 表示仅测形态逻辑")
    args = ap.parse_args()

    v4 = _v4_pkg()
    if not (v4 / "auto_iterate_v4.py").is_file():
        print(f"[v4_probe] V4 目录无效: {v4}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(v4))
    from auto_iterate_v4 import entry_ok_sqlite  # noqa: E402
    from config import StrategyV4Config  # noqa: E402

    dp = (args.duckdb or _default_duckdb()).resolve()
    if not dp.is_file():
        print(f"[v4_probe] duckdb 不存在: {dp}", file=sys.stderr)
        return 3

    con = duckdb.connect(str(dp), read_only=True)
    try:
        df5 = load_range(con, args.code, "5m", args.tail_5m)
        df60 = load_range(con, args.code, "60m", args.tail_60m)
    finally:
        con.close()

    cfg = StrategyV4Config()
    ok = entry_ok_sqlite(df5, df60, float(args.support), cfg)
    print(f"[v4_probe] code={args.code} rows5m={len(df5)} rows60m={len(df60)} entry_ok_sqlite={ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
