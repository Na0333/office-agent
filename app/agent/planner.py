# Agent Planning (simplified)

class IntentPlanner:
    """Simple intent planner for office tasks."""

    def plan(self, request):
        """Plan based on request content."""
        content = request.content.lower()

        if "读取" in content or "read" in content:
            return Plan(intent="document_read", steps=["read_document"], confirmation_steps=[])
        elif "创建" in content or "生成" in content:
            return Plan(intent="document_create", steps=["create_document"], confirmation_steps=[])
        elif "发送" in content or "邮件" in content:
            return Plan(intent="email_send", steps=["generate_email"], confirmation_steps=["send_email"])
        elif "任务" in content or "待办" in content:
            return Plan(intent="task_management", steps=["extract_todos"], confirmation_steps=["create_tasks"])
        else:
            return Plan(intent="office_qa", steps=["office_qa"], confirmation_steps=[])

class Plan:
    """Planning result."""

    def __init__(self, intent: str, steps: list, confirmation_steps: list = None):
        self.intent = intent
        self.steps = steps
        self.confirmation_steps = confirmation_steps or []
        self.need_confirmation = len(self.confirmation_steps) > 0