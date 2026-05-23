"""启动三个模拟 agent 节点（db / web / storage）"""
import subprocess
import os
import sys
import time

AGENTS = [
    {"role": "db",      "hostname": "Node-DB-Shanghai"},
    {"role": "web",     "hostname": "Node-Web-Tokyo"},
    {"role": "storage", "hostname": "Node-Storage-Frankfurt"},
]

DB_URL = "mysql+pymysql://root:why20030319@127.0.0.1:3306/aiops_monitor"

procs = []

for cfg in AGENTS:
    env = os.environ.copy()
    env["NODE_ROLE"] = cfg["role"]
    env["NODE_HOSTNAME"] = cfg["hostname"]
    env["DB_URL"] = DB_URL

    proc = subprocess.Popen(
        [sys.executable, "agent.py"],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    procs.append((cfg, proc))
    print(f"[启动] {cfg['hostname']} (角色: {cfg['role']}) PID={proc.pid}")

print(f"\n3 个 Agent 节点已启动，持续上报数据中...")
print("按 Ctrl+C 停止所有节点\n")

try:
    while True:
        time.sleep(10)
        for cfg, proc in procs:
            if proc.poll() is not None:
                print(f"[警告] {cfg['hostname']} 已退出 (code={proc.returncode})")
except KeyboardInterrupt:
    print("\n正在停止所有节点...")
    for cfg, proc in procs:
        proc.terminate()
    print("已停止。")
