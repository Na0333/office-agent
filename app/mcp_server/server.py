import sys

from app.config import get_settings
from app.mcp_server.tools.dingtalk_tools import read_dingtalk_document, validate_dingtalk_config
from app.mcp_server.tools.document_tools import (
    convert_document,
    create_document,
    process_table_data,
    read_document,
    summarize_document,
)
from app.mcp_server.tools.email_tools import send_email, validate_email_config
from app.mcp_server.tools.notice_tools import list_notice_channels, send_platform_notice
from app.mcp_server.tools.task_tools import create_tasks, query_task_status
from app.mcp_server.tools.text_tools import extract_todos, generate_email, generate_notice

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None


if FastMCP is not None:
    settings = get_settings()
    mcp = FastMCP(
        "office-agent-tools",
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path=settings.mcp_streamable_http_path,
        sse_path=settings.mcp_sse_path,
        message_path=settings.mcp_message_path,
        stateless_http=settings.mcp_stateless_http,
    )
    print("office-agent MCP tools: direct", file=sys.stderr, flush=True)

    @mcp.tool()
    def summarize_document_tool(file_path: str | None = None, fallback_text: str = "") -> dict:
        """文档摘要工具：只读取文件或文本并返回摘要，不创建、不发送。"""
        return summarize_document(file_path=file_path, fallback_text=fallback_text)

    @mcp.tool()
    def read_document_tool(file_path: str, extract_tables: bool = True, extract_images: bool = False) -> dict:
        """文档读取工具：解析本地文档内容，不生成摘要、不创建文件。"""
        return read_document(file_path=file_path, extract_tables=extract_tables, extract_images=extract_images)

    @mcp.tool()
    def create_document_tool(file_type: str, content: dict, output_path: str) -> dict:
        """文档创建工具：根据结构化 content 写出文件，不发送消息。"""
        return create_document(file_type=file_type, content=content, output_path=output_path)

    @mcp.tool()
    def convert_document_tool(input_path: str, output_path: str, target_format: str) -> dict:
        """文档转换工具：把 input_path 转为 target_format 并保存到 output_path。"""
        return convert_document(input_path=input_path, output_path=output_path, target_format=target_format)

    @mcp.tool()
    def process_table_data_tool(table_data: list[list], operation: str, options: dict | None = None) -> dict:
        """表格处理工具：只对传入二维表做 filter/sort/merge/pivot/analyze。"""
        return process_table_data(table_data=table_data, operation=operation, **(options or {}))

    @mcp.tool()
    def extract_todos_tool(text: str) -> dict:
        """待办提取工具：从文本中提取待办结构，不写入数据库。"""
        return extract_todos(text)

    @mcp.tool()
    def create_tasks_tool(
        todos: list[dict],
        source_platform: str | None = None,
        source_user_id: str | None = None,
        source_group_id: str | None = None,
        confirmed: bool = False,
    ) -> dict:
        """任务创建工具：confirmed=true 时才把 todos 写入任务数据库。"""
        if not confirmed:
            return {
                "success": False,
                "need_confirmation": True,
                "message": "请确认后再创建任务。",
                "preview": {
                    "todos": todos,
                    "source_platform": source_platform,
                    "source_user_id": source_user_id,
                    "source_group_id": source_group_id,
                },
            }
        result = create_tasks(todos, source_platform, source_user_id, source_group_id)
        result["success"] = True
        return result

    @mcp.tool()
    def query_task_status_tool(user_id: str | None = None) -> dict:
        """任务查询工具：查询任务数据库，不创建、不修改。"""
        return query_task_status(user_id)

    @mcp.tool()
    def generate_notice_tool(todos: list[dict]) -> dict:
        """通知草稿工具：根据 todos 生成文本草稿，不发送 webhook。"""
        return generate_notice(todos)

    @mcp.tool()
    def generate_email_tool(content: str) -> dict:
        """邮件草稿工具：根据内容生成邮件草稿，不发送邮件。"""
        return generate_email(content)

    @mcp.tool()
    async def send_email_tool(
        to_addresses: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        confirmed: bool = False,
    ) -> dict:
        """邮件发送工具：confirmed=true 时才通过 SMTP 发送纯文本邮件。"""
        if not confirmed:
            return {
                "success": False,
                "need_confirmation": True,
                "message": "请确认后再发送邮件。",
                "preview": {
                    "to_addresses": to_addresses,
                    "subject": subject,
                    "body": body,
                    "cc": cc,
                    "bcc": bcc,
                },
            }
        return await send_email(to_addresses, subject, body, cc, bcc)

    @mcp.tool()
    async def validate_email_config_tool() -> dict:
        """邮件配置检查工具：只验证 SMTP 配置，不发送业务邮件。"""
        return await validate_email_config()

    @mcp.tool()
    def list_notice_channels_tool() -> dict:
        """通知通道查询工具：列出可用 channel_id、平台和名称，不发送。"""
        return list_notice_channels()

    @mcp.tool()
    async def send_platform_notice_tool(
        channel_ids: list[str] | str,
        content: str,
        title: str = "办公通知",
        confirmed: bool = False,
    ) -> dict:
        """Webhook 通知发送工具：confirmed=true 时才向指定 channel_ids 发送。"""
        if not confirmed:
            return {
                "success": False,
                "need_confirmation": True,
                "message": "请确认后再发送 webhook 通知。",
                "preview": {
                    "channel_ids": channel_ids,
                    "title": title,
                    "content": content,
                },
            }
        return await send_platform_notice(channel_ids=channel_ids, content=content, title=title)

    @mcp.tool()
    async def read_dingtalk_document_tool(
        document_id: str,
        extract_tables: bool = True,
        extract_images: bool = False,
    ) -> dict:
        """钉钉文档读取工具：读取指定 document_id，不做通知或任务处理。"""
        return await read_dingtalk_document(document_id, extract_tables, extract_images)

    @mcp.tool()
    async def validate_dingtalk_config_tool() -> dict:
        """钉钉配置检查工具：只验证开放平台配置。"""
        return await validate_dingtalk_config()


def main() -> None:
    if FastMCP is None:
        raise RuntimeError("Package 'mcp' is not installed. Run: pip install -r requirements.txt")
    settings = get_settings()
    transport = settings.mcp_transport
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be one of: stdio, sse, streamable-http")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
