# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from core.database import SessionLocal, User, SystemLog, save_to_mysql
from core.auth import verify_password, get_password_hash, create_access_token
from core.sys_monitor import get_system_data, get_history_data
from core.ai_helper import get_diagnose_report

app = FastAPI()

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 客户端必须拿着 token 才能访问
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# 初始化一个超级管理员账号
def init_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(username="admin", password_hash=get_password_hash("123456"), role="admin")
        db.add(new_admin)
        db.commit()
    db.close()

init_admin() # 启动时执行

#  登录接口（负责核对密码并下发 Token）
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
    
    # 密码正确，发放 Token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# 以下是加密区域，必须携带 Token 才能访问
# ==========================================

#  接口1：获取状态 (支持多节点切换)
@app.get("/api/system_status")
def get_status(host: Optional[str] = None, token: str = Depends(oauth2_scheme)):
    #如果是远端节点，直接去 MySQL 数据库里捞它的最新数据
    if host == "Server-Node-B (Beijing)":
        db = SessionLocal()
        # 倒序排列，拿这个节点的最后一条记录
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
                "top_processes": [], # 远端服务器没有进程权限，传空列表
                "time": log.log_time.strftime('%H:%M:%S')
            }
        return {"status": "error", "detail": "该节点暂无数据"}
    data = get_system_data()
    return {"status": "success", **data}

# 接口2：获取历史记录
# main.py
@app.get("/api/history")
def get_history(token: str = Depends(oauth2_scheme)):
    try:
        from core.sys_monitor import get_history_data
        data = get_history_data(limit=100) 
        return {"status": "success", "data": data}
    except Exception as e:
        print(f"读取历史接口崩溃: {e}")
        return {"status": "error", "message": str(e)}

#  接口3：AI诊断
@app.get("/api/diagnose")
def ai_diagnose(token: str = Depends(oauth2_scheme)):
    sys_data = get_system_data()
    if not sys_data["top_processes"]:
        return {"status": "error", "report": "未抓取到进程数据"}
        
    top_proc = sys_data["top_processes"][0]
    report = get_diagnose_report(top_proc['name'], top_proc['cpu_percent'])
    
    return {"status": "success", "report": report}