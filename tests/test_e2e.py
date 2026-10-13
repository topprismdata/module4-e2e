"""WP29 门禁：偏差→诊断→工单→台账 闭环 + KPI 预警 + episode 重放锚。"""

import pytest
from dq_workbench import Workbench
from dq_workbench.models import IssueStatus
from module4_e2e.bridge import proposal_to_findings, proposals_from_report
from perf_reconcile import ActualCheckin, PlanVisit, reconcile, render_report
from perf_reconcile.ledger import ActionLedger
from service_rules import RuleSetVersion, RuleType, Severity, evaluate_kpi, Rule


@pytest.fixture
def env(tmp_path):
    return {"wb": Workbench(tmp_path / "w.db"),
            "led": ActionLedger(tmp_path / "l.jsonl")}


def _report():
    plan = [
        PlanVisit("S1", "2026-11-03", "张三", "B#1"),
        PlanVisit("S2", "2026-11-04", "李四", "B#1"),
    ]
    act = [ActualCheckin("S2", "2026-11-04", "王五"),
           ActualCheckin("S9", "2026-11-05", "赵六")]
    return reconcile(plan, act)


def test_g1_偏差到工单闭环(env):
    r = _report()
    props = proposals_from_report(r, subject="B#1")
    kinds = {p.kind for p in props}
    assert {"MISS", "REP_MISMATCH", "OFF_PLAN"} <= kinds
    assert all(p.requires_approval for p in props)  # 恒需批准
    assert all(p.primary_route and p.primary_route.startswith("DP") for p in props)
    findings = proposal_to_findings(props, "B#1")
    ids = env["wb"].ingest(findings)
    issue = env["wb"].open_issue(ids, title="执行偏差 B#1")
    assert issue.status is IssueStatus.OPEN
    # 台账回写带强键，逐条提案入账
    for p in props:
        env["led"].append({"plan_version_ref": "B#1", "kind": p.kind,
                           "diagnosis": p.diagnosis, "route": p.primary_route})
    assert env["led"].verify() == len(props)


def test_g2_报告逐字节稳定经pin矩阵复现():
    a = render_report(_report())
    b = render_report(_report())
    assert a == b
    assert '"REP_MISMATCH"' in a


def test_g3_KPI预警进工作台(env):
    rs = RuleSetVersion("v", (Rule("R-K", RuleType.KPI_THRESHOLD, Severity.C2,
                                   False, kpi="miss_rate", kpi_lo=None, kpi_hi=0.05),))
    evals = evaluate_kpi(rs, "B#1", {"miss_rate": 0.30})
    assert evals[0].verdict.name == "REVIEW"
    from dq_workbench.models import Finding, Layer, Severity as WS
    f = Finding(finding_id=f"KPI:B#1:{evals[0].rule_id}", layer=Layer.STATISTICAL,
                rule_id=evals[0].rule_id, subject="B#1", severity=WS.C2,
                message=evals[0].measured, evidence=["KPI_THRESHOLD"])
    env["wb"].ingest([f])
    assert env["wb"].open_issue([f.finding_id], title="KPI 越界").status is IssueStatus.OPEN


def test_g4_episode重放锚跨仓可用():
    """visitmodel DecisionEpisode：同决策重放同哈希（对照的时间锚）。"""
    from visit_math_api import DecisionEpisode, episode_hash

    def ep(sol_id):
        return DecisionEpisode(
            episode_id="uuid-忽略", source_snapshot_id="snap1",
            semantic_spec_version="1.0", semantic_spec_hash="h1",
            instance_hash="i1", solver_backend="cpsat", solver_version="9.7",
            solver_config_hash="c1", seed=42, solution_id=sol_id,
            status="OPTIMAL", termination_reason="time")
    assert episode_hash(ep("s1")) == episode_hash(ep("s1"))  # 重放同哈希
    assert episode_hash(ep("s1")) != episode_hash(ep("s2"))  # 解变更哈希变


def test_g5_台账篡改必红(env):
    env["led"].append({"plan_version_ref": "B#1", "kind": "MISS"})
    env["led"].append({"plan_version_ref": "B#1", "kind": "OFF_PLAN"})
    assert env["led"].verify() == 2
    import json
    from perf_reconcile.ledger import LedgerTamperError
    rows = [json.loads(x) for x in
            env["led"].path.read_text(encoding="utf-8").splitlines()]
    rows[0]["entry"]["kind"] = "OK"
    env["led"].path.write_text("\n".join(json.dumps(r, ensure_ascii=False)
                                         for r in rows) + "\n", encoding="utf-8")
    with pytest.raises(LedgerTamperError):
        env["led"].verify()
