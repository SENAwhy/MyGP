import operator
from datetime import datetime
from core.database import SessionLocal, AlertRule, AlertHistory
from core.logger import app_logger


class AlertEngine:
    """告警规则引擎 —— 评估监控数据并触发告警"""

    OPERATORS = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self):
        self._rules_cache = []
        self._cache_time = None
        self._cache_ttl = 30

    def _load_rules(self):
        now = datetime.now()
        if (
            self._cache_time
            and (now - self._cache_time).seconds < self._cache_ttl
        ):
            return self._rules_cache

        db = SessionLocal()
        try:
            self._rules_cache = (
                db.query(AlertRule)
                .filter(AlertRule.enabled == 1)
                .all()
            )
            self._cache_time = now
        except Exception as e:
            app_logger.error(f"加载告警规则失败: {e}")
        finally:
            db.close()
        return self._rules_cache

    def evaluate(self, metrics: dict) -> list[dict]:
        """
        评估所有规则，返回触发的告警列表。
        metrics: {"cpu_usage": 85.0, "memory_usage": 72.0, ...}
        """
        rules = self._load_rules()
        triggered = []

        for rule in rules:
            op_func = self.OPERATORS.get(rule.operator)
            if op_func is None:
                continue

            current_value = metrics.get(rule.metric)
            if current_value is None:
                continue

            if op_func(current_value, rule.threshold):
                alert = {
                    "rule_name": rule.name,
                    "metric": rule.metric,
                    "current_value": current_value,
                    "threshold": rule.threshold,
                    "message": (
                        f"[{rule.name}] {rule.metric} 当前值 {current_value} "
                        f"{rule.operator} 阈值 {rule.threshold}"
                    ),
                }
                triggered.append(alert)
                self._record_alert(alert)

        if triggered:
            app_logger.warning(
                f"触发 {len(triggered)} 条告警规则: "
                + ", ".join(a["rule_name"] for a in triggered)
            )

        return triggered

    def _record_alert(self, alert: dict):
        db = SessionLocal()
        try:
            record = AlertHistory(
                rule_name=alert["rule_name"],
                metric=alert["metric"],
                current_value=alert["current_value"],
                threshold=alert["threshold"],
                message=alert["message"],
            )
            db.add(record)
            db.commit()
        except Exception as e:
            db.rollback()
            app_logger.error(f"记录告警历史失败: {e}")
        finally:
            db.close()

    def get_alert_history(self, limit: int = 50, offset: int = 0):
        db = SessionLocal()
        try:
            total = db.query(AlertHistory).count()
            records = (
                db.query(AlertHistory)
                .order_by(AlertHistory.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            result = []
            for r in records:
                result.append(
                    {
                        "id": r.id,
                        "rule_name": r.rule_name,
                        "metric": r.metric,
                        "current_value": r.current_value,
                        "threshold": r.threshold,
                        "message": r.message,
                        "is_ai_anomaly": bool(r.is_ai_anomaly),
                        "created_at": (
                            r.created_at.strftime("%Y-%m-%d %H:%M:%S")
                            if r.created_at
                            else ""
                        ),
                    }
                )
            return {"total": total, "items": result}
        except Exception as e:
            app_logger.error(f"查询告警历史失败: {e}")
            return {"total": 0, "items": []}
        finally:
            db.close()

    def get_rules(self):
        db = SessionLocal()
        try:
            rules = db.query(AlertRule).all()
            result = []
            for r in rules:
                result.append(
                    {
                        "id": r.id,
                        "name": r.name,
                        "description": r.description,
                        "metric": r.metric,
                        "operator": r.operator,
                        "threshold": r.threshold,
                        "enabled": bool(r.enabled),
                        "created_at": (
                            r.created_at.strftime("%Y-%m-%d %H:%M:%S")
                            if r.created_at
                            else ""
                        ),
                    }
                )
            return result
        except Exception as e:
            app_logger.error(f"查询规则列表失败: {e}")
            return []
        finally:
            db.close()

    def toggle_rule(self, rule_id: int, enabled: bool) -> bool:
        db = SessionLocal()
        try:
            rule = (
                db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            )
            if rule:
                rule.enabled = 1 if enabled else 0
                db.commit()
                self._cache_time = None
                return True
            return False
        except Exception as e:
            db.rollback()
            app_logger.error(f"切换规则状态失败: {e}")
            return False
        finally:
            db.close()


alert_engine = AlertEngine()
