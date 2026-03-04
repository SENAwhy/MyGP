from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import threading  # 导入线程库，用于后台发邮件
import time       # 用于计时，防止邮件轰炸

from core.database import SessionLocal, User, SystemLog
from core.auth import verify_password, get_password_hash, create_access_token
from core.sys_monitor import get_system_data, get_history_data
from core.ai_helper import get_diagnose_report
from core.notifier import send_alert_email # 导入你的邮件模块

app = FastAPI()

# 全局变量：记录上次发送报警邮件的时间（初始为 0）
last_email_time = 0 

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# 初始化管理员账号
def init_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(username="admin", password_hash=get_password_hash("123456"), role="admin")
        db.add(new_admin)
        db.commit()
    db.close()

init_admin()

@app.post("/api/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()
    db.close()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# --- 核心接口：获取状态 + 邮件报警触发 ---
@app.get("/api/system_status")
def get_status(host: Optional[str] = None, token: str = Depends(oauth2_scheme)):
    global last_email_time
    
    # 远程节点逻辑
    if host == "Server-Node-B (Beijing)":
        db = SessionLocal()
        log = db.query(SystemLog).filter(SystemLog.hostname == host).order_by(SystemLog.id.desc()).first()
        db.close()
        if log:
            return {
                "status": "success",
                "hostname": log.hostname,
                "local_ip": "云端节点 (Remote)",
                "cpu_usage": log.cpu_usage,
                "memory_usage": log.mem_usage,
                "net_upload": log.net_upload,
                "net_download": log.net_download,
                "disk_percent": log.disk_percent,
                "top_processes": [],
                "time": log.log_time.strftime('%H:%M:%S'),
                "is_anomaly": False # 远程暂不开启 AI 异常检测
            }
        return {"status": "error", "detail": "该节点暂无数据"}
    
    # 本地节点逻辑
    data = get_system_data()
    
    #  触发邮件报警判断
    # 条件：AI 判定异常 且 距离上次发信超过 600 秒 (10分钟)
    current_time = time.time()
    if data.get("is_anomaly") and (current_time - last_email_time > 600):
        subject = f"🚨 AIOps 紧急警报：{data['hostname']} 运行异常"
        content = (f"警告！AI 孤立森林算法检测到您的系统行为偏离常态。\n\n"
                   f"当前状态：\n"
                   f"- CPU 占用：{data['cpu_usage']}%\n"
                   f"- 内存占用：{data['memory_usage']}%\n"
                   f"- 时间：{data['time']}\n\n"
                   f"请立即登录 AIOps 监控大屏查看详情。")
        
        # 开启新线程发送邮件，不阻塞主程序
        threading.Thread(target=send_alert_email, args=(subject, content)).start()
        
        # 更新最后发信时间
        last_email_time = current_time
        print(f"📧 已触发异常邮件预警，下次预警将在 10 分钟后开启。")

    return {"status": "success", **data}

@app.get("/api/history")
def get_history(token: str = Depends(oauth2_scheme)):
    try:
        data = get_history_data(limit=100) 
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/diagnose")
def ai_diagnose(token: str = Depends(oauth2_scheme)):
    sys_data = get_system_data()
    if not sys_data["top_processes"]:
        return {"status": "error", "report": "未抓取到进程数据"}
    top_proc = sys_data["top_processes"][0]
    report = get_diagnose_report(top_proc['name'], top_proc['cpu_percent'])
    return {"status": "success", "report": report}