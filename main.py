# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 把干活的函数导入进来
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