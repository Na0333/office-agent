# MCP 驱动的多平台办公协同智能体

该项目是一个面向 AstrBot + MCP 场景的办公 Agent 后端系统。第一版目标是跑通：

```text
用户消息 -> Agent 意图识别 -> 工具编排 -> 待办/通知/邮件草稿 -> 用户确认 -> 执行记录
```

## 两种运行模式

Office Agent 支持两种运行模式，可以通过 `ENABLE_AGENT_BRAIN` 配置切换：

### 🧠 大脑模式 (`ENABLE_AGENT_BRAIN=true`)

启用完整的自主Agent，具有：
- 意图识别和任务规划
- 会话记忆和上下文管理
- AI 工具推理和决策
- 工具编排和执行
- 用户确认流程

**适用场景**：
- 作为独立聊天机器人
- 需要复杂任务编排的场景
- 原型演示和测试

**配置**：
```bash
echo "ENABLE_AGENT_BRAIN=true" >> .env
echo "DEEPSEEK_API_KEY=your-key" >> .env
```

### 🔧 纯工具模式 (`ENABLE_AGENT_BRAIN=false`) - 默认

作为MCP工具服务器，让外部 AI 工具编排：
- 提供标准化办公工具
- 外部客户端负责决策和编排
- 避免与平台AI工具冲突
- 更好的集成性

**适用场景**：
- 与 AstrBot 等客户端集成
- 作为工具增强现有 AI 应用
- 生产环境部署

**配置**：
```bash
echo "ENABLE_AGENT_BRAIN=false" >> .env  # 或不设置（默认false）
```

## 目录结构

```text
office-agent/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── agent/
│   ├── database/
│   ├── mcp_client/
│   ├── mcp_server/
│   ├── schemas/
│   └── services/
├── data/
│   └── files/
├── tests/
├── requirements.txt
└── README.md
```

## AI 工具接入位置

根据运行模式，AI 工具接入位置不同：

### 大脑模式下的 AI 工具接入

当 `ENABLE_AGENT_BRAIN=true` 时，Agent 内部使用 AI 工具进行推理：

```env
# DeepSeek API（推荐）
DEEPSEEK_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 或其他比赛允许的 AI 工具接口
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama2:7b
```

### 纯工具模式下的 AI 工具接入

当 `ENABLE_AGENT_BRAIN=false` 时，AI 工具在外部（AstrBot 等客户端）：

- **AstrBot 集成**：在 AstrBot 的 MCP 配置中接入，无需额外 AI 工具配置
- **本地 MCP 客户端**：在客户端的 MCP 设置中接入
- **其他 MCP 客户端**：配置指向 Office Agent 的 MCP 端点

这种模式下，Office Agent 作为工具提供者，AI 工具推理在客户端进行，避免冲突。

### 推荐配置

| 场景 | ENABLE_AGENT_BRAIN | AI 工具配置位置 | 优势 |
|---|---|---|---|
| AstrBot 插件 | `false` | AstrBot 侧 | 避免冲突，无缝集成 |
| 独立演示 | `true` | Office Agent 侧 | 完整自主能力 |
| 本地 MCP 客户端 | `false` | 客户端侧 | 标准化工具集成 |
| API 服务 | `true` | Office Agent 侧 | 自主 API 服务 |

### 📧 邮件功能配置（可选）

Office Agent 内置邮件发送功能，配置非常简单。选择以下任一方式：

#### 🎯 方式1：一键配置（推荐！最快速）

```bash
python init.py
```

这会打开一个友好的菜单界面，可以：
- 📧 交互式配置邮箱
- 🔍 诊断配置问题
- 🧪 快速测试功能
- 📚 查看文档

#### 📝 方式2：交互式向导

如果只想配置邮箱：

```bash
python setup_email.py
```

逐步完成配置：
1. 选择邮箱提供商（QQ / Gmail / Outlook / 企业邮等）
2. 输入邮箱地址
3. 输入授权码（系统会自动告诉你如何获取）
4. 验证配置
5. 自动保存到 `.env`

#### 🔧 方式3：手动配置

编辑 `.env` 文件：

```bash
cp .env.example .env
nano .env  # 编辑配置
```

QQ 邮箱配置示例：
```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USERNAME=your-email@qq.com
SMTP_PASSWORD=your-auth-code
SMTP_USE_TLS=true
SMTP_USE_STARTTLS=false
```

#### ✅ 验证配置

```bash
python diagnose_email.py
```

会自动检查：
- ✅ .env 文件
- ✅ SMTP 连接
- ✅ 邮件发送
- ✅ Agent 集成
- 💡 提供修复建议

详见 [📧 邮箱配置快速开始](./docs/邮箱配置快速开始-用户指南.md)

测试：

```bash
curl http://127.0.0.1:8000/health
```

查看对外能力清单：

```bash
curl http://127.0.0.1:8000/capabilities
```

## 对外调用与复用

本项目现在定位为 MCP 办公工具服务：

| 入口 | 适用对象 | 说明 |
|---|---|---|
| MCP Server | AstrBot MCP、自研 Agent 及其他支持 MCP 协议的客户端 | 推荐入口。由外部客户端决策，直接调用文档、待办、邮件、通知等单一职责工具 |
| HTTP API | 健康检查、能力描述、文件上传 | `/chat` 仅保留兼容提示，不再做 Agent 编排 |

MCP stdio 模式适合同机/同容器工具调用：

```bash
PYTHONPATH=/Users/xiaokeji/Agent/office-agent \
DATABASE_PATH=/Users/xiaokeji/Agent/office-agent/data/office_agent.db \
MCP_TRANSPORT=stdio \
/Users/xiaokeji/Agent/office-agent/.venv/bin/python -m app.mcp_server.server
```

MCP Streamable HTTP 模式适合服务器部署和远程工具调用：

```bash
PYTHONPATH=/AstrBot/data/office-agent \
DATABASE_PATH=/AstrBot/data/office-agent/data/office_agent.db \
MCP_TRANSPORT=streamable-http \
MCP_HOST=0.0.0.0 \
MCP_PORT=8010 \
/AstrBot/data/office-agent/.venv/bin/python -m app.mcp_server.server
```

远程 MCP 地址：

```text
http://服务器IP:8010/mcp
```

AstrBot MCP 会看到单一职责工具：
`list_notice_channels_tool`、`send_platform_notice_tool`、`send_email_tool`、
`read_document_tool`、`extract_todos_tool` 等。

详细说明见 [对外调用与复用指南](./docs/对外调用与复用指南.md)，部署模板见 `deploy/` 目录。


### PDF 转制（Gotenberg）

服务器已部署 Gotenberg 后，配置 `GOTENBERG_URL` 即可让 `convert_document_tool` 和 PDF 创建流程优先走 Gotenberg：

```bash
# 宿主机进程运行
GOTENBERG_URL=http://127.0.0.1:3000

# Docker 容器调用同机已映射端口的 Gotenberg
GOTENBERG_URL=http://host.docker.internal:3000
OFFICE_AGENT_FONT_DIR=/usr/local/share/fonts/office-agent
OFFICE_AGENT_DOCX_FONT="Noto Serif CJK SC"
```

Gotenberg 镜像会安装 `fonts-noto-cjk`、`fonts-noto-cjk-extra`、文泉驿字体，并加载仓库根目录 `gotenberg/fonts` 中的自定义字体；`office-agent/docker-compose.yml` 也会把同一目录挂载到应用容器，供 ReportLab PDF 兜底使用。

调用工具时保持原参数即可：`input_path`、`output_path`、`target_format=pdf`。

### 基础示例

整理会议纪要成待办并生成通知：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "web",
    "user_id": "u001",
    "session_id": "s001",
    "content": "请把这段会议纪要整理成待办，并生成通知：张三周五前完成需求文档，李四下周一提交测试计划。"
  }'
```

### 邮件发送示例

发送邮件到指定收件人（需配置SMTP）：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "web",
    "user_id": "u001",
    "session_id": "s001",
    "content": "整理会议纪要成待办并发送邮件到 zhangsan@company.com：张三周五前完成需求文档，李四下周一提交测试计划。"
  }'
```

## 后续开发重点

1. ✅ 邮件发送功能已实现 - 独立SMTP邮件服务，支持多种邮箱配置
2. 把 AstrBot 消息转发到 `/chat`。
3. 将已有"Office 助手"插件中的工具完整封装为 Agent 可调用工具。
4. 完善 `extract_todos`、`create_task`、`generate_notice` 的高级特性。
5. 增加用户确认后的真实发送能力。
6. 增加操作日志、权限控制和异常处理。

## 文档处理（读写/转换/表格）

新增文档能力已集成到 Agent 流程，支持：

- 读取：Word(`.docx`)、Excel(`.xlsx/.xlsm`)、PDF、文本
- 生成：Word、Excel、PDF、文本；PDF 优先通过 Gotenberg 转换，保留版式
- 转换：Word/Excel 等转 PDF 调用 Gotenberg HTTP API
- 表格处理：筛选、排序、透视、分析

### 上传文档

```bash
curl -X POST http://127.0.0.1:8000/files/upload \
  -F "file=@/path/to/meeting.xlsx"
```

返回 `file_path` 后，可通过 `/chat` 传入：

```json
{
  "platform": "web",
  "user_id": "u001",
  "session_id": "s-doc-001",
  "content": "请读取这个文档并提取表格",
  "file": {
    "file_name": "meeting.xlsx",
    "file_path": "data/files/meeting.xlsx"
  }
}
```

也支持结构化参数（推荐，避免在 `content` 里拼 JSON）：

```json
{
  "platform": "web",
  "user_id": "u001",
  "session_id": "s-doc-002",
  "content": "请创建文档",
  "document_action": {
    "action": "create_document",
    "file_type": "xlsx",
    "output_path": "data/files/monthly_report.xlsx",
    "content": {
      "sheets": [
        {
          "name": "Summary",
          "headers": ["姓名", "任务"],
          "data": [["张三", "需求文档"], ["李四", "测试计划"]]
        }
      ]
    }
  }
}
```

### 生成文档示例

`content` 中包含 JSON 负载即可触发创建：

```text
请生成word文档 {"file_type":"docx","output_path":"data/files/notice.docx","content":{"title":"周会纪要","paragraphs":["本周目标已同步。"]}}
```

### 会话文件命令（对齐 `/doc` 工作流）

- `/doc list`：列出当前会话已上传文件（带 `f1/f2` ID）
- `/doc clear`：清空当前会话文件
- `/doc clear f1`：删除指定文件ID
- `/doc use f1 f2 根据这些文件整理成周报`：选定文件并继续执行任务
- `/doc resend f1`：查询并重发历史文件（基于持久化文件索引）
- `/doc cleanup`：清理失效文件索引记录

上传时可附带会话信息自动登记到 `/doc`：

```bash
curl -X POST http://127.0.0.1:8000/files/upload \
  -F "file=@/path/to/meeting.docx" \
  -F "platform=web" \
  -F "user_id=u001" \
  -F "session_id=s001"
```

### Word 四段式流程（create/add/finalize/export）

通过 `document_action.action` 使用：

- `create_document`：创建草稿
- `add_blocks`：添加段落/表格块
- `finalize_document`：锁定草稿
- `export_document`：导出为 `docx`

## 📚 文档

- [📧 邮箱配置快速开始](./docs/邮箱配置快速开始-用户指南.md) - 用户配置指南（新手必读 ⭐⭐⭐⭐⭐）
- [📧 邮件发送功能使用指南](./docs/邮件发送功能使用指南.md) - 完整的邮件功能文档
- [📖 邮件功能实现总结](./docs/邮件功能实现总结.md) - 技术实现细节
- [📖 邮件功能-项目结构变化](./docs/邮件功能-项目结构变化.md) - 项目修改说明
- [📋 邮件功能-完成清单](./docs/邮件功能-完成清单.md) - 完成检查清单

## 🚀 快速命令

### 💡 新手推荐（首次使用）

```bash
# 🎯 一键启动配置菜单（推荐！）
python init.py
```

提供交互式菜单：
- 📧 交互式邮箱配置
- 🔍 配置诊断检查
- 🧪 快速测试功能
- 📚 文档导航
- 🚀 启动 Agent 服务

### 📧 邮件配置工具

```bash
# 交互式配置向导（最推荐）
python setup_email.py

# 配置诊断和故障排除
python diagnose_email.py

# 快速功能测试
python test_email_quick.py
```

### 🧪 测试命令

```bash
# 运行单元测试
pytest tests/test_email_service.py -v

# 运行集成测试
pytest tests/test_email_integration.py -v
```

### 🚀 启动服务

```bash
# 启动 Agent 服务
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 健康检查
curl http://127.0.0.1:8000/health
```
# office-agent
