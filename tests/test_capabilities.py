from fastapi.testclient import TestClient

from app.main import app


def test_capabilities_endpoint_exposes_http_and_mcp_entries():
    client = TestClient(app)
    response = client.get("/capabilities")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "office-agent"
    assert "agent_api" in data["entrypoints"]
    assert "mcp_stdio" in data["entrypoints"]
    assert "mcp_streamable_http" in data["entrypoints"]
    assert any(tool["name"] == "extract_todos_tool" for tool in data["tools"])
    assert any(tool["name"] == "send_email_tool" and tool["sensitive"] for tool in data["tools"])
    assert not any(tool["name"] == "office_agent_chat_tool" for tool in data["tools"])
