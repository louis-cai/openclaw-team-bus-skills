# HEARTBEAT.md (Worker Agent)

- 运行 worker 脚本: python3 /path/to/openclaw-team-bus-skills/scripts/worker.py worker-coder
- 脚本会自动:
  1. 扫描 pending 目录
  2. 抢占任务
  3. 发送 Telegram 状态 (开始)
  4. 执行任务
  5. 发送 Telegram 状态 (完成/失败)
  6. 归档任务
- 如果无任务，回复 HEARTBEAT_OK
