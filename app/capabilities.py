from __future__ import annotations

from typing import Any

from app.config import get_settings


MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "summarize_document_tool",
        "category": "document",
        "description": "总结 Word/PDF/Excel/文本内容，返回摘要、文本片段和字符数。",
    },
    {
        "name": "read_document_tool",
        "category": "document",
        "description": "读取并解析文档内容，可提取 Word/Excel/PDF/文本中的段落和表格。",
    },
    {
        "name": "create_document_tool",
        "category": "document",
        "description": "根据结构化内容生成 Word、Excel、PDF 或文本文件。",
    },
    {
        "name": "convert_document_tool",
        "category": "document",
        "description": "读取源文档并导出为目标格式。",
    },
    {
        "name": "process_table_data_tool",
        "category": "spreadsheet",
        "description": "对二维表格数据进行筛选、排序、合并、透视和统计分析。",
    },
    {
        "name": "extract_todos_tool",
        "category": "task",
        "description": "从会议纪要或办公聊天文本中提取待办、负责人和截止时间。",
    },
    {
        "name": "create_tasks_tool",
        "category": "task",
        "description": "将待办写入任务数据库。",
        "sensitive": True,
    },
    {
        "name": "query_task_status_tool",
        "category": "task",
        "description": "查询当前用户或全部任务状态。",
    },
    {
        "name": "generate_notice_tool",
        "category": "writing",
        "description": "根据待办清单生成群通知/公告草稿。",
    },
    {
        "name": "generate_email_tool",
        "category": "writing",
        "description": "根据办公事项生成正式邮件草稿。",
    },
    {
        "name": "send_email_tool",
        "category": "email",
        "description": "通过 SMTP 发送纯文本邮件。只负责发送，confirmed=true 时执行。",
        "sensitive": True,
    },
    {
        "name": "validate_email_config_tool",
        "category": "email",
        "description": "检查 SMTP 邮件配置是否可用。",
    },
    {
        "name": "list_notice_channels_tool",
        "category": "notice",
        "description": "列出已配置的钉钉、企业微信、飞书通知通道。",
    },
    {
        "name": "send_platform_notice_tool",
        "category": "notice",
        "description": "通过配置好的群机器人 Webhook 发送跨平台通知，confirmed=true 时执行。",
        "sensitive": True,
    },
    {
        "name": "read_dingtalk_document_tool",
        "category": "document",
        "description": "读取钉钉在线文档内容（需要配置钉钉开放平台 AppKey 和 AppSecret）。",
    },
    {
        "name": "validate_dingtalk_config_tool",
        "category": "document",
        "description": "验证钉钉开放平台配置是否正确。",
    },
]


def build_capabilities() -> dict[str, Any]:
    settings = get_settings()
    api_base = settings.public_base_url.rstrip("/")
    local_api_base = f"http://{settings.host}:{settings.port}"
    api_base = api_base or local_api_base
    mcp_http_base = f"http://{settings.mcp_host}:{settings.mcp_port}"

    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "recommended_deployment": "mcp_tools_server",
        "entrypoints": {
            "agent_api": {
                "type": "http",
                "base_url": api_base,
                "health": f"{api_base}/health",
                "chat": f"{api_base}/chat",
                "upload": f"{api_base}/files/upload",
                "capabilities": f"{api_base}/capabilities",
                "openapi": f"{api_base}/openapi.json",
            },
            "mcp_stdio": {
                "type": "mcp_stdio",
                "command": "python",
                "args": ["-m", "app.mcp_server.server"],
                "env": {
                    "PYTHONPATH": "<office-agent-project-root>",
                    "DATABASE_PATH": "<office-agent-project-root>/data/office_agent.db",
                },
            },
            "mcp_streamable_http": {
                "type": "mcp_streamable_http",
                "url": f"{mcp_http_base}{settings.mcp_streamable_http_path}",
                "transport_env": {
                    "MCP_TRANSPORT": "streamable-http",
                    "MCP_HOST": settings.mcp_host,
                    "MCP_PORT": settings.mcp_port,
                },
            },
        },
        "tools": MCP_TOOLS,
        "integration_guidance": [
            "AstrBot MCP 建议把自身 LLM 作为决策大脑，直接调用分类清晰的 MCP 工具。",
            "Office Agent 不再包含内部 LLM 或 Planner；/chat 仅保留兼容提示。",
            "同机部署使用 stdio MCP；跨机器/服务器部署使用 streamable-http MCP。",
            "发送邮件、创建任务、发送 webhook 等敏感工具必须传 confirmed=true 才会执行。",
        ],
    }
