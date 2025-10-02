# AI Agent 协作蓝图（规划稿）

> 本文在 `master_plan.md` 与阶段预览文档的基础上，进一步细化 Orchestrator 与各 Agent 之间的协同方式、数据依赖、提示词契约及人机共建流程，确保进入开发阶段前对自动化闭环有统一理解。

## 1. 总览
- **目标**：针对 1-3 年持有期的研究需求，建立可解释、可审计的多 Agent 协作框架，支持宏观—行业—公司—组合的逐层分析，并将政策与舆情信号快速注入决策链路。
- **核心组件**：
  1. **Orchestrator（Codex）** — 统一调度、上下文管理、日志与权限控制。
  2. **数据底座** — ODS/DWD/ADS 三层结构，提供结构化指标、文本嵌入与缓存。
  3. **六大分析 Agent** — Macro Sentinel、Policy Watcher、Industry Mapper、Company Analyst、News & Sentiment Scout、Risk Controller。
  4. **Portfolio Strategist** — 汇总信号构建组合建议，与 Orchestrator 共同完成报告与提醒。
  5. **人类研究者** — 拥有最终决策权，提供估值假设、策略偏好、反馈评分。

## 2. 任务生命周期
1. **触发方式**
   - 定时：周度宏观回顾、月度行业巡检、季度财报、半年度策略复盘。
   - 事件驱动：政策快讯、重大公告、舆情激增、风险阈值触发。
   - 人工请求：研究者通过 CLI/UI 下发即时分析任务。
2. **Orchestrator 流程**
   1. 解析任务类型 → 组装上下文（数据切片、历史输出）。
   2. 生成或调用相应 Prompt 模板 → 调用目标 Agent。
   3. 收集 Agent 输出 → 运行校验器（JSON Schema、指标范围、时间戳）→ 写入知识库。
   4. 依据策略调用 Portfolio Strategist 与 Risk Controller，生成综合建议。
   5. 推送结果（邮件/IM/看板），并等待人工反馈。
3. **反馈闭环**
   - 研究者可在 UI/Markdown 中对每个输出打分并留下备注。
   - Orchestrator 将反馈映射至 Prompt 调整、权重调整或任务重跑。
   - 所有任务留存 `run_id`、版本号，便于复盘与回溯。

## 3. 数据依赖矩阵
| Agent | 必需数据集 | 辅助数据集 | 输出写入 | 更新频率 |
| --- | --- | --- | --- | --- |
| Macro Sentinel | `dwd_macro_dashboard` | 全球指数、商品价格、政策评分 | `ads_macro_view` | 周/月 |
| Policy Watcher | `ods_policy_bulletins` | `ods_company_disclosures`、LLM 嵌入库 | `ads_policy_cards` | 事件驱动 |
| Industry Mapper | `dwd_industry_kpis` | 舆情热度、进出口数据 | `ads_industry_briefs` | 月/季 |
| Company Analyst | `dwd_financial_facts`、`dwd_equity_factors` | 政策事件、舆情摘要 | `ads_company_scorecard` | 季/事件 |
| News & Sentiment Scout | `ods_news_stream` | 社区讨论、搜索指数 | `ads_sentiment_pulse` | 日/事件 |
| Risk Controller | `dwd_equity_factors`、`ads_macro_view` | 组合持仓、政策事件 | `ads_risk_dashboard` | 日/周 |
| Portfolio Strategist | 所有 ADS 输出 | 历史回测结果 | `ads_portfolio_proposals` | 周/月/事件 |

> 注：ADS 层统一使用 JSON/Parquet + DuckDB 视图形式，并通过向量库记录文本嵌入，供多 Agent 共享。

## 4. Prompt 与输出契约
- **Prompt 模板结构**：`背景信息 + 数据摘要 + 任务目标 + 输出格式 + 注意事项`。
- **输出契约**：所有 Agent 同时返回 Markdown 摘要与 JSON 结构，JSON 满足 `schema_registry` 中的定义，字段包括 `timestamp`、`data_source`、`confidence`、`key_findings` 等。
- **示例**（Macro Sentinel）：
  ```json
  {
    "agent": "macro_sentinel",
    "timestamp": "2024-04-15T08:00:00+08:00",
    "macro_phase": "缓慢复苏",
    "drivers": ["社融回升", "PPI 触底"],
    "style_bias": {"growth": 0.6, "value": 0.4},
    "confidence": 0.7,
    "alerts": ["关注房地产政策跟进"]
  }
  ```
- **验证机制**：Orchestrator 在写入前执行 Schema 校验；失败则自动回退并提示人工审核。

## 5. 调度与资源管理
- Prefect 负责常规调度，Orchestrator 处理事件型任务与 Agent 协作。
- 每个 Agent 独立容器或微服务，利用队列（Redis/Message Queue）接收任务。
- 对 LLM 调用设置速率限制与成本监控（记录 Token 消耗、运行时长）。
- 日志统一写入 `logs/agent_runs/` 并定期汇总至观测面板（Prometheus + Grafana / Prefect UI）。

## 6. 人机协作要点
- **人工优先环节**：估值假设、策略约束设定、重大组合调整决策。
- **AI 优先环节**：数据处理、政策文本初筛、指标计算、初稿生成。
- **协作机制**：
  - 研究者可通过“指令面板”对任意 Agent 下达追加任务或修改提示。
  - Orchestrator 记录手动干预信息，供后续回顾分析。
  - 设立“复盘周记”模板，总结 AI 建议与人工决策差异。

## 7. 风险与安全控制
- **权限分层**：Orchestrator 负责鉴权，Agent 只读必要数据；关键操作需双因子确认。
- **异常处理**：当 Agent 输出置信度低于阈值或数据缺失时，标记为“需人工审核”，并阻止自动推送组合建议。
- **合规审计**：保留所有 API 调用日志与数据来源记录，满足监管和版权要求。

## 8. 里程碑对应关系
| 里程碑 | 蓝图要素 | 对应文档/模块 |
| --- | --- | --- |
| Phase 0 收尾 | 权限、日志、Schema 注册 | `phase0/module03`、`phase0/module04` |
| Phase 1 评审 | Prompt 模板、数据契约、核心 Agent 流程 | `phase1_data_foundation_preview.md` |
| Phase 2 扩展 | 行业/舆情知识库与反馈回路 | `phase2_industry_sentiment_risk_preview.md` |
| Phase 3 闭环 | Orchestrator 工作流、组合建议自动化 | `phase3_portfolio_automation_preview.md` |

确认本蓝图后，后续预览与实现将直接引用此协同框架，以减少在编码阶段的结构性调整。
