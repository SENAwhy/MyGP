from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import threading
import time
import os
import socket

from core.database import SessionLocal, User, SystemLog, init_default_rules
from core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    oauth2_scheme,
    get_current_user,
    RequireRole,
)
from core.sys_monitor import (
    get_system_data,
    get_history_data,
    get_system_info,
    get_dashboard_summary,
)
from core.ai_helper import get_diagnose_report
from core.ai_anomaly import ai_engine
from core.notifier import send_alert_email
from core.alert_engine import alert_engine
from core.config import settings
from core.logger import app_logger

app = FastAPI(title="AIOps 监控大屏 Max", version="2.0.0")

last_email_time = 0

# CORS 配置 — 开发阶段允许所有源，生产环境请限制为前端域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    """请求日志中间件"""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    app_logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)"
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    app_logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "服务器内部错误"},
    )



def init_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="admin",
        )
        db.add(new_admin)
        db.commit()
    db.close()


init_admin()
init_default_rules()


# ==================== 静态文件 & 前端页面 ====================

FRONTEND_DIST = "frontend/dist"
FRONTEND_DIST_INDEX = os.path.join(FRONTEND_DIST, "index.html")

if os.path.isdir(FRONTEND_DIST) and os.path.isfile(FRONTEND_DIST_INDEX):
    # Production: serve built frontend from frontend/dist
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend_assets")

    @app.get("/")
    async def root():
        return FileResponse(FRONTEND_DIST_INDEX)

elif os.path.isdir("static"):
    # Legacy: serve CDN-based frontend
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    async def root():
        if os.path.isfile("index.html"):
            return FileResponse("index.html")
        return {"message": "AIOps 监控大屏 API 服务运行中", "version": "2.0.0"}
else:

    @app.get("/")
    async def root():
        return {"message": "AIOps 监控大屏 API 服务运行中", "version": "2.0.0"}


# ==================== 认证接口 ====================

@app.post("/api/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = (
        db.query(User)
        .filter(User.username == form_data.username)
        .first()
    )
    db.close()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ==================== 监控数据接口 ====================

@app.get("/api/system_status")
def get_status(
    host: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    global last_email_time
    local_hostname = socket.gethostname()

    # 远程节点逻辑：host 非空且不是本地主机名
    if host and host != "" and host != local_hostname:
        db = SessionLocal()
        log = (
            db.query(SystemLog)
            .filter(SystemLog.hostname == host)
            .order_by(SystemLog.id.desc())
            .first()
        )
        db.close()
        if log:
            data = {
                "status": "success",
                "hostname": log.hostname,
                "local_ip": "云端节点 (Remote)",
                "cpu_usage": log.cpu_usage,
                "memory_usage": log.mem_usage,
                "net_upload": log.net_upload,
                "net_download": log.net_download,
                "disk_percent": log.disk_percent,
                "swap_percent": 0,
                "disk_read_mbps": 0,
                "disk_write_mbps": 0,
                "net_connections": 0,
                "top_processes": [],
                "docker_containers": [],
                "time": log.log_time.strftime("%H:%M:%S"),
                "is_anomaly": False,
                "anomaly_detail": {},
            }
            data["triggered_alerts"] = alert_engine.evaluate(data)
            return data
        return {"status": "error", "detail": "该节点暂无数据"}

    # 本地节点逻辑
    data = get_system_data()

    # 规则引擎评估告警
    triggered = alert_engine.evaluate(data)
    data["triggered_alerts"] = triggered

    # AI 异常邮件报警
    current_time = time.time()
    if data.get("is_anomaly") and (
        current_time - last_email_time > settings.ALERT_COOLDOWN_SECONDS
    ):
        subject = f"AIOps 紧急警报：{data['hostname']} 运行异常"
        detail = data.get("anomaly_detail", {})
        content = (
            f"警告！AI 双模型算法检测到您的系统行为偏离常态。\n\n"
            f"当前状态：\n"
            f"- CPU 占用：{data['cpu_usage']}%\n"
            f"- 内存占用：{data['memory_usage']}%\n"
            f"- 磁盘占用：{data['disk_percent']}%\n"
            f"- 交换分区：{data['swap_percent']}%\n"
            f"- 时间：{data['time']}\n\n"
            f"AI 分析详情：\n{detail.get('detail', '无')}\n\n"
            f"请立即登录 AIOps 监控大屏查看详情。"
        )

        t = threading.Thread(
            target=send_alert_email, args=(subject, content)
        )
        t.daemon = True
        t.start()

        last_email_time = current_time
        app_logger.warning("已触发 AI 异常邮件预警")

    return {"status": "success", **data}


@app.get("/api/history")
def get_history(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    metric: str = Query("all"),
    current_user: dict = Depends(get_current_user),
):
    try:
        data = get_history_data(limit=limit, offset=offset, metric=metric)
        return {"status": "success", **data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/diagnose")
def ai_diagnose(current_user: dict = Depends(get_current_user)):
    sys_data = get_system_data()
    if not sys_data["top_processes"]:
        return {"status": "error", "report": "未抓取到进程数据"}
    top_proc = sys_data["top_processes"][0]
    report = get_diagnose_report(top_proc["name"], top_proc["cpu_percent"])
    return {"status": "success", "report": report}


# ==================== 系统信息接口 ====================

@app.get("/api/system_info")
def system_info(current_user: dict = Depends(get_current_user)):
    """获取系统静态信息"""
    try:
        info = get_system_info()
        info["model_info"] = ai_engine.get_model_info()
        return {"status": "success", **info}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== 仪表盘摘要接口 ====================

@app.get("/api/dashboard_summary")
def dashboard_summary(current_user: dict = Depends(get_current_user)):
    """获取仪表盘摘要统计"""
    try:
        summary = get_dashboard_summary()
        return {"status": "success", **summary}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==================== 告警接口 ====================

@app.get("/api/alerts")
def get_alerts(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """获取告警历史"""
    return alert_engine.get_alert_history(limit=limit, offset=offset)


@app.get("/api/alert_rules")
def get_alert_rules(current_user: dict = Depends(get_current_user)):
    """获取告警规则列表"""
    rules = alert_engine.get_rules()
    return {"status": "success", "rules": rules}


@app.put("/api/alert_rules/{rule_id}")
def toggle_alert_rule(
    rule_id: int,
    enabled: bool = Query(True),
    current_user: dict = Depends(RequireRole("admin")),
):
    """启用或禁用告警规则（需要管理员角色）"""
    ok = alert_engine.toggle_rule(rule_id, enabled)
    if ok:
        return {"status": "success", "message": f"规则 {rule_id} 已{'启用' if enabled else '禁用'}"}
    raise HTTPException(status_code=404, detail="规则不存在")


# ==================== AI 模型信息接口 ====================

@app.get("/api/model_info")
def model_info(current_user: dict = Depends(get_current_user)):
    """获取 AI 异常检测模型的训练信息"""
    return {"status": "success", **ai_engine.get_model_info()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
