from typing import Any

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    data: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    error: str | None = None

