# core/ai_anomaly.py
import pandas as pd
from sklearn.ensemble import IsolationForest
from core.database import SessionLocal, SystemLog
import warnings

# 忽略 sklearn 的一些版本警告
warnings.filterwarnings('ignore')

class AnomalyDetector:
    def __init__(self):
        # contamination=0.05 意味着我们假设历史数据中大概有 5% 是异常的
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_trained = False
        self.train_model()

    def train_model(self):
        print(" [AI 引擎] 正在从数据库读取历史数据进行无监督学习训练...")
        db = SessionLocal()
        # 抓取本地主机最近的 500 条数据作为“正常基线”
        logs = db.query(SystemLog).filter(SystemLog.hostname == "LAPTOP-33OCQVST").order_by(SystemLog.id.desc()).limit(500).all()
        db.close()

        if len(logs) < 50:
            print("⚠️ [AI 引擎] 历史数据不足 50 条，模型暂不启动。")
            return

        # 把数据库里的记录提取成 AI 能看懂的 DataFrame 格式
        data = [[log.cpu_usage, log.mem_usage] for log in logs]
        df = pd.DataFrame(data, columns=['cpu', 'mem'])

        # 开始训练(拟合基线)
        self.model.fit(df)
        self.is_trained = True
        print("✅ [AI 引擎] 孤立森林模型训练完成！系统日常行为基线已建立。")

    def detect(self, cpu, mem):
        """预测当前数据是否异常"""
        if not self.is_trained:
            return False            
        df = pd.DataFrame([[cpu, mem]], columns=['cpu', 'mem'])
        # 预测结果： 1 是正常，-1 是异常
        prediction = self.model.predict(df)[0]
        return prediction == -1

# 全局实例化这个 AI 引擎
ai_engine = AnomalyDetector()