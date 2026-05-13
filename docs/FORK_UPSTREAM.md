# 本 fork 与上游同步说明

- **origin**：你的 fork — [duanju9/SilverM-quant](https://github.com/duanju9/SilverM-quant)（推送目标）。
- **upstream**：原作者仓库 — [wmaa0002/SilverM-quant](https://github.com/wmaa0002/SilverM-quant)（拉取上游更新用）。

上游**不会**自动合并到你的 fork；需定期执行：

```bash
git fetch upstream
git checkout main
git merge upstream/main
# 或: git rebase upstream/main
git push origin main
```

GitHub 网页上也可用 **Sync fork**（与上游分支对齐时）。

## 本 fork 相对上游的增量（合并冲突时优先保留）

- `tools/miniqmt_etl/`：miniqmt.sqlite → DuckDB `bars_compat`、可选 `dwd_daily_price` 同步、校验与 V4 探针。
- `docs/VNPY_YUE_MIGRATION.md`、`docs/BACKTEST_SMOKE.md`、`docs/agent_module_log.md`。
- 根目录 `README.md` 中「Vnpy_Yue / miniqmt」小节。

首次推送若认证失败，请在本机配置 `gh auth login` 或 SSH key 后执行：

```bash
git push -u origin main
```

就绪自检清单：[GO_LIVE_CHECKLIST.md](./GO_LIVE_CHECKLIST.md)。
