# core/sys_monitor.py
import psutil
import time

# 🚀 初始化记录：在大厂性能优化中，这叫“热启动”
last_net_io = psutil.net_io_counters()
last_time = time.time()

# 提前初始化一次，防止第一次调用返回 0
psutil.cpu_percent(interval=None)

def get_system_data():
    global last_net_io, last_time
    
    # 1. 计算极速时间差
    current_time = time.time()
    time_diff = current_time - last_time
    if time_diff <= 0: time_diff = 0.001 # 防御性编程：防止除以零
    
    # 2. 计算实时网速 (MB/s)
    current_net_io = psutil.net_io_counters()
    upload_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / time_diff / 1024 / 1024
    download_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / time_diff / 1024 / 1024
    
    # 更新记录点
    last_net_io = current_net_io
    last_time = current_time

    # 3. 🚀 关键改进：interval=None！不让系统在此阻塞死等
    cpu_usage = psutil.cpu_percent(interval=None)

    # 4. 优化进程抓取：过滤掉无意义的系统空闲进程
    processes = []
    # 遍历所有进程，只拿我们需要的数据
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            # 过滤掉 PID 0 (System Idle) 和 PID 4 (System)，这两个是“伪占用”
            if p.info['pid'] > 4: 
                processes.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    # 只取前 3 名吃性能的真程序
    top_processes = sorted(processes, key=lambda x: (x['cpu_percent'] or 0), reverse=True)[:3]

    return {
        "time": time.strftime("%H:%M:%S"),
        "cpu_usage": cpu_usage,
        "memory_usage": psutil.virtual_memory().percent,
        "net_upload": round(upload_speed, 2),
        "net_download": round(download_speed, 2),
        "top_processes": top_processes
    }