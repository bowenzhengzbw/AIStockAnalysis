# AIStockAnalysis Platform

AIStockAnalysis 是一个模块化的多智能体证券分析平台，旨在从宏观、行业到个股提供全链路研究流程。本仓库包含初始版本的后端核心代码，采用金融行业常用的研究标准，如自上而下的宏观-行业-个股框架、政策与风险评估流程以及合规化的风控指标体系。

## 设计目标
- **宏观→微观联动**：整合宏观经济指标、政策文件、行业景气度数据与个股基本面。
- **多 Agent 协作**：引入宏观、行业、个股、舆情、策略、风控等 AI Agent，基于统一的上下文共享机制协作。
- **投资者画像驱动**：根据用户的投资期限、风险偏好与关注主题提供差异化的策略建议。
- **合规与审计**：保留数据血缘与模型版本信息，支持审计追踪与合规审查。

## 仓库结构
```
├── pyproject.toml
├── README.md
└── src
    └── aistockanalysis
        ├── agents
        ├── data
        ├── pipelines
        ├── services
        └── utils
```

## 快速开始
1. 安装依赖
   ```bash
   pip install -e .
   ```
2. 运行演示 API
   ```bash
   uvicorn aistockanalysis.main:app --reload
   ```

## 下一步计划
- 接入真实数据源与 ETL 管线。
- 为各类 Agent 构建特定的 Prompt 与记忆模块。
- 扩展组合优化与风险测算模型。
- 提供前端仪表盘与多语言支持。
