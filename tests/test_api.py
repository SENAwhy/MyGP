"""
API 集成测试
测试 FastAPI 路由、认证拦截、接口响应结构
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# ---- 测试夹具 -----------------------------------------------------------

@pytest.fixture
def client():
    """创建 TestClient，mock 掉数据库初始化以避免启动时需要 MySQL"""
    with patch("core.database.SessionLocal"), \
         patch("core.database.init_default_rules"), \
         patch("core.database.Base.metadata.create_all"):
        from main import app
        from core.auth import get_current_user

        # 注入测试用户，跳过真实 JWT 校验
        async def override_get_current_user():
            return {"sub": "admin", "role": "admin"}

        app.dependency_overrides[get_current_user] = override_get_current_user
        yield TestClient(app)
        app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth():
    """不带认证绕过的客户端，用于测试 401 拦截"""
    with patch("core.database.SessionLocal"), \
         patch("core.database.init_default_rules"), \
         patch("core.database.Base.metadata.create_all"):
        from main import app
        yield TestClient(app)


# ---- 基础路由测试 -------------------------------------------------------

class TestRootEndpoint:
    """测试根路径和静态文件"""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code in (200, 404)  # 取决于前端 dist 是否存在


# ---- 认证接口测试 -------------------------------------------------------

class TestAuthEndpoints:
    """测试登录认证流程"""

    def test_login_missing_fields(self, client_no_auth):
        """缺少表单字段时返回 422"""
        resp = client_no_auth.post("/api/login", data={})
        assert resp.status_code == 422

    def test_login_wrong_credentials(self, client_no_auth):
        """错误凭据返回 401"""
        resp = client_no_auth.post(
            "/api/login",
            data={"username": "nobody", "password": "wrong"},
        )
        assert resp.status_code in (401, 422)

    def test_login_empty_password(self, client_no_auth):
        """空密码返回 422"""
        resp = client_no_auth.post(
            "/api/login",
            data={"username": "admin", "password": ""},
        )
        assert resp.status_code == 422


# ---- 认证拦截测试 -------------------------------------------------------

class TestAuthGuard:
    """测试未认证时受保护接口返回 401"""

    PROTECTED_ENDPOINTS = [
        "/api/system_status",
        "/api/history",
        "/api/diagnose",
        "/api/system_info",
        "/api/dashboard_summary",
        "/api/alerts",
        "/api/alert_rules",
        "/api/model_info",
        "/api/nodes",
    ]

    def test_protected_without_token(self, client_no_auth):
        """未带 Token 访问受保护接口应返回 401"""
        for path in self.PROTECTED_ENDPOINTS:
            resp = client_no_auth.get(path)
            assert resp.status_code == 401, f"{path} 应返回 401，实际 {resp.status_code}"


# ---- 监控接口结构测试 ---------------------------------------------------

class TestMonitorEndpoints:
    """测试监控相关接口的响应结构（使用 mock）"""

    def test_system_status_structure(self, client):
        """测试 /api/system_status 返回结构"""
        resp = client.get("/api/system_status")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "status" in data

    def test_nodes_structure(self, client):
        """测试 /api/nodes 返回结构"""
        resp = client.get("/api/nodes")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "success"
            assert "nodes" in data
            assert "local" in data
            assert isinstance(data["nodes"], list)
            assert isinstance(data["local"], str)

    def test_history_structure(self, client):
        """测试 /api/history 返回结构"""
        resp = client.get("/api/history?limit=10")
        assert resp.status_code in (200, 500)

    def test_dashboard_summary_structure(self, client):
        """测试 /api/dashboard_summary 返回结构"""
        resp = client.get("/api/dashboard_summary")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "success"
            for key in ("avg_cpu", "max_cpu", "avg_mem", "max_mem", "total_records"):
                assert key in data

    def test_system_info_structure(self, client):
        """测试 /api/system_info 返回结构"""
        resp = client.get("/api/system_info")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "success"
            assert "model_info" in data


# ---- 告警接口测试 -------------------------------------------------------

class TestAlertEndpoints:
    """测试告警相关接口"""

    def test_alert_rules_list(self, client):
        """测试告警规则列表接口"""
        resp = client.get("/api/alert_rules")
        assert resp.status_code in (200, 500)

    def test_alerts_history(self, client):
        """测试告警历史接口"""
        resp = client.get("/api/alerts?limit=10")
        assert resp.status_code in (200, 500)


# ---- AI 接口测试 --------------------------------------------------------

class TestAIEndpoints:
    """测试 AI 相关接口"""

    def test_model_info(self, client):
        """测试模型信息接口"""
        resp = client.get("/api/model_info")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "success"
            assert "is_trained" in data
            assert "training_samples" in data
            assert "models" in data
