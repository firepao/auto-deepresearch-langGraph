# LangGraph Migration Roadmap

本文档是 `auto-deepresearch-langGraph` 的 LangGraph 重构开发路线。目标不是一次性推倒重写，而是在保持当前 Deep Research 功能可运行的前提下，把手写编排逐步迁移到 LangGraph。

## 0. 迁移结论

当前项目适合迁移到 LangGraph。

原因：

- 当前 `DeepResearchAgent` 已经是典型的多步骤研究工作流；
- 代码已经有明确的阶段：Planner、Search、Summarizer、Reporter、Note；
- 后端已有共享状态对象 `SummaryState` 和任务对象 `TodoItem`；
- 前端通过 SSE 消费过程事件，LangGraph 支持流式输出和自定义事件；
- 后续需要 checkpoint、恢复、人类确认、调试追踪，这些正是 LangGraph 的优势。

推荐策略：

1. 先保留 HelloAgents 的 LLM 和 Tool 实现；
2. 只把 `DeepResearchAgent` 的流程编排替换为 LangGraph；
3. 保持 FastAPI 接口和前端 SSE 事件尽量不变；
4. 等图工作流跑通后，再逐步替换为 LangChain/LangGraph 原生模型和工具。

## 1. 现状基线

当前主要文件：

```text
backend/src/main.py
backend/src/agent.py
backend/src/models.py
backend/src/config.py
backend/src/services/planner.py
backend/src/services/search.py
backend/src/services/summarizer.py
backend/src/services/reporter.py
backend/src/services/tool_events.py
frontend/src/App.vue
frontend/src/services/api.ts
```

当前流程：

```text
topic
  -> DeepResearchAgent.run / run_stream
  -> PlanningService.plan_todo_list
  -> for each TodoItem:
       dispatch_search
       prepare_research_context
       SummarizationService.summarize_task / stream_task_summary
  -> ReportingService.generate_report
  -> optional NoteTool persistence
  -> FastAPI SSE response
  -> Vue frontend display
```

当前 HelloAgents 依赖点：

- `HelloAgentsLLM`
- `ToolAwareSimpleAgent`
- `ToolRegistry`
- `SearchTool`
- `NoteTool`
- tool call listener / tracker

这些依赖不必第一阶段全部替换。

## 2. 目标架构

目标后端结构：

```text
backend/src/
├── graph/
│   ├── __init__.py
│   ├── state.py          # ResearchState, TaskState, event models
│   ├── nodes.py          # graph nodes wrapping planner/search/summarizer/reporter
│   ├── workflow.py       # graph construction and compile
│   ├── streaming.py      # LangGraph event -> existing SSE event mapping
│   └── checkpoints.py    # optional checkpointer config
├── services/
│   └── ...               # keep existing service implementations first
└── agent.py              # compatibility wrapper used by FastAPI
```

目标工作流：

```text
START
  -> plan_tasks
  -> dispatch_workers
      -> search_task
      -> summarize_task
      -> persist_task_note
  -> collect_task_results
  -> write_report
  -> persist_report
  -> END
```

可以先实现为简单顺序图，再升级为动态 worker 并行图。

## 3. 不变更约束

迁移前期必须尽量保持这些外部契约不变：

- `POST /research`
- `POST /research/stream`
- `ResearchRequest`
- `ResearchResponse`
- 前端消费的 SSE 事件类型：
  - `status`
  - `todo_list`
  - `task_status`
  - `sources`
  - `task_summary_chunk`
  - `tool_call`
  - `report_note`
  - `final_report`
  - `done`
  - `error`

只要这些契约稳定，前端可以暂时不重构。

## 4. 开发阶段

### Phase 0: 基线清理

目标：先让项目可维护、可验证。

任务：

- 修复源码和 `.env.example` 中的中文乱码；
- 明确 Python 依赖安装方式，确认 `uv sync` 可用；
- 明确 Node 依赖安装方式，确认 `npm install && npm run build` 可用；
- 增加根目录开发说明，区分后端和前端启动命令；
- 建立最小 `.env.example`，覆盖：
  - `LLM_PROVIDER`
  - `LOCAL_LLM`
  - `LLM_MODEL_ID`
  - `LLM_API_KEY`
  - `LLM_BASE_URL`
  - `OLLAMA_BASE_URL`
  - `LMSTUDIO_BASE_URL`
  - `SEARCH_API`
  - `ENABLE_NOTES`
  - `NOTES_WORKSPACE`
  - `MAX_WEB_RESEARCH_LOOPS`
  - `FETCH_FULL_PAGE`

验收：

- 后端能启动；
- `/healthz` 返回 `{"status":"ok"}`；
- 前端能构建；
- `dev-log/` 记录验证结果。

### Phase 1: 契约冻结和测试基线

目标：迁移前先知道“什么不能破”。

任务：

- 为 `/research/stream` 定义事件协议文档；
- 用一个固定 topic 记录一次样例 SSE 事件序列；
- 给以下模块增加最小测试：
  - `Configuration.from_env`
  - `PlanningService._extract_tasks`
  - `deduplicate_and_format_sources`
  - `format_sources`
  - `strip_thinking_tokens`
- 给前端 API 解析逻辑保留一个最小 fixture 或说明。

建议新增：

```text
docs/sse-event-contract.md
backend/tests/
backend/tests/test_config.py
backend/tests/test_planner.py
backend/tests/test_utils.py
```

验收：

- 不调用真实 LLM 和搜索服务也能跑基础测试；
- 已记录当前事件契约；
- 确认前端依赖的字段不会在迁移中随意改名。

### Phase 2: 引入 LangGraph 但不替换行为

目标：安装依赖并建立空图骨架。

任务：

- 在 `backend/pyproject.toml` 增加 `langgraph` 和必要的 `langchain` 依赖；
- 新增 `backend/src/graph/state.py`：
  - `ResearchState`
  - `ResearchTask`
  - `ResearchEvent`
- 新增 `backend/src/graph/workflow.py`，先实现最小可编译 graph；
- 新增 feature flag：
  - `USE_LANGGRAPH_WORKFLOW=false`
- `DeepResearchAgent` 根据配置选择：
  - false：走旧流程；
  - true：走 LangGraph workflow。

验收：

- 默认仍走旧流程；
- 打开 feature flag 后可以跑最小图；
- 不影响现有 FastAPI 接口。

### Phase 3: 节点化现有服务

目标：把现有服务包成 LangGraph node。

节点设计：

```text
plan_tasks(state) -> {"todo_items": [...]}
search_task(state) -> {"task_results": [...]}
summarize_task(state) -> {"task_results": [...]}
write_report(state) -> {"report_markdown": "..."}
persist_report(state) -> {"report_note_id": "...", "report_note_path": "..."}
```

第一版可以使用顺序执行：

```text
START -> plan_tasks -> run_all_tasks -> write_report -> persist_report -> END
```

其中 `run_all_tasks` 内部仍可以复用当前 for-loop 逻辑，先降低迁移风险。

验收：

- `USE_LANGGRAPH_WORKFLOW=true` 时，非流式 `/research` 能返回与旧流程同结构的结果；
- 旧流程仍可回退；
- 没有前端改动。

### Phase 4: 流式事件兼容

目标：让 LangGraph workflow 支持现有前端 SSE。

任务：

- 新增 `backend/src/graph/streaming.py`；
- 将 LangGraph stream event 映射为现有 SSE payload；
- 替换 `DeepResearchAgent.run_stream` 内部线程和 Queue 逻辑；
- 保留前端事件类型和主要字段。

事件映射建议：

```text
plan_tasks start      -> status
plan_tasks output     -> todo_list
search_task output    -> sources
summarize chunk       -> task_summary_chunk
task complete         -> task_status
write_report output   -> final_report
workflow end          -> done
exception             -> error
```

验收：

- 前端无需改动即可看到研究进度；
- 取消请求仍可停止流式读取；
- 出错时前端能显示错误。

### Phase 5: 动态 worker 和并行任务

目标：发挥 LangGraph 的 orchestrator-worker 能力。

任务：

- 将 `plan_tasks` 输出动态分发给多个 task worker；
- 每个 worker 执行 search + summarize；
- 汇总所有 worker 结果后进入 report；
- 控制并发数，避免搜索后端和本地模型被打满。

注意：

- 并行会改变事件顺序；
- 前端现在有 `task_id` 和 `stream_token`，应继续保留；
- 需要为任务状态更新加更清晰的状态流。

验收：

- 多任务可以并行或受控并发执行；
- 前端 task panel 能正确更新；
- report 汇总包含全部 completed/skipped 任务。

### Phase 6: Checkpoint 和恢复

目标：支持长研究任务恢复和调试。

任务：

- 增加 LangGraph checkpointer；
- 为每次研究生成 `thread_id`；
- SSE 事件返回 `thread_id`；
- 支持按 `thread_id` 查询或恢复任务；
- 记录每个节点 state 变化，便于调试。

验收：

- 研究中断后可以从 checkpoint 继续；
- 开发者可以检查某次研究的中间 state；
- 失败节点有可定位错误信息。

### Phase 7: Human-in-the-loop

目标：让用户可以确认研究计划再执行。

任务：

- Planner 生成 TODO 后暂停；
- 前端展示计划并允许用户确认、删除、编辑任务；
- 用户确认后继续执行 graph；
- 未确认时不执行搜索和总结。

验收：

- 用户可以干预研究计划；
- 后端 state 能保存用户编辑后的 tasks；
- 兼容直接自动执行模式。

### Phase 8: 替换 HelloAgents 组件

目标：逐步降低 HelloAgents 依赖。

替换顺序建议：

1. `HelloAgentsLLM` -> LangChain chat model；
2. `ToolAwareSimpleAgent` -> LangChain agent 或直接 model invoke；
3. `SearchTool` -> LangChain tool / 自定义 search tool；
4. `NoteTool` -> LangGraph node 或 LangChain `@tool`；
5. `ToolCallTracker` -> LangGraph custom stream events。

不要在 Phase 3/4 就做这一步。先换编排层，再换工具层。

验收：

- 移除或显著减少 `hello-agents` 依赖；
- LLM provider 配置仍支持 Ollama、LMStudio、自定义 OpenAI-compatible API；
- 搜索后端仍支持 DuckDuckGo、Tavily、Perplexity、SearXNG。

### Phase 9: 产品化增强

目标：让项目成为真正可持续开发的 Deep Research 工具。

候选任务：

- 报告导出 Markdown / PDF / DOCX；
- 研究历史列表；
- sources 去重和可信度评分；
- 引用格式化；
- 搜索结果缓存；
- 前端 task timeline 优化；
- 研究模板；
- 多语言报告；
- LangSmith tracing；
- CI 测试和构建。

## 5. 推荐优先级

近期优先做：

1. 修乱码；
2. 跑通后端和前端；
3. 写 SSE 事件契约；
4. 加测试基线；
5. 引入 LangGraph 空图；
6. feature flag 双轨运行；
7. 非流式迁移；
8. 流式迁移。

暂时不要优先做：

- 大改前端 UI；
- 直接移除 HelloAgents；
- 一开始就做 checkpoint；
- 一开始就做并行 worker；
- 一开始就做完整 agent/tool 重写。

## 6. 风险清单

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| 中文乱码影响 prompt 和 UI | LLM 输出和前端展示不可控 | Phase 0 优先修复 |
| 缺少测试基线 | 迁移后不知道是否退化 | Phase 1 补最小测试 |
| 前端依赖 SSE 字段 | 后端重构容易破坏 UI | 先冻结事件契约 |
| LangGraph 并行改变事件顺序 | UI 可能跳动或状态错乱 | 先顺序图，再并行图 |
| HelloAgents tool listener 与 LangGraph stream 不兼容 | 工具调用记录丢失 | 先保留 tracker，再逐步替换 |
| 搜索服务不稳定 | 测试不可重复 | 单测 mock search，集成测试单独跑 |
| 本地模型速度慢 | 流式体验差 | 增加 task status 和 heartbeat |

## 7. Definition of Done

LangGraph 迁移完成的最低标准：

- 默认工作流使用 LangGraph；
- `/research` 和 `/research/stream` API 保持可用；
- 前端不需要大改即可展示完整流程；
- Planner、Search、Summarizer、Reporter 均是可独立测试的 graph node；
- 有最小测试覆盖状态解析、事件映射、工具函数；
- 开发日志记录每个阶段的验证结果；
- README 和 AGENTS 说明新的 LangGraph 架构。

## 8. 参考资料

- LangChain docs: https://docs.langchain.com/oss/python/langchain/overview
- LangGraph docs: https://docs.langchain.com/oss/python/langgraph/overview
- Thinking in LangGraph: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
- Workflows and agents: https://docs.langchain.com/oss/python/langgraph/workflows-agents
- Streaming: https://docs.langchain.com/oss/python/langgraph/streaming
- Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph GitHub: https://github.com/langchain-ai/langgraph
- LangChain GitHub: https://github.com/langchain-ai/langchain
