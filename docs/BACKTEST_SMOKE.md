# 回测冒烟（ETL 同步日线后）

`run_backtest.py` 从 `dwd_daily_price` 读数（见 `backtest/strategy_backtest/run_backtest.py`）。在已执行：

```bash
python tools/miniqmt_etl/etl_sqlite_bars_to_duckdb.py --periods 1d --sync-dwd-daily
```

且目标标的在 SQLite 中有足够 **1d** 数据后，可试：

```bash
cd <SilverM-quant 根>
python backtest/strategy_backtest/run_backtest.py --stock 000001 --start 20240101 --end 20241231 --strategy 天宫B1策略backet --no-save
```

说明：

- `--stock` 为 **6 位**代码；脚本会自动加 `.SH` / `.SZ`。
- 若策略文件或图表依赖缺失导致报错，可仅做数据库校验：`python tools/miniqmt_etl/validate_miniqmt_etl.py`。
- `pct_chg` 在 ETL 中为 NULL；若策略强依赖涨跌幅字段，需在 ETL 中补算 `LAG` 后再跑回测。
