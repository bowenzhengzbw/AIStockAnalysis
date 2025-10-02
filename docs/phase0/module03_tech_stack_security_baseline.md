# Module 0.3 — 技术栈与安全基线（签核稿）

> 本文在 Phase 0 预览的基础上，确定实施阶段的技术栈、环境规格与安全合规要求，为 Phase 1 数据底座建设提供落地指南。

## 1. 架构总览
```
+-----------------+        +--------------------+        +-----------------+
| Data Sources    | -----> | Ingestion Layer    | -----> | Storage Layer   |
| (Tushare,       |        | (Prefect Flows,    |        | (Parquet/       |
|  财联社, 官方)   |        |  Python Scripts)   |        |  DuckDB/CH)     |
+-----------------+        +--------------------+        +-----------------+
                                                   |           |
                                                   v           v
                                          +----------------+  +-------------------+
                                          | Processing &   |  | Metadata / Config |
                                          | Harmonization  |  | (Postgres)        |
                                          +----------------+  +-------------------+
                                                   |
                                                   v
                                          +-------------------+
                                          | Agent Layer       |
                                          | (Macro/Policy/    |
                                          |  Company)         |
                                          +-------------------+
                                                   |
                                                   v
                                          +-------------------+
                                          | Delivery Layer    |
                                          | (Dashboards,      |
                                          |  Reports)         |
                                          +-------------------+
```

## 2. 环境规划
| 层级 | 工具/服务 | 目的 | 备注 |
| --- | --- | --- | --- |
| 数据采集 | Python 3.11 + `tushare`, `httpx`, `pandas`, `polars` | 编写 ETL 脚本 | 使用 `poetry` 管理依赖 |
| 调度编排 | Prefect 2.x | 任务调度、重试、日志 | 本地 Prefect Agent + Web UI | 
| 存储 | Parquet + DuckDB | ODS/DWD 层数据存储与分析 | DuckDB 嵌入式，便于本地分析 |
| OLAP 扩展 | ClickHouse（可选） | 如后续需要高并发查询 | Phase 1 可暂缓 |
| 元数据 | PostgreSQL 14（Docker 或本地实例） | 存储任务日志、数据字典、配置 | 与 Prefect 共用 |
| 可视化 | Streamlit / Plotly Dash | 快速构建看板与报告 | Phase 2 正式搭建 |
| 文档与版本 | Git + Markdown + Obsidian | 管理规划文档与研究笔记 | 现有仓库延用 |

## 3. 环境搭建步骤（Phase 1 前完成）
1. **本地基础设施**
   - 安装 Python 3.11、Poetry、Docker（用于 Postgres）。
   - 创建虚拟环境：`poetry init` → 添加核心依赖。
2. **数据库与存储**
   - 启动 Postgres：`docker run -d --name aistock-postgres -p 5432:5432 -e POSTGRES_PASSWORD=*** postgres:14`。
   - 初始化元数据表（通过 Alembic 脚本，Phase 1 实施）。
   - 准备 `data/` 目录，并在 `.gitignore` 中排除大文件。
3. **Prefect 配置**
   - 安装 Prefect：`poetry add prefect`。
   - 初始化工作区：`prefect profile create aistock`，配置本地 API。
   - 定义默认存储位置（本地文件系统）与并发限制。
4. **密钥管理**
   - 在项目根目录创建 `config/credentials_template.env`，列出 `TUSHARE_TOKEN`, `CAILIAN_API_KEY` 等。
   - 使用 `prefect secret set` 将敏感值注入运行环境。
5. **日志与监控**
   - Prefect 设置任务失败通知（邮件或企业微信 Webhook）。
   - DuckDB/Parquet 操作通过 Python Logging 输出到 `logs/`，便于审计。

## 4. 安全与合规基线
| 项目 | 要求 | 实施方式 |
| --- | --- | --- |
| 身份认证 | 所有账号启用双重验证（若支持） | 财联社、邮箱账号开启二次验证 |
| 密钥管理 | 禁止在仓库中明文存储 API Key | `.env` 加密存储，Git 忽略；Prefect Secret Block |
| 数据分类 | 标记数据敏感级别（公开/付费/敏感） | 数据字典增加 `sensitivity` 字段 |
| 访问控制 | 本地设备使用独立账户，启用磁盘加密 | macOS FileVault / Windows BitLocker |
| 合规记录 | 保留数据使用日志、引用来源 | 报告模板中自动附注数据来源 |
| 备份策略 | 关键配置与脚本定期备份 | Git + 云端私有仓库或本地备份盘 |

## 5. 性能与容量估算
- **数据量**：日线行情（5,000 证券 * 200 字段）≈ 10 MB/日；年度合计 < 4 GB。财务报表约 1 GB/年。
- **计算资源**：本地 16GB RAM + 4 核 CPU 足够；如需回测可考虑云端弹性实例。
- **扩展预案**：数据量超过单机处理能力时，引入 ClickHouse + 云对象存储，将 Prefect Agent 部署至云主机。

## 6. 风险与缓解
| 风险 | 描述 | 应对 |
| --- | --- | --- |
| 本地环境不稳定 | 操作系统更新或依赖冲突 | 使用 Poetry 锁定依赖；定期备份虚拟环境 |
| Prefect 学习曲线 | 初期配置复杂 | 编写内部使用手册；准备模板 Flow |
| 数据泄露 | 本地设备遗失或被攻击 | 启用磁盘加密、密码管理器；定期更换密钥 |
| 合规问题 | 数据使用违反条款 | 审核每个数据源的使用协议；必要时寻求法律意见 |

## 7. 审批记录
- **投资者确认**：`待填写`
- **确认日期**：`待填写`
- **备注**：`如需指定其他工具或部署环境，请在此说明`

本文件获批后，即可按照步骤实施 Phase 1 环境搭建与安全配置。
