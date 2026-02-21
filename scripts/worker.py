#!/usr/bin/env python3
"""
Worker wrapper - 供 HEARTBEAT 调用
Usage: python3 worker.py <worker-id>

简化版，内部调用 bus.py poll
"""

import sys
import os

# 设置当前 agent ID
if len(sys.argv) > 1:
    os.environ["TEAM_BUS_AGENT"] = sys.argv[1]

# 调用 bus.py poll
os.execv(sys.executable, [sys.executable, "/root/openclaw-team-bus-skills/scripts/bus.py", "poll", sys.argv[1] if len(sys.argv) > 1 else "worker"])
