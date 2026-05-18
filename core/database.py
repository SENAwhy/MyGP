import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

engine = create_engine(settings.DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SystemLog(Base):
    """系统监控日志表"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_time = Column(DateTime, default=datetime.datetime.now)
    hostname = Column(String(50))
    cpu_usage = Column(Float)
    mem_usage = Column(Float)
    net_upload = Column(Float)
    net_download = Column(Float)
    disk_percent = Column(Float)


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(20), default="viewer")


class AlertRule(Base):
    """告警规则表"""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(String(255), default="", comment="规则描述")
    metric = Column(String(50), nullable=False, comment="监控指标")
    operator = Column(String(10), nullable=False, default=">", comment="比较运算符")
    threshold = Column(Float, nullable=False, comment="阈值")
    enabled = Column(Integer, default=1, comment="是否启用: 1启用 0禁用")
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )


class AlertHistory(Base):
    """告警历史表"""
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), comment="触发规则名称")
    hostname = Column(String(50), default="", comment="节点名称")
    metric = Column(String(50), comment="触发指标")
    current_value = Column(Float, comment="当前值")
    threshold = Column(Float, comment="阈值")
    message = Column(String(500), comment="告警消息")
    is_ai_anomaly = Column(Integer, default=0, comment="是否AI判定异常")
    created_at = Column(DateTime, default=datetime.datetime.now)


class SystemInfo(Base):
    """系统静态信息表"""
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(50), unique=True, index=True)
    os_name = Column(String(100))
    cpu_model = Column(String(200))
    cpu_cores_logical = Column(Integer)
    cpu_cores_physical = Column(Integer)
    total_ram_gb = Column(Float)
    total_disk_gb = Column(Float)
    local_ip = Column(String(50))
    last_updated = Column(DateTime, default=datetime.datetime.now)


Base.metadata.create_all(bind=engine)


def save_to_mysql(data):
    """把字典数据存入数据库"""
    db = SessionLocal()
    try:
        log_entry = SystemLog(
            hostname=data.get("hostname", "Unknown"),
            cpu_usage=data.get("cpu_usage", 0.0),
            mem_usage=data.get("memory_usage", 0.0),
            net_upload=data.get("net_upload", 0.0),
            net_download=data.get("net_download", 0.0),
            disk_percent=data.get("disk_percent", 0.0),
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f" 数据库写入失败: {e}")
    finally:
        db.close()


def init_default_rules():
    """初始化默认告警规则"""
    db = SessionLocal()
    try:
        existing = db.query(AlertRule).count()
        if existing == 0:
            defaults = [
                AlertRule(
                    name="CPU高负载告警",
                    description="CPU使用率超过阈值时触发",
                    metric="cpu_usage",
                    operator=">",
                    threshold=80.0,
                ),
                AlertRule(
                    name="内存高负载告警",
                    description="内存使用率超过阈值时触发",
                    metric="memory_usage",
                    operator=">",
                    threshold=90.0,
                ),
                AlertRule(
                    name="磁盘空间告警",
                    description="磁盘使用率超过阈值时触发",
                    metric="disk_percent",
                    operator=">",
                    threshold=90.0,
                ),
                AlertRule(
                    name="网络上传异常",
                    description="网络上传速度异常升高时触发",
                    metric="net_upload",
                    operator=">",
                    threshold=10.0,
                ),
            ]
            db.add_all(defaults)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"初始化默认规则失败: {e}")
    finally:
        db.close()
