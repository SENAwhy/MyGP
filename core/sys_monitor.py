# core/sys_monitor.py
import psutil
import time
import csv
import os

#  1. 初始化配置
last_net_io = psutil.net_io_counters()
last_time = time.time()
LOG_FILE = "monitor_log.csv"

# 初始化 CPU 采样
psutil.cpu_percent(interval=None)

def save_to_csv(data):
    """将监控数据持久化到 CSV 文件"""
    file_exists = os.path.isfile(LOG_FILE)
    try:
        # 'a' 代表 append（追加模式）
        with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
            fieldnames = ["time", "cpu_usage", "memory_usage", "net_upload", "net_download"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # 如果是第一次創建文件，先寫入表頭
            if not file_exists:
                writer.writeheader()
            
            # 只写入基数
            writer.writerow({
                "time": data["time"],
                "cpu_usage": data["cpu_usage"],
                "memory_usage": data["memory_usage"],
                "net_upload": data["net_upload"],
                "net_download": data["net_download"]
            })
    except Exception as e:
        print(f"日志写入失败: {e}")

def get_system_data():
    global last_net_io, last_time
    
    # 计算时间与网速
    current_time = time.time()
    time_diff = current_time - last_time
    if time_diff <= 0: time_diff = 0.001
    
    current_net_io = psutil.net_io_counters()
    upload_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / time_diff / 1024 / 1024
    download_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / time_diff / 1024 / 1024
    
    last_net_io = current_net_io
    last_time = current_time

    # 获取CPU和进程
    cpu_usage = psutil.cpu_percent(interval=None)
    processes = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if p.info['pid'] > 4: 
                processes.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    top_processes = sorted(processes, key=lambda x: (x['cpu_percent'] or 0), reverse=True)[:3]

    # 封装結果
    result_data = {
        "time": time.strftime("%H:%M:%S"),
        "cpu_usage": cpu_usage,
        "memory_usage": psutil.virtual_memory().percent,
        "net_upload": round(upload_speed, 2),
        "net_download": round(download_speed, 2),
        "top_processes": top_processes
    }

    # 存一份到硬盘
    save_to_csv(result_data)

    return result_data