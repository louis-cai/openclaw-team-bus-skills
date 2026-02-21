#!/usr/bin/env python3
"""
OpenClaw Team Bus - Unified communication script for multi-agent teams

Usage: python3 bus.py <command> [args]

Commands:
  send <to-agent> <title> <description> [chat-id]   # 发送任务给另一个 agent
  poll <my-agent>                                  # 扫描并执行任务
  reply <to-agent> <task-id> <message>           # 回复任务/结果
  broadcast <message>                             # 广播消息给所有 agent
  list-agents                                     # 列出所有 agent
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse

BUS_ROOT = Path(os.environ.get("BUS_ROOT", "/root/.openclaw/team-bus"))

def ensure_dirs():
    """确保必要的目录存在"""
    for d in ["inbox", "outbox", "broadcast", "tasks/pending", "tasks/processing", "tasks/completed", "tasks/failed"]:
        (BUS_ROOT / d).mkdir(parents=True, exist_ok=True)

# ============ 消息相关 ============

def cmd_send(to_agent: str, title: str, description: str, chat_id: str = ""):
    """发送任务/消息给另一个 agent"""
    from_agent = os.environ.get("TEAM_BUS_AGENT", "unknown")
    
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

def cmd_poll(my_agent: str):
    """扫描 inbox，执行任务"""
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

def cmd_reply(to_agent: str, task_id: str, message: str):
    """回复任务/消息"""
    from_agent = os.environ.get("TEAM_BUS_AGENT", "unknown")
    
    # 查找原始消息
    processing_dir = BUS_ROOT / "processing" / to_agent
    msg_file = None
    
    if processing_dir.exists():
        for f in processing_dir.glob("*.json"):
            if task_id in f.name or task_id in f.read_text():
                msg_file = f
                break
    
    if not msg_file:
        # 尝试在 completed 找
        completed_dir = BUS_ROOT / "tasks" / "completed" / to_agent
        if completed_dir.exists():
            for f in completed_dir.glob("*.json"):
                if task_id in f.name or task_id in f.read_text():
                    msg_file = f
                    break
    
    if msg_file:
        msg = json.loads(msg_file.read_text(encoding="utf-8"))
        if "replies" not in msg:
            msg["replies"] = []
        
        reply = {
            "from": from_agent,
            "at": datetime.now().isoformat(),
            "message": message
        }
        msg["replies"].append(reply)
        msg_file.write_text(json.dumps(msg, indent=2, ensure_ascii=False), encoding="utf-8")
        
        print(f"✅ Replied to {to_agent} on {task_id}")
    else:
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
            "createdAt": datetime.now().isoformat()
        }
        
        outbox_file = outbox_dir / f"{reply_msg['id']}.json"
        outbox_file.write_text(json.dumps(reply_msg, indent=2, ensure_ascii=False), encoding="utf-8")
        
        print(f"✅ Sent reply to {to_agent} (via outbox)")

def cmd_broadcast(message: str):
    """广播消息给所有 agent"""
    from_agent = os.environ.get("TEAM_BUS_AGENT", "unknown")
    
    broadcast_dir = BUS_ROOT / "broadcast"
    broadcast_dir.mkdir(parents=True, exist_ok=True)
    
    msg = {
        "id": f"broadcast-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "type": "broadcast",
        "from": from_agent,
        "message": message,
        "createdAt": datetime.now().isoformat()
    }
    
    broadcast_file = broadcast_dir / f"{msg['id']}.json"
    broadcast_file.write_text(json.dumps(msg, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"📢 Broadcast: {message}")

def cmd_list_agents():
    """列出所有 agent"""
    inbox_base = BUS_ROOT / "inbox"
    
    if not inbox_base.exists():
        print("No agents found")
        return
    
    agents = [d.name for d in inbox_base.iterdir() if d.is_dir()]
    
    if agents:
        print("Registered agents:")
        for agent in sorted(agents):
            # 统计消息数
            pending = len((inbox_base / agent).glob("*.json"))
            print(f"  - {agent} ({pending} pending)")
    else:
        print("No agents registered")

def cmd_complete(task_id: str, my_agent: str, result: str = ""):
    """标记任务完成"""
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

def cmd_fail(task_id: str, my_agent: str, error: str):
    """标记任务失败"""
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
    send_parser.add_argument("chat_id", nargs="?", default="", help="Telegram chat ID")
    
    # poll
    poll_parser = subparsers.add_parser("poll", help="Poll inbox for tasks")
    poll_parser.add_argument("agent", help="My agent ID")
    
    # reply
    reply_parser = subparsers.add_parser("reply", help="Reply to task")
    reply_parser.add_argument("to", help="Target agent")
    reply_parser.add_argument("task_id", help="Task ID")
    reply_parser.add_argument("message", help="Reply message")
    
    # broadcast
    broadcast_parser = subparsers.add_parser("broadcast", help="Broadcast message")
    broadcast_parser.add_argument("message", help="Broadcast message")
    
    # list-agents
    subparsers.add_parser("list-agents", help="List all agents")
    
    # complete
    complete_parser = subparsers.add_parser("complete", help="Complete task")
    complete_parser.add_argument("task_id", help="Task ID")
    complete_parser.add_argument("agent", help="My agent ID")
    complete_parser.add_argument("result", nargs="?", default="", help="Result")
    
    # fail
    fail_parser = subparsers.add_parser("fail", help="Fail task")
    fail_parser.add_argument("task_id", help="Task ID")
    fail_parser.add_argument("agent", help="My agent ID")
    fail_parser.add_argument("error", help="Error message")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "send":
        cmd_send(args.to, args.title, args.description, args.chat_id)
    elif args.command == "poll":
        cmd_poll(args.agent)
    elif args.command == "reply":
        cmd_reply(args.to, args.task_id, args.message)
    elif args.command == "broadcast":
        cmd_broadcast(args.message)
    elif args.command == "list-agents":
        cmd_list_agents()
    elif args.command == "complete":
        cmd_complete(args.task_id, args.agent, args.result)
    elif args.command == "fail":
        cmd_fail(args.task_id, args.agent, args.error)

if __name__ == "__main__":
    main()
