from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi import HTTPException

from app.capabilities import build_capabilities
from app.config import get_settings
from app.database.db import init_db
from app.schemas.message import ChatRequest, ChatResponse, HealthResponse, UploadResponse
from app.services.file_record_service import FileRecordService

app = FastAPI(title="Office Agent", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="office-agent")


@app.get("/capabilities")
def capabilities() -> dict:
    return build_capabilities()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()

    if settings.enable_agent_brain:
        # Brain mode: autonomous agent with planning and memory
        try:
            from app.agent.core import OfficeAgent
            agent = OfficeAgent()
            return await agent.handle_message(request)
        except ImportError as e:
            return ChatResponse(
                session_id=request.session_id,
                reply=f"Agent大脑模式启用失败：{str(e)}，已回退到工具模式。",
                intent="error",
                need_confirmation=False,
                tool_results=[],
            )
    else:
        # Tool mode: pure MCP tools, let external LLM orchestrate
        return ChatResponse(
            session_id=request.session_id,
            reply="Office Agent 已切换为 MCP 工具服务模式。请让外部 LLM 直接调用 MCP 工具完成任务。",
            intent="mcp_tools_only",
            need_confirmation=False,
            tool_results=[],
        )


@app.post("/files/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    platform: str = Form(default="web"),
    user_id: str | None = Form(default=None),
    session_id: str | None = Form(default=None),
) -> UploadResponse:
    settings = get_settings()
    target_dir = settings.resolved_upload_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / file.filename
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail=f"文件超过 {settings.max_file_size_mb}MB 限制")
    file_path.write_bytes(content)
    if user_id and session_id:
        records = FileRecordService()
        next_number = len(records.list_records(session_id, user_id)) + 1
        records.upsert_record(
            file_id=f"f{next_number}",
            session_id=session_id,
            user_id=user_id,
            file_name=file.filename,
            file_path=str(file_path),
            source=platform or "upload",
        )
    return UploadResponse(
        file_name=file.filename,
        file_path=str(file_path),
        mime_type=file.content_type,
        size=len(content),
    )
