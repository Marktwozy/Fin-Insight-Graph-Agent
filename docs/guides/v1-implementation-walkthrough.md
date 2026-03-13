# V1 Implementation Walkthrough

## 这次一共做了什么
这次实现把 Fin-Insight-Graph-Agent 从一个想法收敛成了一个可运行、可测试、可观测、可评测的 V1 工程底座。目标不是先做一个只会演示的 toy demo，而是先把未来能持续演进的骨架搭起来。

V1 当前覆盖的能力包括：
- 基于 `Postgres + Qdrant + Neo4j` 的双存储分层数据平面
- 基于 `LangGraph` 的研究问答流和事件驱动分析流
- 结构化短期记忆、压缩与恢复
- `OpenTelemetry + Prometheus + Grafana` 的可观测性骨架
- `RAGAS-style` 评测 harness 与业务指标
- `FastAPI` API 入口、worker 入口、evaluator 入口

## 为什么这样分层
### 1. Postgres 是系统真相源
`Postgres` 负责保存文档、chunk、行情、batch、memory、agent run、evaluation result。这一层解决的是“系统最终以什么为准”。

### 2. Qdrant 是文本检索执行面
`Qdrant` 负责 hybrid text retrieval，把 dense / sparse / metadata payload 组织成统一的文本召回层。它解决的是“怎么把文本候选找出来”。

### 3. Neo4j 是关系扩展层
`Neo4j` 当前先承载 entity / event / topic 邻域扩展，后续可以自然扩展到企业关系、供应链传播和多跳影响分析。它解决的是“怎么走关系、看传播路径”。

## 代码结构怎么理解
### Foundation
- [pyproject.toml](D:/myAgent/.worktrees/fin-insight-v1/pyproject.toml)
- [docker-compose.yml](D:/myAgent/.worktrees/fin-insight-v1/docker-compose.yml)
- [common/settings.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/common/settings.py)
- [common/container.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/common/container.py)

这一层负责项目依赖、配置、容器装配和本地开发体验。

### Canonical data plane
- [document_loader.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/ingestion/document_loader.py)
- [chunker.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/ingestion/chunker.py)
- [market_loader.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/ingestion/market_loader.py)
- [publish_batch.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/ingestion/publish_batch.py)
- [0001_initial_schema.py](D:/myAgent/.worktrees/fin-insight-v1/infra/migrations/versions/0001_initial_schema.py)
- [0002_batch_publications.py](D:/myAgent/.worktrees/fin-insight-v1/infra/migrations/versions/0002_batch_publications.py)

这一层解决“数据怎么进系统”和“每天发布哪一个 batch”。

### Retrieval plane
- [text_retriever.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/retrieval/text_retriever.py)
- [graph_retriever.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/graph/graph_retriever.py)
- [evidence_merger.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/retrieval/evidence_merger.py)
- [reranker.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/retrieval/reranker.py)

这一层把文本、图谱、市场上下文统一成 `EvidenceBundle`，再做 merge 和 rerank，保证下游 graph node 面对的是统一证据对象，而不是杂乱的存储客户端。

### Agent and memory plane
- [research.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/agent/graphs/research.py)
- [event.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/agent/graphs/event.py)
- [models.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/memory/models.py)
- [compression.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/memory/compression.py)
- [checkpointer.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/memory/checkpointer.py)

这里是整个 agent 的推理中枢。
研究问答流负责把问题改写、拆解、检索、生成回答。
事件流负责把事件标准化、检索证据、做影响草稿、执行 bounded reflection、必要时修订。

记忆没有走“纯对话自动提取”的路线，而是采用结构化快照：`confirmed_facts`、`open_hypotheses`、`evidence_pointers`、`pending_questions` 等。这么做的原因是金融分析更强调可审计和可恢复，而不是只追求自动记忆。

### Observability and evaluation
- [middleware.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/observability/middleware.py)
- [metrics.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/observability/metrics.py)
- [runner.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/evaluation/runner.py)
- [main.py](D:/myAgent/.worktrees/fin-insight-v1/apps/evaluator/main.py)

这一层解决两个问题：
- 在线上如何看见 agent 在做什么
- 离线如何持续验证 agent 是否变好

当前已经把 request latency、graph node latency、token/cost、retrieval candidate、reranker latency、reflection trigger、unsupported claim 等指标注册好；同时也有 research / event 两套 smoke evaluation suite。

## 两条主链路是怎么跑的
### 研究问答流
入口是 `/v1/query`，当请求里有 `question` 时进入 research graph。
大致流程是：
`query -> rewrite -> decompose -> multi-source retrieval -> rerank -> grounded draft`

### 事件驱动流
同样走 `/v1/query`，当请求里主要是 `event_input` 时进入 event graph。
大致流程是：
`event normalize -> multi-source retrieval -> impact draft -> reflection check -> single revision gate`

这里的 reflection 不是无限自我反思，而是有界的一次检查与修订。它主要压制 unsupported certainty，比如把没有足够证据支撑的绝对判断压回到更谨慎的表达。

## 这次工程实现的关键取舍
### 1. 先做工程底座，而不是先接满真实数据源
这样可以先把 API、存储、检索、评测、可观测性、测试体系搭稳，后面接真实 SEC/新闻/行情数据时改动面更小。

### 2. 先做结构化 memory，而不是把 Mem0 当主记忆
因为当前场景更像分析系统，不是泛聊天助手。结构化记忆更适合保留“已确认事实”和“待验证假设”的边界。

### 3. 先做 heuristic evaluation adapter，但保留 RAGAS 演进入口
当前 harness 已经用 RAGAS 风格指标名和业务指标把实验框架立住，后续只需要把 metric adapter 换成真实线上评测配置，而不用重写整套 evaluator 框架。

## 你可以怎么继续学这份代码
推荐按下面顺序看：
1. 先看 [README.md](D:/myAgent/.worktrees/fin-insight-v1/README.md)
2. 再看 [common/models.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/common/models.py)，理解统一证据对象
3. 看 [research.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/agent/graphs/research.py) 和 [event.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/agent/graphs/event.py)
4. 回头看 retrieval 和 memory 模块，理解 agent 依赖的数据形状
5. 最后看 [runner.py](D:/myAgent/.worktrees/fin-insight-v1/src/fin_insight_graph_agent/evaluation/runner.py) 和 observability 模块，理解“如何度量它是否好用”

## 当前还没有做满的地方
这版是 V1 foundation，不是最终版投研系统。当前仍然是这些边界：
- 还没有接真实生产级金融数据采集源
- reranker 和 embedding 还是 adapter 化骨架，尚未接真实线上模型配置
- reflection 还是单次 bounded gate，不是更强的 verifier pipeline
- graph schema 还没有扩展到完整企业关系和供应链传播
- evaluation 目前是 smoke-friendly harness，后续还要接真实 case curation 和实验管理

## 这份代码最值得保留的东西
如果后面你继续演进，我最建议保留的是这些设计原则：
- 统一证据对象，不让下游 node 直接依赖底层存储细节
- 把 Postgres 作为 canonical source，而不是让向量库变成真相源
- 让 observability 和 evaluation 从第一天就是正式模块，而不是上线前临时补
- 让 memory 保留事实 / 假设 / 证据引用之间的边界
- 让 reflection 做有界质检，而不是无限生成