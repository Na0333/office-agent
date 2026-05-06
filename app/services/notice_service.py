"""Cross-platform office notice delivery through group robot webhooks."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Any
from urllib.parse import quote_plus

import httpx

from app.config import get_settings


class NoticeService:
    """Send notices to configured DingTalk, WeCom and Feishu webhook channels."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def list_channels(self) -> dict[str, Any]:
        channels = []
        for channel_id, config in self.settings.configured_notice_channels.items():
            channels.append(
                {
                    "channel_id": channel_id,
                    "name": config.get("name") or channel_id,
                    "platform": self._normalize_platform(config.get("platform", "")),
                    "enabled": bool(config.get("webhook_url")),
                }
            )
        return {"channels": channels, "count": len(channels)}

    async def send_platform_notice(
        self,
        channel_ids: list[str] | str,
        content: str,
        title: str = "办公通知",
    ) -> dict[str, Any]:
        if isinstance(channel_ids, str):
            channel_ids = [item.strip() for item in channel_ids.split(",") if item.strip()]

        if not channel_ids:
            return {
                "success": False,
                "sent_count": 0,
                "failed_count": 1,
                "results": [],
                "error": "未指定通知通道，请使用 channel_id 或在指令中说明钉钉/企业微信/飞书目标群。",
            }

        results = []
        for channel_id in channel_ids:
            results.append(await self._send_one(channel_id=channel_id, title=title, content=content))

        sent_count = sum(1 for item in results if item.get("success"))
        failed_count = len(results) - sent_count
        return {
            "success": failed_count == 0,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "results": results,
            "error": None if failed_count == 0 else results[-1].get("error"),
        }

    async def _send_one(self, channel_id: str, title: str, content: str) -> dict[str, Any]:
        config = self.settings.configured_notice_channels.get(channel_id)
        if not config:
            return {
                "success": False,
                "channel_id": channel_id,
                "platform": "unknown",
                "message": "channel_not_configured",
                "error": f"未配置通知通道：{channel_id}",
            }

        platform = self._normalize_platform(config.get("platform", ""))
        webhook_url = config.get("webhook_url", "")
        if not webhook_url:
            return {
                "success": False,
                "channel_id": channel_id,
                "platform": platform,
                "message": "missing_webhook_url",
                "error": f"通知通道 {channel_id} 缺少 webhook_url",
            }

        payload = self._build_payload(platform=platform, title=title, content=content)
        url = self._signed_dingtalk_url(webhook_url, config.get("secret")) if platform == "dingtalk" else webhook_url
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
            response_body = self._parse_response_body(response)
            success = 200 <= response.status_code < 300 and self._webhook_body_success(platform, response_body)
            return {
                "success": success,
                "channel_id": channel_id,
                "name": config.get("name") or channel_id,
                "platform": platform,
                "status_code": response.status_code,
                "response": response_body,
                "message": "sent" if success else "send_failed",
                "error": None if success else self._response_error_text(response_body),
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "channel_id": channel_id,
                "name": config.get("name") or channel_id,
                "platform": platform,
                "message": "send_exception",
                "error": str(exc),
            }

    def _build_payload(self, platform: str, title: str, content: str) -> dict[str, Any]:
        text = f"【{title}】\n{content.strip()}" if title else content.strip()
        if platform == "feishu":
            return {"msg_type": "text", "content": {"text": text}}
        if platform == "wecom":
            return {"msgtype": "text", "text": {"content": text}}
        return {"msgtype": "text", "text": {"content": text}}

    def _signed_dingtalk_url(self, webhook_url: str, secret: str | None) -> str:
        if not secret:
            return webhook_url
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
        secret_enc = secret.encode("utf-8")
        sign = quote_plus(base64.b64encode(hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()))
        separator = "&" if "?" in webhook_url else "?"
        return f"{webhook_url}{separator}timestamp={timestamp}&sign={sign}"

    def _parse_response_body(self, response: httpx.Response) -> dict[str, Any] | str:
        try:
            parsed = response.json()
            return parsed if isinstance(parsed, dict) else str(parsed)
        except ValueError:
            return response.text.strip()

    def _webhook_body_success(self, platform: str, body: dict[str, Any] | str) -> bool:
        if body == "":
            return True
        if isinstance(body, dict):
            if platform in {"dingtalk", "wecom"}:
                return body.get("errcode") == 0
            if platform == "feishu":
                return body.get("code") == 0 or body.get("StatusCode") == 0
            return True

        normalized = body.lower()
        if platform in {"dingtalk", "wecom"}:
            return '"errcode":0' in normalized or '"errcode": 0' in normalized or body.strip() == ""
        if platform == "feishu":
            return '"code":0' in normalized or '"code": 0' in normalized or body.strip() == ""
        return True

    def _response_error_text(self, body: dict[str, Any] | str) -> str:
        if isinstance(body, dict):
            return str(
                body.get("errmsg")
                or body.get("msg")
                or body.get("message")
                or body.get("Message")
                or body
            )[:500]
        return body[:500]

    def _normalize_platform(self, platform: str) -> str:
        value = platform.lower().strip()
        mapping = {
            "dingding": "dingtalk",
            "钉钉": "dingtalk",
            "wechat": "wecom",
            "wechat_work": "wecom",
            "企业微信": "wecom",
            "微信": "wecom",
            "lark": "feishu",
            "飞书": "feishu",
        }
        return mapping.get(value, value or "unknown")
