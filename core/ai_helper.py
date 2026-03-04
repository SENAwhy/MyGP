# core/ai_helper.py
import os
from openai import OpenAI

# 尝试获取 API Key
api_key = os.getenv("DEEPSEEK_API_KEY", "sk-c07cd4a6ac3546509ec40c526577793a")

def get_diagnose_report(process_name, cpu_percent):
    # 兜底的本地 AI 报告模板
    fallback_report = f"""
    (⚠️ 离线专家诊断模式) 
    检测到异常高耗能进程：【{process_name}】，当前 CPU 占用率达 {cpu_percent}%！
    
    🧠 智能运维中枢分析：
    1. 【进程属性】该进程正霸占极其庞大的算力资源，已打破系统日常运行基线。
    2. 【风险评估】若此程序为大型游戏或编译任务，属正常现象；若在后台静默运行，极度疑似“挖矿木马”或遭遇“严重内存泄漏”。
    3. 【执行建议】请立即唤醒终端，输入 `taskkill /F /IM {process_name}` 强行终止该进程，并进行全盘深度扫描！
    """

    try:
        # 尝试呼叫 DeepSeek
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        system_prompt = "你是一个AIOps智能运维专家，请用简短、专业的语言，诊断以下高耗能进程可能存在的问题，并给出处理建议。"
        user_prompt = f"当前系统异常！发现高耗能进程：{process_name}，CPU占用率高达 {cpu_percent}%。请分析原因并给出建议。"
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            timeout=5  # 设置5秒超时
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"⚠️ [警告] DeepSeek 大模型调用失败，已切换至本地离线诊断。错误原因: {e}")
        # 如果断网、API报错、或者超时，立刻返回写好的报告
        return fallback_report