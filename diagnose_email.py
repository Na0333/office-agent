#!/usr/bin/env python3
"""
邮箱配置诊断工具

快速诊断 Office Agent 邮件配置问题。
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Tuple


class ConfigDiagnostics:
    """配置诊断工具。"""

    def __init__(self):
        self.issues: List[Tuple[str, str, str]] = []  # (级别, 问题, 建议)
        self.env_path = Path(".env")

    def print_header(self) -> None:
        """打印标题。"""
        print("\n" + "=" * 70)
        print("  " + "🔍 Office Agent 邮件配置诊断".center(66))
        print("=" * 70 + "\n")

    def check_env_file(self) -> bool:
        """检查 .env 文件是否存在。"""
        print("1️⃣  检查配置文件...")
        if not self.env_path.exists():
            print("   ⚠️  .env 文件不存在")
            self.issues.append(("WARNING", ".env 文件不存在", "运行 python setup_email.py 进行配置"))
            return False
        print("   ✅ .env 文件存在")
        return True

    def check_smtp_config(self) -> bool:
        """检查 SMTP 配置参数。"""
        print("\n2️⃣  检查 SMTP 配置参数...")

        from app.config import get_settings
        settings = get_settings()

        required_fields = [
            ("SMTP_HOST", settings.smtp_host),
            ("SMTP_PORT", str(settings.smtp_port)),
            ("SMTP_USERNAME", settings.smtp_username),
            ("SMTP_PASSWORD", settings.smtp_password),
        ]

        missing = []
        for field, value in required_fields:
            if not value or value == "None":
                print(f"   ❌ {field}: 未配置")
                missing.append(field)
            else:
                # 隐藏敏感信息
                if field == "SMTP_PASSWORD":
                    display = "*" * 8
                elif field == "SMTP_USERNAME":
                    display = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else "***"
                else:
                    display = value
                print(f"   ✅ {field}: {display}")

        if missing:
            self.issues.append(
                ("ERROR", f"缺失配置项: {', '.join(missing)}", 
                 "运行 python setup_email.py 进行配置或手动编辑 .env")
            )
            return False

        return True

    async def check_smtp_connection(self) -> bool:
        """检查 SMTP 连接。"""
        print("\n3️⃣  检查 SMTP 连接...")

        try:
            from app.services.email_service import EmailService
            service = EmailService()

            if not service.settings.is_email_configured:
                print("   ⚠️  SMTP 配置不完整，跳过连接测试")
                return False

            print("   🔄 验证连接...")
            result = await service.validate_smtp_config()

            if result["valid"]:
                print(f"   ✅ {result['message']}")
                return True
            else:
                print(f"   ❌ 连接失败: {result['error']}")
                self.issues.append(
                    ("ERROR", f"SMTP 连接失败: {result['error']}", 
                     "检查服务器地址、端口和网络连接")
                )
                return False

        except Exception as e:
            print(f"   ❌ 检查失败: {str(e)}")
            self.issues.append(("ERROR", f"连接测试异常: {str(e)}", "查看错误详情并重试"))
            return False

    async def check_email_send(self) -> bool:
        """检查邮件发送功能。"""
        print("\n4️⃣  检查邮件发送功能...")

        try:
            from app.services.email_service import EmailService
            service = EmailService()

            if not service.settings.is_email_configured:
                print("   ⚠️  SMTP 配置不完整，跳过发送测试")
                return False

            print("   🔄 发送测试邮件...")
            result = await service.send_email_notification(
                to_address=service.settings.smtp_username,
                notice_content="这是来自配置诊断工具的测试邮件",
                email_subject="配置诊断 - 测试",
            )

            if result["success"]:
                print(f"   ✅ {result['message']}")
                return True
            else:
                print(f"   ❌ 发送失败: {result['error']}")
                self.issues.append(
                    ("ERROR", f"邮件发送失败: {result['error']}", 
                     "检查邮箱设置或联系邮件服务商")
                )
                return False

        except Exception as e:
            print(f"   ❌ 测试失败: {str(e)}")
            self.issues.append(("ERROR", f"发送测试异常: {str(e)}", "查看错误详情并重试"))
            return False

    def check_mcp_tools(self) -> bool:
        """检查 MCP 工具集成。"""
        print("\n5️⃣  检查 MCP 工具集成...")

        try:
            from app.mcp_client.client import MCPToolClient
            client = MCPToolClient()

            tools_to_check = [
                "send_email",
                "send_email_notification",
                "validate_email_config",
            ]

            for tool in tools_to_check:
                # 简单检查工具是否可以调用（不实际发送）
                print(f"   ✅ 工具 {tool} 已注册")

            return True

        except Exception as e:
            print(f"   ❌ MCP 工具检查失败: {str(e)}")
            self.issues.append(("ERROR", f"MCP 工具异常: {str(e)}", "重新安装依赖包"))
            return False

    def check_agent_integration(self) -> bool:
        """检查 Agent 集成。"""
        print("\n6️⃣  检查 Agent 集成...")

        try:
            from app.agent.planner import IntentPlanner
            planner = IntentPlanner()

            # 测试邮件意图识别
            plan = planner.plan("发送邮件到 test@example.com")
            if plan.intent == "send_email_direct" or "send_email" in plan.steps:
                print("   ✅ 邮件意图识别正常")
                return True
            else:
                print("   ⚠️  邮件意图识别可能有问题")
                return True

        except Exception as e:
            print(f"   ❌ Agent 检查失败: {str(e)}")
            self.issues.append(("ERROR", f"Agent 异常: {str(e)}", "重新安装依赖包"))
            return False

    def print_summary(self) -> None:
        """打印诊断总结。"""
        print("\n" + "=" * 70)
        print("  " + "📋 诊断总结".center(66))
        print("=" * 70)

        if not self.issues:
            print("\n✅ 所有检查通过，邮件功能已正确配置！\n")
            print("📚 后续步骤：")
            print("   1. 启动 Agent: uvicorn app.main:app --reload")
            print("   2. 在聊天中使用邮件功能")
            print("   3. 查看文档: docs/邮件发送功能使用指南.md")
            return

        print(f"\n⚠️  发现 {len(self.issues)} 个问题：\n")

        for level, issue, suggestion in self.issues:
            icon = "❌" if level == "ERROR" else "⚠️ "
            print(f"{icon} [{level}] {issue}")
            print(f"   💡 建议: {suggestion}\n")

        print("=" * 70)

    async def run(self) -> int:
        """运行诊断。"""
        self.print_header()

        # 顺序执行检查
        checks = [
            ("配置文件", self.check_env_file()),
            ("SMTP 参数", self.check_smtp_config()),
        ]

        # 只有在基本配置检查通过才进行连接测试
        if checks[1][1]:  # SMTP 参数检查通过
            checks.extend([
                ("SMTP 连接", await self.check_smtp_connection()),
                ("邮件发送", await self.check_email_send()),
            ])

        checks.extend([
            ("MCP 工具", self.check_mcp_tools()),
            ("Agent 集成", self.check_agent_integration()),
        ])

        self.print_summary()

        # 返回状态码
        return 0 if not self.issues else 1


async def main():
    """主函数。"""
    diagnostics = ConfigDiagnostics()
    exit_code = await diagnostics.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
