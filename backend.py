from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psutil
from openai import OpenAI
import time  # 引入时间模块

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

#  注意替换你的真实 API Key
client = OpenAI(api_key="sk-c07cd4a6ac3546509ec40c526577793a", base_url="https://api.deepseek.com")

@app.get("/api/system_status")
def get_status():
    # 抓取前3大吃性能的进程
    processes = []
    # 遍历所有进程，抓取 pid, 名字 和 cpu占用率
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if p.info['cpu_percent'] is not None:
                processes.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    # 按 CPU 占用率从大到小排序，只取前 3 名
    top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:3]

    return {
        "status": "success",
        "time": time.strftime("%H:%M:%S"), # 把当前时间发给前端画图
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "top_processes": top_processes     # 把排行榜也发过去
    }

@app.get("/api/diagnose")
def ai_diagnose():
    try:
        processes = [p.info for p in psutil.process_iter(['name', 'cpu_percent']) if p.info['cpu_percent'] is not None]
        top_process = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[0]
        
        prompt = f"我的服务器当前CPU异常，占用最高的进程是 {top_process['name']} (占用 {top_process['cpu_percent']}%CPU)。请用50个字以内给出一个运维排查建议。"
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一名资深的AIOps智能运维专家。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        ai_reply = response.choices[0].message.content
        return {"status": "success", "report": ai_reply}
    except Exception as e:
        return {"status": "error", "report": f"AI 调用失败，原因：{str(e)}"}