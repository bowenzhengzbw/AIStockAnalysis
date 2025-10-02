# Implementation Module Breakdown (Preview)

This document translates the high-level planning captured in [`master_plan.md`](./master_plan.md) into actionable, reviewable modules. Each module is scoped so that it can be delivered incrementally, reviewed, and adjusted based on feedback before deeper implementation work proceeds.

## Phase 0 — Foundations & Governance

### Module 0.1: Project Charter & Success Metrics
- Deliverables: Refined objectives, KPIs (alpha, drawdown, hit-rate), review cadence.
- Dependencies: None.
- Notes: Capture in Markdown template for ongoing updates. → See [`phase0/module01_charter_success_metrics.md`](./phase0/module01_charter_success_metrics.md).

### Module 0.2: Data Source Inventory & Access Plan
- Deliverables: Source catalog (Tushare Pro, iFinD, official statistics, sentiment feeds), access methods, refresh frequency, cost tracking.
- Dependencies: 0.1.
- Notes: Align with annual budget ≤ ¥2,000 by prioritizing core + supplemental sources. → See [`phase0/module02_data_inventory_access_plan.md`](./phase0/module02_data_inventory_access_plan.md) 与 [`data_source_strategy.md`](./data_source_strategy.md).

### Module 0.3: Tech Stack & Security Baseline
- Deliverables: Infrastructure decision (storage, compute, workflow), access control policy, compliance checklist.
- Dependencies: 0.1, 0.2.
- Notes: Define environment requirements for both local and cloud deployments. → See [`phase0/module03_tech_stack_security_baseline.md`](./phase0/module03_tech_stack_security_baseline.md).

### Module 0.4: Review Cadence & Governance Playbook
- Deliverables: Review schedule, feedback templates, versioning conventions, RACI chart aligned with [`phase0_charter.md`](./phase0_charter.md).
- Dependencies: 0.1.
- Notes: Ensures every subsequent module has a clear approval path and documentation archive. → See [`phase0/module04_governance_playbook.md`](./phase0/module04_governance_playbook.md).

## Phase 1 — Data Layer & Core Agents MVP

> 详见 [Phase 1 预览：数据底座与核心 Agent MVP](./phase1_data_foundation_preview.md)，了解任务拆分、交付物与验收标准。

### Module 1.1: Data Ingestion Pipelines (ODS Layer)
- Deliverables: ETL scripts/templates for Tushare & public data, storage schema, data quality checks.
- Dependencies: Phase 0 modules.
- Preview Criteria: DAG diagrams, sample ingestion notebooks.

### Module 1.2: Data Harmonization (DWD Layer)
- Deliverables: Standardized field names, calendars, currency units; anomaly handling rules.
- Dependencies: 1.1.
- Preview Criteria: Data dictionary excerpts, transformation configs.

### Module 1.3: Macro Sentinel Agent MVP
- Deliverables: Macro indicator fetch, trend detection heuristics, summary report template.
- Dependencies: 1.1, 1.2.
- Preview Criteria: Prompt design, expected output schema.

### Module 1.4: Policy Watcher Agent MVP
- Deliverables: Policy ingestion workflow, NLP parsing pipeline, impact tagging schema.
- Dependencies: 1.1, 1.2.
- Preview Criteria: Example parsing outputs, policy-to-sector mapping table.

### Module 1.5: Company Analyst Agent MVP
- Deliverables: Financial statement loader, valuation workbook template, qualitative scorecard draft.
- Dependencies: 1.1, 1.2.
- Preview Criteria: Model outline, scoring rubric mockup.

## Phase 2 — Expanded Intelligence & Collaboration

> 详见 [Phase 2 预览：行业、舆情与风险扩展包](./phase2_industry_sentiment_risk_preview.md)，了解 Industry Mapper、News & Sentiment Scout、Risk Controller 以及知识库集成的任务拆分与验收标准。

### Module 2.1: Industry Mapper Agent
- Deliverables: Industry KPI library, supply-demand dashboards, cycle classification logic.
- Dependencies: 1.x.
- Preview Criteria: Feature list, sample industry report skeleton.

### Module 2.2: News & Sentiment Scout
- Deliverables: Multi-source news ingestion, sentiment scoring model selection, alerting rules.
- Dependencies: 1.x.
- Preview Criteria: Data pipeline diagram, sentiment taxonomy.

### Module 2.3: Risk Controller Foundations
- Deliverables: Risk factor definitions, stress test scenarios, monitoring dashboards.
- Dependencies: 1.x, 2.1, 2.2.
- Preview Criteria: Scenario library outline, risk metric table.

### Module 2.4: Knowledge Base & Feedback Loop
- Deliverables: Vector store schema, tagging ontology, human-in-the-loop review workflow.
- Dependencies: 1.x.
- Preview Criteria: Knowledge card templates, feedback capture process.

## Phase 3 — Portfolio Strategy & Automation

> 详见 [Phase 3 预览：组合策略与自动化闭环](./phase3_portfolio_automation_preview.md)，了解 Portfolio Strategist、回测分析、Orchestrator 协同与报告自动化的任务拆分与验收标准。

### Module 3.1: Portfolio Strategist Engine
- Deliverables: Scoring aggregation, optimization constraints, rebalancing logic.
- Dependencies: 2.x agents.
- Preview Criteria: Optimization pseudocode, signal weighting plan.

### Module 3.2: Backtesting & Performance Analytics
- Deliverables: Backtest framework integration, attribution reports, benchmarking toolkit.
- Dependencies: 3.1.
- Preview Criteria: Backtest template, reporting dashboard mockups.

### Module 3.3: Orchestrator & Workflow Automation
- Deliverables: Agent coordination scripts, task scheduler integration, audit logging.
- Dependencies: 1.x–3.2.
- Preview Criteria: Sequence diagrams, task playbook.

### Module 3.4: User Interface & Reporting
- Deliverables: Research notebook templates, dashboards, automated reporting pipelines.
- Dependencies: 3.1, 3.2, 3.3.
- Preview Criteria: UI wireframes, report layout samples.

## Review & Iteration Protocol
- Each module will be delivered first as a **preview package**: architecture notes, schemas, prompt drafts, or mockups.
- Agent 协同与 Orchestrator 交互遵循 [`agent_system_blueprint.md`](./agent_system_blueprint.md) 中定义的契约，确保跨模块接口一致。
- Upon approval, implementation proceeds with iterative commits targeting functionality, documentation, and tests.
- Feedback loops: Weekly sync summaries, change logs, and milestone retrospectives.

## Immediate Action Items
1. Validate this modular breakdown with the project owner.
2. Prioritize Phase 0 deliverables and confirm desired preview format (documents vs. prototypes).
3. Establish communication cadence and review checkpoints before coding begins.

