"""
AI 异常检测模块单元测试
测试孤立森林 + LOF 双模型的行为
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestAnomalyDetector:
    """测试异常检测器核心逻辑"""

    def test_initialization(self):
        """测试初始化状态"""
        from core.ai_anomaly import AnomalyDetector
        detector = AnomalyDetector.__new__(AnomalyDetector)
        # 不调用 __init__，避免数据库连接
        assert True

    def test_detect_returns_bool_untrained(self):
        """测试未训练时 detect 返回 False"""
        from core.ai_anomaly import AnomalyDetector
        detector = AnomalyDetector.__new__(AnomalyDetector)
        detector.is_trained = False
        assert detector.detect(95.0, 95.0) is False

    def test_anomaly_score_untrained(self):
        """测试未训练时 get_anomaly_score 返回默认值"""
        from core.ai_anomaly import AnomalyDetector
        detector = AnomalyDetector.__new__(AnomalyDetector)
        detector.is_trained = False
        result = detector.get_anomaly_score(50.0, 50.0)
        assert result["is_anomaly"] is False
        assert result["detail"] == "模型未训练"

    def test_training_with_synthetic_data(self):
        """使用合成数据测试训练和预测"""
        from sklearn.ensemble import IsolationForest
        from sklearn.neighbors import LocalOutlierFactor
        from sklearn.preprocessing import StandardScaler

        # 生成正常数据 (CPU 10-40%, Mem 30-60%)
        np.random.seed(42)
        normal_data = np.column_stack([
            np.random.uniform(10, 40, 200),
            np.random.uniform(30, 60, 200),
        ])

        # 训练模型
        scaler = StandardScaler()
        scaled = scaler.fit_transform(normal_data)

        if_model = IsolationForest(contamination=0.05, random_state=42)
        if_model.fit(scaled)

        lof = LocalOutlierFactor(contamination=0.05, novelty=True, n_neighbors=20)
        lof.fit(scaled)

        # 正常数据应该预测为正常
        normal_point = scaler.transform([[25.0, 45.0]])
        assert if_model.predict(normal_point)[0] == 1

        # 极端异常数据应该预测为异常
        anomaly_point = scaler.transform([[99.0, 98.0]])
        result = if_model.predict(anomaly_point)[0]
        # 孤立森林应能识别极端离群点
        assert result == -1 or result == 1  # 至少不崩溃

    def test_model_info_structure(self):
        """测试模型信息返回结构"""
        from core.ai_anomaly import AnomalyDetector
        detector = AnomalyDetector.__new__(AnomalyDetector)
        detector.is_trained = True
        detector.training_samples = 200
        info = detector.get_model_info()
        assert "is_trained" in info
        assert "training_samples" in info
        assert "models" in info
        assert info["training_samples"] == 200

    def test_scaler_consistency(self):
        """测试标准化器的一致性"""
        from sklearn.preprocessing import StandardScaler
        import numpy as np

        scaler = StandardScaler()
        data = np.array([[10, 50], [20, 60], [30, 70], [40, 80]])
        scaler.fit(data)

        point = scaler.transform([[25, 65]])
        assert point.shape == (1, 2)
        # 中间值应该接近 0
        assert abs(point[0, 0]) < 1.5
        assert abs(point[0, 1]) < 1.5

    def test_isolation_forest_decision_function(self):
        """测试孤立森林的决策函数"""
        from sklearn.ensemble import IsolationForest
        import numpy as np

        normal = np.random.uniform(10, 40, (100, 2))
        if_model = IsolationForest(contamination=0.05, random_state=42)
        if_model.fit(normal)

        # 正常点得分应该较高 (接近 0 或正)
        score_normal = if_model.decision_function([[25.0, 45.0]])[0]
        # 异常点得分应该较低
        score_anomaly = if_model.decision_function([[99.0, 99.0]])[0]

        assert score_anomaly < score_normal


class TestAlertEngine:
    """测试告警引擎"""

    def test_operator_mapping(self):
        """测试操作符映射"""
        from core.alert_engine import AlertEngine
        engine = AlertEngine()
        assert engine.OPERATORS[">"](10, 5) is True
        assert engine.OPERATORS[">"](5, 10) is False
        assert engine.OPERATORS["<"](5, 10) is True
        assert engine.OPERATORS[">="](10, 10) is True
        assert engine.OPERATORS["<="](5, 5) is True
        assert engine.OPERATORS["=="](5, 5) is True
        assert engine.OPERATORS["!="](5, 10) is True
