"""钉钉开放平台 API 服务"""
import time
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class DingTalkService:
    """钉钉开放平台 API 服务类"""

    TOKEN_EXPIRE_BUFFER_SECONDS = 300  # 提前 5 分钟刷新

    def __init__(self) -> None:
        self.settings = get_settings()
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    @property
    def is_configured(self) -> bool:
        return self.settings.is_dingtalk_configured

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """获取 access_token，带内存缓存和自动刷新"""
        if force_refresh:
            self._access_token = None
            self._token_expires_at = 0.0

        # 检查缓存是否有效
        if self._access_token and time.time() < self._token_expires_at - self.TOKEN_EXPIRE_BUFFER_SECONDS:
            return self._access_token

        if not self.is_configured:
            raise ValueError("钉钉应用未配置 DINGTALK_APP_KEY 或 DINGTALK_APP_SECRET")

        # 调用钉钉 API 获取 token
        url = f"{self.settings.dingtalk_api_base_url}/oauth2/access_token"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={
                "appkey": self.settings.dingtalk_app_key,
                "appsecret": self.settings.dingtalk_app_secret,
            })
            response.raise_for_status()
            data = response.json()

        if data.get("errcode") != 0:
            raise RuntimeError(f"钉钉 API 错误: {data.get('errmsg', '未知错误')}")

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200)
        return self._access_token

    async def read_document(
        self,
        document_id: str,
        extract_tables: bool = True,
        extract_images: bool = False,
    ) -> dict[str, Any]:
        """读取钉钉在线文档内容

        Args:
            document_id: 钉钉文档 ID（通常在文档 URL 中可以找到）
            extract_tables: 是否提取表格
            extract_images: 是否提取图片引用

        Returns:
            与 read_document 返回格式一致的字典
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "钉钉应用未配置",
                "content": None,
            }

        try:
            token = await self.get_access_token()

            # 调用钉钉文档 API 获取文档内容
            url = f"{self.settings.dingtalk_api_base_url}/document/v1/documents/{document_id}/raw_content"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    url,
                    headers={"x-acs-dingtalk-access-token": token},
                    params={"documentVersion": "v1"},
                )
                response.raise_for_status()
                data = response.json()

            if data.get("errcode") != 0:
                return {
                    "success": False,
                    "error": f"钉钉文档 API 错误: {data.get('errmsg', '未知错误')}",
                    "content": None,
                }

            # 解析并转换为统一格式
            content = self._parse_content(
                data.get("data", {}),
                extract_tables=extract_tables,
                extract_images=extract_images,
            )

            return {
                "success": True,
                "file_path": document_id,
                "file_name": data.get("data", {}).get("title", f"钉钉文档_{document_id}"),
                "file_type": ".dingtalk",
                "content": content,
                "metadata": {
                    "source": "dingtalk",
                    "document_id": document_id,
                    "url": data.get("data", {}).get("url"),
                },
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"钉钉 API HTTP 错误: {e}")
            return {"success": False, "error": f"钉钉 API 请求失败: {str(e)}", "content": None}
        except Exception as e:
            logger.error(f"读取钉钉文档异常: {e}")
            return {"success": False, "error": str(e), "content": None}

    def _parse_content(
        self,
        api_data: dict[str, Any],
        extract_tables: bool = True,
        extract_images: bool = False,
    ) -> dict[str, Any]:
        """将钉钉 API 返回数据解析为统一格式

        钉钉文档返回的内容结构可能包含:
        - blocks: 文档块列表（段落、标题、表格等）
        - markdown: Markdown 格式文本
        - html: HTML 格式文本
        """
        result = {
            "text_content": [],
            "tables": [],
            "images": [],
            "metadata": {},
        }

        if not api_data:
            return result

        # 解析 blocks 结构
        blocks = api_data.get("blocks", [])
        for block in blocks:
            block_type = block.get("block_type", block.get("type", ""))

            if block_type in ("text", "paragraph", "p"):
                text = block.get("text", block.get("content", ""))
                if text:
                    result["text_content"].append({
                        "type": "paragraph",
                        "text": text,
                        "block_id": block.get("block_id"),
                    })

            elif block_type in ("heading", "h1", "h2", "h3"):
                text = block.get("text", block.get("content", ""))
                if text:
                    result["text_content"].append({
                        "type": block_type,
                        "text": text,
                        "block_id": block.get("block_id"),
                    })

            elif block_type in ("table", "tbl"):
                if extract_tables:
                    table_data = block.get("cells", [])
                    if table_data:
                        result["tables"].append({
                            "rows": len(table_data),
                            "columns": len(table_data[0]) if table_data else 0,
                            "data": table_data,
                            "block_id": block.get("block_id"),
                        })

            elif block_type in ("image", "img"):
                if extract_images:
                    result["images"].append({
                        "url": block.get("url", block.get("src", "")),
                        "block_id": block.get("block_id"),
                    })

        # 如果有 markdown 内容，直接提取
        if not result["text_content"] and api_data.get("markdown"):
            result["text_content"].append({
                "type": "paragraph",
                "text": api_data["markdown"],
            })

        result["metadata"] = {
            "document_id": api_data.get("document_id"),
            "title": api_data.get("title"),
            "version": api_data.get("version"),
            "blocks_count": len(blocks),
        }

        return result
