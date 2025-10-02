# Phase 1 预览：数据底座与核心 Agent MVP

> 本文聚焦 Phase 1（数据底座与 Macro/Policy/Company 三大 Agent MVP）的预览包，明确任务分解、工件清单、技术栈与评审标准，确保进入实施前对齐期望。

## 1. 目标概述
- 在预算内打通 **Tushare Pro + 财联社 Lite/雪球 VIP + 免费公开源** 的数据采集、治理与存储流程。
- 交付 Macro Sentinel、Policy Watcher、Company Analyst 的最小可行版本（MVP），具备定期输出结构化结论的能力。
- 为后续行业扩展、舆情分析、风控模块奠定统一数据模式和调度框架。

## 2. 数据管道与存储设计
### 2.1 数据集分类
| 层级 | 数据集 | 来源 | 更新频率 | 用途 |
| --- | --- | --- | --- | --- |
| ODS | `market_quotes` | Tushare Pro 行情 | 日度 | 行情回测、组合风控 | 
| ODS | `financial_reports` | Tushare Pro 财报 | 季度 | 财务建模、估值 | 
| ODS | `macro_indicators` | 统计局/央行公开数据 | 月/季 | 宏观判断 | 
| ODS | `policy_bulletins` | 财联社 Lite / 官方文件 | 事件驱动 | 政策解读 | 
| ODS | `company_disclosures` | 交易所公告、同花顺导出 | 日度 | 信息面分析 | 
| DWD | `equity_factors` | 量价 + 财务衍生因子 | 日/周 | 风险/选股因子 | 
| DWD | `macro_dashboard` | 清洗后的宏观指标 | 周/月 | Macro Sentinel 输入 | 
| DWD | `policy_insights` | LLM 摘要与影响标签 | 事件驱动 | Policy Watcher 输出 | 
| ADS | `macro_view` | 宏观观点与风格建议 | 周/月 | 投资决策参考 | 
| ADS | `company_scorecard` | 财务+估值+信息面评分 | 季度/事件 | Company Analyst 输出 | 

### 2.2 技术栈落地
- **存储**：DuckDB（本地分析）+ Parquet（中间存储）+ PostgreSQL（元数据、调度日志）。
- **调度**：Prefect 2.x；配置本地 Agent + 定时任务，支持手动触发。
- **工具库**：`tushare`, `requests`, `pandas/Polars`, `SQLAlchemy`, `prefect`。
- **配置管理**：`.env` 存放 API Token，使用 `pydantic` / `dynaconf` 读取。

### 2.3 数据质量控制
- 缺失值校验：交易日完整性、财务季度齐全、宏观指标更新时间。
- 异常检测：价格/指标跳变 > 3σ 触发告警，记录在 `data_quality_logs`。
- 重跑策略：Prefect 任务失败自动重试 3 次，失败后记录并推送通知（邮件/IM）。

## 3. Agent MVP 范围
### 3.1 Macro Sentinel MVP
- **输入**：`macro_dashboard`、全球指数（Tushare 指数接口）、政策事件摘要。
- **处理流程**：
  1. 计算领先/同步/滞后指标的环比、同比变化。
  2. 结合政策力度评分（来自 Policy Watcher），给出经济周期阶段判断。
  3. 输出风格建议（偏成长/价值、大小盘、行业权重倾向）。
- **输出格式**：Markdown 周报 + JSON (`macro_view`) 包含指标、结论、信心评分。

### 3.2 Policy Watcher MVP
- **输入**：政策/公告文本、财联社快讯。
- **处理流程**：
  1. 文本抓取 → LLM 摘要（政策意图、执行主体、时间框架）。
  2. 行业映射：基于预设关键词 + 公司行业表，生成受益/受损列表。
  3. 影响评分：力度（1-5）、紧迫性（小时/天/周）、覆盖度（行业/公司数量）。
- **输出格式**：事件卡片（Markdown + JSON），推送至知识库与告警渠道。

### 3.3 Company Analyst MVP
- **输入**：`financial_reports`、`market_quotes`、政策/公告事件。
- **处理流程**：
  1. 自动计算财务指标（ROE、ROIC、现金比率、毛利率趋势等）。
  2. 估值监测：当前估值与 3 年均值、行业分位对比。
  3. 信息面整合：关联 Policy Watcher 事件，判断短期催化或风险。
  4. 生成质地评分（财务 40%、估值 30%、信息面 20%、政策敏感度 10%）。
- **输出格式**：公司卡片（Markdown）+ 结构化评分 JSON (`company_scorecard`)。

## 4. 任务分解与里程碑
| 周次 | 任务 | 主要交付物 | 依赖 | 责任 |
| --- | --- | --- | --- | --- |
| 第 1 周 | 环境搭建、API 测试、Prefect 基础配置 | `.env` 模板、调度示例脚本 | Phase 0 charter 审批 | 工程 | 
| 第 2 周 | 行情/财务/宏观数据管道 | ETL 脚本、Parquet 数据、质量报告 | Tushare 授权 | 数据 | 
| 第 3 周 | 政策/公告采集与 NLP 摘要 | 抓取脚本、摘要模型、事件卡片模板 | 财联社/公开源接入 | 数据 + NLP | 
| 第 4 周 | Agent MVP 规则实现与输出模板 | Macro/Policy/Company 周报样例 | 数据管道稳定 | 研究 | 
| 第 5 周 | 集成与复盘 | Phase 1 评审材料、回顾报告 | 前续任务完成 | 所有人 | 

## 5. 评审与验收标准
1. **数据完整性**：样例周内数据覆盖 ≥ 95%，失败任务有重试与日志。
2. **Agent 输出质量**：
   - Macro Sentinel：宏观指标与结论一致，提供定量支撑。
   - Policy Watcher：事件卡片包含摘要、影响、受益标的；延迟 < 1 天。
   - Company Analyst：财务指标与估值计算可复现，评分逻辑透明。
3. **可操作性**：Prefect 流程可手动触发；提供 README/文档说明。
4. **安全合规**：API 密钥未入库；数据来源/版权在文档中注明。

## 6. 风险与对策
- **数据源限制**：财联社接口变动 → 保留网页抓取/备用 RSS；监控结构变化。
- **调度稳定性**：本地环境易受网络影响 → 引入离线缓存与失败重试。
- **LLM 成本与隐私**：优先使用本地/开放模型；敏感文本脱敏后处理。
- **人工审核压力**：设置每周固定窗口人工审阅 Agent 输出，反馈优化提示词。

## 7. 下一步行动
- 审阅本预览文档，确认任务排期与交付物是否符合预期。
- 明确首选的政策资讯源（财联社 Lite 或雪球 VIP 等）。
- 针对 Prefect 与存储技术栈，如有指定偏好请告知，以便在实施前调整。
