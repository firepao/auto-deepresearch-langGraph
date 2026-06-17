# AGENTS.md

本文件是 `auto-deepresearch-langGraph` 项目的项目级协作说明。后续使用 Codex、其他代码代理或人工协作时，优先阅读本文件和 `README.md`。

## 项目背景

- 这是从 `https://github.com/datawhalechina/hello-agents` 复制出来的学习项目。
- 当前仓库用于学习 Deep Research 流程，并逐步用 LangGraph 重构原有 HelloAgents 编排逻辑。
- 当前代码仍以 HelloAgents 实现为主，LangGraph 重构应循序渐进，避免一次性大改导致行为不可验证。

## 当前项目总结

项目由 `backend/` 和 `frontend/` 两部分组成。

后端是 FastAPI 服务，核心入口是 `backend/src/main.py`。它暴露 `/healthz`、`/research` 和 `/research/stream` 接口，其中 `/research/stream` 使用 SSE 向前端推送研究过程。

核心编排类是 `backend/src/agent.py` 中的 `DeepResearchAgent`。它负责：

- 初始化 LLM；
- 初始化可选的 NoteTool；
- 调用 Planner 生成研究任务；
- 对每个任务执行搜索；
- 汇总每个任务的资料；
- 生成最终 Markdown 报告；
- 在流式模式下推送任务状态、来源、摘要和最终报告事件。

服务层在 `backend/src/services/`：

- `planner.py`：把用户研究主题拆成结构化 TODO；
- `search.py`：调用 HelloAgents `SearchTool`，按配置选择搜索后端；
- `summarizer.py`：对单个任务的搜索上下文生成总结；
- `reporter.py`：生成最终报告；
- `notes.py`：构造笔记工具相关提示；
- `tool_events.py`：追踪工具调用事件。

前端位于 `frontend/`，使用 Vue 3 + TypeScript + Vite。`frontend/src/services/api.ts` 负责连接后端 SSE 接口，`frontend/src/App.vue` 展示研究输入、任务列表、来源、工具调用、摘要和最终报告。

## 开发原则

- 优先保持现有行为可运行，再逐步重构。
- LangGraph 重构时优先替换后端编排层，不要先大改前端协议。
- 保持 `/research/stream` 的事件结构尽量稳定，避免前端跟随后端频繁改动。
- 每次重构一个明确边界，例如先重构 Planner 节点，再重构 Search 节点。
- 新增配置时同步更新 `README.md` 和 `.env.example`。
- 涉及较大改动时同步更新 `dev-log/`。

## 开发日志规范

开发日志保存在 `dev-log/`，按日期命名：

```text
dev-log/YYYY-MM-DD.md
```

每篇日志建议包含：

- 当天目标；
- 已完成改动；
- 验证结果；
- 发现的问题；
- 下一步计划。

不要把日志写成流水账，重点记录后续继续开发时真正有帮助的上下文。

## 已知问题

- 当前 Windows PowerShell `Get-Content` 可能把 UTF-8 中文显示成乱码；Python 按 UTF-8 读取源码时中文正常。不要在未验证原始字节的情况下做批量编码转换。
- 后端 `pyproject.toml` 的项目 README 指向 `README.md`，但当前后端目录内没有独立 README；仓库根 README 已补充项目说明。
- 已加入实验性 LangGraph scaffold，但还没有迁移真实研究节点。
- 已建立基础测试，但还没有覆盖真实 LLM、搜索和 SSE 集成流程。

## 推荐重构路线

1. 建立最小可运行验证：后端启动、前端启动、一次简单研究任务。
2. 修复中文乱码和 `.env.example`。
3. 给 `PlanningService`、`dispatch_search`、`SummarizationService` 增加最小测试。
4. 引入 LangGraph，并把 `SummaryState` 整理为新的 `ResearchState`。
5. 将 Planner、Search、Summarize、Report 改造成 LangGraph 节点。
6. 保持 FastAPI API 不变，用新 workflow 替换 `DeepResearchAgent` 内部实现。
7. 再考虑前端体验优化和报告导出能力。

详细 LangGraph 迁移路线见：

```text
docs/langgraph-migration-roadmap.md
```

当前迁移入口：

```text
backend/src/graph/
docs/sse-event-contract.md
USE_LANGGRAPH_WORKFLOW=false
```

## 提交前检查

提交前至少检查：

```bash
git status --short
```

如改动后端 Python：

```bash
python -m py_compile backend/src/main.py backend/src/agent.py
```

如改动前端 TypeScript / Vue：

```bash
cd frontend
npm run build
```

如果本地缺依赖或环境无法验证，需要在开发日志和提交说明中说明。
