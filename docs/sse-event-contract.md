# SSE Event Contract

`POST /research/stream` returns `text/event-stream` events. Each event is sent as:

```text
data: <json payload>

```

The frontend currently parses only `data:` messages and stops when it receives `done` or `error`.

## Request

```json
{
  "topic": "research topic",
  "search_api": "duckduckgo"
}
```

`search_api` is optional. If omitted, the backend uses environment configuration.

## Event Types

### status

General progress notification.

```json
{
  "type": "status",
  "message": "initializing research workflow",
  "task_id": 1,
  "step": 1
}
```

Required fields:

- `type`
- `message`

Optional fields:

- `task_id`
- `step`
- `stream_token`

### todo_list

Initial task plan.

```json
{
  "type": "todo_list",
  "tasks": [
    {
      "id": 1,
      "title": "Task title",
      "intent": "Task intent",
      "query": "Search query",
      "status": "pending",
      "summary": null,
      "sources_summary": null,
      "note_id": null,
      "note_path": null,
      "stream_token": "task_1"
    }
  ],
  "step": 0
}
```

Required fields:

- `type`
- `tasks`

### task_status

Task lifecycle update.

```json
{
  "type": "task_status",
  "task_id": 1,
  "status": "completed",
  "title": "Task title",
  "intent": "Task intent",
  "summary": "Markdown summary",
  "sources_summary": "* Source : https://example.com",
  "note_id": "note-id",
  "note_path": "./notes/note-id.md",
  "step": 1
}
```

Known statuses:

- `pending`
- `in_progress`
- `completed`
- `skipped`
- `failed`

Required fields:

- `type`
- `task_id`
- `status`

### sources

Search result payload for one task.

```json
{
  "type": "sources",
  "task_id": 1,
  "latest_sources": "* Source : https://example.com",
  "raw_context": "formatted search context",
  "backend": "duckduckgo",
  "note_id": "note-id",
  "note_path": "./notes/note-id.md",
  "step": 1
}
```

Required fields:

- `type`
- `task_id`
- `latest_sources`

### task_summary_chunk

Streaming text chunk from the task summarizer.

```json
{
  "type": "task_summary_chunk",
  "task_id": 1,
  "content": "partial markdown",
  "note_id": "note-id",
  "step": 1
}
```

Required fields:

- `type`
- `task_id`
- `content`

### tool_call

Tool execution trace.

```json
{
  "type": "tool_call",
  "event_id": 1,
  "agent": "planner",
  "tool": "note",
  "parameters": {},
  "result": "tool result",
  "task_id": 1,
  "note_id": "note-id",
  "note_path": "./notes/note-id.md",
  "step": 1
}
```

Required fields:

- `type`
- `event_id`
- `agent`
- `tool`
- `parameters`
- `result`

### report_note

Final report persistence result.

```json
{
  "type": "report_note",
  "note_id": "note-id",
  "note_path": "./notes/note-id.md",
  "title": "Research report: topic",
  "content": "final report markdown"
}
```

Required fields:

- `type`
- `note_id`
- `title`
- `content`

### final_report

Final report payload.

```json
{
  "type": "final_report",
  "report": "final report markdown",
  "note_id": "note-id",
  "note_path": "./notes/note-id.md"
}
```

Required fields:

- `type`
- `report`

### done

Terminal success event.

```json
{
  "type": "done"
}
```

### error

Terminal error event.

```json
{
  "type": "error",
  "detail": "error message"
}
```

## Migration Rule

LangGraph migration must preserve these event types during the early migration phases. New fields may be added, but existing fields used by `frontend/src/App.vue` and `frontend/src/services/api.ts` should not be removed or renamed without a matching frontend change.
