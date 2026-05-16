import time
import random
from datetime import datetime
from core.database import SessionLocal, SystemLog
from core.config import settings

FAKE_HOSTNAME = "Server-Node-B (Beijing)"


def run_agent():
    print(f" [幽灵探针] {FAKE_HOSTNAME} 启动成功！")
    print(" 正在向 MySQL 数据库总部持续发送伪装数据...\n")

    while True:
        db = SessionLocal()
        try:
            is_spike = random.random() > 0.9
            cpu = (
                round(random.uniform(85.0, 99.0), 1)
                if is_spike
                else round(random.uniform(5.0, 40.0), 1)
            )
            mem = round(random.uniform(40.0, 75.0), 1)
            up = round(random.uniform(0.1, 5.0), 2)
            down = round(random.uniform(1.0, 20.0), 2)
            disk = round(random.uniform(50.0, 70.0), 1)

            log_entry = SystemLog(
                hostname=FAKE_HOSTNAME,
                cpu_usage=cpu,
                mem_usage=mem,
                net_upload=up,
                net_download=down,
                disk_percent=disk,
            )

            db.add(log_entry)
            db.commit()

            now_str = datetime.now().strftime("%H:%M:%S")
            mark = " [尖峰!]" if is_spike else ""
            print(
                f"[{now_str}] 发送数据包 -> CPU: {cpu}% | "
                f"内存: {mem}% | 磁盘: {disk}%{mark}"
            )

        except Exception as e:
            db.rollback()
            print(f" 发送失败，网络异常: {e}")
        finally:
            db.close()

        time.sleep(2)


if __name__ == "__main__":
    run_agent()
