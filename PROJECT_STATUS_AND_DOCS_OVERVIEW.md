# Fin-Insight-Graph-Agent 项目文档与进度总览

## 1. 文档结构总览

### 根目录核心文件
- [README.md](D:/myAgent/.worktrees/fin-insight-v1/README.md)
  项目总入口，包含架构摘要、本地开发步骤、`/v1/query` 示例、source sync 和 batch publish 命令。
- [.env.example](D:/myAgent/.worktrees/fin-insight-v1/.env.example)
  环境变量模板，已经包含 OpenAI-compatible 与阿里云百炼兼容配置示例。
- [docker-compose.yml](D:/myAgent/.worktrees/fin-insight-v1/docker-compose.yml)
  本地基础设施编排，当前覆盖 `Postgres / Qdrant / Neo4j / Prometheus / Grafana`。
- [pyproject.toml](D:/myAgent/.worktrees/fin-insight-v1/pyproject.toml)
  Python 工程依赖与工具配置入口。
- [alembic.ini](D:/myAgent/.worktrees/fin-insight-v1/alembic.ini)
  数据库迁移配置。
- [Makefile](D:/myAgent/.worktrees/fin-insight-v1/Makefile)
  常用开发命令封装。

### `docs/` 文档目录
- [0001-postgres-qdrant-neo4j.md](D:/myAgent/.worktrees/fin-insight-v1/docs/adr/0001-postgres-qdrant-neo4j.md)
  ADR，记录为什么选择 `Postgres + Qdrant + Neo4j` 三平面架构。
- [v1-technical-brief.md](D:/myAgent/.worktrees/fin-insight-v1/docs/reports/v1-technical-brief.md)
  偏汇报/评审风格的技术说明，适合给导师、面试官、评审看。
- [v1-implementation-walkthrough.md](D:/myAgent/.worktrees/fin-insight-v1/docs/guides/v1-implementation-walkthrough.md)
  偏学习导览的实现说明，适合快速理解项目模块分层。
  当前风险：这个文件目前存在编码异常，中文显示乱码，建议后续修复为 UTF-8 正常内容。
- [local-dev.md](D:/myAgent/.worktrees/fin-insight-v1/docs/runbooks/local-dev.md)
  本地开发 runbook，包含启动栈、基础检查、测试命令。
- [daily-batch-ops.md](D:/myAgent/.worktrees/fin-insight-v1/docs/runbooks/daily-batch-ops.md)
  日级 batch 运行手册，已经包含 source sync、multi-company batch、publish 和 query 检查命令。

### 代码目录
- `apps/`
  进程入口层，包含 API、worker、evaluator。
- `src/fin_insight_graph_agent/`
  业务主代码。
- `infra/`
  迁移与基础设施相关资源。
- `tests/`
  单测、集成测试、评测测试。
- `examples/`
  示例配置文件，目前包含多公司 source sync 的 target 清单。

### 示例与辅助文件
- [source_sync_targets.example.json](D:/myAgent/.worktrees/fin-insight-v1/examples/source_sync_targets.example.json)
  多公司 batch 同步示例输入。

## 2. 当前已完成事项

### 2.1 工程基础设施
- 已完成 Python 工程化脚手架，包括 `uv / pytest / ruff / mypy / alembic`。
- 已完成本地开发基础设施栈：
  - `Postgres`
  - `Qdrant`
  - `Neo4j`
  - `Prometheus`
  - `Grafana`
- 已完成数据库 schema 与迁移，支持文档、chunk、行情、batch、评测、质量门禁等核心对象。

### 2.2 数据平面
- 已完成 canonical 数据底座，`Postgres` 作为系统真相源。
- 已完成文档 ingestion、chunking、market ingestion 和 batch publish 流程。
- 已完成真实官方数据源接入：
  - `SEC EDGAR submissions`
  - `SEC EDGAR company facts`
  - `Alpha Vantage daily bars`
  - `Alpha Vantage news sentiment`
- 已完成单公司 source sync。
- 已完成多公司 `source-sync-batch`，可以将多家公司同步到同一 `batch_id`。

### 2.3 检索与图谱
- 已完成 `Qdrant` hybrid retrieval。
- 已完成 `Neo4j` 图投影与图邻域检索。
- 已完成新闻到图谱的抽取与投影：
  - 公司实体
  - 事件
  - topic
- 已增强新闻抽取规则，支持多实体、多 topic、多事件类型。
- 已完成图检索质量集成测试：
  `source sync -> 新闻抽取 -> Neo4j -> GraphRetriever`

### 2.4 Agent 主链路
- 已完成 `LangGraph` 双入口：
  - `research graph`
  - `event graph`
- 已完成多路召回融合：
  - 文本召回
  - 图召回
  - 市场上下文
- 已完成 reranker 接口层。
- 已完成 bounded reflection 基础层。

### 2.5 记忆与上下文治理
- 已完成结构化短期/长期记忆基础模型。
- 已完成 memory checkpointer。
- 已完成结构化压缩与恢复能力。
- 已明确采用“结构化记忆对象”作为主记忆系统，而不是自动事实抽取做 canonical memory。

### 2.6 可观测性与评测
- 已完成 `OpenTelemetry + Prometheus + Grafana` 基础埋点与指标骨架。
- 已完成 research/event 评测 harness。
- 已完成 graph retrieval benchmark。
- 已完成 graph benchmark threshold gate。
- 已完成 graph quality gate 接入 batch publish。

### 2.7 真实模型接入
- 已完成 OpenAI-compatible 模型运行时配置。
- 已完成真实 embedding provider 接入 `Qdrant` 建索引链路。
- 已完成真实 LLM 接入 `/v1/query`。
- 已在本地用阿里云百炼兼容接口完成 live smoke：
  `real embedding -> Qdrant -> LangGraph -> real LLM -> /v1/query`

## 3. 当前阶段结论

当前项目已经不再是 toy 级原型，而是具备以下特征的 `V1 engineering foundation`：
- 有真实数据接入能力
- 有真实模型接入能力
- 有可追踪的 batch 机制
- 有图谱检索与质量门禁
- 有 API / worker / evaluator 三类入口
- 有本地开发、运行、评测和发布手册

简化判断：
- `Phase 1`：基本完成
  已将 graph quality gate 真正接进 batch publish。
- `Phase 2`：部分完成且已经跨过关键里程碑
  已接入真实 embedding 和真实 LLM，但真实 reranker、统一 prompt/version 追踪深化、生产级 smoke/回归还未完全做完。
- `Phase 3`：刚起步
  目前图谱还主要是新闻抽取得到的 `entity/event/topic` 投影，企业关系图远未完整。
- `Phase 4`：部分起步
  已有 single-company 和 multi-company batch sync，但幂等、调度、去重、失败重试仍未完善。
- `Phase 5`：部分起步
  已有 smoke benchmark 和 graph gate，但 curated regression 与长期回归体系还未建设完成。

## 4. 当前未完成待办事项

### 高优先级待办
- 接入真实 reranker 服务并做端到端验证。
- 将 research/event 评测结果与真实模型版本、prompt 版本、batch 版本做更完整绑定。
- 为真实 source sync 增加幂等控制，避免重复写入同 batch 的文档、chunk、图投影和向量。
- 为 source sync 增加失败重试与错误恢复策略。
- 将 batch 同步做成稳定的日级调度任务，而不只是手工命令触发。

### 图谱增强待办
- 扩展企业关系图谱，不再只停留在新闻投影：
  - company-to-company
  - supplier/customer
  - policy/region/industry theme
- 将“同事件关联公司”扩展成“影响传播路径”。
- 为事件分析补 path explanation，支持回答“为什么这家公司会被牵连”。

### 数据治理待办
- 增加新闻去重。
- 增加文档版本控制。
- 增加 batch 级 trace 和 source sync 审计字段。
- 评估是否引入更多真实新闻源，而不仅依赖 `Alpha Vantage news sentiment`。

### 评测体系待办
- 将 smoke benchmark 扩成 curated case 数据集。
- 建立 regression baseline。
- 将 quality gate 从 graph retrieval 扩展到 research/event 主链路。
- 将评测结果接入 CI 或定时 batch 运行。

### Agent 能力待办
- 增强 reflection，从 bounded gate 升级成更强的 grounded verifier pipeline。
- 完善事件流对多跳关系、关系强弱和时间错配的处理。
- 提升 research flow 的 query decomposition、实体抽取与 market context 联动。

### 文档待办
- 修复 [v1-implementation-walkthrough.md](D:/myAgent/.worktrees/fin-insight-v1/docs/guides/v1-implementation-walkthrough.md) 的编码问题。
- 补一份“从 0 到 1 跑通真实 batch + query”的中文操作手册。
- 补一份“模块依赖关系图”或 mermaid 架构图文档。

## 5. 推荐的下一步优先级

### 建议按这个顺序推进
1. 真实 reranker 接入与验证
   原因：当前 embedding 和 LLM 已经接通，reranker 是提升回答质量最直接的一环。
2. source sync 的幂等、重试、去重
   原因：这是从“能跑”走向“稳定工程任务”的关键。
3. 扩展企业关系图谱与传播路径
   原因：这是项目从金融问答底座跃迁到企业图谱分析智能体的核心。
4. 完善评测与回归体系
   原因：后续能力变强后，如果没有回归门禁，质量会难以稳定。

## 6. 近期关键提交摘要

- `31aca07` `feat: add multi-company source sync batch`
- `7d8d6f7` `feat: add local env model config support`
- `a27b16c` `feat: index source sync chunks with configured embeddings`
- `c8a9f26` `feat: add configurable model providers`
- `88c89b2` `feat: gate batch publication on graph quality`
- `03bd1f8` `feat: add graph benchmark quality gates`
- `9e40881` `feat: add graph retrieval benchmark`
- `533da2a` `test: validate source sync graph retrieval quality`
- `838f3fa` `feat: improve news graph extraction rules`
- `16f591d` `feat: project news entities into neo4j`
- `39b08ea` `feat: add news ingestion to source sync`
- `a1eb51f` `feat: add official source sync job`

## 7. 一句话总结

项目当前已经完成了“工程级金融智能体底座”的主体骨架，下一阶段的重点不再是从 0 搭框架，而是围绕“更稳定的真实数据编排、更强的检索质量、更完整的企业关系图谱、更严格的评测回归”持续增强。