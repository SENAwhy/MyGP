import psutil
import time
import csv
import os
import socket
import subprocess
import platform
from core.database import save_to_mysql, SessionLocal, SystemInfo
from core.ai_anomaly import ai_engine
from core.config import settings
from core.logger import app_logger

last_net_io = psutil.net_io_counters()
last_disk_io = psutil.disk_io_counters()
last_time = time.time()
LOG_FILE = settings.MONITOR_LOG_FILE
psutil.cpu_percent(interval=None)


def _get_docker_stats() -> list[dict]:
    """尝试获取 Docker 容器状态（Docker 未安装时返回空列表）"""
    try:
        result = subprocess.run(
            [
                "docker", "stats", "--no-stream",
                "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}|{{.MemUsage}}",
            ],
            capture_output=True, text=True, timeout=5,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )
        if result.returncode != 0:
            return []

        containers = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                containers.append({
                    "name": parts[0],
                    "cpu_percent": parts[1].replace("%", "").strip(),
                    "mem_percent": parts[2].replace("%", "").strip(),
                    "mem_usage": parts[3].strip(),
                })
        return containers
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return []


def get_system_info() -> dict:
    """获取系统静态信息（操作系统、CPU型号、内存等）"""
    try:
        cpu_freq = psutil.cpu_freq()
        boot_time = datetime_from_timestamp(psutil.boot_time())
    except Exception:
        cpu_freq = None
        boot_time = "未知"

    try:
        cpu_model = platform.processor() or "未知"
    except Exception:
        cpu_model = "未知"

    return {
        "os_name": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu_model": cpu_model,
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_freq_current": round(cpu_freq.current, 2) if cpu_freq else 0,
        "cpu_freq_max": round(cpu_freq.max, 2) if cpu_freq else 0,
        "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "total_disk_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
        "boot_time": boot_time,
        "python_version": platform.python_version(),
    }


def datetime_from_timestamp(ts: float) -> str:
    """时间戳转可读时间字符串"""
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def save_to_csv(data: dict):
    """将监控数据存入 CSV 文件"""
    file_exists = os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
            fieldnames = [
                "time", "cpu_usage", "memory_usage",
                "net_upload", "net_download", "disk_percent", "swap_percent",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        app_logger.error(f"CSV 写入失败: {e}")


def get_system_data() -> dict:
    """采集当前系统全部监控指标"""
    global last_net_io, last_disk_io, last_time

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    disk = psutil.disk_usage("/")

    current_time = time.time()
    time_diff = current_time - last_time
    if time_diff <= 0:
        time_diff = 0.001

    # 网络速率
    current_net_io = psutil.net_io_counters()
    upload_speed = (
        (current_net_io.bytes_sent - last_net_io.bytes_sent)
        / time_diff / 1024 / 1024
    )
    download_speed = (
        (current_net_io.bytes_recv - last_net_io.bytes_recv)
        / time_diff / 1024 / 1024
    )
    last_net_io = current_net_io

    # 磁盘 I/O 速率
    try:
        current_disk_io = psutil.disk_io_counters()
        disk_read_speed = (
            (current_disk_io.read_bytes - last_disk_io.read_bytes)
            / time_diff / 1024 / 1024
        )
        disk_write_speed = (
            (current_disk_io.write_bytes - last_disk_io.write_bytes)
            / time_diff / 1024 / 1024
        )
        last_disk_io = current_disk_io
    except Exception:
        disk_read_speed = 0
        disk_write_speed = 0

    last_time = current_time

    cpu_usage = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # 进程列表
    processes = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "exe", "memory_info"]):
        try:
            if p.info["pid"] > 4:
                mem_mb = p.info["memory_info"].rss / 1024 / 1024
                processes.append({
                    "pid": p.info["pid"],
                    "name": p.info["name"] or "未知",
                    "cpu_percent": p.info["cpu_percent"] or 0,
                    "path": p.info["exe"] or "未知路径",
                    "mem_mb": round(mem_mb, 2),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_processes = sorted(
        processes, key=lambda x: (x["cpu_percent"] or 0), reverse=True
    )[:5]

    # 网络连接数
    try:
        net_connections = len(psutil.net_connections(kind="inet"))
    except Exception:
        net_connections = 0

    # Docker 容器
    docker_containers = _get_docker_stats()

    result_data = {
        "time": time.strftime("%H:%M:%S"),
        "hostname": hostname,
        "local_ip": local_ip,
        "disk_percent": disk.percent,
        "cpu_usage": cpu_usage,
        "memory_usage": mem.percent,
        "swap_percent": swap.percent,
        "net_upload": round(upload_speed, 2),
        "net_download": round(download_speed, 2),
        "disk_read_mbps": round(disk_read_speed, 2),
        "disk_write_mbps": round(disk_write_speed, 2),
        "net_connections": net_connections,
        "top_processes": top_processes,
        "docker_containers": docker_containers,
    }

    save_to_csv(result_data)
    save_to_mysql(result_data)

    anomaly_score = ai_engine.get_anomaly_score(
        result_data["cpu_usage"], result_data["memory_usage"]
    )
    result_data["is_anomaly"] = anomaly_score["is_anomaly"]
    result_data["anomaly_detail"] = anomaly_score

    return result_data


def get_history_data(limit: int = 100, offset: int = 0, metric: str = "all") -> dict:
    """读取历史监控数据，支持分页和指标筛选"""
    if not os.path.exists(LOG_FILE):
        return {"total": 0, "items": []}

    all_rows = []
    try:
        with open(LOG_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_rows.append({
                    "time": row.get("time", ""),
                    "cpu": float(row.get("cpu_usage", 0)),
                    "mem": float(row.get("memory_usage", 0)),
                    "net_up": float(row.get("net_upload", 0)),
                    "net_down": float(row.get("net_download", 0)),
                    "disk": float(row.get("disk_percent", 0)),
                    "swap": float(row.get("swap_percent", 0)),
                })

        total = len(all_rows)
        items = all_rows[offset : offset + limit]

        if metric != "all":
            items = [
                {"time": r["time"], metric: r[metric]}
                for r in items
            ]

        return {"total": total, "items": items}
    except Exception as e:
        app_logger.error(f"读取历史数据失败: {e}")
        return {"total": 0, "items": []}


def get_dashboard_summary() -> dict:
    """获取仪表盘摘要统计"""
    history = get_history_data(limit=500)
    items = history["items"]

    if not items:
        return {
            "avg_cpu": 0, "max_cpu": 0,
            "avg_mem": 0, "max_mem": 0,
            "total_records": 0,
            "anomaly_count_24h": 0,
        }

    cpu_values = [r["cpu"] for r in items]
    mem_values = [r["mem"] for r in items]

    return {
        "avg_cpu": round(sum(cpu_values) / len(cpu_values), 1),
        "max_cpu": round(max(cpu_values), 1),
        "avg_mem": round(sum(mem_values) / len(mem_values), 1),
        "max_mem": round(max(mem_values), 1),
        "total_records": history["total"],
        "anomaly_count_24h": sum(
            1 for r in items if r["cpu"] > 80 or r["mem"] > 90
        ),
    }
