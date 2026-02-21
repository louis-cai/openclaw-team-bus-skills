# OpenClaw Team Bus

Multi-agent communication system for OpenClaw with unified command interface.

## Quick Start

### 1. 创建 Worker Agents

```bash
openclaw agents add worker-coder
openclaw agents add worker-writer
openclaw agents add worker-researcher
```

### 2. 配置 HEARTBEAT

复制模板并修改 agent ID:

```bash
# 复制模板
cp examples/HEARTBEAT.template <workspace>/HEARTBEAT.md

# 编辑，替换 <your-agent-id> 为实际的 agent ID
# 例如: worker-coder
```

模板内容:
```markdown
# HEARTBEAT.md

- 运行: python3 /path/to/openclaw-team-bus-skills/scripts/bus.py poll <your-agent-id>
- 如果无消息，回复 HEARTBEAT_OK
```

### 3. Leader 派发任务

```bash
python3 scripts/bus.py send worker-coder "修复登录bug" "用户点击登录无响应"
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

## Telegram 状态

在任务中指定 `chatId`，Worker 执行时会自动发送状态:
- 🔵 `[agent] started <title>` - 开始
- ✅ `[agent] completed <title>` - 完成  
- ❌ `[agent] failed <title>: <error>` - 失败

## 示例

### 完整工作流

```bash
# 1. Leader 发送任务
python3 scripts/bus.py send worker-coder "修复登录bug" "用户点击登录无响应"

# 2. Worker-Coder 的 HEARTBEAT 被触发，扫描到任务
#    (输出任务详情供 agent 处理)

# 3. Agent 处理任务...

# 4. 完成任务
python3 scripts/bus.py complete task-xxx worker-coder "已修复"

# 5. 或者任务失败
python3 scripts/bus.py fail task-xxx worker-coder "无法复现问题"

# 6. Agent 间相互沟通
python3 scripts/bus.py reply worker-writer task-xxx "文档已更新"
```
