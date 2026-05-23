"""AIOps 分布式节点采集代理 — 运行在 Docker 容器中。

每个容器扮演一种服务器角色，基于容器内真实的 psutil 指标，
叠加角色特征负载后上报到 MySQL 的 system_logs 表。
"""

import psutil
import time
import os
import random
import socket
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.orm import Session, declarative_base

# ---- 配置 ----
DB_URL = os.environ.get(
    "DB_URL",
    "mysql+pymysql://root:why20030319@host.docker.internal:3306/aiops_monitor",
)
ROLE = os.environ.get("NODE_ROLE", "generic")
NODE_HOSTNAME = os.environ.get("NODE_HOSTNAME", socket.gethostname())
INTERVAL = 2  # 采集间隔（秒）

# 角色标签 —— 使用 NODE_HOSTNAME 作为数据库中的节点标识
ROLE_LABELS = {
    "db": NODE_HOSTNAME,
    "web": NODE_HOSTNAME,
    "storage": NODE_HOSTNAME,
}

Base = declarative_base()


class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True)
    log_time = Column(DateTime, default=datetime.now)
    hostname = Column(String(50))
    cpu_usage = Column(Float)
    mem_usage = Column(Float)
    net_upload = Column(Float)
    net_download = Column(Float)
    disk_percent = Column(Float)


def apply_role_profile(cpu, mem, disk):
    """根据不同角色叠加负载特征，让各节点指标有明显差异。"""
    if ROLE == "db":
        # 数据库服务器：内存高、CPU 中等偏高、磁盘稳定
        mem = min(mem + random.uniform(25, 45), 98)
        cpu = cpu + random.uniform(10, 30)
        disk = disk + random.uniform(5, 20)
    elif ROLE == "web":
        # Web 服务器：CPU 波动大（模拟请求峰值）、内存中等
        spike = random.random() < 0.15  # 15% 概率出现请求峰值
        if spike:
            cpu = cpu + random.uniform(40, 60)
        else:
            cpu = cpu + random.uniform(5, 20)
        mem = min(mem + random.uniform(10, 25), 90)
    elif ROLE == "storage":
        # 存储服务器：磁盘使用率高、CPU 和内存低
        disk = min(disk + random.uniform(25, 50), 97)
        cpu = cpu + random.uniform(0, 10)
        mem = mem + random.uniform(5, 15)

    return (
        round(min(cpu, 99), 1),
        round(min(mem, 98), 1),
        round(min(disk, 97), 1),
    )


def collect(engine):
    """采集一次指标并写入数据库。"""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    # 网络速率在容器内通常很低，叠加一些模拟流量
    net_up = round(random.uniform(0.3, 4.0), 2)
    net_down = round(random.uniform(0.5, 10.0), 2)

    cpu, mem, disk = apply_role_profile(cpu, mem, disk)

    display_name = ROLE_LABELS.get(ROLE, NODE_HOSTNAME)

    with Session(engine) as session:
        log = SystemLog(
            hostname=display_name,
            cpu_usage=cpu,
            mem_usage=mem,
            net_upload=net_up,
            net_download=net_down,
            disk_percent=disk,
        )
        session.add(log)
        session.commit()

    # 尖峰标记
    flag = " [高负载!]" if (cpu > 80 or mem > 90) else ""
    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] {display_name}  |  "
        f"CPU: {cpu:5.1f}%  MEM: {mem:5.1f}%  DISK: {disk:5.1f}%  "
        f"NET↑{net_up:.1f} ↓{net_down:.1f} MB/s{flag}"
    )


def _mask_db_url(url: str) -> str:
    """安全地脱敏数据库连接字符串中的密码。"""
    try:
        if "@" not in url:
            return url
        prefix, rest = url.split("@", 1)
        if ":" in prefix:
            parts = prefix.rsplit(":", 1)
            return parts[0] + ":***@" + rest
        return url
    except Exception:
        return "[无法解析的数据库URL]"


def main():
    print(f"=== AIOps Agent 启动 ===")
    print(f"节点: {NODE_HOSTNAME}")
    print(f"角色: {ROLE}")
    print(f"数据库: {_mask_db_url(DB_URL)}")
    print()

    engine = create_engine(DB_URL, pool_pre_ping=True)

    # 验证数据库连接
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("数据库连接成功\n")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return

    while True:
        try:
            collect(engine)
        except Exception as e:
            print(f"采集异常: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
