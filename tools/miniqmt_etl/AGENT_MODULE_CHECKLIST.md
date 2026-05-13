# Agent 模块完成检查清单（miniqmt_etl / 迁移）

每完成计划中的一个模块（M1–M7），勾选并保留命令与退出码，便于复盘。

## 通用

- [ ] 命令与当前工作目录已写入 `docs/agent_module_log.md`（或本文件末尾追加一节）
- [ ] 本机 Python venv 与 SilverM `requirements.txt` 一致（不与 Vnpy_Yue 混用同一 venv，除非明确管理）

## M1 基线

- [ ] `pip install -r requirements.txt` 成功
- [ ] `python scripts/init_database.py --db data/Astock3.duckdb` 成功（若需完整表）
- [ ] （可选）`python scripts/init_database.py --list` 可列出表名

## M2 映射

- [ ] 已阅读 `tools/miniqmt_etl/docs/MINIQMT_TO_DUCKDB_MAPPING.md` 并与 `database_schema.md` 核对

## M3 ETL

- [ ] `python tools/miniqmt_etl/etl_sqlite_bars_to_duckdb.py --limit-rows <N>` 退出码 0
- [ ] DuckDB 中 `SELECT COUNT(*) FROM bars_compat` > 0

## M4 校验

- [ ] `python tools/miniqmt_etl/validate_miniqmt_etl.py` 对至少 2 个 `period` 显示 `OK`
- [ ] 抽样 `000001.SZ`（或你库内存在代码）sqlite 与 duckdb 三行一致或差异已记录

## M5 V4 探针

- [ ] `VNPY_YUE_STRATEGY_V4` 指向含 `auto_iterate_v4.py` 的目录
- [ ] `python tools/miniqmt_etl/v4_entry_probe.py` 退出码 0 并打印 `entry_ok_sqlite=...`

## M6 回测冒烟

- [ ] `python tools/miniqmt_etl/smoke_duckdb_read.py` exit 0（不依赖策略文件 / pytest）
- [ ] 若已 `--sync-dwd-daily` 且存在目标策略 py：按 `docs/BACKTEST_SMOKE.md` 执行 `run_backtest.py`
- [ ] 指标与 Vnpy_Yue walk-forward 的差异已记在 `docs/VNPY_YUE_MIGRATION.md`

## M7 文档

- [ ] 环境变量表已更新 `docs/VNPY_YUE_MIGRATION.md`
- [ ] 实盘仍在 Vnpy_Yue 的说明已告知使用方
