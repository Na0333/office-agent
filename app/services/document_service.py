from pathlib import Path

from app.mcp_server.tools.document_tools import extract_document_text

class DocumentService:
    def extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)
        return extract_document_text(path)
