---
name: openclaw-team-bus
description: Multi-agent task queue with Python-based worker for OpenClaw. Use for coordinating team work, task distribution, and status reporting to Telegram.
metadata: {"clawdbot":{"emoji":"👥","requires":{"bins":["python3"],"dirs":["/root/.openclaw/team-bus"]}}}
---

# OpenClaw Team Bus

Multi-agent task queue system for coordinating worker agents with Telegram status reporting.

## Directory Structure

```
/root/.openclaw/team-bus/
├── tasks/
│   ├── pending/      # 待执行任务 (Main 放入)
│   ├── processing/   # 正在执行
│   ├── completed/    # 已完成
│   └── failed/       # 失败 (可重试)
└── workers/
    └── <worker-id>/
        └── config.json  # Worker 配置
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

## Worker Script

```bash
python3 <skill-dir>/scripts/worker.py <worker-id>
```

Example in HEARTBEAT.md:
```
- 运行: python3 /path/to/worker.py worker-coder
- 如果无任务回复 HEARTBEAT_OK
```

## Main Agent Usage

1. 读取 MEMORY.md 了解 team members 和分工
2. 根据任务类型匹配合适的 worker
3. 写任务到 pending 目录

## Dependencies

- Python 3
- openclaw (for sendMessage tool)
