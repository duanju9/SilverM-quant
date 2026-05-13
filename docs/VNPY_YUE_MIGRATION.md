# Vnpy_Yue 与 SilverM-quant 并行说明（迁移期）

## 角色划分

| 仓库 | 职责 |
|------|------|
| **SilverM-quant（本 Fork）** | DuckDB 存储、信号扫描、批量回测、Dashboard、Agent 投研；**本变更**增加 `tools/miniqmt_etl` 将 `miniqmt.sqlite` 的 `bars` 迁入 `bars_compat`（可选同步 `dwd_daily_price` 日线）。 |
| **Vnpy_Yue** | miniQMT **实盘** Strategy V4（`v4_live_runner`）、xtdata 下载落 SQLite、原 walk-forward 与验收文档。 |

## 环境变量

| 变量 | 用途 |
|------|------|
| `MINIQMT_SQLITE_PATH` | Vnpy_Yue 侧 `miniqmt.sqlite`；ETL/校验默认若与 `../Vnpy_Yue/...` 同盘布局可省略。 |
| `SILVERM_DUCKDB` | 目标 DuckDB 文件，默认 `<SilverM>/data/Astock3.duckdb`。 |
| `VNPY_YUE_STRATEGY_V4` | `v4_entry_probe.py` 导入用，指向 `Vnpy_Yue/examples/miniqmt_live/strategy_v4`。 |

## 推荐执行顺序

1. `python scripts/init_database.py --db data/Astock3.duckdb`（若需 `dwd_daily_price` / 回测读该表）
2. `python tools/miniqmt_etl/etl_sqlite_bars_to_duckdb.py`（大库建议先 `--limit-rows` 试跑）
3. `python tools/miniqmt_etl/validate_miniqmt_etl.py`
4. 可选 `--sync-dwd-daily` 后见 [BACKTEST_SMOKE.md](BACKTEST_SMOKE.md)

## 与 Vnpy_Yue walk-forward 的对比（M6）

- SilverM 回测引擎与手续费、复权、**pct_chg 缺失** 等口径可能与 `auto_iterate_v4` 不一致；**不要求**数值逐笔一致。
- 对比时记录：数据源（miniqmt_sqlite）、区间、标的数、是否仅日线层回测。

## 实盘

**miniQMT 下单仍在 Vnpy_Yue**；本仓库不替代 `XtQuantTrader` 路径，直至单独里程碑迁移。
