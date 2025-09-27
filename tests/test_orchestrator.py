"""Unit tests for orchestrator baseline behaviour."""

from __future__ import annotations

from aistockanalysis.agents.orchestrator import AgentOrchestrator


def test_orchestrator_generates_summary() -> None:
    orchestrator = AgentOrchestrator()
    context = {
        "macro": {"gdp_growth": 4.5, "cpi": 2.1},
        "policy": {"support_score": 0.7, "highlights": ["财政扩张"]},
        "industries": {
            "scores": {"technology": 0.8},
            "overweight": ["technology"],
            "underweight": ["utilities"],
            "policy_sensitive": ["infrastructure"],
        },
        "equity": {
            "valuation": {"pe": 15.2, "pb": 2.3},
            "quality": {"roe": 18.5, "net_margin": 12.0},
            "growth_drivers": ["AI"],
            "risk_factors": ["监管"],
            "esg_flags": [],
        },
    }
    results = orchestrator.run(context)
    assert "summary" in results
    assert "宏观层面" in results["summary"]


def test_orchestrator_handles_missing_numeric_values() -> None:
    orchestrator = AgentOrchestrator()
    context = {
        "macro": {"gdp_growth": None, "cpi": "2.5"},
        "policy": {"support_score": None, "highlights": []},
        "industries": {
            "scores": {"technology": None, "finance": "0.55"},
            "overweight": [],
            "underweight": [],
            "policy_sensitive": [],
        },
        "equity": {
            "valuation": {"pe": None, "pb": "1.8"},
            "quality": {"roe": float("nan"), "net_margin": "15.4"},
            "growth_drivers": [],
            "risk_factors": [],
            "esg_flags": [],
        },
    }

    results = orchestrator.run(context)

    macro_metrics = results["macro_agent"]["metrics"]
    industry_metrics = results["industry_agent"]["metrics"]
    equity_metrics = results["equity_agent"]["metrics"]

    assert macro_metrics["growth_score"] == 0.0
    assert macro_metrics["inflation_score"] == 2.5
    assert macro_metrics["policy_support"] == 0.0

    assert industry_metrics["technology_score"] == 0.0
    assert industry_metrics["finance_score"] == 0.55

    assert equity_metrics["pe"] == 0.0
    assert equity_metrics["pb"] == 1.8
    assert equity_metrics["roe"] == 0.0
    assert equity_metrics["net_margin"] == 15.4
