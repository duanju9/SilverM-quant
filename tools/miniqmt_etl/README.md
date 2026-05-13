# miniqmt → SilverM（Vnpy_Yue 数据迁移）

本目录为 **Fork 主工程** 上的增量：不修改 SilverM 核心信号/回测逻辑，仅增加 **ETL、校验、V4 探针**。

## 前置

1. 已 clone / fork 本仓库，Python 3.10+ 推荐。
2. `pip install -r requirements.txt`（含 `duckdb`、`pandas`）。
3. 若需 `dwd_daily_price` 同步：先初始化 DuckDB 表结构：

```bash
cd <SilverM-quant 根目录>
python scripts/init_database.py --db data/Astock3.duckdb
```

（若仅要 `bars_compat` 做研究，可跳过 init，ETL 会创建/覆盖 `bars_compat`。）

## ETL

```bash
# 默认读 ../Vnpy_Yue/.../miniqmt.sqlite，写入 data/Astock3.duckdb（分块 35 万行/批，防内存爆）
python tools/miniqmt_etl/etl_sqlite_bars_to_duckdb.py

# 显式路径 + 日线同步到 dwd_daily_price（需已 init_database）
python tools/miniqmt_etl/etl_sqlite_bars_to_duckdb.py ^
  --sqlite D:\Vnpy\Vnpy_Yue\examples\miniqmt_research\data\miniqmt.sqlite ^
  --duckdb D:\Vnpy\SilverM-quant\data\Astock3.duckdb ^
  --sync-dwd-daily

# 仅日线子集调试
python tools/miniqmt_etl/etl_sqlite_bars_to_duckdb.py --periods 1d --limit-rows 100000
```

环境变量：`MINIQMT_SQLITE_PATH`、`SILVERM_DUCKDB`。可选 `--chunk-rows 0` 强制一次性读入（**仅小库**）。

## 校验

```bash
python tools/miniqmt_etl/validate_miniqmt_etl.py --sqlite "D:\Vnpy\Vnpy_Yue\examples\miniqmt_research\data\miniqmt.sqlite" --duckdb "D:\Vnpy\SilverM-quant\data\Astock3.duckdb" --periods "1d,5m"
```

若 ETL 使用了 `--limit-rows`，DuckDB 行数为子集，**校验脚本出现 MISMATCH 属预期**；全量迁移后应 `OK`。PowerShell 传多 period 请加引号：`--periods "1d,5m"`。

## V4 入场探针（依赖 Vnpy_Yue 源码）

```bash
set VNPY_YUE_STRATEGY_V4=D:\Vnpy\Vnpy_Yue\examples\miniqmt_live\strategy_v4
python tools/miniqmt_etl/v4_entry_probe.py --code 000001.SZ
```

## DuckDB 只读冒烟（不依赖策略 py / pytest）

```bash
python tools/miniqmt_etl/smoke_duckdb_read.py
```

## 文档

- [docs/MINIQMT_TO_DUCKDB_MAPPING.md](docs/MINIQMT_TO_DUCKDB_MAPPING.md) 字段映射
- [../docs/VNPY_YUE_MIGRATION.md](../docs/VNPY_YUE_MIGRATION.md) 总览与回测冒烟
- [AGENT_MODULE_CHECKLIST.md](AGENT_MODULE_CHECKLIST.md) 每模块完成检查

实盘 miniQMT **仍在 Vnpy_Yue** 的 `strategy_v4`，本仓库以研究/回测为主。
