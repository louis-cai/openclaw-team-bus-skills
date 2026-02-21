# OpenClaw Team Bus

Multi-agent communication system for OpenClaw with unified command interface.

## Team Setup

### 1. 配置团队信息

复制 team.json.template 并拷贝到 team-bus 目录：

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
# 每个 agent 的 workspace
cd <agent-workspace>/skills
git clone https://github.com/louis-cai/openclaw-team-bus-skills.git openclaw-team-bus
```

### 3. 配置 TOOLS.md

```markdown
### Team Bus
- 路径: skills/openclaw-team-bus/
- 团队信息: /root/.openclaw/team-bus/team.json
```

### 4. 配置 HEARTBEAT

复制模板：
```bash
cp examples/HEARTBEAT.template <workspace>/HEARTBEAT.md
```

修改 `<your-agent-id>` 为实际的 agent ID（如 coder, product 等）

## Commands

| Command | 用途 |
|---------|------|
| `send <agent> <title> <desc> [chat]` | 发送任务 |
| `poll` | 扫描收件箱（自动获取自己的agent ID） |
| `reply <agent> <task-id> <msg>` | 回复任务 |
| `broadcast <msg>` | 广播 |
| `list-agents` | 列出 agent |
| `complete <task-id> <result>` | 完成任务 |
| `fail <task-id> <error>` | 标记失败 |

## Communication Flow

```
用户 → Prism(lead) → Scope(product) → Pixel(coder) → Lens(architect) → Shutter(ops)
                ↓                  ↓              ↓              ↓            ↓
            Telegram          team-bus      team-bus      team-bus    team-bus
```
