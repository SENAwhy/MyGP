import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 数据库 — 默认值留空，强制从环境变量或 .env 读取
    DB_URL: str = os.getenv(
        "DB_URL",
        "",
    )

    # JWT 认证 — 生产环境务必通过环境变量覆盖
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", ""
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

# 启动时校验关键配置
if not settings.SECRET_KEY:
    import warnings
    warnings.warn(
        "SECRET_KEY 未配置！请通过环境变量或 .env 文件设置一个安全的密钥。",
        RuntimeWarning,
    )
if not settings.DB_URL:
    import warnings
    warnings.warn(
        "DB_URL 未配置！请通过环境变量或 .env 文件设置数据库连接。",
        RuntimeWarning,
    )
