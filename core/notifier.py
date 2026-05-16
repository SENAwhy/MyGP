import smtplib
from email.mime.text import MIMEText
from email.header import Header
from core.config import settings
from core.logger import app_logger


def send_alert_email(subject: str, content: str) -> bool:
    """发送报警邮件，返回是否成功"""
    if not settings.SENDER_EMAIL or not settings.SENDER_PASS:
        app_logger.warning("邮件配置不完整，跳过发送")
        return False

    message = MIMEText(content, "plain", "utf-8")
    message["From"] = settings.SENDER_EMAIL
    message["To"] = settings.RECEIVER_EMAIL
    message["Subject"] = Header(subject, "utf-8")

    try:
        server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.login(settings.SENDER_EMAIL, settings.SENDER_PASS)
        server.sendmail(
            settings.SENDER_EMAIL,
            [settings.RECEIVER_EMAIL],
            message.as_string(),
        )
        server.quit()
        app_logger.info("报警邮件已成功发送")
        return True
    except Exception as e:
        app_logger.error(f"邮件发送失败: {e}")
        return False
