"""
认证模块单元测试
测试密码哈希、JWT Token 生成与验证
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import time


class TestPasswordHashing:
    """测试密码加密与校验"""

    def test_hash_and_verify(self):
        """测试哈希后可以验证"""
        from core.auth import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        """测试错误密码验证失败"""
        from core.auth import get_password_hash, verify_password

        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_unique(self):
        """测试每次哈希结果不同（盐不同）"""
        from core.auth import get_password_hash

        h1 = get_password_hash("same_password")
        h2 = get_password_hash("same_password")
        assert h1 != h2

    def test_empty_password(self):
        """测试空密码处理"""
        from core.auth import get_password_hash, verify_password

        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("x", hashed) is False

    def test_special_characters(self):
        """测试特殊字符密码"""
        from core.auth import get_password_hash, verify_password

        special = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~中文密码"
        hashed = get_password_hash(special)
        assert verify_password(special, hashed) is True


class TestJWTToken:
    """测试 JWT Token"""

    def test_create_token_returns_string(self):
        """测试 Token 创建返回字符串"""
        from core.auth import create_access_token

        token = create_access_token({"sub": "admin", "role": "admin"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_claims(self):
        """测试 Token 包含自定义字段"""
        from core.auth import create_access_token
        from jose import jwt
        from core.config import settings

        token = create_access_token({"sub": "test_user", "role": "viewer"})
        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert decoded["sub"] == "test_user"
        assert decoded["role"] == "viewer"
        assert "exp" in decoded

    def test_token_expiration_set(self):
        """测试 Token 有过期时间"""
        from core.auth import create_access_token
        from jose import jwt
        from core.config import settings
        from datetime import datetime, timedelta

        token = create_access_token({"sub": "user"})
        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        expire_time = datetime.utcfromtimestamp(decoded["exp"])
        expected = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        # 允许 5 秒误差
        diff = abs((expire_time - expected).total_seconds())
        assert diff < 5

    def test_expired_token_rejected(self):
        """测试过期 Token 被拒绝"""
        from core.auth import create_access_token
        from core.config import settings
        from jose import jwt, JWTError
        from datetime import datetime, timedelta

        # 手动创建一个已过期的 Token
        expire = datetime.utcnow() - timedelta(minutes=10)
        to_encode = {"sub": "test", "exp": expire}
        expired_token = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        try:
            jwt.decode(
                expired_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            # 如果没有抛出异常，测试失败
            assert False, "过期 Token 应该被拒绝"
        except JWTError:
            assert True

    def test_invalid_signature_rejected(self):
        """测试错误签名被拒绝"""
        from core.auth import create_access_token
        from jose import jwt, JWTError

        token = create_access_token({"sub": "test"})
        try:
            jwt.decode(token, "wrong_secret_key", algorithms=["HS256"])
            assert False, "错误签名的 Token 应该被拒绝"
        except JWTError:
            assert True
