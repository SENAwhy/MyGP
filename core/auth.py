# core/auth.py
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# 专属密钥
SECRET_KEY = "AIOps_Max_Super_Secret_Key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # 登录状态保持 60 分钟

# 密码加密器
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """校验密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """把明文密码变成乱码（哈希）"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """制作通行证（JWT Token）"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt