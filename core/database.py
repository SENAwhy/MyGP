# core/database.py
import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ：把 root:123456 换成你真实的 MySQL 账号和密码！
# 格式：mysql+pymysql://账号:密码@IP:端口/数据库名
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:why20030319@127.0.0.1:3306/aiops_monitor"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 定义数据表模型 (Schema)
class SystemLog(Base):
    __tablename__ = "system_logs"  # 表名
    
    id = Column(Integer, primary_key=True, index=True)
    log_time = Column(DateTime, default=datetime.datetime.now) # 自动生成当前时间
    hostname = Column(String(50))
    cpu_usage = Column(Float)
    mem_usage = Column(Float)
    net_upload = Column(Float)
    net_download = Column(Float)
    disk_percent = Column(Float)

# 自动在 MySQL 中创建这张表（如果不存在的话）
Base.metadata.create_all(bind=engine)

def save_to_mysql(data):
    """把字典数据存入数据库"""
    db = SessionLocal()
    try:
        log_entry = SystemLog(
            hostname=data.get('hostname', 'Unknown'),
            cpu_usage=data.get('cpu_usage', 0.0),
            mem_usage=data.get('memory_usage', 0.0),
            net_upload=data.get('net_upload', 0.0),
            net_download=data.get('net_download', 0.0),
            disk_percent=data.get('disk_percent', 0.0)
        )
        db.add(log_entry)
        db.commit() # 提交事务
    except Exception as e:
        db.rollback() # 发生错误就回滚
        print(f" 数据库写入失败: {e}")
    finally:
        db.close()