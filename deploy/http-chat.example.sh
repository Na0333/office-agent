#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

curl -sS -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "external-tool",
    "user_id": "u001",
    "session_id": "external-demo-001",
    "content": "请把会议纪要整理成待办并生成通知：张三周五前完成需求文档，李四下周一提交测试计划。"
  }'
