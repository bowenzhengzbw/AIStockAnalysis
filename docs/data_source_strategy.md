# 数据源整合策略（个人投资者版）

> 目标：在年费不超过 ¥2,000 的前提下，搭建覆盖宏观、行业、公司与舆情的多源数据底座，为 1-3 年期 A 股投资提供可靠、可复现的输入。

## 1. 成本与角色映射
| 数据源 | 年费估算 | 核心覆盖 | 支持的 Agent | 集成方式 |
| --- | --- | --- | --- | --- |
| **Tushare Pro 高级会员** | ~¥1,000 | 行情、财务、指数、宏观指标 | Macro Sentinel、Company Analyst、Risk Controller、Portfolio Strategist | 官方 SDK (`tushare`)，Prefect 定时任务，落地至 ODS→DWD 表 |
| **财联社 Lite**（或雪球 VIP） | ~¥980 | 政策快讯、事件点评、舆情摘要 | Policy Watcher、News & Sentiment Scout | API / RSS / 抓取脚本 → LLM 摘要 → 事件卡片 |
| **国家统计局、央行、发改委公开数据** | 免费 | GDP、社融、物价、行业产出等宏观指标 | Macro Sentinel、Industry Mapper | `requests` + 定制解析器，加入结构变动监控 |
| **东方财富数据中心 / 同花顺导出** | 免费/低成本 | 公告、行业指标、估值分位 | Company Analyst、Industry Mapper | 批量导出（CSV/Excel）→ 清洗脚本 → 统一字段 |
| **雪球社区 & 微博热搜** | ¥198（雪球 VIP，可选） | 投资者舆情、热点事件 | News & Sentiment Scout | 爬虫/开放 API → 文本去噪 → 情绪打分 |
| **企查查（月度开通，可选）** | <¥150/ 月 | 工商变更、股权结构、司法风险 | Company Analyst、Risk Controller | 按需导出 → 事件库备查 |

> 核心支出聚焦在 Tushare Pro + 财联社 Lite ≈ ¥1,980，其他数据根据研究周期择优启用，确保整体预算可控。

## 2. 数据层设计与刷新频率
- **ODS 层**：保留原始字段与 `source`、`cost_center` 元数据；按 `dataset/交易日` 分区存储。
- **DWD 层**：统一口径（复权、币种、行业分类）、补齐缺失值、标记异常；宏观数据按月/季对齐。
- **ADS 层**：输出 Macro View、Policy Event、Company Scorecard 等 Agent 所需的宽表/索引。
- **刷新策略**：
  - 日度：行情、公告、政策快讯、舆情。
  - 周度：行业指标、事件聚合、风险报告。
  - 月/季度：宏观指标、财务报表、估值回溯。

## 3. 接入与调度流程
1. **凭证与配置**：
   - `.env` 保存 API Token（`TUSHARE_TOKEN`、`CLS_TOKEN` 等）。
   - `configs/data_sources.personal.toml` 维护预算与来源列表，供测试与监控逻辑读取。
2. **调度层**：
   - Prefect 流程分为 `daily_ingest`、`weekly_refresh`、`event_listener`，由 Orchestrator 根据需求触发。
   - 失败任务自动重试 3 次；持续失败写入 `data_quality_logs` 并通知人工。
3. **质量监控**：
   - 覆盖率、更新延迟、指标跳变三类监控；结合 Agent 输出进行交叉验证（例如政策事件触发后是否出现行业资金流变化）。
4. **成本监控**：
   - Prefect 任务记录 API 调用次数与估算费用，月度生成 `data_budget_report`。

## 4. Agent 数据映射清单
| Agent | 主要输入 | 关键派生字段 | 校验点 |
| --- | --- | --- | --- |
| Macro Sentinel | `macro_dashboard`（Tushare + 官方）、全球指数 | 领先/同步/滞后指标、经济周期标签 | 指标覆盖率 ≥95%，缺失补齐策略记录 |
| Policy Watcher | 财联社快讯、政策原文 | 摘要、力度/紧迫性评分、受益行业 | 摘要与原文双存档，人工抽检准确率 ≥85% |
| Industry Mapper | 行业产出、价格指数、舆情热度 | 景气度评分、催化事件列表 | 行业分类与证券代码映射一致 |
| Company Analyst | 财报、估值分位、公告事件 | 财务四象限得分、估值偏离度、政策敏感度 | 指标计算复现性，估值对比逻辑透明 |
| News & Sentiment Scout | 快讯、雪球/微博文本 | 情绪打分、事件类型 | 情绪阈值与人工标注一致性 ≥80% |
| Risk Controller | 行情、因子、政策事件 | 风险预算占用、压力测试结果 | 数据延迟 < T+1，场景参数可追溯 |
| Portfolio Strategist | Macro/Policy/Company 汇总信号 | 信号加权、候选组合、调仓建议 | 信号来源可追踪，权重配置记录 |

## 5. 里程碑与评审要点
1. **准备阶段（第 0-1 周）**：完成付费账户开通、API 连接性测试、数据字典初稿。
2. **数据管道搭建（第 2-3 周）**：完成行情/财务/政策/舆情的 ODS→DWD 流程，生成首份质量报告。
3. **Agent 联调（第 4-5 周）**：Macro/Policy/Company Agent 能调用 ADS 数据形成周报；记录人工反馈。
4. **预算回顾（第 6 周）**：生成首份 `data_budget_report`，评估调用成本与剩余额度。

## 6. 风险与缓解措施
- **接口策略变更**：订阅官方公告、设置结构变更报警；必要时准备备用爬虫方案。
- **成本超支**：对高频接口设置上限，超限自动退化为缓存数据；引入调用黑名单机制。
- **数据质量下降**：引入交叉验证（例如 Tushare 与东方财富行情比对），人工审阅关键指标。
- **法规与合规**：记录所有数据来源及使用条款，定期复核个人投资者使用限制。

## 7. 下一步
- 审阅并确认核心数据源组合是否满足研究需求。
- 如需增补特定行业/另类数据，请在 Phase 1 开发前指出，以便提前纳入预算与调度计划。
- 一旦规划确认，将在 `phase1_data_foundation_preview.md` 的基础上补充实施手册与代码骨架。
