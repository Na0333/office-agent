from pathlib import Path

import pytest

from app.config import get_settings
from app.mcp_server.tools.document_tools import (
    convert_document,
    create_document,
    process_table_data,
    summarize_document,
)


def test_summarize_text_file(tmp_path: Path):
    file_path = tmp_path / "meeting.txt"
    file_path.write_text("张三周五前完成需求文档。\n李四下周一提交测试计划。", encoding="utf-8")

    result = summarize_document(file_path=str(file_path))

    assert result["source"] == str(file_path)
    assert "张三" in result["text"]
    assert result["character_count"] > 0


def test_summarize_docx_file(tmp_path: Path):
    docx = pytest.importorskip("docx")
    file_path = tmp_path / "meeting.docx"
    document = docx.Document()
    document.add_paragraph("张三周五前完成需求文档。")
    document.add_paragraph("李四下周一提交测试计划。")
    document.save(file_path)

    result = summarize_document(file_path=str(file_path))

    assert "张三周五前完成需求文档" in result["text"]
    assert result["character_count"] > 0


def test_create_excel_document(tmp_path: Path):
    output_path = tmp_path / "report.xlsx"
    result = create_document(
        file_type="xlsx",
        content={
            "sheets": [
                {
                    "name": "Summary",
                    "headers": ["姓名", "任务"],
                    "data": [["张三", "需求文档"], ["李四", "测试计划"]],
                }
            ]
        },
        output_path=str(output_path),
    )
    assert result["success"] is True
    assert output_path.exists()


def test_create_pdf_document_with_chinese_content(tmp_path: Path):
    pytest.importorskip("reportlab")
    output_path = tmp_path / "resume.pdf"

    result = create_document(
        file_type="pdf",
        content={
            "title": "Linux运维简历",
            "paragraphs": ["附件是Linux运维简历模板，请查收。"],
            "tables": [[["姓名", "岗位"], ["张三", "Linux运维"]]],
        },
        output_path=str(output_path),
    )

    assert result["success"] is True
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_convert_document_to_pdf_uses_gotenberg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    get_settings.cache_clear()
    monkeypatch.setenv("GOTENBERG_URL", "http://gotenberg:3000")
    monkeypatch.setenv("GOTENBERG_TIMEOUT", "7")

    input_path = tmp_path / "source.docx"
    output_path = tmp_path / "source.pdf"
    input_path.write_bytes(b"fake docx bytes")

    posted = {}

    class FakeResponse:
        content = b"%PDF-1.4 fake pdf"

        def raise_for_status(self):
            return None

    def fake_post(self, url, files):
        posted["url"] = url
        posted["file_name"] = files["files"][0]
        return FakeResponse()

    monkeypatch.setattr("app.mcp_server.tools.document_tools.httpx.Client.post", fake_post)

    result = convert_document(str(input_path), str(output_path), "pdf")

    assert result["success"] is True
    assert result["converter"] == "gotenberg"
    assert posted == {
        "url": "http://gotenberg:3000/forms/libreoffice/convert",
        "file_name": "source.docx",
    }
    assert output_path.read_bytes() == b"%PDF-1.4 fake pdf"
    get_settings.cache_clear()


def test_convert_document_to_pdf_returns_gotenberg_error_without_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    get_settings.cache_clear()
    monkeypatch.setenv("GOTENBERG_URL", "http://gotenberg:3000")

    input_path = tmp_path / "source.docx"
    output_path = tmp_path / "source.pdf"
    input_path.write_bytes(b"fake docx bytes")

    def fake_post(self, url, files):
        import httpx

        raise httpx.RequestError("connection refused")

    monkeypatch.setattr("app.mcp_server.tools.document_tools.httpx.Client.post", fake_post)

    result = convert_document(str(input_path), str(output_path), "pdf")

    assert result["success"] is False
    assert "Gotenberg 请求失败" in result["error"]
    assert not output_path.exists()
    get_settings.cache_clear()


def test_process_table_analyze():
    table = [["姓名", "分数"], ["张三", "90"], ["李四", "80"]]
    result = process_table_data(table, "analyze")
    assert result["total_rows"] == 3
    assert result["total_columns"] == 2
