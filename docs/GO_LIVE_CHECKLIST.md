# 可直接使用新项目了吗？（G1–G5）

在将日常工作切到 **[duanju9/SilverM-quant](https://github.com/duanju9/SilverM-quant)** 前，建议逐项勾选。细节见 [FORK_UPSTREAM.md](FORK_UPSTREAM.md)、[VNPY_YUE_MIGRATION.md](VNPY_YUE_MIGRATION.md)。

| ID | 条件 | 状态 |
|----|------|------|
| G1 | fork 已 push；已配置 `upstream`（wmaa0002）；知晓 **Sync fork / fetch+merge** | 本机已 `git push origin main`；`upstream` 已添加 |
| G2 | 全量 ETL 完成；`validate_miniqmt_etl.py --periods "1d,5m,60m"` 均为 **OK** | 已跑通（约 7226 万行 bars_compat） |
| G3 | `init_database` +（按需）`--sync-dwd-daily`；`smoke_duckdb_read.py` exit 0 | 已跑通 |
| G4 | 已知口径差异：**pct_chg** 为 NULL、回测手续费/复权与 Vnpy 可能不同 | 已记入 [VNPY_YUE_MIGRATION.md](VNPY_YUE_MIGRATION.md) |
| G5 | **实盘 miniQMT** 仍明确在 **Vnpy_Yue strategy_v4**，未误以为 SilverM 已接管下单 | 文档已写明 |

`run_backtest.py` 依赖 `strategies/<名称>.py` 存在；若默认策略文件不在仓库中，需自备策略或改 `--strategy` 后再做完整回测冒烟。

**结论（当前会话执行结果）**：研究/回测侧 **可开始使用本 fork + 本机 DuckDB 数据**；**实盘** 请继续在 Vnpy_Yue 运行。
