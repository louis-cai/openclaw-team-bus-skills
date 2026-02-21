#!/usr/bin/env python3
"""
OpenClaw Team Bus Worker
Usage: python3 worker.py <worker-id>

扫描 pending 目录，抢占任务，执行并报告 Telegram 状态
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 配置
BUS_ROOT = Path(os.environ.get("BUS_ROOT", "/root/.openclaw/team-bus"))
TASKS_DIR = BUS_ROOT / "tasks"

def get_pending_tasks(worker_id: str) -> list[dict]:
    """扫描 pending 目录，返回属于该 worker 的任务"""
    pending_dir = TASKS_DIR / "pending"
    if not pending_dir.exists():
        return []
    
    tasks = []
    for f in pending_dir.glob(f"{worker_id}_*.json"):
        try:
            tasks.append({
                "file": f,
                "data": json.loads(f.read_text(encoding="utf-8"))
            })
        except Exception as e:
            print(f"Error reading {f}: {e}")
    return sorted(tasks, key=lambda x: x["data"].get("createdAt", ""))

def claim_task(worker_id: str, task_id: str) -> bool:
    """抢占任务（原子操作：移动到 processing）"""
    src = TASKS_DIR / "pending" / f"{worker_id}_{task_id}.json"
    dst = TASKS_DIR / "processing" / f"{worker_id}_{task_id}.json"
    
    if src.exists():
        # 确保 processing 目录存在
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.rename(src, dst)
        return True
    return False

def complete_task(worker_id: str, task_id: str, result: dict):
    """完成任务"""
    task_file = TASKS_DIR / "processing" / f"{worker_id}_{task_id}.json"
    if not task_file.exists():
        return
    
    task = json.loads(task_file.read_text(encoding="utf-8"))
    task["status"] = "completed"
    task["completedAt"] = datetime.now().isoformat()
    task["result"] = result
    
    dst = TASKS_DIR / "completed" / f"{worker_id}_{task_id}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # 删除 processing 状态的文件
    task_file.unlink()

def fail_task(worker_id: str, task_id: str, error: str):
    """任务失败"""
    task_file = TASKS_DIR / "processing" / f"{worker_id}_{task_id}.json"
    if not task_file.exists():
        return
    
    task = json.loads(task_file.read_text(encoding="utf-8"))
    task["status"] = "failed"
    task["failedAt"] = datetime.now().isoformat()
    task["error"] = error
    
    dst = TASKS_DIR / "failed" / f"{worker_id}_{task_id}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    
    task_file.unlink()

def send_status(chat_id: str, worker_id: str, task_title: str, status: str):
    """发送 Telegram 状态（需要 OpenClaw sendMessage 工具）"""
    emoji = {"started": "🔵", "completed": "✅", "failed": "❌"}.get(status, "⚪")
    message = f"{emoji} [{worker_id}] {status} {task_title}"
    
    # 输出给 OpenClaw 处理
    print(f"[TELEGRAM] chatId={chat_id} message={message}")
    return message

def execute_task(task: dict) -> dict:
    """执行任务的逻辑 - 由具体 worker 实现"""
    # 这里返回空结果，实际由 OpenClaw agent 执行
    return {"executed": True}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 worker.py <worker-id>")
        sys.exit(1)
    
    worker_id = sys.argv[1]
    print(f"[Worker] {worker_id} starting...")
    
    # 1. 扫描 pending 任务
    tasks = get_pending_tasks(worker_id)
    
    if not tasks:
        print(f"[Worker] No pending tasks for {worker_id}")
        sys.exit(0)
    
    print(f"[Worker] Found {len(tasks)} pending task(s)")
    
    # 2. 逐个处理任务
    for task_info in tasks:
        task = task_info["data"]
        task_id = task["id"]
        
        # 3. 抢任务
        if not claim_task(worker_id, task_id):
            print(f"[Worker] Failed to claim task {task_id} (可能被其他 worker 抢走)")
            continue
        
        print(f"[Worker] Claimed task {task_id}: {task.get('payload', {}).get('title', 'No title')}")
        
        # 4. 获取 Telegram 配置
        payload = task.get("payload", {})
        telegram_config = payload.get("telegram", {})
        chat_id = telegram_config.get("chatId", "")
        task_title = payload.get("title", task_id)
        
        # 5. 报告开始
        if chat_id:
            send_status(chat_id, worker_id, task_title, "started")
        
        try:
            # 6. 执行任务
            # 注意：这里只是示例，实际执行由 OpenClaw agent 通过 HEARTBEAT 完成
            result = execute_task(task)
            
            # 7. 完成任务
            complete_task(worker_id, task_id, result)
            
            # 8. 报告完成
            if chat_id:
                send_status(chat_id, worker_id, task_title, "completed")
            
            print(f"[Worker] Task {task_id} completed")
            
        except Exception as e:
            # 9. 失败
            fail_task(worker_id, task_id, str(e))
            
            # 10. 报告失败
            if chat_id:
                send_status(chat_id, worker_id, task_title, "failed")
            
            print(f"[Worker] Task {task_id} failed: {e}")

if __name__ == "__main__":
    main()
