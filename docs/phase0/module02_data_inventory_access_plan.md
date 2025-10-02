# Module 0.2 — 数据源清单与接入计划（签核稿）

> 本文盘点在年度预算 ≤ ¥2,000 情况下的核心数据源、补充渠道与接入流程，确保覆盖宏观、政策、行业、公司、舆情五大维度，并明确后续实施所需的账号与脚本准备。

## 1. 数据源概览
| 类型 | 数据集 | 主来源 | 年度成本 | 刷新频率 | 覆盖范围 | 用途 / Agent |
| --- | --- | --- | --- | --- | --- | --- |
| 行情 | 日线/分钟行情、指数、复权数据 | Tushare Pro 高级会员 | ~¥1,000 | 日度（分钟可需额外配额） | 全市场 A 股、指数 | Macro Sentinel、Risk Controller、Portfolio Strategist |
| 财务 | 财务报表、经营指标、分红配送 | Tushare Pro | 已含在会员费 | 季度/年度 | 主板/创业板/科创板 | Company Analyst |
| 宏观 | GDP、PMI、社融、进出口、金融数据 | 国家统计局、央行、海关总署 | 免费 | 月度/季度 | 全国/行业层级 | Macro Sentinel |
| 政策快讯 | 重大政策、产业扶持、监管动态 | 财联社 Lite | ~¥998 | 实时 | 全国、重点行业 | Policy Watcher、News & Sentiment Scout |
| 公告/研报 | 上市公司公告、调研纪要、研报摘要 | 交易所官网、同花顺 iFinD（可替换为手动导出） | 0（手动导出）~¥1,200（iFinD 个人版） | 日度 | 全市场 | Company Analyst、Policy Watcher |
| 舆情 | 社区讨论、热点事件、情绪标签 | 雪球、微博、36Kr、财联社评论区 | 免费/低成本（雪球 VIP ¥198 可选） | 实时 | 市场热点 | News & Sentiment Scout |
| 行业 | 价格指数、开工率、装机量、销量 | 东方财富数据中心、统计年鉴、协会公开数据 | 免费（需爬虫） | 周/月/季度 | 重点行业 | Industry Mapper（后续阶段） |
| 备用 | 工商、股权结构、专利信息 | 企查查/启信宝 专业版（月付） | ~¥150/月（按需） | 按需 | 指定公司 | Company Analyst（专项研究） |

> 预算策略：核心订阅锁定在 **Tushare Pro + 财联社 Lite ≈ ¥1,998**；其余按需补充，尽量使用免费公开数据或短期订阅以控制成本。

## 2. 接入优先级与时间表
| 阶段 | 数据源 | 目标 | 责任 Agent | 预计完成时间 |
| --- | --- | --- | --- | --- |
| Phase 0 | Tushare Pro | 完成账号开通、API 测试、限额评估 | Data Engineer Agent | 第 2 周 |
| Phase 0 | 财联社 Lite | 完成账号/终端配置，确认推送渠道（邮件/APP） | Policy Watcher | 第 2 周 |
| Phase 1 | 官方宏观数据 | 建立 Prefect 抓取任务、字段映射 | Macro Sentinel | 第 2-3 周 |
| Phase 1 | 公告/研报 | 确定自动化抓取脚本或半自动导入流程 | Company Analyst | 第 3 周 |
| Phase 1 | 舆情源 | 搭建基础爬虫与情绪标签映射 | News & Sentiment Scout | 第 3-4 周 |
| Phase 2 | 行业数据 | 构建行业指标库与手动补充模板 | Industry Mapper | 第 5-8 周 |
| Phase 2 | 备用源 | 针对重点研究主题按月开通并记录成本 | Company Analyst | 按需 |

## 3. 接入流程与脚本规划
1. **账号与密钥管理**
   - 所有付费接口密钥保存在 `.env`，通过 `dotenv` 或 `pydantic` Settings 加载。
   - 建立 `config/credentials_template.env`，用于记录所需键名及申请说明。
   - Prefect Secret Block（本地）存储敏感凭证，运行时注入。
2. **数据拉取脚本结构**
   - `src/data_ingestion/` 下按来源拆分模块：`tushare_client.py`、`macro_official.py`、`news_crawler.py` 等。
   - 每个脚本提供 `fetch(date_range)` 与 `normalize(df)` 两类接口，保证与 DWD 层对接。
   - 对于网页数据，使用 `httpx` + `BeautifulSoup`/`lxml`，并加入随机延迟、User-Agent 轮换。
3. **数据质量与日志**
   - Prefect Flow 在写入前执行 Schema 校验（`pandera`）。
   - 写入成功后记录在 `metadata.ingestion_runs` 表，字段包含 `source`、`records`、`status`、`duration`。
   - 异常情况下触发邮件/IM 提醒，并自动重试（默认 3 次）。
4. **数据存储策略**
   - ODS 层：Parquet 分区按 `source=xxx/trade_date=YYYY-MM-DD`，存放于 `data/ods/`。
   - DWD 层：DuckDB/ClickHouse 表；命名规范 `dwd_{domain}_{dataset}`。
   - ADS 层：面向 Agent 的视图或物化表，由 Prefect 任务定期刷新。

## 4. 预算与续费监控
- 维护 `docs/phase0/data_budget_tracker.csv`（后续自动化），字段：`source`、`cost_per_year`、`billing_cycle`、`renewal_date`、`notes`。
- Prefect 每月 1 日运行 `budget_check` 任务，读取成本配置并输出续费提醒。
- 对按月订阅的数据源，设置提醒提前 5 日评估是否续费或暂停。

## 5. 合规与使用规范
- 遵守数据提供方的使用协议，禁止对外公开或商业化再分发付费数据。
- 对于网页抓取：尊重 robots 协议，控制抓取频率，必要时采用缓存。
- 研究输出中标注数据来源与时间，确保追溯性。

## 6. 风险与应对
| 风险 | 描述 | 应对措施 |
| --- | --- | --- |
| API 限额不足 | 高频调用超出 Tushare 配额 | 调整调度频率；提前缓存历史数据；必要时申请提额 |
| 结构变动 | 网页/接口字段发生变化 | 定期运行结构检测；设置监控报警；保留手动导入模板 |
| 成本上升 | 会员涨价或新增数据需求 | 预留 10% 预算弹性；评估替代源或临时停用 |
| 法规限制 | 政策对数据抓取或使用设限 | 关注监管动态；必要时寻求法律意见 |

## 7. 审批记录
- **投资者确认**：`待填写`
- **确认日期**：`待填写`
- **备注**：`对预算或数据覆盖如有调整需求，请注明`

确认本文件后，可按计划启动账号申请与脚本开发工作。
