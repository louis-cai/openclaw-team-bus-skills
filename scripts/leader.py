#!/usr/bin/env python3
"""
OpenClaw Team Bus Leader
Usage: python3 leader.py <worker-id> <task-title> <task-description> [chat-id]

Main Agent 使用此脚本派发任务给 worker
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

BUS_ROOT = Path(os.environ.get("BUS_ROOT", "/root/.openclaw/team-bus"))
TASKS_DIR = BUS_ROOT / "tasks"

def create_task(worker_id: str, title: str, description: str, chat_id: str = "", subtype: str = "general") -> str:
    """创建任务文件"""
    import time
    import random
    
    task_id = f"task-{int(time.time())}-{random.randint(1000, 9999)}"
    
    task = {
        "id": task_id,
        "type": "task",
        "subtype": subtype,
        "status": "pending",
        "from": "lead",
        "to": worker_id,
        "createdAt": datetime.now().isoformat(),
        "payload": {
            "title": title,
            "description": description,
            "telegram": {
                "chatId": chat_id
            }
        },
        "result": None,
        "error": None
    }
    
    # 确保目录存在
    pending_dir = TASKS_DIR / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    task_file = pending_dir / f"{worker_id}_{task_id}.json"
    task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"[Leader] Created task {task_id} for {worker_id}: {title}")
    return task_id

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 leader.py <worker-id> <task-title> <task-description> [chat-id]")
        print("Example: python3 leader.py worker-coder 'Fix login bug' '用户点击登录无响应' -100123456")
        sys.exit(1)
    
    worker_id = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    chat_id = sys.argv[4] if len(sys.argv) > 4 else ""
    
    task_id = create_task(worker_id, title, description, chat_id)
    print(f"Task dispatched: {task_id}")

if __name__ == "__main__":
    main()
