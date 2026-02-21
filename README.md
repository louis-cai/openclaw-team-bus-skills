# OpenClaw Team Bus

Multi-agent communication system for OpenClaw with unified command interface.

## Installation

```bash
# 克隆到每个 agent 的 skills 目录
cd <agent-workspace>/skills
git clone https://github.com/louis-cai/openclaw-team-bus-skills.git openclaw-team-bus
```

## Configuration

### 1. 配置 TOOLS.md

在 agent workspace 的 TOOLS.md 中添加:

```markdown
### Team Bus
- 路径: <agent-workspace>/skills/openclaw-team-bus
- 命令: python3 skills/openclaw-team-bus/scripts/bus.py
```

### 2. 配置 HEARTBEAT.md

复制模板并修改:

```bash
cp examples/HEARTBEAT.template <workspace>/HEARTBEAT.md
```

修改内容，把 `<skill-path>` 和 `<your-agent-id>` 替换为实际值:

```markdown
# HEARTBEAT.md

- 运行: python3 skills/openclaw-team-bus/scripts/bus.py poll worker-coder
- 如果无消息，回复 HEARTBEAT_OK
```

## Commands

| Command | 用途 |
|---------|------|
| `send <agent> <title> <desc> [chat]` | 发送任务 |
| `poll <agent>` | 扫描收件箱 |
| `reply <agent> <task-id> <msg>` | 回复任务 |
| `broadcast <msg>` | 广播 |
| `list-agents` | 列出 agent |
| `complete <task-id> <agent> [result]` | 完成任务 |
| `fail <task-id> <agent> <error>` | 标记失败 |

## Agent Communication

```
┌─────────────────────────────────────────────┐
│              Team Bus                        │
│         (/root/.openclaw/team-bus/)         │
├─────────────────────────────────────────────┤
│  inbox/<agent>/    ← 收到的消息             │
│  outbox/<agent>/   ← 发出的回复             │
│  broadcast/        ← 广播消息                 │
└─────────────────────────────────────────────┘
        ▲                    ▲
        │                    │
   Worker A ◀──────────────▶ Worker B
        │                    │
        └─────────▶ Telegram ◀┘
```
