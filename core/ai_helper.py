# core/ai_helper.py
from openai import OpenAI

# 初始化大模型客户端 (记得填你的真实 Key)
client = OpenAI(api_key="sk-c07cd4a6ac3546509ec40c526577793a", base_url="https://api.deepseek.com")

def get_diagnose_report(top_process_name, top_process_cpu):
    """专门负责调用大模型的函数"""
    prompt = f"我的服务器当前CPU异常，占用最高的进程是 {top_process_name} (占用 {top_process_cpu}%CPU)。请用50个字以内给出一个运维排查建议。"
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一名资深的AIOps智能运维专家。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 调用失败，原因：{str(e)}"