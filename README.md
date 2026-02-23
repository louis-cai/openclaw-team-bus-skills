# OpenClaw Team Bus

Multi-agent communication system for OpenClaw with unified command interface.

## Team Setup

### 1. 配置团队信息

```bash
cp examples/team.json.template /root/.openclaw/team-bus/team.json
```

团队成员：

| 代号 | AgentID | 职责 |
|------|---------|------|
| Prism | lead | 协调、汇总、Telegram沟通 |
| Scope | product | 需求、PRD、User Stories |
| Pixel | coder | 代码实现、bug修复、测试 |
| Lens | architect | 架构设计、接口定义、代码审查 |
| Shutter | ops | 部署、CI、集成测试、安全监控 |

### 2. 安装 Skill

```bash
cd <agent-workspace>/skills
git clone https://github.com/louis-cai/openclaw-team-bus-skills.git openclaw-team-bus
```

### 3. 配置 HEARTBEAT

```bash
cp examples/HEARTBEAT.template <workspace>/HEARTBEAT.md
```

## Commands

| Command | 用途 |
|---------|------|
| `send <agent> <title> <desc> <chat> --from <agent>` | 发送任务给指定 agent（必传） |
| `poll` | 扫描收件箱（自动获取agent ID） |
| `reply <agent> <task-id> <msg> --accountId <id>` | 回复任务（accountId 必传） |
| `broadcast <msg> [--chatId <id>] [--accountId <id>]` | 广播给所有 agent（写入各自 inbox） |
| `list-agents` | 列出 agent |
| `team` | 显示团队信息（我是谁） |
| `complete <task-id> [result]` | 完成任务 |
| `fail <task-id> <error>` | 标记失败 |

## Communication Flow

```
                    Team Bus
                 (/root/.openclaw/team-bus/)
                   ┌───────┐
                   │inbox/ │
                   │outbox/│
                   │broadcast/
                   └───────┘
                      │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌────────┐     ┌────────┐      ┌────────┐
│  Lead  │◀───▶│ Product│◀────▶│ Coder  │
│(Prism) │     │(Scope) │      │(Pixel) │
└───┬────┘     └────┬────┘      └───┬────┘
    │                │                │
    │                │          ┌────▼────┐
    │                │          │Architect │
    │                │          │ (Lens)  │
    │                │          └───┬──────┘
    │                │              │
    │                │         ┌───▼────┐
    │                │         │  Ops    │
    │                │         │(Shutter)│
    │                │         └─────────┘
    │                │
    └───────┬────────┘
            │
            ▼
      Telegram 群
```

## Examples

### 线性流程（瀑布模型）

```
Lead → Product → Coder → Architect → Ops
```

### 网状通信（任意连接）

```
# Lead 直接找 Coder
python3 bus.py send coder "修bug" "登录页报错" "-1003761710887" --from lead

# Coder 完成后通知 Architect 审查
python3 bus.py send architect "代码审查" "PR #123" "-1003761710887" --from coder

# Architect 审查后通知 Lead 和 Coder
python3 bus.py broadcast "代码审查通过" --chatId "-1003790843669" --accountId lead

# Ops 部署后通知全队
python3 bus.py broadcast "已部署到生产环境" --chatId "-1003790843669" --accountId lead
```

### 任务协作

```
# Lead 分配任务
python3 bus.py send product "新功能需求" "用户登录模块" "-1003761710887" --from lead

# Product 完成需求，通知 Coder
python3 bus.py send coder "实现登录功能" "详见PRD" "-1003761710887" --from product

# Coder 实现中遇到问题，询问 Architect
python3 bus.py send architect "架构问题" "登录流程设计" "-1003761710887" --from coder

# Coder 完成，通知 Architect 审查
python3 bus.py send architect "代码审查" "PR #456" "-1003761710887" --from coder

# Architect 审查通过，通知 Ops 部署
python3 bus.py send ops "部署" "v1.2.0" "-1003761710887" --from architect
```

### 指定发送者

使用 `--from` 参数显式指定发送者：
```bash
python3 bus.py send coder "修bug" "登录页报错" "-1003761710887" --from lead
```

或通过环境变量：
```bash
TEAM_BUS_AGENT=lead python3 bus.py send coder "修bug" "登录页报错" "-1003761710887"
```

## Agent ID / Account ID 自动识别

Agent ID 和 Account ID 自动从环境变量获取：

| 环境变量 | 用途 |
|---------|------|
| `TEAM_BUS_AGENT` | Agent ID（可选） |
| `CLAW_AGENT_ID` | Agent ID（OpenClaw 自动提供） |
| `TEAM_BUS_ACCOUNT` | Telegram Account ID（用于发消息） |
| `CLAW_ACCOUNT_ID` | Telegram Account ID（备用） |

设置示例：
```bash
export TEAM_BUS_AGENT=product
export TEAM_BUS_ACCOUNT=lead
python3 bus.py poll
```
