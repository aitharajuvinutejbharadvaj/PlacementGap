from __future__ import annotations

from typing import Any


def parse_document(file_bytes: bytes, kind: str) -> dict[str, Any]:
    if kind == "text":
        text = file_bytes.decode("utf-8", "replace")
        return {"text": text, "records": [{"text": text, "char_span": [0, len(text)]}]}
    if kind == "pdf":
        try:
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
            return {"text": text, "records": [{"text": text, "char_span": [0, len(text)]}]}
        except Exception as e:
            raise ValueError(f"PDF extraction failed (OCR unavailable): {e}") from e
    if kind == "docx":
        try:
            import io

            from docx import Document

            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs)
            return {"text": text, "records": [{"text": text, "char_span": [0, len(text)]}]}
        except Exception as e:
            raise ValueError(f"DOCX extraction failed: {e}") from e
    raise ValueError(f"unsupported document kind: {kind}")
