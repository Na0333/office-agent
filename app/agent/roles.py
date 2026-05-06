# Agent Roles (simplified stubs)

class CoordinatorAgent:
    def __init__(self, planner):
        self.planner = planner

    def plan(self, request):
        return self.planner.plan(request)

class DocumentAgent:
    def __init__(self, tools):
        self.tools = tools

    async def summarize(self, request):
        # Stub implementation
        return {"tool_name": "summarize_document", "success": True, "data": {"summary": "文档摘要"}}

    async def read_document(self, request, extract_tables, extract_images):
        # Stub implementation
        return {"tool_name": "read_document", "success": True, "data": {"content": "文档内容"}}

class TaskAgent:
    def __init__(self, tools, llm):
        self.tools = tools
        self.llm = llm

    async def extract_todos(self, material):
        # Stub implementation
        return {"tool_name": "extract_todos", "success": True, "data": {"todos": []}}

    async def create_tasks(self, request, todos):
        # Stub implementation
        return {"tool_name": "create_tasks", "success": True, "data": {"created_count": len(todos)}}

class WriterAgent:
    def __init__(self, tools):
        self.tools = tools

    async def generate_notice(self, todos):
        # Stub implementation
        return {"tool_name": "generate_notice", "success": True, "data": {"notice": "通知内容"}}

    async def generate_email(self, content):
        # Stub implementation
        return {"tool_name": "generate_email", "success": True, "data": {"subject": "邮件主题", "body": "邮件内容"}}

class SafetyAgent:
    def build_pending_action(self, **kwargs):
        # Stub implementation
        return {"confirmation_steps": [], "tool_results": []}