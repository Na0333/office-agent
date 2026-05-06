"""Tests for the direct MCP tool layer."""

import pytest

from app.mcp_client.client import MCPToolClient
from app.mcp_server.tools.text_tools import extract_email_addresses


def test_email_address_extraction():
    assert sorted(extract_email_addresses("发送到 alice@company.com 和 bob@example.com")) == [
        "alice@company.com",
        "bob@example.com",
    ]


@pytest.mark.asyncio
async def test_send_email_requires_confirmation():
    client = MCPToolClient()
    result = await client.call(
        "send_email",
        {
            "to_addresses": "test@example.com",
            "subject": "Test",
            "body": "Hello",
            "attachments": [{"file_path": "data/files/report.pdf"}],
            "html": True,
        },
    )

    assert result.success is False
    assert result.data["need_confirmation"] is True
    assert result.data["preview"]["to_addresses"] == "test@example.com"
    assert "attachments" not in result.data["preview"]
    assert "html" not in result.data["preview"]


@pytest.mark.asyncio
async def test_send_platform_notice_requires_confirmation():
    client = MCPToolClient()
    result = await client.call(
        "send_platform_notice",
        {
            "channel_ids": ["dev_group"],
            "title": "测试",
            "content": "你好",
        },
    )

    assert result.success is False
    assert result.data["need_confirmation"] is True
    assert result.data["preview"]["channel_ids"] == ["dev_group"]


@pytest.mark.asyncio
async def test_create_tasks_requires_confirmation():
    client = MCPToolClient()
    result = await client.call(
        "create_tasks",
        {
            "todos": [{"title": "写测试"}],
            "source_user_id": "u1",
        },
    )

    assert result.success is False
    assert result.data["need_confirmation"] is True
    assert result.data["preview"]["todos"][0]["title"] == "写测试"
