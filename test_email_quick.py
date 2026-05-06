"""Quick email functionality test and demo script."""

import asyncio
from app.services.email_service import EmailService
from app.mcp_server.tools.text_tools import extract_email_addresses
from app.mcp_server.tools.email_tools import validate_email_config
from app.config import get_settings


async def main() -> None:
    """Run email functionality tests."""
    settings = get_settings()

    print("=" * 60)
    print("邮件功能快速测试")
    print("=" * 60)

    # 1. Check SMTP configuration
    print("\n1️⃣  检查 SMTP 配置...")
    if settings.is_email_configured:
        print(f"✅ SMTP 已配置:")
        print(f"   - 服务器: {settings.smtp_host}:{settings.smtp_port}")
        print(f"   - 用户名: {settings.smtp_username}")
        print(f"   - TLS 方式: {'隐式 TLS' if settings.smtp_use_tls else 'STARTTLS'}")

        # Validate connection
        print("\n   验证连接...")
        validation = await validate_email_config()
        if validation["valid"]:
            print(f"   ✅ 连接验证成功: {validation['message']}")
        else:
            print(f"   ❌ 连接验证失败: {validation['error']}")
    else:
        print("❌ SMTP 未配置。需要设置以下环境变量:")
        print("   - SMTP_HOST")
        print("   - SMTP_PORT")
        print("   - SMTP_USERNAME")
        print("   - SMTP_PASSWORD")

    # 2. Test email extraction
    print("\n2️⃣  测试邮件地址提取...")
    test_texts = [
        "请发送通知到 alice@company.com 和 bob@company.com",
        "将报告发送到 report@example.com",
        "没有邮件地址的文本",
    ]
    for text in test_texts:
        addresses = extract_email_addresses(text)
        print(f"   文本: '{text}'")
        print(f"   提取结果: {addresses if addresses else '(无)'}")

    # 3. Test email sending (if configured)
    if settings.is_email_configured:
        print("\n3️⃣  测试邮件发送...")
        service = EmailService()

        # Test sending notification email
        result = await service.send_email_notification(
            to_address=settings.smtp_username,  # Send to self for testing
            notice_content="这是一个测试通知邮件\n\n系统已成功集成邮件发送功能！",
            email_subject="Office Agent 测试通知",
        )

        if result["success"]:
            print(f"✅ 邮件发送成功")
            print(f"   收件人: {settings.smtp_username}")
            print(f"   Message ID: {result['message_id']}")
        else:
            print(f"❌ 邮件发送失败")
            print(f"   错误: {result['error']}")
    else:
        print("\n3️⃣  邮件发送测试")
        print("⏭️  已跳过（SMTP 未配置）")

    print("\n" + "=" * 60)
    print("✨ 邮件功能测试完成")
    print("=" * 60)
    print("\n📚 使用指南: 详见 docs/邮件发送功能使用指南.md")


if __name__ == "__main__":
    asyncio.run(main())
