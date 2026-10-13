# -*- coding: utf-8 -*-
"""偏差→诊断→行动提案桥（④WP29；只居集成层）。

映射口径（04 §28 诊断词表对齐）：
- MISS → CoverageAllocationMismatch（计划覆盖未执行）
- OFF_PLAN → TerritoryImbalance（计划外=计划与现实失衡）
- DATE_DRIFT → SchedulingInfeasibility（排班侧不可行证据）
- REP_MISMATCH → PersonnelConstraint（人店约束）
未知偏差 kind → 不臆测路由（router 对未知诊断返回 primary=None+
"更多证据"——fail-closed 语义原样透传）。
提案恒 requires_approval：行动=建议不是授权（WP05 纪律）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from dq_workbench.models import Finding, Layer, Severity
from sraf_intel.router import ProblemRouter

DEVIATION_DIAGNOSIS = {
    "MISS": "CoverageAllocationMismatch",
    "OFF_PLAN": "TerritoryImbalance",
    "DATE_DRIFT": "SchedulingInfeasibility",
    "REP_MISMATCH": "PersonnelConstraint",
}

_ROUTER = ProblemRouter()


@dataclass(frozen=True)
class ActionProposal:
    kind: str
    diagnosis: str
    primary_route: str | None
    reason: str
    count: int
    requires_approval: bool = field(default=True, init=False)


def proposals_from_report(report, subject: str = "visit-plan") -> list[ActionProposal]:
    """ReconcileReport → 按偏差 kind 聚合的行动提案（确定性：kind 升序）。"""
    counts: dict[str, int] = {}
    for d in report.deviations:
        counts[d.kind] = counts.get(d.kind, 0) + 1
    out: list[ActionProposal] = []
    for kind in sorted(counts):
        diagnosis = DEVIATION_DIAGNOSIS.get(kind, f"Unknown:{kind}")
        route = _ROUTER.route(diagnosis)
        out.append(ActionProposal(kind, diagnosis, route.primary_route,
                                  route.reason, counts[kind]))
    return out


def proposal_to_findings(proposals, subject: str) -> list[Finding]:
    """提案 → 工作台 Finding（确定性 finding_id：subject+kind）。"""
    findings = []
    for p in proposals:
        findings.append(Finding(
            finding_id=f"DIAG:{subject}:{p.kind}",
            layer=Layer.STATISTICAL,
            rule_id=f"DEVIANCE_{p.kind}",
            subject=subject,
            severity=Severity.C2,
            message=f"{p.diagnosis} ×{p.count} → {p.primary_route or '需更多证据'}",
            evidence=[p.reason],
        ))
    return findings
