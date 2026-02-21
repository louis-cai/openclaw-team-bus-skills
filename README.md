# OpenClaw Team Bus Skills

Multi-agent task queue system for OpenClaw with Telegram status reporting.

## Overview

```
┌─────────────┐     tasks      ┌─────────────┐
│   Leader    │ ──────────────▶│   Worker    │
│  (Main)     │   pending/     │  (Agent)    │
└─────────────┘                └─────────────┘
       │                              │
       │                              ▼
       │                     ┌─────────────┐
       │                     │  Telegram   │
       └─────────────────────│   Group     │
         completed/          └─────────────┘
```

## Directory Structure

```
/root/.openclaw/team-bus/
├── tasks/
│   ├── pending/      # Main 放入待执行任务
│   ├── processing/  # 正在执行
│   ├── completed/   # 已完成
│   └── failed/      # 失败（可重试）
└── workers/
    └── <worker-id>/
        └── config.json
```

## Quick Start

### 1. 创建 Worker Agents

```bash
openclaw agents add worker-coder
openclaw agents add worker-writer
openclaw agents add worker-researcher
```

### 2. 配置 Worker HEARTBEAT.md

在每个 worker 的 workspace 添加 HEARTBEAT.md:

```markdown
# HEARTBEAT.md
- 运行: python3 /path/to/openclaw-team-bus-skills/scripts/worker.py worker-coder
- 如果无任务，回复 HEARTBEAT_OK
```

### 3. Leader 派发任务

在 Main Agent 的 Memory 记录 team 分工:

```markdown
## Team Members
| Agent | 擅长 |
|-------|------|
| worker-coder | 编码 |
| worker-writer | 写作 |
| worker-researcher | 调研 |
```

派发任务:

```bash
python3 scripts/leader.py worker-coder "修复登录bug" "用户点击登录无响应" -100123456
```

## Task Format

```json
{
  "id": "task-001",
  "type": "task",
  "subtype": "fix-bug",
  "status": "pending",
  "from": "lead",
  "to": "worker-coder",
  "createdAt": "2026-02-21T10:00:00Z",
  "payload": {
    "title": "修复登录 bug",
    "description": "用户点击登录后无响应",
    "telegram": {
      "chatId": "-100xxxxx"
    }
  },
  "result": null,
  "error": null
}
```

## Scripts

| Script | 用途 |
|--------|------|
| worker.py | Worker 扫描并执行任务 |
| leader.py | Main 派发任务 |

## Telegram Status

Worker 执行时会自动发送状态到指定群:

- 🔵 `[worker-id] started <task-title>` - 开始执行
- ✅ `[worker-id] completed <task-title>` - 执行完成  
- ❌ `[worker-id] failed <task-title>: <error>` - 执行失败
