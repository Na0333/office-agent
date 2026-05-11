<div align="center">

# Office Agent

**MCP 驱动的多平台办公协同智能体**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

让 AI 自动处理你的会议纪要、待办任务、文档转换、邮件发送和跨平台通知。

[快速开始](#快速开始) | [功能特性](#功能特性) | [集成指南](#集成指南) | [文档](#文档)

</div>

---

## 它能做什么

你把一段会议纪要丢给它：

> 张三周五前完成需求文档，李四下周一提交测试计划

它会自动帮你：

1. 提取待办事项，识别负责人和截止时间
2. 将待办写入任务数据库
3. 生成群通知草稿
4. 草拟一封正式邮件
5. 等你确认后发送到钉钉群 / 企业微信群 / 邮箱

整个过程通过 **MCP 协议** 标准化封装，可以接入 AstrBot、Claude Desktop 或任何支持 MCP 的 AI 客户端。

## 功能特性

| 能力 | 描述 |
|:-----|:-----|
| **会议纪要 → 待办** | 自动解析文本，提取任务、负责人、截止时间 |
| **文档处理** | 读取/创建/转换 Word、Excel、PDF、TXT |
| **表格分析** | 对 Excel 数据做筛选、排序、透视、统计 |
| **邮件发送** | SMTP 支持 QQ、Gmail、Outlook、企业邮箱 |
| **跨平台通知** | Webhook 推送到钉钉、企业微信、飞书 |
| **钉钉文档** | 读取钉钉在线文档内容 |
| **任务管理** | 创建、查询待办任务，SQLite 持久化 |
| **安全确认** | 敏感操作（发邮件/发通知/写任务）需用户确认才执行 |

## 架构

```
用户
 ↓  (QQ / 钉钉 / 企业微信 / Web)
AstrBot
 ↓
Office Agent (FastAPI :8000 / MCP Server :8010)
 ├── Agent Core — 意图识别、任务编排、上下文记忆
 ├── MCP Tools  — 文档、任务、邮件、通知等标准化工具
 └── SQLite     — 任务持久化
```

**两种运行模式：**

| 模式 | 配置 | 说明 |
|:-----|:-----|:-----|
| **MCP Tools** (默认) | `ENABLE_AGENT_BRAIN=false` | 作为工具服务器，由外部 AI 客户端编排调用 |
| **Agent Brain** | `ENABLE_AGENT_BRAIN=true` | 内置自主 Agent，独立完成意图识别和任务规划 |

## 快速开始

### 1. 安装

```bash
git clone https://github.com/xiaokeji/office-agent.git
cd office-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填入最少配置：

```env
DATABASE_PATH=data/office_agent.db
```

### 2. 启动

```bash
# 初始化数据库
python -c "from app.database.db import init_db; init_db()"

# 启动 MCP 服务（默认端口 8010）
python -m app.mcp_server.server

# 或启动 HTTP API 服务（默认端口 8000）
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 验证

```bash
curl http://localhost:8000/health
# → {"status": "ok", "service": "office-agent"}
```

### Docker 一键启动

```bash
docker compose up -d mcp          # 仅 MCP 服务
docker compose --profile api up -d # MCP + API
```

> 也可以运行 `python init.py` 进入交互式配置菜单，适合新手。

## 使用示例

### HTTP API 调用

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "web",
    "user_id": "u001",
    "session_id": "s001",
    "content": "请把会议纪要整理成待办并生成通知：张三周五前完成需求文档，李四下周一提交测试计划。"
  }'
```

返回：

```json
{
  "session_id": "s001",
  "reply": "已提取出以下待办：\n1. 完成需求文档（负责人：张三，截止：周五）\n2. 提交测试计划（负责人：李四，截止：下周一）\n\n通知草稿：...",
  "intent": "meeting_todos_and_notice",
  "need_confirmation": true
}
```

### MCP 工具调用

在任何 MCP 客户端中，可以直接调用单个工具：

```json
{
  "name": "extract_todos_tool",
  "arguments": {
    "text": "张三周五前完成需求文档，李四下周一提交测试计划。"
  }
}
```

### 文件上传 + 文档处理

```bash
# 上传文件
curl -X POST http://localhost:8000/files/upload \
  -F "file=@meeting.xlsx" -F "platform=web" -F "user_id=u001" -F "session_id=s001"

# 在 /chat 中引用已上传的文件
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "web",
    "user_id": "u001",
    "session_id": "s001",
    "content": "读取这个表格并按负责人汇总",
    "file": {"file_name": "meeting.xlsx", "file_path": "data/files/meeting.xlsx"}
  }'
```

## 集成指南

### 接入 AstrBot

在 AstrBot 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "office-agent": {
      "command": "python",
      "args": ["-m", "app.mcp_server.server"],
      "env": {
        "PYTHONPATH": "/path/to/office-agent",
        "DATABASE_PATH": "/path/to/office-agent/data/office_agent.db"
      }
    }
  }
}
```

AstrBot 的 LLM 会自动发现并调用 Office Agent 提供的工具。

### 接入 Claude Desktop / 其他 MCP 客户端

```json
{
  "mcpServers": {
    "office-agent": {
      "type": "streamable-http",
      "url": "http://your-server:8010/mcp"
    }
  }
}
```

### 作为 HTTP API 集成

任何能发 HTTP 请求的系统都可以调用：

```python
import httpx

resp = httpx.post("http://your-server:8000/chat", json={
    "platform": "external",
    "user_id": "u001",
    "session_id": "session-001",
    "content": "请总结今天的工作进展"
})
print(resp.json())
```

## MCP 工具清单

Office Agent 提供以下标准化 MCP 工具，外部 AI 客户端可按需调用：

**文档类**
- `summarize_document_tool` — 文档摘要
- `read_document_tool` — 读取文档内容（Word/Excel/PDF/TXT）
- `create_document_tool` — 创建文档
- `convert_document_tool` — 格式转换

**任务类**
- `extract_todos_tool` — 从文本提取待办
- `create_tasks_tool` — 写入任务数据库
- `query_task_status_tool` — 查询任务状态

**写作类**
- `generate_notice_tool` — 生成群通知草稿
- `generate_email_tool` — 生成邮件草稿

**通信类**
- `send_email_tool` — 发送邮件（SMTP）
- `send_platform_notice_tool` — 发送跨平台通知（Webhook）
- `list_notice_channels_tool` — 列出通知通道

**表格类**
- `process_table_data_tool` — 筛选/排序/透视/统计

**钉钉类**
- `read_dingtalk_document_tool` — 读取钉钉在线文档
- `validate_dingtalk_config_tool` — 验证钉钉配置

**Agent 类**
- `office_agent_chat_tool` — 调用完整 Agent 流程

> 标记为敏感操作的工具（`create_tasks`、`send_email`、`send_platform_notice`）必须传 `confirmed=true` 才会真正执行。

## 配置说明

完整配置见 [`.env.example`](.env.example)，以下是关键项：

### 核心配置

| 变量 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `MCP_TRANSPORT` | `streamable-http` | MCP 传输模式：`stdio` / `streamable-http` |
| `MCP_PORT` | `8010` | MCP 服务端口 |
| `PORT` | `8000` | HTTP API 端口 |
| `ENABLE_AGENT_BRAIN` | `false` | 是否启用自主 Agent 模式 |
| `DATABASE_PATH` | `data/office_agent.db` | SQLite 数据库路径 |

### LLM 配置（Agent Brain 模式需要）

| 变量 | 说明 |
|:-----|:-----|
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | API 地址，默认 `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称，默认 `deepseek-chat` |

### SMTP 邮件配置（可选）

| 邮件服务 | `SMTP_HOST` | `SMTP_PORT` | TLS | STARTTLS |
|:---------|:------------|:------------|:----|:---------|
| QQ 邮箱 | `smtp.qq.com` | 465 | true | false |
| Gmail | `smtp.gmail.com` | 587 | false | true |
| Outlook | `smtp.office365.com` | 587 | false | true |

配置后运行 `python setup_email.py` 可进入交互式向导，或 `python diagnose_email.py` 诊断问题。

### 跨平台通知（可选）

在 `.env` 中配置 `NOTICE_CHANNELS`（JSON 格式），支持钉钉、企业微信、飞书的群机器人 Webhook。

## 目录结构

```
office-agent/
├── app/
│   ├── main.py                   # FastAPI 入口
│   ├── config.py                 # 配置管理
│   ├── capabilities.py           # 能力清单
│   ├── agent/                    # Agent 核心
│   │   ├── core.py               # 主控
│   │   ├── planner.py            # 意图识别
│   │   └── memory.py             # 上下文记忆
│   ├── mcp_server/
│   │   └── server.py             # MCP Server 入口
│   ├── services/                 # 业务服务
│   │   ├── document_service.py   # 文档处理
│   │   ├── task_service.py       # 任务管理
│   │   ├── email_service.py      # 邮件发送
│   │   └── notice_service.py     # 通知推送
│   ├── database/                 # 数据库层
│   └── schemas/                  # 数据模式
├── data/                         # 运行时数据（SQLite、上传文件）
├── deploy/                       # 部署配置模板
├── docs/                         # 开发文档
├── tests/                        # 测试用例
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行特定模块
pytest tests/test_document_tools.py -v
pytest tests/test_email_service.py -v
pytest tests/test_mcp_tools.py -v
pytest tests/test_task_service.py -v
```

## 部署

### Docker Compose（推荐）

```bash
docker compose up -d mcp              # MCP 服务
docker compose --profile api up -d     # MCP + API
```

### systemd 服务

参考 [`deploy/`](./deploy/) 目录下的 `.service.example` 文件：

```bash
sudo cp deploy/office-agent-api.service.example /etc/systemd/system/office-agent-api.service
sudo systemctl enable --now office-agent-api
```

### Nginx 反向代理

参考 [`deploy/reverse-proxy.nginx.example.conf`](./deploy/reverse-proxy.nginx.example.conf)。

详细部署说明见 [部署指南](./docs/部署指南.md)。

## 文档

| 文档 | 说明 |
|:-----|:-----|
| [详细开发文档](./docs/详细开发文档.md) | API 调用、MCP 工具详解、集成指南 |
| [部署指南](./docs/部署指南.md) | 服务器部署、Docker、systemd、Nginx |
| [系统架构说明](./docs/项目整体思路与系统架构说明.md) | 设计思路、架构、业务流程 |
| [对外调用与复用指南](./docs/对外调用与复用指南.md) | HTTP API + MCP Server 双入口方案 |
| [项目使用说明](./docs/项目使用说明.md) | 安装、配置、故障排除 |
| [邮箱配置指南](./docs/邮箱配置快速开始-用户指南.md) | 邮箱配置快速上手 |

## 技术栈

- **Web 框架** — [FastAPI](https://fastapi.tiangolo.com/)
- **MCP 协议** — [mcp](https://github.com/modelcontextprotocol/python-sdk) (Python SDK)
- **数据库** — SQLite
- **文档处理** — python-docx / openpyxl / pdfplumber / pypdf / reportlab
- **PDF 转制** — [Gotenberg](https://gotenberg.dev/)（可选）
- **部署** — Docker / Docker Compose / systemd

## 贡献

欢迎提交 Issue 和 Pull Request。

```bash
# 开发环境
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

## 许可证

[MIT License](./LICENSE)
