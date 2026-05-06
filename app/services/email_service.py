"""Email sending service using SMTP.

This service provides email sending functionality independent of AstrBot.
It supports configurable SMTP servers with TLS/STARTTLS support.
"""

import smtplib
import logging
import os
import asyncio
import json
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
from typing import Any

from app.config import get_settings


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_email(
        self,
        to_addresses: str | list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send a plain text email.

        Args:
            to_addresses: Recipient email address(es).
            subject: Email subject.
            body: Plain text email body content.
            cc: CC recipients.
            bcc: BCC recipients.

        Returns:
            Dict with keys: success (bool), message (str), message_id (str or None), error (str or None)
        """
        # Check if SMTP is configured
        if not self.settings.is_email_configured:
            return {
                "success": False,
                "message": "SMTP not configured",
                "message_id": None,
                "error": "Missing SMTP_HOST, SMTP_USERNAME, or SMTP_PASSWORD in environment variables.",
            }

        # Normalize recipient addresses
        to_addresses = self._normalize_recipients(to_addresses)
        cc = self._normalize_recipients(cc or [])
        bcc = self._normalize_recipients(bcc or [])

        try:
            # Create message
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.settings.smtp_username
            msg["To"] = ", ".join(to_addresses)
            msg["Message-ID"] = make_msgid(domain=self._message_id_domain())
            msg["Date"] = formatdate(localtime=True)
            if cc:
                msg["CC"] = ", ".join(cc)

            msg.set_content(body, subtype="plain", charset="utf-8")

            # Combine all recipients for SMTP
            all_recipients = to_addresses + cc + bcc

            # Connect and send
            message_id = await self._send_via_smtp(msg, all_recipients)

            logger.info(f"Email sent successfully to {to_addresses}")
            return {
                "success": True,
                "message": f"Email sent to {', '.join(to_addresses)}",
                "message_id": message_id,
                "error": None,
            }

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": "Failed to send email",
                "message_id": None,
                "error": error_msg,
            }

    async def _send_via_smtp(self, msg: EmailMessage, recipients: list[str]) -> str:
        """Connect to SMTP server and send message.

        Args:
            msg: Email message object.
            recipients: List of recipient addresses.

        Returns:
            Message ID from SMTP server.
        """
        if self._is_test_runtime() and not os.getenv("OFFICE_AGENT_ALLOW_TEST_EMAIL_SEND"):
            return msg.get("Message-ID", "test-dry-run")

        return await asyncio.to_thread(self._send_via_smtp_sync, msg, recipients)

    def _send_via_smtp_sync(self, msg: EmailMessage, recipients: list[str]) -> str:
        server = self._connect_smtp()

        try:
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg, from_addr=self.settings.smtp_username, to_addrs=recipients)
            return msg.get("Message-ID", "unknown")
        finally:
            server.quit()

    def _connect_smtp(self) -> smtplib.SMTP | smtplib.SMTP_SSL:
        if self.settings.smtp_use_starttls:
            server = smtplib.SMTP(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=self.settings.smtp_timeout,
            )
            server.ehlo()
            server.starttls()
            server.ehlo()
            return server

        if self.settings.smtp_use_tls:
            return smtplib.SMTP_SSL(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=self.settings.smtp_timeout,
            )

        return smtplib.SMTP(
            self.settings.smtp_host,
            self.settings.smtp_port,
            timeout=self.settings.smtp_timeout,
        )

    def _normalize_recipients(self, recipients: str | list[str]) -> list[str]:
        """Normalize recipient input into a clean list of addresses."""
        if isinstance(recipients, str):
            value = recipients.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, str):
                        return [parsed.strip()]
                    if isinstance(parsed, list):
                        return [addr.strip() for addr in parsed if isinstance(addr, str) and addr.strip()]
                except json.JSONDecodeError:
                    pass
            return [addr.strip() for addr in value.split(",") if addr.strip()]

        return [addr.strip() for addr in recipients if isinstance(addr, str) and addr.strip()]

    async def validate_smtp_config(self) -> dict[str, Any]:
        """Validate SMTP configuration by attempting a test connection.

        Returns:
            Dict with keys: valid (bool), message (str), error (str or None)
        """
        if not self.settings.is_email_configured:
            return {
                "valid": False,
                "message": "SMTP configuration incomplete",
                "error": "Missing SMTP_HOST, SMTP_USERNAME, or SMTP_PASSWORD",
            }

        if self._is_test_runtime() and not os.getenv("OFFICE_AGENT_ALLOW_TEST_EMAIL_SEND"):
            return {
                "valid": True,
                "message": "SMTP configuration accepted in test dry-run mode",
                "error": None,
            }

        try:
            # Try to connect and login
            server = self._connect_smtp()

            try:
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                return {
                    "valid": True,
                    "message": f"SMTP connection successful: {self.settings.smtp_host}:{self.settings.smtp_port}",
                    "error": None,
                }
            except smtplib.SMTPAuthenticationError:
                return {
                    "valid": False,
                    "message": "SMTP authentication failed",
                    "error": "Invalid username or password",
                }
            finally:
                server.quit()

        except Exception as e:
            return {
                "valid": False,
                "message": "SMTP connection failed",
                "error": str(e),
            }

    def _is_test_runtime(self) -> bool:
        return self.settings.app_env == "test" or "PYTEST_CURRENT_TEST" in os.environ

    def _message_id_domain(self) -> str:
        if self.settings.smtp_username and "@" in self.settings.smtp_username:
            return self.settings.smtp_username.rsplit("@", 1)[1]
        return "office-agent.local"
