# core/sys_monitor.py
import psutil
import time
import csv
import os
import socket  # 引入这个库来获取网络信息

# 1. 初始化配置
last_net_io = psutil.net_io_counters()
last_time = time.time()
LOG_FILE = "monitor_log.csv"
psutil.cpu_percent(interval=None)

def save_to_csv(data):
    """将数据存入 CSV"""
    file_exists = os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
            # 只记录核心数值数据
            fieldnames = ["time", "cpu_usage", "memory_usage", "net_upload", "net_download"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print(f"写入日志失败: {e}")

def get_system_data():
    global last_net_io, last_time
    
    #  2. 获取静态系统画像
    hostname = socket.gethostname()
    try:
        # 获取局域网 IP
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"
    
    # 获取 C 盘磁盘占用
    disk = psutil.disk_usage('/')
    
    # 3. 计算动态数据
    current_time = time.time()
    time_diff = current_time - last_time
    if time_diff <= 0: time_diff = 0.001
    
    current_net_io = psutil.net_io_counters()
    upload_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / time_diff / 1024 / 1024
    download_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / time_diff / 1024 / 1024
    
    last_net_io = current_net_io
    last_time = current_time

    cpu_usage = psutil.cpu_percent(interval=None)
    processes = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'exe', 'memory_info']):
        try:
            if p.info['pid'] > 4: 
                mem_mb = p.info['memory_info'].rss / 1024 / 1024
                processes.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "cpu_percent": p.info['cpu_percent'] or 0,
                    "path": p.info['exe'] or "未知路径",
                    "mem_mb": round(mem_mb, 2)
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    top_processes = sorted(processes, key=lambda x: (x['cpu_percent'] or 0), reverse=True)[:3]

    # 🚀 4. 把新抓到的数据塞进结果里发给前端
    result_data = {
        "time": time.strftime("%H:%M:%S"),
        "hostname": hostname,       # 传递主机名
        "local_ip": local_ip,       # 传递 IP
        "disk_percent": disk.percent,# 传递磁盘百分比
        "cpu_usage": cpu_usage,
        "memory_usage": psutil.virtual_memory().percent,
        "net_upload": round(upload_speed, 2),
        "net_download": round(download_speed, 2),
        "top_processes": top_processes
    }

    save_to_csv(result_data)
    return result_data