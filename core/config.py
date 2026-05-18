import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 数据库
    DB_URL: str = os.getenv(
        "DB_URL",
        "mysql+pymysql://root:your possword@127.0.0.1:3306/aiops_monitor",
    )

    # JWT 认证
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "AIOps_Max_Super_Secret_Key_2026"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    # SMTP 邮件
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")
    SENDER_PASS: str = os.getenv("SENDER_PASS", "")
    RECEIVER_EMAIL: str = os.getenv("RECEIVER_EMAIL", "")

    # DeepSeek 大模型
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv(
        "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
    )

    # 告警
    ALERT_COOLDOWN_SECONDS: int = int(
        os.getenv("ALERT_COOLDOWN_SECONDS", "600")
    )

    # 监控
    MONITOR_LOG_FILE: str = os.getenv(
        "MONITOR_LOG_FILE", "monitor_log.csv"
    )
    HISTORY_LIMIT: int = int(os.getenv("HISTORY_LIMIT", "100"))


settings = Settings()
