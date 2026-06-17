# Auto DeepResearch LangGraph

这是一个学习型 Deep Research 项目，代码来源于
[datawhalechina/hello-agents](https://github.com/datawhalechina/hello-agents)
中的示例项目，并在本仓库中作为独立项目继续维护。

本项目的目标是学习 HelloAgents 的 Deep Research 实现，并逐步用
LangGraph 重构研究流程编排能力，形成一个可持续迭代的自动化深度研究助手。

## 项目定位

- 原始来源：fork / copy 自 `datawhalechina/hello-agents`
- 项目性质：个人学习、复现、重构和二次开发项目
- 重构方向：以 LangGraph 重新组织 Planner、Search、Summarizer、Reporter 等流程节点
- 当前状态：保留 HelloAgents 版本的后端编排和 Vue 前端，作为后续 LangGraph 重构基线

## 功能概览

当前项目是一个前后端分离的深度研究助手：

- 用户输入研究主题；
- 后端将主题拆解成 TODO 研究任务；
- 每个任务执行网页搜索；
- 汇总搜索结果并生成任务级 Markdown 摘要；
- 最后生成完整研究报告；
- 前端通过 SSE 实时展示任务进度、来源、摘要和最终报告；
- 可选启用 HelloAgents NoteTool，将任务过程和最终报告保存为本地笔记。

## 技术栈

后端：

- Python 3.10+
- FastAPI
- HelloAgents
- OpenAI-compatible LLM / Ollama / LMStudio
- DuckDuckGo、Tavily、Perplexity、SearXNG 等搜索后端

前端：

- Vue 3
- TypeScript
- Vite
- Server-Sent Events streaming

## 目录结构

```text
.
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── src/
│       ├── main.py              # FastAPI 入口，提供 /research 和 /research/stream
│       ├── agent.py             # DeepResearchAgent 编排入口
│       ├── config.py            # 环境变量配置
│       ├── models.py            # 研究任务和状态模型
│       ├── prompts.py           # Planner / Summarizer / Reporter 提示词
│       └── services/
│           ├── planner.py       # 主题拆解为 TODO 任务
│           ├── search.py        # 搜索后端调度
│           ├── summarizer.py    # 单任务总结
│           ├── reporter.py      # 最终报告生成
│           └── tool_events.py   # 工具调用事件追踪
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.vue              # 主界面和研究进度展示
│       └── services/api.ts      # SSE API 客户端
├── dev-log/                     # 按时间线维护开发日志
├── AGENTS.md                    # 项目级协作和开发约定
└── README.md
```

## 后端启动

进入后端目录：

```bash
cd backend
```

安装依赖：

```bash
uv sync
```

配置环境变量。常用配置示例：

```bash
LLM_PROVIDER=ollama
LOCAL_LLM=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
SEARCH_API=duckduckgo
ENABLE_NOTES=true
NOTES_WORKSPACE=./notes
```

启动服务：

```bash
uv run python src/main.py
```

默认后端地址：

```text
http://localhost:8000
```

健康检查：

```text
GET /healthz
```

主要接口：

```text
POST /research
POST /research/stream
```

## 前端启动

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务：

```bash
npm run dev
```

如果后端不是 `http://localhost:8000`，可以配置：

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 当前架构理解

当前后端以 `DeepResearchAgent` 为中心，主要流程如下：

1. `PlanningService` 根据研究主题生成多个 TODO 子任务；
2. `dispatch_search` 根据配置调用搜索工具获取网页结果；
3. `SummarizationService` 对每个任务的搜索上下文做总结；
4. `ReportingService` 基于任务摘要生成最终报告；
5. `ToolCallTracker` 记录笔记工具调用和流式事件；
6. FastAPI 通过 `/research/stream` 将任务进度、来源、摘要和最终报告推送到前端。

这个结构适合作为 LangGraph 重构基线：可以把 Planning、Search、Summarize、Report、Note
分别改造成图节点，再用状态对象连接每个节点的输入输出。

## 后续重构方向

- 将 `DeepResearchAgent.run` 和 `run_stream` 拆成 LangGraph workflow；
- 定义统一的 `ResearchState`，替换当前分散的 `SummaryState` 更新逻辑；
- 为 Planner、Search、Summarizer、Reporter 建立可测试的节点函数；
- 保留 SSE 事件协议，降低前端改造成本；
- 清理当前代码中的中文乱码，统一文件编码为 UTF-8；
- 为核心流程增加单元测试和最小集成测试；
- 增加 `.env.example`，明确本地模型、搜索服务和笔记目录配置。

## 开发日志

开发日志维护在 `dev-log/` 目录中，按日期命名，例如：

```text
dev-log/2026-06-17.md
```

每次较大的学习、重构、修复或验证，都应写入当天日志，记录背景、改动、验证结果和后续 TODO。

## 许可证

本项目源自 `datawhalechina/hello-agents` 的学习示例。后续维护时应继续遵守原项目许可证和依赖库许可证。
