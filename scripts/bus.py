#!/usr/bin/env python3
"""
OpenClaw Team Bus - Unified communication script for multi-agent teams

Usage: python3 bus.py <command> [args]

Commands:
  send <to-agent> <title> <description> [chat-id]   # 发送任务给另一个 agent
  poll                                           # 扫描并执行任务（自动获取agent ID）
  reply <to-agent> <task-id> <message>           # 回复任务/结果
  broadcast <message>                            # 广播消息给所有 agent
  list-agents                                    # 列出所有 agent
  team                                           # 显示团队信息
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse

BUS_ROOT = Path(os.environ.get("BUS_ROOT", "/root/.openclaw/team-bus"))
SKILL_DIR = Path(os.environ.get("SKILL_DIR", "/root/.openclaw/skills/openclaw-team-bus"))

def get_my_agent_id():
    """自动获取当前 agent ID"""
    # 优先从环境变量读取
    agent_id = os.environ.get("TEAM_BUS_AGENT")
    if agent_id:
        return agent_id
    
    # 从 CLAW_AGENT_ID 读取（OpenClaw 提供）
    agent_id = os.environ.get("CLAW_AGENT_ID")
    if agent_id:
        return agent_id
    
    return None

def get_my_account_id():
    """自动获取当前 account ID"""
    account_id = os.environ.get("TEAM_BUS_ACCOUNT")
    if account_id:
        return account_id
    
    # 备用：从 CLAW_ACCOUNT_ID 读取
    account_id = os.environ.get("CLAW_ACCOUNT_ID")
    if account_id:
        return account_id
    
    return None

def get_team_info():
    """读取团队信息"""
    team_file = BUS_ROOT / "team.json"
    if team_file.exists():
        return json.loads(team_file.read_text(encoding="utf-8"))
    return {}

def ensure_dirs():
    """确保必要的目录存在"""
    for d in ["inbox", "outbox", "broadcast", "tasks/pending", "tasks/processing", "tasks/completed", "tasks/failed"]:
        (BUS_ROOT / d).mkdir(parents=True, exist_ok=True)

# ============ 消息相关 ============

def cmd_send(to_agent: str, title: str, description: str, chat_id: str = "", from_agent: str = ""):
    """发送任务/消息给另一个 agent"""
    # from_agent 已经是必传参数，这里保留作为备用
    
    msg = {
        "id": f"msg-{datetime.now().strftime('%Y%m%d%H%M%S')}-{abs(hash(to_agent)) % 10000}",
        "type": "task",
        "from": from_agent,
        "to": to_agent,
        "createdAt": datetime.now().isoformat(),
        "payload": {
            "title": title,
            "description": description,
            "telegram": {"chatId": chat_id} if chat_id else {}
        },
        "replies": []
    }
    
    inbox_dir = BUS_ROOT / "inbox" / to_agent
    inbox_dir.mkdir(parents=True, exist_ok=True)
    
    msg_file = inbox_dir / f"{msg['id']}.json"
    msg_file.write_text(json.dumps(msg, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"✅ Sent to {to_agent}: {title}")
    return msg["id"]

def cmd_poll():
    """扫描 inbox，执行任务"""
    my_agent = get_my_agent_id()
    if not my_agent:
        print("❌ Cannot determine agent ID. Set TEAM_BUS_AGENT or CLAW_AGENT_ID")
        sys.exit(1)
    
    inbox_dir = BUS_ROOT / "inbox" / my_agent
    
    if not inbox_dir.exists():
        print(f"📭 No inbox for {my_agent}")
        return
    
    messages = sorted(inbox_dir.glob("*.json"))
    
    if not messages:
        print(f"📭 No messages for {my_agent}")
        return
    
    print(f"📬 Found {len(messages)} message(s) for {my_agent}")
    
    for msg_file in messages:
        # 移动到 processing（原子操作）
        processing_dir = BUS_ROOT / "processing" / my_agent
        processing_dir.mkdir(parents=True, exist_ok=True)
        
        dst = processing_dir / msg_file.name
        shutil.move(str(msg_file), str(dst))
        
        msg = json.loads(dst.read_text(encoding="utf-8"))
        
        # 打印消息内容
        payload = msg.get("payload", {})
        title = payload.get("title", "No title")
        desc = payload.get("description", "")
        from_agent = msg.get("from", "unknown")
        
        print(f"\n📥 Message from {from_agent}:")
        print(f"   Title: {title}")
        print(f"   Desc: {desc}")
        
        # 返回消息内容供 agent 处理
        print(f"\n--- MESSAGE START ---")
        print(json.dumps(msg, ensure_ascii=False))
        print(f"--- MESSAGE END ---")

def cmd_reply(to_agent: str, task_id: str, message: str, account_id: str = None):
    """回复任务/消息"""
    if account_id is None:
        account_id = get_my_account_id() or ""
    
    from_agent = get_my_agent_id() or "unknown"
    
    # 发送到 outbox
    outbox_dir = BUS_ROOT / "outbox" / to_agent
    outbox_dir.mkdir(parents=True, exist_ok=True)
    
    reply_msg = {
        "id": f"reply-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": "reply",
        "from": from_agent,
        "to": to_agent,
        "taskId": task_id,
        "message": message,
        "accountId": account_id,
        "createdAt": datetime.now().isoformat()
    }
    
    outbox_file = outbox_dir / f"{reply_msg['id']}.json"
    outbox_file.write_text(json.dumps(reply_msg, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"✅ Replied to {to_agent} on {task_id}")

def cmd_broadcast(message: str):
    """广播消息给所有 agent（写入每个 agent 的 inbox）"""
    from_agent = get_my_agent_id() or "unknown"

    # 优先使用 team.json 中的团队成员
    team_info = get_team_info()
    team = team_info.get("team", {})
    if team:
        recipients = sorted(team.keys())
    else:
        # 兜底：使用已有 inbox 子目录作为收件人
        inbox_root = BUS_ROOT / "inbox"
        recipients = sorted([p.name for p in inbox_root.iterdir() if p.is_dir()]) if inbox_root.exists() else []

    # 广播默认不发给自己
    recipients = [agent for agent in recipients if agent != from_agent]

    if not recipients:
        print("❌ No recipients found for broadcast. Configure team.json first.")
        return

    broadcast_id = f"broadcast-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    created_at = datetime.now().isoformat()

    sent = 0
    for to_agent in recipients:
        msg = {
            "id": f"{broadcast_id}-{to_agent}",
            "type": "broadcast",
            "from": from_agent,
            "to": to_agent,
            "broadcastId": broadcast_id,
            "createdAt": created_at,
            "payload": {
                "title": f"Broadcast from {from_agent}",
                "description": message,
                "telegram": {}
            },
            "replies": []
        }

        inbox_dir = BUS_ROOT / "inbox" / to_agent
        inbox_dir.mkdir(parents=True, exist_ok=True)
        msg_file = inbox_dir / f"{msg['id']}.json"
        msg_file.write_text(json.dumps(msg, indent=2, ensure_ascii=False), encoding="utf-8")
        sent += 1

    print(f"📢 Broadcast queued to {sent} agent(s): {message}")

def cmd_list_agents():
    """列出所有 agent"""
    team_info = get_team_info()
    team = team_info.get("team", {})
    
    if team:
        print("Team members:")
        for agent_id, info in team.items():
            name = info.get("name", agent_id)
            resp = info.get("responsibility", "")
            print(f"  - {agent_id} ({name}): {resp}")
    else:
        print("No team.json found. Use team.json.template to create one.")

def cmd_team():
    """显示团队信息"""
    team_info = get_team_info()
    team = team_info.get("team", {})
    
    if not team:
        print("No team.json found.")
        return
    
    my_agent = get_my_agent_id()
    
    if my_agent and my_agent in team:
        my_info = team[my_agent]
        print(f"👤 You are: {my_info.get('name', my_agent)} ({my_agent})")
        print(f"   Responsibility: {my_info.get('responsibility', '')}")
        print()
    
    print("Team members:")
    print(f"{'AgentID':<12} {'Name':<10} {'Responsibility'}")
    print("-" * 60)
    for agent_id, info in team.items():
        name = info.get("name", agent_id)
        resp = info.get("responsibility", "")
        marker = " ← You" if agent_id == my_agent else ""
        print(f"{agent_id:<12} {name:<10} {resp}{marker}")

def cmd_complete(task_id: str, result: str = ""):
    """标记任务完成"""
    my_agent = get_my_agent_id()
    if not my_agent:
        print("❌ Cannot determine agent ID")
        return
    
    processing_dir = BUS_ROOT / "processing" / my_agent
    
    if not processing_dir.exists():
        print(f"❌ No processing tasks for {my_agent}")
        return
    
    for f in processing_dir.glob("*.json"):
        if task_id in f.name or task_id in f.read_text():
            msg = json.loads(f.read_text(encoding="utf-8"))
            msg["status"] = "completed"
            msg["completedAt"] = datetime.now().isoformat()
            msg["result"] = result
            
            # 移动到 completed
            completed_dir = BUS_ROOT / "tasks" / "completed" / my_agent
            completed_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(completed_dir / f.name))
            
            print(f"✅ Task {task_id} completed")
            return
    
    print(f"❌ Task {task_id} not found")

def cmd_fail(task_id: str, error: str):
    """标记任务失败"""
    my_agent = get_my_agent_id()
    if not my_agent:
        print("❌ Cannot determine agent ID")
        return
    
    processing_dir = BUS_ROOT / "processing" / my_agent
    
    if not processing_dir.exists():
        return
    
    for f in processing_dir.glob("*.json"):
        if task_id in f.name or task_id in f.read_text():
            msg = json.loads(f.read_text(encoding="utf-8"))
            msg["status"] = "failed"
            msg["failedAt"] = datetime.now().isoformat()
            msg["error"] = error
            
            failed_dir = BUS_ROOT / "tasks" / "failed" / my_agent
            failed_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(failed_dir / f.name))
            
            print(f"❌ Task {task_id} failed: {error}")
            return

def main():
    ensure_dirs()
    
    parser = argparse.ArgumentParser(description="OpenClaw Team Bus")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # send
    send_parser = subparsers.add_parser("send", help="Send task to agent")
    send_parser.add_argument("to", help="Target agent")
    send_parser.add_argument("title", help="Task title")
    send_parser.add_argument("description", help="Task description")
    send_parser.add_argument("chat_id", help="Telegram chat ID (required)")
    send_parser.add_argument("--from", dest="from_agent", required=True, help="From agent (required)")
    
    # poll
    subparsers.add_parser("poll", help="Poll inbox for tasks (auto-detect agent)")
    
    # reply
    reply_parser = subparsers.add_parser("reply", help="Reply to task")
    reply_parser.add_argument("to", help="Target agent")
    reply_parser.add_argument("task_id", help="Task ID")
    reply_parser.add_argument("message", help="Reply message")
    reply_parser.add_argument("--accountId", default=None, help="Telegram accountId (default: TEAM_BUS_ACCOUNT)")
    
    # broadcast
    broadcast_parser = subparsers.add_parser("broadcast", help="Broadcast message")
    broadcast_parser.add_argument("message", help="Broadcast message")
    
    # list-agents
    subparsers.add_parser("list-agents", help="List all agents")
    
    # team
    subparsers.add_parser("team", help="Show team info")
    
    # complete
    complete_parser = subparsers.add_parser("complete", help="Complete task")
    complete_parser.add_argument("task_id", help="Task ID")
    complete_parser.add_argument("result", nargs="?", default="", help="Result")
    
    # fail
    fail_parser = subparsers.add_parser("fail", help="Fail task")
    fail_parser.add_argument("task_id", help="Task ID")
    fail_parser.add_argument("error", help="Error message")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "send":
        cmd_send(args.to, args.title, args.description, args.chat_id, args.from_agent)
    elif args.command == "poll":
        cmd_poll()
    elif args.command == "reply":
        cmd_reply(args.to, args.task_id, args.message, args.accountId)
    elif args.command == "broadcast":
        cmd_broadcast(args.message)
    elif args.command == "list-agents":
        cmd_list_agents()
    elif args.command == "team":
        cmd_team()
    elif args.command == "complete":
        cmd_complete(args.task_id, args.result)
    elif args.command == "fail":
        cmd_fail(args.task_id, args.error)

if __name__ == "__main__":
    main()
