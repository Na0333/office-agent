#!/usr/bin/env python3
"""
Office Agent 一键初始化工具

简化新用户的配置流程。
"""

import sys
import asyncio
from pathlib import Path


def print_welcome():
    """打印欢迎信息。"""
    print("\n" + "=" * 70)
    print("  " + "🎉 欢迎使用 Office Agent".center(66))
    print("=" * 70)
    print("""
这个工具将帮助你快速配置 Office Agent 的邮件功能。

主要功能：
  📧 邮件发送   - 通过 SMTP 发送邮件通知
  📝 待办管理   - 从会议纪要提取待办事项
  🔔 通知生成   - 生成格式化的群组通知

无论你是否有邮件配置经验，我们都能帮助你快速上手！
""")


def print_menu():
    """打印菜单。"""
    print("\n" + "-" * 70)
    print("请选择操作：\n")
    print("  1️⃣  交互式邮箱配置   - 按步骤配置你的邮箱")
    print("  2️⃣  配置诊断          - 检查现有配置是否正确")
    print("  3️⃣  快速测试          - 快速测试邮件功能")
    print("  4️⃣  查看文档          - 查看详细使用文档")
    print("  5️⃣  启动 Agent        - 启动 Office Agent 服务")
    print("  0️⃣  退出              - 退出程序\n")


def print_section(title: str):
    """打印小标题。"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def run_setup():
    """运行配置向导。"""
    print_section("📧 邮箱配置向导")
    try:
        from setup_email import ConfigWizard
        wizard = ConfigWizard()
        await wizard.run()
    except Exception as e:
        print(f"❌ 配置出错: {str(e)}")


async def run_diagnostics():
    """运行诊断工具。"""
    print_section("🔍 配置诊断")
    try:
        from diagnose_email import ConfigDiagnostics
        diagnostics = ConfigDiagnostics()
        await diagnostics.run()
    except Exception as e:
        print(f"❌ 诊断出错: {str(e)}")


async def run_quick_test():
    """运行快速测试。"""
    print_section("🧪 快速测试")
    try:
        from test_email_quick import main
        main()
    except Exception as e:
        print(f"❌ 测试出错: {str(e)}")


def view_documentation():
    """查看文档。"""
    print_section("📚 文档导航")
    print("""
以下是推荐阅读的文档：

📖 快速开始指南
   👉 docs/邮件发送功能使用指南.md
   内容：邮件功能详细说明、常见服务商配置、故障排除

📖 实现细节
   👉 docs/邮件功能实现总结.md
   内容：技术实现、架构设计、工作流程

📖 项目结构
   👉 docs/邮件功能-项目结构变化.md
   内容：文件变化、模块依赖、设计决策

📖 配置完成清单
   👉 docs/邮件功能-完成清单.md
   内容：功能清单、部署步骤、后续改进

🔗 快速链接
   - 项目根目录 README: README.md
   - 配置示例: .env.example
""")


def start_agent():
    """启动 Agent。"""
    print_section("🚀 启动 Office Agent")
    print("""
在启动前，请确保：
  ✅ 已安装依赖包: pip install -r requirements.txt
  ✅ 已配置 .env 文件（至少需要应用基本配置）
  ✅ 邮件配置是可选的（可以稍后添加）

启动命令：

  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

启动后：
  - 访问 http://127.0.0.1:8000/health 检查健康状态
  - 使用 /chat 接口发送请求
  - 查看文档了解 API 使用方式
""")

    start = input("\n是否执行启动命令？(y/n) [n]: ").lower()
    if start == "y":
        import subprocess
        try:
            subprocess.run(
                ["uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
                check=False
            )
        except KeyboardInterrupt:
            print("\n⏹️  Agent 已停止")
        except Exception as e:
            print(f"❌ 启动失败: {str(e)}")
            print("   请手动运行上述启动命令")


async def main():
    """主程序。"""
    print_welcome()

    while True:
        print_menu()
        choice = input("请输入选项 (0-5): ").strip()

        if choice == "1":
            await run_setup()
        elif choice == "2":
            await run_diagnostics()
        elif choice == "3":
            await run_quick_test()
        elif choice == "4":
            view_documentation()
        elif choice == "5":
            start_agent()
        elif choice == "0":
            print("\n👋 感谢使用 Office Agent，再见！\n")
            break
        else:
            print("❌ 无效选择，请重试")

        input("\n按 Enter 继续...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  程序已退出")
        sys.exit(0)
