# miniqmt.sqlite → SilverM DuckDB 字段映射（决策）

## 源端（Vnpy_Yue `miniqmt_db`）

表 **`bars`**：

| 列 | 类型（SQLite） | 说明 |
|----|----------------|------|
| period | TEXT | `1d` / `60m` / `5m` |
| code | TEXT | 如 `000001.SZ`（与 tushare `ts_code` 形式一致） |
| ts | TEXT | K 线时间戳字符串 |
| open, high, low, close, volume, amount | REAL | OHLCV、成交额 |

表 **`dl_job` / `dl_meta`**：下载断点，**默认不迁入** SilverM（避免与 SilverM 自有 pipeline 键冲突）。若需审计可后续加表 `miniqmt_dl_job_compat`。

## 目标端（SilverM）

### A. 兼容层（推荐，本工具默认创建）

表 **`bars_compat`**：与源 `bars` **同名列**，便于 V4 / 研究脚本用 SQL 直接读多周期，**不改** SilverM 核心 DWD 表。

```sql
CREATE TABLE bars_compat (
  period VARCHAR,
  code VARCHAR,
  ts VARCHAR,
  open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
  volume DOUBLE, amount DOUBLE,
  PRIMARY KEY (period, code, ts)
);
```

### B. 可选：对齐 `dwd_daily_price`（仅 `period='1d'`）

SilverM 核心日线表（见根目录 `database_schema.md` 中 **`dwd_daily_price`**）：

| SilverM 列 | 来源 |
|------------|------|
| trade_date | `CAST` / `strptime` 自 `bars.ts` 的日期部分 |
| ts_code | `bars.code` |
| open, high, low, close | 同左 |
| vol | `CAST(volume AS BIGINT)` |
| amount | `amount` |
| pct_chg | 可用 `LAG(close)` 计算；ETL 默认 **NULL**（回测若依赖需补算） |
| data_source | 固定 **`miniqmt_sqlite`**（便于与 tushare 行区分） |

**注意**：`5m` / `60m` **不写入** `dwd_daily_price`；分钟级留在 `bars_compat`，供 V4 类逻辑查询。

## 代码格式

`000001.SZ` 与 SilverM / tushare `ts_code` 一致，**无需**转换交易所后缀（已是后缀形式）。

## 时间戳

源库 `ts` 多为 ISO 风格字符串；ETL 使用 DuckDB `try_cast(ts AS TIMESTAMP)` 或 Python `pd.to_datetime` 再写回，以实际数据抽样为准。

## 权威引用

- 源 DDL：Vnpy_Yue 仓库内 `examples/miniqmt_research/miniqmt_db.py` 的 `SCHEMA_SQLITE`
- 目标文档：本仓库根目录 [database_schema.md](../../database_schema.md)、[数据库初始化.md](../../数据库初始化.md)
