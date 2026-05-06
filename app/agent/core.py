# Office Agent with Brain Mode
# This module provides autonomous agent capabilities when ENABLE_AGENT_BRAIN=true

from app.config import get_settings
from app.schemas.message import ChatRequest, ChatResponse
from app.services.memory_service import MemoryService
from app.database.db import get_connection
import json
import logging

logger = logging.getLogger(__name__)

class OfficeAgent:
    """Autonomous office agent with planning, memory, and tool orchestration."""

    def __init__(self):
        self.settings = get_settings()
        self.memory_service = MemoryService()
        # Initialize components based on available services
        self._init_components()

    def _init_components(self):
        """Initialize agent components."""
        # Memory system
        from app.agent.memory import MemoryStore
        self.memory = MemoryStore(self.memory_service)

        # Tool client for MCP tools
        from app.mcp_client.client import MCPToolClient
        self.tools = MCPToolClient()

        # LLM service if available
        try:
            from app.services.llm_service import LLMService
            self.llm = LLMService()
        except ImportError:
            self.llm = None
            logger.warning("LLMService not available, agent will use rule-based logic")

    async def handle_message(self, request: ChatRequest) -> ChatResponse:
        """Handle user message with autonomous agent logic."""
        try:
            # Get or create session memory
            memory = self.memory.get(request.session_id, request.user_id)
            memory.history.append({"role": "user", "content": request.content})

            # Handle /office prefix for direct execution
            content = request.content.strip()
            bypass_confirmation = False
            if content.startswith("/office"):
                bypass_confirmation = True
                request.content = content[len("/office"):].strip()
                request.force_execute = True

            # Basic intent recognition and tool orchestration
            response = await self._process_request(request, bypass_confirmation)

            # Save memory
            memory.history.append({"role": "assistant", "content": response.reply})
            self.memory.save(request.session_id, request.user_id)

            return response

        except Exception as e:
            logger.error(f"Agent error: {e}")
            return ChatResponse(
                session_id=request.session_id,
                reply=f"Agent处理出错：{str(e)}",
                intent="error",
                need_confirmation=False,
                tool_results=[]
            )

    async def _process_request(self, request: ChatRequest, bypass_confirmation: bool) -> ChatResponse:
        """Process request with basic agent logic."""
        content = request.content.lower()

        # Simple intent matching
        if "创建" in content or "生成" in content or "create" in content:
            return await self._handle_document_create(request)
        elif "读取" in content or "read" in content:
            return await self._handle_document_read(request)
        elif request.file and any(keyword in content for keyword in ["文档", "文件", "处理"]):
            return await self._handle_document_read(request)
        elif "发送" in content or "邮件" in content or "send" in content:
            return await self._handle_email_send(request, bypass_confirmation)
        elif "任务" in content or "待办" in content or "task" in content:
            return await self._handle_task_management(request, bypass_confirmation)
        else:
            # Default to LLM answer if available
            if self.llm:
                answer = await self.llm.answer_office_question(request.content)
                return ChatResponse(
                    session_id=request.session_id,
                    reply=answer,
                    intent="office_qa",
                    need_confirmation=False,
                    tool_results=[]
                )
            else:
                return ChatResponse(
                    session_id=request.session_id,
                    reply="我可以帮您处理文档读取、创建、邮件发送、任务管理等办公事务。请告诉我具体需要什么帮助。",
                    intent="unknown",
                    need_confirmation=False,
                    tool_results=[]
                )

    async def _handle_document_read(self, request: ChatRequest) -> ChatResponse:
        """Handle document reading requests."""
        if not request.file or not request.file.file_path:
            return ChatResponse(
                session_id=request.session_id,
                reply="请先上传文档文件，然后告诉我需要读取的内容。",
                intent="document_read",
                need_confirmation=False,
                tool_results=[]
            )

        # Use document reading tool
        from app.mcp_server.tools.document_tools import read_document
        result = read_document(
            file_path=request.file.file_path,
            extract_tables=True,
            extract_images=False
        )

        if result.get("error"):
            reply = f"文档读取失败：{result['error']}"
        else:
            content_preview = result.get("content", "无内容")
            if isinstance(content_preview, dict):
                if "text" in content_preview:
                    content_preview = content_preview["text"]
                elif "text_content" in content_preview:
                    items = content_preview["text_content"]
                    if isinstance(items, list):
                        content_preview = "\n".join(
                            item.get("text", "") if isinstance(item, dict) else str(item)
                            for item in items[:10]
                        )
                    else:
                        content_preview = str(items)
                else:
                    import json as _json
                    content_preview = _json.dumps(content_preview, ensure_ascii=False)
            reply = f"文档读取完成：{str(content_preview)[:500]}..."

        return ChatResponse(
            session_id=request.session_id,
            reply=reply,
            intent="document_read",
            need_confirmation=False,
            tool_results=[result]
        )

    async def _handle_document_create(self, request: ChatRequest) -> ChatResponse:
        """Handle document creation requests."""
        # Simple document creation logic
        content = {
            "title": "自动生成文档",
            "paragraphs": [request.content]
        }

        from app.mcp_server.tools.document_tools import create_document
        result = create_document(
            file_type="docx",
            content=content,
            output_path=f"data/files/generated_{request.session_id}.docx"
        )

        return ChatResponse(
            session_id=request.session_id,
            reply=f"文档创建完成：{result.get('file_path', '未知路径')}",
            intent="document_create",
            need_confirmation=False,
            tool_results=[result]
        )

    async def _handle_email_send(self, request: ChatRequest, bypass_confirmation: bool) -> ChatResponse:
        """Handle email sending requests."""
        if not bypass_confirmation:
            return ChatResponse(
                session_id=request.session_id,
                reply="需要发送邮件，请回复'确认'来执行。",
                intent="email_send",
                need_confirmation=True,
                tool_results=[]
            )

        # Extract email content and send
        from app.mcp_server.tools.text_tools import extract_email_addresses, generate_email
        email_content = generate_email(request.content)
        to_addresses = extract_email_addresses(request.content) or ["recipient@example.com"]

        from app.mcp_server.tools.email_tools import send_email
        result = await send_email(
            to_addresses=to_addresses,
            subject=email_content.get("subject", "办公邮件"),
            body=email_content.get("body", request.content),
        )

        return ChatResponse(
            session_id=request.session_id,
            reply=f"邮件发送结果：{result.get('message', '完成')}",
            intent="email_send",
            need_confirmation=False,
            tool_results=[result]
        )

    async def _handle_task_management(self, request: ChatRequest, bypass_confirmation: bool) -> ChatResponse:
        """Handle task management requests."""
        if not bypass_confirmation:
            return ChatResponse(
                session_id=request.session_id,
                reply="需要创建任务，请回复'确认'来执行。",
                intent="task_create",
                need_confirmation=True,
                tool_results=[]
            )

        # Extract and create tasks
        from app.mcp_server.tools.text_tools import extract_todos
        todos = extract_todos(request.content)

        if todos:
            from app.mcp_server.tools.task_tools import create_tasks
            result = create_tasks(request.session_id, todos)
            return ChatResponse(
                session_id=request.session_id,
                reply=f"已创建 {len(todos)} 个任务",
                intent="task_create",
                need_confirmation=False,
                tool_results=[result]
            )
        else:
            return ChatResponse(
                session_id=request.session_id,
                reply="未检测到待办事项",
                intent="task_create",
                need_confirmation=False,
                tool_results=[]
            )
