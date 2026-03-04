# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from core.database import SessionLocal, User, save_to_mysql # 引入 User
from core.auth import verify_password, get_password_hash, create_access_token
from core.sys_monitor import get_system_data, get_history_data
from core.sys_monitor import get_system_data
from core.ai_helper import get_diagnose_report

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 接口1：获取状态
@app.get("/api/system_status")
def get_status():
    data = get_system_data() # 让侦察兵去干活
    return {"status": "success", **data}

# 接口2：AI诊断
@app.get("/api/diagnose")
def ai_diagnose():
    # 1. 先让侦察兵查出当前第一名的进程
    sys_data = get_system_data()
    if not sys_data["top_processes"]:
        return {"status": "error", "report": "未抓取到进程数据"}
        
    top_proc = sys_data["top_processes"][0]
    
    # 2. 把第一名的名字和CPU，扔给AI去写报告
    report = get_diagnose_report(top_proc['name'], top_proc['cpu_percent'])
    
    return {"status": "success", "report": report}

from core.sys_monitor import get_system_data, get_history_data # 引入新函数

@app.get("/api/history")
def get_history():
    data = get_history_data()
    return {"status": "success", "history": data}

# 设置保安关卡：客户端必须拿着 token 才能访问
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# 初始化一个超级管理员账号（如果数据库里没有的话）
def init_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(username="admin", password_hash=get_password_hash("123456"), role="admin")
        db.add(new_admin)
        db.commit()
    db.close()

init_admin() # 启动时执行

#登录接口（负责发放 Token）
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

#  修改：给数据接口加锁 (依赖 oauth2_scheme)
@app.get("/api/system_status")
def get_status(token: str = Depends(oauth2_scheme)):
    # 只要代码能走到这里，说明 Token 是合法的
    data = get_system_data()
    return {"status": "success", **data}

@app.get("/api/history")
def get_history(token: str = Depends(oauth2_scheme)):
    data = get_history_data()
    return {"status": "success", "history": data}