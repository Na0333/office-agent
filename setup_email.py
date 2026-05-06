#!/usr/bin/env python3
"""
邮箱配置向导 - 交互式配置工具

帮助用户快速配置 Office Agent 的邮件功能。
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any


# 常见邮箱服务商配置
SMTP_PRESETS = {
    "qq": {
        "name": "QQ 邮箱",
        "host": "smtp.qq.com",
        "port": "465",
        "use_tls": "true",
        "use_starttls": "false",
        "help": "📖 如何获取授权码？\n   1. 登录 QQ 邮箱\n   2. 进入 '设置' → '账户'\n   3. 找到 'POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务'\n   4. 点击 '生成授权码'",
    },
    "gmail": {
        "name": "Gmail",
        "host": "smtp.gmail.com",
        "port": "587",
        "use_tls": "false",
        "use_starttls": "true",
        "help": "📖 如何获取应用密码？\n   1. 访问 myaccount.google.com\n   2. 进入 '安全' 标签\n   3. 启用 '两步验证'\n   4. 生成 '应用专用密码'",
    },
    "outlook": {
        "name": "Outlook / Hotmail",
        "host": "smtp.office365.com",
        "port": "587",
        "use_tls": "false",
        "use_starttls": "true",
        "help": "📖 使用说明\n   1. 使用 Outlook 账户登录\n   2. 使用账户密码或应用密码\n   3. 端口使用 587 (STARTTLS)",
    },
    "exmail": {
        "name": "腾讯企业邮",
        "host": "smtp.exmail.qq.com",
        "port": "465",
        "use_tls": "true",
        "use_starttls": "false",
        "help": "📖 企业邮箱配置\n   1. 使用企业域名邮箱账号\n   2. 使用邮箱密码\n   3. 端口使用 465 (TLS)",
    },
    "custom": {
        "name": "其他 SMTP 服务",
        "host": None,
        "port": "465",
        "use_tls": "true",
        "use_starttls": "false",
        "help": "📖 自定义配置\n   请填入你的 SMTP 服务器信息",
    },
}


class ConfigWizard:
    """邮箱配置向导。"""

    def __init__(self):
        self.config: Dict[str, str] = {}
        self.env_path = Path(".env")

    def print_header(self) -> None:
        """打印欢迎信息。"""
        print("\n" + "=" * 70)
        print("  " + "🚀 Office Agent 邮箱配置向导".center(66))
        print("=" * 70)

    def print_step(self, step: int, total: int, title: str) -> None:
        """打印步骤信息。"""
        print(f"\n📍 步骤 {step}/{total}: {title}")
        print("-" * 70)

    def clear_screen(self) -> None:
        """清屏（跨平台）。"""
        os.system("clear" if os.name == "posix" else "cls")

    def read_input(self, prompt: str, default: Optional[str] = None) -> str:
        """读取用户输入。"""
        if default:
            display = f"{prompt} [{default}]: "
        else:
            display = f"{prompt}: "

        value = input(display).strip()
        return value if value else default or ""

    def step1_select_provider(self) -> str:
        """第一步：选择邮箱提供商。"""
        self.print_step(1, 5, "选择邮箱提供商")

        print("请选择你的邮箱提供商：\n")
        for idx, (key, preset) in enumerate(SMTP_PRESETS.items(), 1):
            print(f"  {idx}. {preset['name']}")

        while True:
            choice = self.read_input(f"\n请输入选项 (1-{len(SMTP_PRESETS)}) 或邮箱域名")
            
            # 数字选择
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(SMTP_PRESETS):
                    return list(SMTP_PRESETS.keys())[idx]
            except ValueError:
                pass

            # 域名选择（自动识别）
            if "@" in choice and "." in choice:
                domain = choice.split("@")[1].lower()
                if domain in ["qq.com", "foxmail.com"]:
                    return "qq"
                elif domain in ["gmail.com", "googlemail.com"]:
                    return "gmail"
                elif domain in ["outlook.com", "hotmail.com", "live.com"]:
                    return "outlook"
                elif domain.startswith("exmail.qq.com"):
                    return "exmail"

            print("❌ 无效的选择，请重试")

    def step2_enter_email(self) -> str:
        """第二步：输入邮箱地址。"""
        self.print_step(2, 5, "输入邮箱地址")

        while True:
            email = self.read_input("请输入你的邮箱地址")
            if "@" in email and "." in email:
                return email
            print("❌ 邮箱格式无效，请重试")

    def step3_enter_password(self, provider: str) -> str:
        """第三步：输入密码/授权码。"""
        self.print_step(3, 5, "输入授权码")

        preset = SMTP_PRESETS[provider]
        print(preset["help"])
        print()

        while True:
            password = self.read_input("请输入授权码或密码")
            if len(password) >= 4:
                return password
            print("❌ 授权码太短，请检查是否正确")

    def step4_configure_smtp(self, provider: str) -> None:
        """第四步：配置SMTP参数。"""
        self.print_step(4, 5, "配置 SMTP 参数")

        preset = SMTP_PRESETS[provider]

        if provider == "custom":
            print("请输入你的 SMTP 服务器信息：\n")
            self.config["SMTP_HOST"] = self.read_input("SMTP 服务器地址")
            while not self.config["SMTP_HOST"]:
                self.config["SMTP_HOST"] = self.read_input("SMTP 服务器地址（必填）")

            self.config["SMTP_PORT"] = self.read_input("SMTP 端口", "465")

            use_tls = self.read_input("使用 TLS (端口465)? (y/n)", "y").lower()
            self.config["SMTP_USE_TLS"] = "true" if use_tls == "y" else "false"

            use_starttls = self.read_input("使用 STARTTLS (端口587)? (y/n)", "n").lower()
            self.config["SMTP_USE_STARTTLS"] = "true" if use_starttls == "y" else "false"
        else:
            print(f"已为 {preset['name']} 预设配置参数：\n")
            self.config["SMTP_HOST"] = preset["host"]
            self.config["SMTP_PORT"] = preset["port"]
            self.config["SMTP_USE_TLS"] = preset["use_tls"]
            self.config["SMTP_USE_STARTTLS"] = preset["use_starttls"]

            print(f"  ✓ SMTP 服务器: {preset['host']}")
            print(f"  ✓ SMTP 端口: {preset['port']}")
            print(f"  ✓ 使用 TLS: {preset['use_tls']}")
            print(f"  ✓ 使用 STARTTLS: {preset['use_starttls']}")

        # 其他配置
        self.config["SMTP_TIMEOUT"] = "30"
        self.config["SMTP_USERNAME"] = ""  # 在后续步骤中设置

    def step5_review_and_save(self, email: str, password: str) -> bool:
        """第五步：确认并保存配置。"""
        self.print_step(5, 5, "确认配置")

        print("📋 配置摘要：\n")
        print(f"  邮箱地址: {email}")
        print(f"  SMTP 服务器: {self.config['SMTP_HOST']}")
        print(f"  SMTP 端口: {self.config['SMTP_PORT']}")
        print(f"  使用 TLS: {self.config['SMTP_USE_TLS']}")
        print(f"  使用 STARTTLS: {self.config['SMTP_USE_STARTTLS']}")

        confirm = self.read_input("\n确认配置正确? (y/n)", "y").lower()
        if confirm != "y":
            print("❌ 已取消配置")
            return False

        # 生成 .env 内容
        env_content = self._generate_env_content(email, password)

        # 检查是否覆盖现有配置
        if self.env_path.exists():
            print(f"\n⚠️  文件 .env 已存在")
            action = self.read_input("是否覆盖? (y/n)", "n").lower()
            if action != "y":
                print("已保存到 .env.new")
                self.env_path.write_text(env_content)
                return True
        
        # 保存 .env
        self.env_path.write_text(env_content)
        print(f"\n✅ 配置已保存到 {self.env_path.absolute()}")
        return True

    def _generate_env_content(self, email: str, password: str) -> str:
        """生成 .env 文件内容。"""
        # 读取现有配置（保留其他配置）
        existing_config = {}
        if self.env_path.exists():
            for line in self.env_path.read_text().splitlines():
                if line.strip() and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        existing_config[key.strip()] = value.strip()

        # 更新SMTP配置
        existing_config.update({
            "SMTP_HOST": self.config["SMTP_HOST"],
            "SMTP_PORT": self.config["SMTP_PORT"],
            "SMTP_USERNAME": email,
            "SMTP_PASSWORD": password,
            "SMTP_TIMEOUT": self.config["SMTP_TIMEOUT"],
            "SMTP_USE_TLS": self.config["SMTP_USE_TLS"],
            "SMTP_USE_STARTTLS": self.config["SMTP_USE_STARTTLS"],
        })

        # 生成文件内容
        lines = [
            "# Office Agent 配置",
            "",
            "# 应用配置",
            f"APP_NAME={existing_config.get('APP_NAME', 'office-agent')}",
            f"APP_ENV={existing_config.get('APP_ENV', 'local')}",
            f"HOST={existing_config.get('HOST', '127.0.0.1')}",
            f"PORT={existing_config.get('PORT', '8000')}",
            "",
            "# LLM 配置",
            f"DEEPSEEK_API_KEY={existing_config.get('DEEPSEEK_API_KEY', '')}",
            f"DEEPSEEK_BASE_URL={existing_config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')}",
            f"DEEPSEEK_MODEL={existing_config.get('DEEPSEEK_MODEL', 'deepseek-chat')}",
            "",
            "# 数据库配置",
            f"DATABASE_PATH={existing_config.get('DATABASE_PATH', 'data/office_agent.db')}",
            "",
            "# SMTP 邮件配置",
            f"SMTP_HOST={existing_config.get('SMTP_HOST')}",
            f"SMTP_PORT={existing_config.get('SMTP_PORT')}",
            f"SMTP_USERNAME={existing_config.get('SMTP_USERNAME')}",
            f"SMTP_PASSWORD={existing_config.get('SMTP_PASSWORD')}",
            f"SMTP_TIMEOUT={existing_config.get('SMTP_TIMEOUT')}",
            f"SMTP_USE_TLS={existing_config.get('SMTP_USE_TLS')}",
            f"SMTP_USE_STARTTLS={existing_config.get('SMTP_USE_STARTTLS')}",
        ]

        return "\n".join(lines) + "\n"

    async def test_configuration(self) -> None:
        """测试邮件配置。"""
        print("\n" + "=" * 70)
        print("  " + "🧪 测试邮件配置".center(66))
        print("=" * 70)

        try:
            from app.services.email_service import EmailService

            service = EmailService()

            if not service.settings.is_email_configured:
                print("❌ SMTP 配置不完整")
                return

            print("🔍 验证 SMTP 连接...")
            validation = await service.validate_smtp_config()

            if validation["valid"]:
                print(f"✅ {validation['message']}")

                # 询问是否发送测试邮件
                send_test = input("\n是否发送测试邮件? (y/n) [n]: ").lower()
                if send_test == "y":
                    print("\n📧 发送测试邮件...")
                    result = await service.send_email_notification(
                        to_address=service.settings.smtp_username,
                        notice_content="这是来自 Office Agent 的测试邮件。\n\n邮件功能配置成功！",
                        email_subject="Office Agent 测试",
                    )

                    if result["success"]:
                        print(f"✅ {result['message']}")
                        print(f"   Message ID: {result['message_id']}")
                    else:
                        print(f"❌ {result['error']}")
            else:
                print(f"❌ {validation['error']}")

        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")

    async def run(self) -> None:
        """运行配置向导。"""
        self.print_header()

        try:
            # 步骤1：选择提供商
            provider = self.step1_select_provider()

            # 步骤2：输入邮箱
            email = self.step2_enter_email()

            # 步骤3：输入密码
            password = self.step3_enter_password(provider)

            # 步骤4：配置SMTP
            self.step4_configure_smtp(provider)

            # 步骤5：确认并保存
            if self.step5_review_and_save(email, password):
                # 测试配置
                test_config = input("\n是否测试邮件配置? (y/n) [y]: ").lower()
                if test_config != "n":
                    await self.test_configuration()

                print("\n" + "=" * 70)
                print("  " + "✨ 配置完成！".center(66))
                print("=" * 70)
                print("\n📚 后续步骤：")
                print("   1. 启动 Agent: uvicorn app.main:app --reload")
                print("   2. 在聊天中使用邮件功能")
                print("   3. 查看文档: docs/邮件发送功能使用指南.md")
                print()

        except KeyboardInterrupt:
            print("\n\n⏹️  配置已取消")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 配置出错: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


async def main():
    """主函数。"""
    wizard = ConfigWizard()
    await wizard.run()


if __name__ == "__main__":
    asyncio.run(main())
