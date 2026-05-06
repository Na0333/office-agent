"""MCP tools for cross-platform office notice channels."""

from __future__ import annotations

from app.services.notice_service import NoticeService


def list_notice_channels() -> dict:
    """List configured webhook channels."""
    return NoticeService().list_channels()


async def send_platform_notice(channel_ids: list[str] | str, content: str, title: str = "办公通知") -> dict:
    """Send a prepared notice to explicit webhook channel IDs."""
    return await NoticeService().send_platform_notice(channel_ids=channel_ids, content=content, title=title)
