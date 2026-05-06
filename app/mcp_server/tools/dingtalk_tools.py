"""钉钉在线文档 MCP 工具"""
from app.services.dingtalk_service import DingTalkService


async def read_dingtalk_document(
    document_id: str,
    extract_tables: bool = True,
    extract_images: bool = False,
) -> dict:
    """读取钉钉在线文档内容

    Args:
        document_id: 钉钉文档 ID（可以从文档 URL 中提取，如 https://xxx.dingtalk.com/doc/d/XXXXX 中的 XXXXX）
        extract_tables: 是否提取表格数据，默认 True
        extract_images: 是否提取图片引用，默认 False

    Returns:
        与 read_document 格式一致的字典，包含 file_path, file_name, file_type, content, metadata
    """
    service = DingTalkService()

    if not service.is_configured:
        return {
            "success": False,
            "error": "钉钉应用未配置。请设置 DINGTALK_APP_KEY 和 DINGTALK_APP_SECRET 环境变量。",
            "content": None,
        }

    return await service.read_document(
        document_id=document_id,
        extract_tables=extract_tables,
        extract_images=extract_images,
    )


async def validate_dingtalk_config() -> dict:
    """验证钉钉配置是否正确

    尝试获取 access_token 来验证 AppKey 和 AppSecret 是否有效
    """
    service = DingTalkService()

    if not service.is_configured:
        return {
            "valid": False,
            "error": "钉钉应用未配置 DINGTALK_APP_KEY 或 DINGTALK_APP_SECRET",
        }

    try:
        token = await service.get_access_token()
        return {
            "valid": True,
            "message": "钉钉配置验证成功",
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"钉钉配置验证失败: {str(e)}",
        }
