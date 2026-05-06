# LLM Service for agent brain

import os
import json
import logging
from typing import Optional, Dict, Any
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service for agent reasoning and content generation."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.model = settings.llm_model

        if not self.api_key:
            logger.warning("No LLM API key configured, agent will use rule-based logic")

    async def answer_office_question(self, question: str) -> str:
        """Answer office-related questions using DeepSeek."""
        if not self.api_key:
            return "我可以帮您处理文档、邮件、任务等办公事务。请问需要什么帮助？"

        try:
            prompt = f"""你是一个专业的办公助手，请回答以下办公相关问题。
如果问题不属于办公范畴，请礼貌地说明你只能处理办公事务。

问题：{question}

请用中文回答，提供实用的办公建议。"""

            response = await self._call_llm(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "抱歉，暂时无法提供智能回答。请告诉我具体需要什么帮助。"

    async def extract_structured_data(self, text: str, schema: dict) -> dict:
        """Extract structured data from text using LLM."""
        if not self.api_key:
            return {}

        try:
            prompt = f"""请从以下文本中提取结构化数据，输出JSON格式：

文本内容：
{text}

请按照以下schema提取：
{json.dumps(schema, ensure_ascii=False, indent=2)}

只输出JSON，不要其他内容。"""

            response = await self._call_llm(prompt)
            # Try to parse JSON response
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response}")
                return {}
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {}

    async def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call DeepSeek API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    raise Exception(f"API call failed: {response.status_code}")
                
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Unexpected LLM response format: {data}")
                    raise Exception("Invalid response format")
                    
        except httpx.TimeoutException:
            logger.error("LLM API call timed out")
            raise Exception("API call timed out")
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise