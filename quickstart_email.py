#!/usr/bin/env python3
"""
邮件功能快速开始指南 - 配置和测试

这个脚本帮助你快速配置和测试Office Agent的邮件功能。
"""

import os
import sys
from pathlib import Path


def print_header(text: str) -> None:
    """打印标题。"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_section(text: str) -> None:
    """打印小标题。"""
    print(f"\n📌 {text}")
    print("-" * 60)


def create_env_template() -> None:
    """创建.env文件模板。"""
    env_template = """# Office Agent 邮件功能配置

# SMTP Configuration - QQ邮箱示例
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-auth-code
SMTP_TIMEOUT=30
SMTP_USE_TLS=true
SMTP_USE_STARTTLS=false

# 其他配置保持不变
APP_NAME=office-agent
APP_ENV=local
DATABASE_PATH=data/office_agent.db
"""

    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env 文件已存在")
    else:
        env_path.write_text(env_template)
        print("✨ 已创建 .env 文件模板")
        print(f"📝 位置: {env_path.absolute()}")
        print("⚠️  请编辑.env文件，填入你的SMTP服务器信息")


def print_smtp_guides() -> None:
    """打印SMTP配置指南。"""
    print_section("常见邮箱SMTP配置")
    
    configs = {
        "QQ邮箱": {
            "SMTP_HOST": "smtp.qq.com",
            "SMTP_PORT": "465",
            "SMTP_USE_TLS": "true",
            "SMTP_USE_STARTTLS": "false",
            "说明": "需要授权码（在QQ邮箱设置中获取）"
        },
        "Gmail": {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USE_TLS": "false",
            "SMTP_USE_STARTTLS": "true",
            "说明": "需要应用专用密码"
        },
        "Outlook": {
            "SMTP_HOST": "smtp.office365.com",
            "SMTP_PORT": "587",
            "SMTP_USE_TLS": "false",
            "SMTP_USE_STARTTLS": "true",
            "说明": "使用账户密码或应用密码"
        },
        "腾讯企业邮": {
            "SMTP_HOST": "smtp.exmail.qq.com",
            "SMTP_PORT": "465",
            "SMTP_USE_TLS": "true",
            "SMTP_USE_STARTTLS": "false",
            "说明": "企业域名邮箱"
        }
    }
    
    for service, config in configs.items():
        print(f"\n🔹 {service}:")
        for key, value in config.items():
            if key != "说明":
                print(f"   {key}={value}")
            else:
                print(f"   💡 {value}")


def print_usage_examples() -> None:
    """打印使用示例。"""
    print_section("使用示例")
    
    examples = [
        {
            "title": "示例1: 基础邮件发送",
            "input": "请发送邮件到 recipient@example.com，内容是：会议已完成",
            "output": "邮件已发送到 recipient@example.com"
        },
        {
            "title": "示例2: 会议纪要转邮件",
            "input": "整理会议纪要成待办并发送邮件到 zhang@company.com：张三完成需求文档",
            "output": "已提取1条待办，已发送邮件通知"
        },
        {
            "title": "示例3: 多个收件人",
            "input": "发送通知邮件到 alice@company.com 和 bob@company.com",
            "output": "邮件已发送到 alice@company.com 和 bob@company.com"
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}:")
        print(f"  💬 用户: {example['input']}")
        print(f"  🤖 Agent: {example['output']}")


def print_testing_guide() -> None:
    """打印测试指南。"""
    print_section("测试邮件功能")
    
    print("""
1️⃣  快速功能测试（推荐）:
    python test_email_quick.py

2️⃣  单元测试:
    pytest tests/test_email_service.py -v

3️⃣  集成测试:
    pytest tests/test_email_integration.py -v

4️⃣  验证SMTP配置:
    python -c "from app.mcp_server.tools.email_tools import validate_email_config; 
               import asyncio; print(asyncio.run(validate_email_config()))"
""")


def print_troubleshooting() -> None:
    """打印故障排除。"""
    print_section("常见问题排除")
    
    issues = [
        {
            "问题": "连接超时",
            "原因": "SMTP服务器无法访问或防火墙限制",
            "解决": "检查SMTP_HOST和SMTP_PORT是否正确"
        },
        {
            "问题": "认证失败",
            "原因": "用户名或密码错误",
            "解决": "确认SMTP_USERNAME和SMTP_PASSWORD正确，特别是授权码"
        },
        {
            "问题": "TLS错误",
            "原因": "连接方式配置错误",
            "解决": "端口465用TLS=true，端口587用STARTTLS=true"
        },
        {
            "问题": "邮件未收到",
            "原因": "可能被标记为垃圾邮件",
            "解决": "检查垃圾邮件文件夹，配置发件人白名单"
        }
    ]
    
    for issue in issues:
        print(f"\n❌ {issue['问题']}:")
        print(f"   原因: {issue['原因']}")
        print(f"   解决: {issue['解决']}")


def print_next_steps() -> None:
    """打印后续步骤。"""
    print_section("后续步骤")
    
    print("""
✅ 完成邮件功能配置后:

1. 编辑 .env 文件，填入SMTP信息
2. 运行 python test_email_quick.py 验证配置
3. 在Agent中使用邮件功能:
   - 单独发邮件: "发送邮件到 recipient@example.com"
   - 待办+邮件: "整理会议纪要并发邮件"
4. 查看完整文档: docs/邮件发送功能使用指南.md

📚 相关文档:
   - 📖 邮件发送功能使用指南.md - 完整使用文档
   - 📖 邮件功能实现总结.md - 技术实现细节
   - 📖 邮件功能-项目结构变化.md - 项目结构修改

🔗 快速链接:
   - 本地测试脚本: test_email_quick.py
   - 单元测试: tests/test_email_service.py
   - 集成测试: tests/test_email_integration.py
""")


def main() -> None:
    """主程序。"""
    print_header("📧 Office Agent 邮件功能快速开始指南")
    
    # 创建.env模板
    create_env_template()
    
    # 打印配置指南
    print_smtp_guides()
    
    # 打印使用示例
    print_usage_examples()
    
    # 打印测试指南
    print_testing_guide()
    
    # 打印故障排除
    print_troubleshooting()
    
    # 打印后续步骤
    print_next_steps()
    
    print_header("🎉 准备完成！祝你使用愉快")


if __name__ == "__main__":
    main()
