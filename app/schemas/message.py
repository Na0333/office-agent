from pydantic import BaseModel, Field


class FileRef(BaseModel):
    file_name: str | None = None
    file_path: str | None = None
    mime_type: str | None = None


class DocumentAction(BaseModel):
    action: str | None = None
    file_type: str | None = None
    output_path: str | None = None
    input_path: str | None = None
    target_format: str | None = None
    content: dict = Field(default_factory=dict)
    table_data: list[list] = Field(default_factory=list)
    operation: str | None = None
    options: dict = Field(default_factory=dict)
    extract_tables: bool = True
    extract_images: bool = False
    draft_id: str | None = None
    blocks: list[dict] = Field(default_factory=list)


class ChatRequest(BaseModel):
    platform: str = Field(default="web", description="Source platform: web, dingtalk, wecom, qq")
    user_id: str
    session_id: str
    content: str
    group_id: str | None = None
    message_id: str | None = None
    file: FileRef | None = None
    document_action: DocumentAction | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    need_confirmation: bool = False
    tool_results: list[dict] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str


class UploadResponse(BaseModel):
    file_name: str
    file_path: str
    mime_type: str | None = None
    size: int

