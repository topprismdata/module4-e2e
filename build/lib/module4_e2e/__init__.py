"""module4-e2e：业绩分析闭环门禁（WP29 起步）。

链：perf-reconcile(偏差) → sraf_intel(诊断→DP) → dq-workbench(行动工单)
→ ActionLedger(append-only 回写) · service-rules(KPI 预警) · visitmodel(episode 锚)。
桥只居集成层：下层互不 import。
"""
__version__ = "0.1.0"
