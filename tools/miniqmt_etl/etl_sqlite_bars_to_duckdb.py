#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 Vnpy_Yue miniqmt.sqlite 的 bars 表迁入本仓库 DuckDB。

默认新建/覆盖表 bars_compat；可选把 period=1d 同步到 dwd_daily_price（需表已存在，见 scripts/init_database.py）。

环境变量:
  MINIQMT_SQLITE_PATH  未传 --sqlite 时使用
  SILVERM_DUCKDB       未传 --duckdb 时使用，默认 <repo>/data/Astock3.duckdb
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _default_sqlite() -> Path:
    raw = (os.environ.get("MINIQMT_SQLITE_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    # 与 Vnpy_Yue 默认相对：SilverM-quant 与 Vnpy_Yue 同属 Vnpy 父目录时的常见布局
    guess = PROJECT_ROOT.parent / "Vnpy_Yue" / "examples" / "miniqmt_research" / "data" / "miniqmt.sqlite"
    return guess.resolve()


def _default_duckdb() -> Path:
    raw = (os.environ.get("SILVERM_DUCKDB") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (PROJECT_ROOT / "data" / "Astock3.duckdb").resolve()


def ensure_bars_compat(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    conn.execute("DROP TABLE IF EXISTS bars_compat")
    conn.register("_bars_df", df)
    conn.execute(
        """
        CREATE TABLE bars_compat AS
        SELECT
          CAST(period AS VARCHAR) AS period,
          CAST(code AS VARCHAR) AS code,
          CAST(ts AS VARCHAR) AS ts,
          CAST(open AS DOUBLE) AS open,
          CAST(high AS DOUBLE) AS high,
          CAST(low AS DOUBLE) AS low,
          CAST(close AS DOUBLE) AS close,
          CAST(volume AS DOUBLE) AS volume,
          CAST(amount AS DOUBLE) AS amount
        FROM _bars_df
        """
    )
    conn.unregister("_bars_df")


def sync_dwd_daily_price(conn: duckdb.DuckDBPyConnection) -> int:
    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
    names = {str(r[0]).lower() for r in tables}
    if "dwd_daily_price" not in names:
        raise RuntimeError("dwd_daily_price 不存在，请先运行: python scripts/init_database.py --db data/Astock3.duckdb")
    conn.execute(
        """
        DELETE FROM dwd_daily_price WHERE data_source = 'miniqmt_sqlite'
        """
    )
    conn.execute(
        """
        INSERT INTO dwd_daily_price (trade_date, ts_code, open, high, low, close, vol, amount, pct_chg, data_source)
        SELECT trade_date, ts_code, open, high, low, close, vol, amount, pct_chg, data_source
        FROM (
            SELECT
              CAST(strptime(substr(ts, 1, 10), '%Y-%m-%d') AS DATE) AS trade_date,
              CAST(code AS VARCHAR) AS ts_code,
              open, high, low, close,
              CAST(round(volume) AS BIGINT) AS vol,
              amount,
              NULL::DOUBLE AS pct_chg,
              'miniqmt_sqlite' AS data_source,
              row_number() OVER (PARTITION BY substr(ts, 1, 10), code ORDER BY ts DESC) AS rn
            FROM bars_compat
            WHERE period = '1d'
              AND ts IS NOT NULL
              AND length(ts) >= 10
        ) x
        WHERE rn = 1
        """
    )
    n = conn.execute("SELECT count(*) FROM dwd_daily_price WHERE data_source='miniqmt_sqlite'").fetchone()[0]
    return int(n)


def main() -> int:
    ap = argparse.ArgumentParser(description="miniqmt.sqlite bars -> DuckDB bars_compat")
    ap.add_argument("--sqlite", type=Path, default=None, help="miniqmt.sqlite 路径")
    ap.add_argument("--duckdb", type=Path, default=None, help="目标 .duckdb 路径")
    ap.add_argument("--periods", default="", help="逗号分隔仅导入 period，如 1d,5m；空为全部")
    ap.add_argument("--limit-rows", type=int, default=0, help="最多导入行数，0 表示不限制（全量可能很大）")
    ap.add_argument("--sync-dwd-daily", action="store_true", help="将 1d 写入 dwd_daily_price（需已 init 库表）")
    args = ap.parse_args()

    sqlite_path = (args.sqlite or _default_sqlite()).resolve()
    duckdb_path = (args.duckdb or _default_duckdb()).resolve()

    if not sqlite_path.is_file():
        print(f"[etl] sqlite 不存在: {sqlite_path}", file=sys.stderr)
        return 2

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    where = "1=1"
    params: list = []
    if args.periods.strip():
        parts = [p.strip() for p in args.periods.split(",") if p.strip()]
        qs = ",".join(["?"] * len(parts))
        where = f"period IN ({qs})"
        params = parts

    lim_sql = ""
    if args.limit_rows and args.limit_rows > 0:
        lim_sql = f"LIMIT {int(args.limit_rows)}"

    sq = sqlite3.connect(str(sqlite_path))
    try:
        q = f"SELECT period, code, ts, open, high, low, close, volume, amount FROM bars WHERE {where} {lim_sql}"
        df = pd.read_sql_query(q, sq, params=params or [])
    finally:
        sq.close()

    if df.empty:
        print("[etl] 无数据行，请检查 period 过滤或 sqlite 是否为空", file=sys.stderr)
        return 3

    con = duckdb.connect(str(duckdb_path))
    try:
        ensure_bars_compat(con, df)
        n = con.execute("SELECT count(*) FROM bars_compat").fetchone()[0]
        print(f"[etl] bars_compat rows={n} duckdb={duckdb_path}")
        if args.sync_dwd_daily:
            m = sync_dwd_daily_price(con)
            print(f"[etl] dwd_daily_price rows (data_source=miniqmt_sqlite)={m}")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
