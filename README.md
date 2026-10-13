# module4-e2e

模块④ 业绩分析集成 E2E：七仓 tag 矩阵上的**偏差→诊断→行动→台账**闭环门禁（WP29 起步）。

```
perf-reconcile v0.3.0 × service-rules v0.3.0 × sraf v0.2.0
× dq-workbench v0.1.1 × plan-release v0.3.0 × visitmodel v0.3.0 × visit-ir v0.2.0
```

## 门禁（5 项）

| # | 不变量 |
|---|---|
| G1 | 偏差→诊断→DP 路由→工单 OPEN→台账回写（提案恒需批准；DP05/DP03/… 不臆测） |
| G2 | 对照报告逐字节稳定（pin 矩阵环境复现） |
| G3 | KPI 越界（evaluate_kpi REVIEW）→工作台工单 |
| G4 | DecisionEpisode 重放锚：同决策同哈希、解变更哈希变（跨仓可用） |
| G5 | 台账篡改必红（改内容/断链 fail-closed） |
| G6 | 聚合四联跨矩阵字节稳定 | dashboard 覆盖率/负载/等级/偏差率 JSON kwargs 序无关复现 |

## 依赖方向

桥（DEVIATION_DIAGNOSIS 映射、proposal→finding）只居本集成层；
perf-reconcile/sraf_intel/service-rules/dq-workbench 互不 import。

## 运行

```bash
git config --global url."https://<PULL_PAT>@github.com/topprismdata/".insteadOf "https://github.com/topprismdata/"
uv pip install "module4-e2e[dev] @ file:///path/to/this/repo"
git config --global --unset url."https://<PULL_PAT>@github.com/topprismdata/".insteadOf  # 用后即撤
python -m pytest tests -q   # 6 passed，全 hermetic
```
