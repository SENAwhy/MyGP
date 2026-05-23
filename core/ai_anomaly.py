import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from core.database import SessionLocal, SystemLog
from core.logger import app_logger
import warnings

warnings.filterwarnings("ignore")


class AnomalyDetector:
    """AI 异常检测器 —— 使用孤立森林 + LOF 双模型进行无监督异常检测"""

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.05, random_state=42, n_estimators=100
        )
        self.lof = LocalOutlierFactor(
            contamination=0.05, novelty=True, n_neighbors=20
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_samples = 0
        self.train_model()

    def train_model(self):
        app_logger.info("正在从数据库读取历史数据进行无监督学习训练...")
        db = SessionLocal()
        try:
            logs = (
                db.query(SystemLog)
                .order_by(SystemLog.id.desc())
                .limit(500)
                .all()
            )
        except Exception as e:
            app_logger.warning(f"数据库查询失败，模型暂不启动: {e}")
            db.close()
            return
        db.close()

        if len(logs) < 50:
            app_logger.warning(f"历史数据仅 {len(logs)} 条，模型暂不启动（需 >= 50）")
            return

        try:
            data = [[log.cpu_usage, log.mem_usage] for log in logs]
            df = pd.DataFrame(data, columns=["cpu", "mem"])

            # 标准化后训练两个模型
            scaled = self.scaler.fit_transform(df)
            self.model.fit(scaled)
            self.lof.fit(scaled)
            self.is_trained = True
            self.training_samples = len(logs)
            app_logger.info(
                f"双模型训练完成！孤立森林 + LOF 已建立基线，样本量: {self.training_samples}"
            )
        except Exception as e:
            app_logger.error(f"模型训练失败: {e}")

    def detect(self, cpu: float, mem: float) -> bool:
        """综合双模型判断当前数据是否异常"""
        if not self.is_trained:
            return False

        df = pd.DataFrame([[cpu, mem]], columns=["cpu", "mem"])
        scaled = self.scaler.transform(df)

        if_pred = self.model.predict(scaled)[0]
        lof_pred = self.lof.predict(scaled)[0]

        # 任一模型判定异常则视为异常
        return if_pred == -1 or lof_pred == -1

    def get_anomaly_score(self, cpu: float, mem: float) -> dict:
        """返回异常评分详情（用于前端展示和论文实验分析）"""
        if not self.is_trained:
            return {
                "is_anomaly": False,
                "if_score": 0.0,
                "lof_score": 0.0,
                "detail": "模型未训练",
            }

        df = pd.DataFrame([[cpu, mem]], columns=["cpu", "mem"])
        scaled = self.scaler.transform(df)

        if_score = float(self.model.decision_function(scaled)[0])
        if_pred = int(self.model.predict(scaled)[0])

        lof_score = float(self.lof.decision_function(scaled)[0])
        lof_pred = int(self.lof.predict(scaled)[0])

        is_anomaly = if_pred == -1 or lof_pred == -1

        return {
            "is_anomaly": is_anomaly,
            "if_score": round(if_score, 4),
            "lof_score": round(lof_score, 4),
            "if_vote": "异常" if if_pred == -1 else "正常",
            "lof_vote": "异常" if lof_pred == -1 else "正常",
            "detail": (
                f"孤立森林评分: {if_score:.4f} ({'异常' if if_pred == -1 else '正常'}) | "
                f"LOF评分: {lof_score:.4f} ({'异常' if lof_pred == -1 else '正常'})"
            ),
        }

    def get_model_info(self) -> dict:
        """返回模型元信息（用于系统信息展示和论文）"""
        return {
            "is_trained": self.is_trained,
            "training_samples": self.training_samples,
            "if_contamination": 0.05,
            "if_n_estimators": 100,
            "lof_n_neighbors": 20,
            "models": ["IsolationForest", "LocalOutlierFactor"],
        }


ai_engine = AnomalyDetector()
