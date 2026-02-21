---
name: openclaw-team-bus
description: Multi-agent communication bus for OpenClaw. Use for team coordination, task distribution, and inter-agent messaging via shared filesystem.
metadata: {"clawdbot":{"emoji":"👥","requires":{"bins":["python3"],"dirs":["/root/.openclaw/team-bus"]}}}
---

# OpenClaw Team Bus

Unified multi-agent communication system for OpenClaw teams.

## Directory Structure

```
/root/.openclaw/team-bus/
├── inbox/<agent>/       # 收件箱
├── outbox/<agent>/     # 发件箱
├── broadcast/          # 广播消息
├── processing/<agent>/ # 正在处理
├── tasks/
│   ├── pending/        # 待执行任务
│   ├── processing/     # 正在执行
│   ├── completed/      # 已完成
│   └── failed/         # 失败
```

## Usage

```bash
python3 bus.py <command> [args]

Commands:
  send <to-agent> <title> <description> [chat-id]   # 发送任务
  poll <my-agent>                                  # 扫描收件箱
  reply <to-agent> <task-id> <message>           # 回复
  broadcast <message>                             # 广播
  list-agents                                     # 列出 agent
  complete <task-id> <agent> [result]            # 完成任务
  fail <task-id> <agent> <error>                 # 标记失败
```

## Examples

```bash
# Leader 发送任务给 Worker
python3 bus.py send worker-coder "修复登录bug" "用户点击登录无响应" -100123456

# Worker 扫描收件箱
python3 bus.py poll worker-coder

# Worker 完成任务
python3 bus.py complete task-123 worker-coder "已修复"

# Agent 间相互回复
python3 bus.py reply worker-writer task-123 "文档已写完"

# 广播
python3 bus.py broadcast "系统维护通知"
```

## HEARTBEAT Integration

Worker 在 HEARTBEAT.md 中配置:
```markdown
# HEARTBEAT.md
- 运行: python3 /path/to/bus.py poll worker-coder
- 如果无消息，回复 HEARTBEAT_OK
```
