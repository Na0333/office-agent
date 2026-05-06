import re


ASSIGNEE_PATTERN = re.compile(r"(?:由|请)?(?P<assignee>[\u4e00-\u9fa5A-Za-zA-Z]{2,8})(?:负责|完成|提交|整理|准备)")
DATE_TEXT = r"今天|明天|后天|本周[一二三四五六日天]?|下周[一二三四五六日天]?|\d{1,2}月\d{1,2}日|周[一二三四五六日天]"
DATE_PATTERN = re.compile(f"({DATE_TEXT})")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def extract_todos(text: str) -> dict:
    material = _task_material(text)
    candidates = [
        line.strip(" ，,")
        for line in re.split(r"[\n。；;，,]", material)
        if line.strip()
    ]
    todos: list[dict] = []

    for line in candidates:
        if not _looks_like_todo(line):
            continue
        assignee = _extract_assignee(line)
        date_match = DATE_PATTERN.search(line)
        todos.append(
            {
                "title": _clean_title(line),
                "assignee": assignee,
                "due_date": date_match.group(0) if date_match else None,
                "description": line,
            }
        )

    if not todos and text.strip():
        todos.append(
            {
                "title": text.strip()[:80],
                "assignee": None,
                "due_date": None,
                "description": text.strip(),
            }
        )

    return {"todos": todos, "summary": f"共识别到 {len(todos)} 条待办"}


def generate_notice(todos: list[dict]) -> dict:
    if not todos:
        return {"notice": "各位同事，本次暂无明确待办事项。"}

    lines = ["各位同事，以下是本次会议形成的待办事项，请相关负责人按时推进："]
    for index, todo in enumerate(todos, start=1):
        assignee = todo.get("assignee") or "待补充"
        due_date = todo.get("due_date") or "待补充"
        lines.append(f"{index}. {todo.get('title')}；负责人：{assignee}；截止时间：{due_date}。")
    lines.append("请大家及时同步进展，如有调整请在群内说明。")
    return {"notice": "\n".join(lines)}


def generate_email(content: str) -> dict:
    parsed = parse_email_request(content)
    if parsed.get("to_addresses") or parsed.get("subject") or parsed.get("body"):
        recipients = "、".join(parsed.get("to_addresses", [])) or "待补充"
        subject = parsed.get("subject") or "待补充"
        body_text = parsed.get("body") or content.strip()
        draft = "\n".join(
            [
                f"收件人：{recipients}",
                f"主题：{subject}",
                "",
                "正文：",
                body_text,
            ]
        )
        return {
            "email": draft,
            "to_addresses": parsed.get("to_addresses", []),
            "subject": parsed.get("subject"),
            "email_body": body_text,
        }

    body = "\n".join(
        [
            "各位好：",
            "",
            "根据当前事项，整理邮件内容如下：",
            content.strip(),
            "",
            "请相关同事查看并反馈，如需调整我可以继续修改。",
            "",
            "谢谢。",
        ]
    )
    return {"email": body}


def _looks_like_todo(line: str) -> bool:
    keywords = ("负责", "完成", "提交", "整理", "准备", "跟进", "截止", "待办", "任务")
    return any(keyword in line for keyword in keywords)


def _task_material(text: str) -> str:
    for marker in ("：", ":"):
        if marker in text:
            return text.split(marker, 1)[1]
    return text


def _extract_assignee(line: str) -> str | None:
    leading = re.match(rf"^(?P<assignee>[\u4e00-\u9fa5A-Za-z]{{2,4}}?)(?=({DATE_TEXT})|负责|完成|提交|整理|准备)", line)
    if leading:
        return leading.group("assignee")

    match = ASSIGNEE_PATTERN.search(line)
    if match:
        return match.group("assignee")

    return None


def _clean_title(line: str) -> str:
    title = re.sub(r"^(请|需要|安排|会议要求|待办[:：]?)", "", line).strip()
    title = re.sub(rf"^[\u4e00-\u9fa5A-Za-z]{{2,4}}?({DATE_TEXT})?前?", "", title).strip()
    return title[:100]


def extract_email_addresses(text: str) -> list[str]:
    """Extract email addresses from text.

    Args:
        text: Text containing email addresses.

    Returns:
        List of extracted email addresses.
    """
    addresses = EMAIL_PATTERN.findall(text)
    return list(set(addresses))  # Remove duplicates


def parse_email_request(text: str) -> dict:
    """Parse common Chinese field-style email requests.

    Supported examples:
    - 收件人：a@example.com, 邮件主题：测试，内容：这是正文
    - to: a@example.com subject: Test body: Hello
    """
    addresses = extract_email_addresses(text)
    subject = _extract_field(
        text,
        labels=("邮件主题", "主题", "subject", "title"),
        stop_labels=("内容", "正文", "body", "text"),
    )
    body = _extract_field(
        text,
        labels=("内容", "正文", "body", "text"),
        stop_labels=(),
    )
    return {
        "to_addresses": addresses,
        "subject": subject,
        "body": body,
    }


def _extract_field(text: str, labels: tuple[str, ...], stop_labels: tuple[str, ...]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    stop_pattern = "|".join(re.escape(label) for label in stop_labels)
    if stop_pattern:
        pattern = rf"(?:{label_pattern})\s*[：:=]\s*(.*?)(?=\s*[,，;；]\s*(?:{stop_pattern})\s*[：:=]|\s*(?:{stop_pattern})\s*[：:=]|$)"
    else:
        pattern = rf"(?:{label_pattern})\s*[：:=]\s*(.*)$"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    value = match.group(1).strip()
    return value.strip(" ,，;；") or None
