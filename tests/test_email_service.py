"""Test email sending functionality."""

import asyncio
from dataclasses import replace

import pytest

from app.services.email_service import EmailService
from app.config import get_settings


@pytest.mark.asyncio
async def test_email_service_instantiation():
    """Test that EmailService can be instantiated."""
    service = EmailService()
    assert service is not None
    assert service.settings is not None


@pytest.mark.asyncio
async def test_email_config_validation():
    """Test SMTP configuration validation."""
    service = EmailService()
    result = await service.validate_smtp_config()

    # Check result structure
    assert isinstance(result, dict)
    assert "valid" in result
    assert "message" in result
    assert "error" in result

    # Without configured SMTP, should fail
    if not service.settings.is_email_configured:
        assert result["valid"] is False


@pytest.mark.asyncio
async def test_send_email_unconfigured():
    """Test sending email without SMTP configuration returns proper error."""
    service = EmailService()

    # Attempt to send email
    result = await service.send_email(
        to_addresses="test@example.com",
        subject="Test",
        body="Test email",
    )

    assert isinstance(result, dict)
    assert "success" in result
    assert "message" in result
    assert "error" in result

    # If not configured, should fail
    if not service.settings.is_email_configured:
        assert result["success"] is False
        assert "SMTP not configured" in result["message"]


@pytest.mark.asyncio
async def test_send_email_is_plain_text_only():
    service = EmailService()
    service.settings = replace(
        service.settings,
        smtp_host="smtp.example.com",
        smtp_username="sender@example.com",
        smtp_password="secret",
    )
    sent = {}

    async def fake_send(msg, recipients):
        sent["msg"] = msg
        sent["recipients"] = recipients
        return msg["Message-ID"]

    service._send_via_smtp = fake_send

    result = await service.send_email(
        to_addresses="receiver@example.com",
        subject="Linux运维简历",
        body="<p>这是纯文本邮件内容。</p>",
    )

    assert result["success"] is True
    assert "attachment_count" not in result
    assert sent["recipients"] == ["receiver@example.com"]

    msg = sent["msg"]
    assert msg.get_content_type() == "text/plain"
    assert not list(msg.iter_attachments())
    assert msg.get_content().strip() == "<p>这是纯文本邮件内容。</p>"


async def manual_test_send_email():
    """Manual test for sending email with SMTP configured.

    Run with: python -m pytest tests/test_email_service.py::manual_test_send_email -s
    """
    settings = get_settings()

    if not settings.is_email_configured:
        print("SMTP not configured. Skipping manual test.")
        print("To test, set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD in .env file")
        return

    service = EmailService()

    # Validate connection first
    validation = await service.validate_smtp_config()
    print(f"SMTP Validation: {validation}")

    if not validation["valid"]:
        print("SMTP validation failed, cannot send test email.")
        return

    # Send test email
    result = await service.send_email(
        to_addresses="test@example.com",
        subject="Office Agent Test Email",
        body="This is a test email from Office Agent.",
    )

    print(f"Email send result: {result}")


if __name__ == "__main__":
    # Run manual test
    asyncio.run(manual_test_send_email())
