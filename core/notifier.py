import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 邮件配置（Gmail） ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "dalembert03@gmail.com"  # 填写发件人
SENDER_PASS = "wxat qsuu udke oktn"         # 注意：这不是登录密码，是 Gmail 的「应用程序密码」
RECEIVER_EMAIL = "wlzj_03@foxmail.com" # 填写你的收件箱

def send_alert_email(subject, content):
    """
    发送报警邮件的函数
    """
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = SENDER_EMAIL
    message['To'] = RECEIVER_EMAIL
    message['Subject'] = Header(subject, 'utf-8')

    try:
        # 使用 SSL 加密连接
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], message.as_string())
        server.quit()
        print("报警邮件已成功发送！")
    except Exception as e:
        print(f"邮件发送失败: {e}")