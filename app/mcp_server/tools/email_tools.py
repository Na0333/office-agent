"""Email sending MCP tools."""

from app.services.email_service import EmailService


async def send_email(
    to_addresses: str | list[str],
    subject: str,
    body: str,
    cc: str | list[str] = "",
    bcc: str | list[str] = "",
) -> dict:
    """Send a plain text email.

    Args:
        to_addresses: Recipient email address(es), comma-separated.
        subject: Email subject.
        body: Plain text email body content.
        cc: CC recipients, comma-separated.
        bcc: BCC recipients, comma-separated.

    Returns:
        Dict with email sending result: success, message, message_id, error.
    """
    service = EmailService()

    def normalize_list(value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return [addr.strip() for addr in value if isinstance(addr, str) and addr.strip()]
        if not value:
            return []
        return [addr.strip() for addr in value.split(",") if addr.strip()]

    cc_list = normalize_list(cc)
    bcc_list = normalize_list(bcc)

    return await service.send_email(
        to_addresses=to_addresses,
        subject=subject,
        body=body,
        cc=cc_list,
        bcc=bcc_list,
    )


async def validate_email_config() -> dict:
    """Validate SMTP configuration.

    Returns:
        Dict with validation result: valid, message, error.
    """
    service = EmailService()
    return await service.validate_smtp_config()
