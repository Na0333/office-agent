from app.mcp_server.tools.dingtalk_tools import read_dingtalk_document, validate_dingtalk_config
from app.mcp_server.tools.document_tools import (
    convert_document,
    create_document,
    process_table_data,
    read_document,
    summarize_document,
)
from app.mcp_server.tools.email_tools import (
    send_email,
    validate_email_config,
)
from app.mcp_server.tools.notice_tools import (
    list_notice_channels,
    send_platform_notice,
)
from app.mcp_server.tools.task_tools import create_tasks, query_task_status
from app.mcp_server.tools.text_tools import extract_todos, generate_email, generate_notice
from app.schemas.tool import ToolResult


class MCPToolClient:
    """In-process tool client for MVP.

    Replace this adapter with a real MCP client when the MCP server is deployed
    separately or when AstrBot's MCP capability is wired in.
    """

    async def call(self, name: str, arguments: dict) -> ToolResult:
        try:
            if name == "extract_todos":
                data = extract_todos(arguments.get("text", ""))
            elif name == "generate_notice":
                data = generate_notice(arguments.get("todos", []))
            elif name == "generate_email":
                data = generate_email(arguments.get("content", ""))
            elif name == "send_email":
                preview = {
                    "to_addresses": arguments.get("to_addresses", ""),
                    "subject": arguments.get("subject", ""),
                    "body": arguments.get("body", ""),
                    "cc": arguments.get("cc", ""),
                    "bcc": arguments.get("bcc", ""),
                }
                if not arguments.get("confirmed", False):
                    data = {
                        "success": False,
                        "need_confirmation": True,
                        "message": "请确认后再发送邮件。",
                        "preview": preview,
                    }
                else:
                    data = await send_email(
                        to_addresses=arguments.get("to_addresses", ""),
                        subject=arguments.get("subject", ""),
                        body=arguments.get("body", ""),
                        cc=arguments.get("cc", ""),
                        bcc=arguments.get("bcc", ""),
                    )
            elif name == "validate_email_config":
                data = await validate_email_config()
            elif name == "list_notice_channels":
                data = list_notice_channels()
            elif name == "send_platform_notice":
                if not arguments.get("confirmed", False):
                    data = {
                        "success": False,
                        "need_confirmation": True,
                        "message": "请确认后再发送 webhook 通知。",
                        "preview": arguments,
                    }
                else:
                    data = await send_platform_notice(
                        channel_ids=arguments.get("channel_ids", []),
                        content=arguments.get("content", ""),
                        title=arguments.get("title", "办公通知"),
                    )
            elif name == "summarize_document":
                data = summarize_document(
                    file_path=arguments.get("file_path"),
                    fallback_text=arguments.get("text", ""),
                )
            elif name == "read_document":
                data = read_document(
                    file_path=arguments.get("file_path", ""),
                    extract_tables=arguments.get("extract_tables", True),
                    extract_images=arguments.get("extract_images", False),
                )
            elif name == "create_document":
                data = create_document(
                    file_type=arguments.get("file_type", ""),
                    content=arguments.get("content", {}),
                    output_path=arguments.get("output_path", ""),
                )
            elif name == "convert_document":
                data = convert_document(
                    input_path=arguments.get("input_path", ""),
                    output_path=arguments.get("output_path", ""),
                    target_format=arguments.get("target_format", ""),
                )
            elif name == "process_table_data":
                data = process_table_data(
                    table_data=arguments.get("table_data", []),
                    operation=arguments.get("operation", ""),
                    **arguments.get("options", {}),
                )
            elif name == "create_tasks":
                if not arguments.get("confirmed", False):
                    data = {
                        "success": False,
                        "need_confirmation": True,
                        "message": "请确认后再创建任务。",
                        "preview": arguments,
                    }
                else:
                    data = create_tasks(
                        todos=arguments.get("todos", []),
                        source_platform=arguments.get("source_platform"),
                        source_user_id=arguments.get("source_user_id"),
                        source_group_id=arguments.get("source_group_id"),
                    )
                    data["success"] = True
            elif name == "query_task_status":
                data = query_task_status(arguments.get("user_id"))
            elif name == "read_dingtalk_document":
                data = await read_dingtalk_document(
                    document_id=arguments.get("document_id", ""),
                    extract_tables=arguments.get("extract_tables", True),
                    extract_images=arguments.get("extract_images", False),
                )
            elif name == "validate_dingtalk_config":
                data = await validate_dingtalk_config()
            else:
                return ToolResult(success=False, tool_name=name, error=f"Unknown tool: {name}")

            success = True
            message = "ok"
            error = None
            if isinstance(data, dict) and isinstance(data.get("success"), bool):
                success = data["success"]
                message = str(data.get("message") or message)
                error = data.get("error")

            return ToolResult(success=success, tool_name=name, data=data, message=message, error=error)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, tool_name=name, error=str(exc))
