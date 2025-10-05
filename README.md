# AIStockAnalysis

Comprehensive AI-driven research platform for China's A-share market, targeting 1-3 year investment horizons. This repository will progressively host data ingestion pipelines, agent-based analysis modules, and portfolio decision support tools.

## Repository Structure (initial draft)
- `docs/` — Planning documents, architecture notes, and research templates.
- `src/` — Source code for agents, orchestrators, utilities, and analytics modules.
- `data/` — Placeholder for raw and processed datasets (excluded from version control where appropriate).

## Current Status
- Planning phase documentation 已完成并转入 Phase 1，现已提供可执行的流水线运行时与合成数据提供器，便于验证调度流程与任务产出。
- 自动化测试覆盖数据源组合、流水线规划、执行模块以及合成数据运行时，随着实现推进将继续扩展。

## Key Planning Artifacts
- [`docs/master_plan.md`](docs/master_plan.md) — End-to-end blueprint for the AI-assisted A-share research loop, covering data strategy, agent roles, analytics framework, and phased roadmap tailored to a personal investor with a ¥2,000 annual data budget.
- [`docs/agent_system_blueprint.md`](docs/agent_system_blueprint.md) — Detailed collaboration design for the Orchestrator and analysis agents, including task lifecycles, data contracts, prompt templates, and human-in-the-loop checkpoints before implementation.
- [`docs/data_source_strategy.md`](docs/data_source_strategy.md) — Consolidated data sourcing plan balancing cost (≤¥2,000/year) and coverage for macro, policy, industry, company, and sentiment inputs tailored to the personal investor scenario.
- [`docs/execution_roadmap.md`](docs/execution_roadmap.md) — Week-by-week execution plan with preview deliverables, Go/No-Go gates, and risk mitigation checkpoints before implementation begins.
- [`docs/module_breakdown.md`](docs/module_breakdown.md) — Phase-by-phase module decomposition with preview deliverables and dependencies.
- [`docs/phase0_preview.md`](docs/phase0_preview.md) — Detailed Phase 0 artifact checklist and decision checkpoints prior to implementation.
- [`docs/phase0_charter.md`](docs/phase0_charter.md) — Draft charter covering Phase 0 scope, timeline, RACI, and review cadence for sign-off before build-out, now linking to completed Module 0.1–0.4 sign-off drafts.
- [`docs/phase0/module01_charter_success_metrics.md`](docs/phase0/module01_charter_success_metrics.md) — Finalized success metrics, KPI targets, and quarterly milestones for Module 0.1.
- [`docs/phase0/module02_data_inventory_access_plan.md`](docs/phase0/module02_data_inventory_access_plan.md) — Comprehensive data catalog, access workflow, and budget controls for Module 0.2.
- [`docs/phase0/module03_tech_stack_security_baseline.md`](docs/phase0/module03_tech_stack_security_baseline.md) — Environment blueprint, tooling decisions, and security guardrails for Module 0.3.
- [`docs/phase0/module04_governance_playbook.md`](docs/phase0/module04_governance_playbook.md) — Review cadence, collaboration process, and documentation governance for Module 0.4.
- [`docs/phase0/signoff_log.md`](docs/phase0/signoff_log.md) — Centralized log to capture approval status for each Phase 0 module.
- [`docs/phase1_data_foundation_preview.md`](docs/phase1_data_foundation_preview.md) — Preview package for Phase 1 data pipelines and core agent MVPs, detailing tasks, deliverables, and acceptance criteria.
- [`docs/phase2_industry_sentiment_risk_preview.md`](docs/phase2_industry_sentiment_risk_preview.md) — Preview package for Phase 2 industry intelligence, sentiment pipelines, risk controls, and knowledge base integration.
- [`docs/phase3_portfolio_automation_preview.md`](docs/phase3_portfolio_automation_preview.md) — Preview package for Phase 3 portfolio strategy, backtesting, orchestration, and reporting automation deliverables.
- [`docs/planning_stage_closeout.md`](docs/planning_stage_closeout.md) — Planning-stage closeout report summarizing key decisions, readiness assessments, and Phase 1 launch checklist.

## Getting Started with the Implementation Track
- `configs/data_sources.personal.toml` — Baseline personal-investor data portfolio aligned with the ¥2,000 annual budget constraint. The configuration is consumed by the utility helpers introduced in the first testing module.
- `configs/pipeline.personal.toml` — Phase 1 ingestion plan describing daily/intraday refresh tasks mapped to the approved data sources, used to bootstrap the scheduling layer.
- `src/utils/data_sources.py` — Data source portfolio domain model and budget validation helpers.
- `src/pipelines/planner.py` — Pipeline planning helpers that transform TOML task definitions into orchestrator-ready objects with dependency validation, topological ordering, and cycle detection.
- `src/pipelines/runtime.py` — Runtime facade wiring plans with registered data providers, ready to execute tasks end-to-end.
- `src/data_providers/` — Synthetic provider implementations (Tushare、财联社、国家统计局) 用于在无真实 API 凭据的环境下验证 Phase 1 任务输出。
- `src/examples/personal_pipeline.py` — 示例命令行工具，会注册合成数据源并输出每个任务的元数据与样例记录，帮助验证调度逻辑。
- `src/agents/` — Agent 实现目录，目前提供 Macro Sentinel、Policy Watcher、Industry Mapper、Company Analyst 以及 Risk Controller 预览，用于从流水线结果生成宏观、政策、行业、风险与公司质地报告。
- `src/examples/macro_sentinel_preview.py` — 基于合成数据的 Macro Sentinel 报告脚本，可快速查看宏观与政策面洞察。
- `src/examples/policy_watcher_preview.py` — Policy Watcher 报告脚本，聚焦政策快讯与舆情信号的结构化总结。
- `src/examples/company_analyst_preview.py` — Company Analyst 报告脚本，聚焦核心覆盖公司的财务、估值与情绪信号。
- `src/examples/industry_mapper_preview.py` — Industry Mapper 报告脚本，聚焦重点行业景气、资金与热门主题信号。
- `src/examples/risk_controller_preview.py` — Risk Controller 报告脚本，聚焦组合波动率、集中度与风险预警信号。
- `src/web/server.py` — 基于标准库的轻量 HTTP 服务，暴露宏观、政策、行业与公司巡检报告以及健康检查端点，便于网页或其他客户端集成。
- `tests/test_data_sources.py` — Pytest-based validation covering TOML loading, categorisation, tag indexing, and budget enforcement logic.
- `tests/test_pipeline_planner.py` — Pytest suite ensuring the ingestion plan loader validates dependencies and guards against incorrect data source wiring。
- `tests/test_pipeline_runtime.py` — 集成级测试，验证运行时对全部任务、依赖子集与元数据透传的处理是否符合预期。
- `tests/test_macro_agent.py` — 覆盖 Macro Sentinel 报告生成逻辑，确保核心指标与政策摘要输出稳定。
- `tests/test_policy_agent.py` — 验证 Policy Watcher 聚合政策事件与舆情信号的表现，并确保 Markdown/HTML 输出稳定。
- `tests/test_industry_agent.py` — 覆盖 Industry Mapper 对行业景气、资金流与主题热度信号的聚合逻辑及报告渲染。
- `tests/test_web_server.py` — Web 端到端烟囱测试，验证健康检查以及宏观、政策、行业与公司报告 HTTP 接口可用。

### Running the Test Suite
1. (Optional) create a virtual environment and install pytest if it is not available: `pip install pytest`.
2. Execute the automated checks:
   ```bash
   pytest
   ```

## Sample Pipeline Execution
仓库提供了基于合成数据的 Phase 1 流水线示例，便于快速体验运行效果：

```bash
python -m src.examples.personal_pipeline
```

命令会加载个人投资者配置、注册合成数据源，并输出每个任务的元数据与样例记录，帮助在真实凭据就绪前验证调度逻辑。

### Macro Sentinel 预览

使用 Macro Sentinel Agent 将流水线数据快速转化为宏观巡检报告：

```bash
python -m src.examples.macro_sentinel_preview
```

脚本会自动运行 Phase 1 流水线、汇总核心宏观指标与政策快讯，并输出 Markdown 报告，便于在人工审核前快速浏览模型结论。

### Policy Watcher 预览

针对政策事件与舆情信号，可执行 Policy Watcher 报告脚本：

```bash
python -m src.examples.policy_watcher_preview
```

该命令会整理财联社政策快讯与新闻情绪数据，输出结构化摘要与重点主题列表，帮助快速识别政策受益方向。

### Industry Mapper 预览

针对重点行业的景气度、资金流向与热门主题，可执行 Industry Mapper 报告脚本：

```bash
python -m src.examples.industry_mapper_preview
```

脚本将自动提取行业景气指数、主力资金流和主题热度，生成行业雷达式的 Markdown 报告，辅助判断景气趋势与资金方向。

### Company Analyst 预览

针对核心覆盖公司的财务表现、估值与情绪速览，可执行 Company Analyst 报告脚本：

```bash
python -m src.examples.company_analyst_preview
```

脚本会读取最新流水线输出，生成包含营收、利润、估值与舆情要点的 Markdown 报告，为公司层面的投资判断提供起点。

### Risk Controller 预览

针对组合风险指标与集中度监控，可执行 Risk Controller 报告脚本：

```bash
python -m src.examples.risk_controller_preview
```

脚本会汇总波动率、最大回撤、因子暴露以及风险预警事件，形成风控巡检报告，帮助在组合层面快速确认风险状态。

## Web 预览（HTTP 访问）

仓库提供了一个使用 Python 标准库实现的轻量 HTTP 服务，无需额外依赖即可运行：

```bash
python -m src.web.server
```

服务默认监听 `http://127.0.0.1:8000`。

- 访问 `/health` 可用于探活，例如 `http://127.0.0.1:8000/health`。
- 访问 `/macro/report` 可获得最新的宏观巡检报告（基于合成数据）及对应的 Markdown 内容。
- 访问 `/macro/report?format=html` 可查看自动生成的网页版本，适合作为后续前端集成的占位实现。
- 访问 `/policy/report` 可获取政策速览巡航的 JSON 结果，包含高频主题与情绪摘要。
- 访问 `/policy/report?format=html` 可直接预览政策速览的网页版本，便于嵌入后续前端看板。
- 访问 `/industry/report` 可获取行业景气雷达的 JSON 结果，覆盖景气度、资金流与主题热度。
- 访问 `/industry/report?format=html` 可查看行业雷达的网页版本，便于与宏观/公司报告统一展示。
- 访问 `/company/report` 可查看 Company Analyst 汇总的 JSON 结构化结论。
- 访问 `/company/report?format=html` 可快速预览公司质地巡检的网页版本。
- 访问 `/risk/report` 可获取组合风险雷达的 JSON 结果，包含波动率、暴露与风险事件摘要。
- 访问 `/risk/report?format=html` 可查看组合风险雷达的网页版本，便于与其他报告合并展示。

如需在容器外部或远程浏览器中访问，可通过如下命令将服务绑定至 `0.0.0.0`：

```bash
python -c "from src.web.server import run; run('0.0.0.0', 8000)"
```

服务可作为后续前端/可视化集成的占位实现，待接入真实数据源后可直接复用接口结构。

## Next Steps
1. 结合 `docs/planning_stage_closeout.md` 中的记录确认 Phase 0 审批已闭环，并跟踪 Phase 1 启动状态。
2. 将合成数据提供器替换为真实的 Tushare / 财联社 接口实现，沿用 `PipelineRuntime` 完成端到端验证。
3. 在 Macro Sentinel/Policy Watcher MVP 中整合执行结果与质量监控，扩展测试矩阵并准备接入真实数据源。
