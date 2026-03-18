from pathlib import Path

from docx import Document


def build_docx(file_path: str, title: str, content: str) -> str:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    document = Document()
    document.add_heading(title, level=1)
    for paragraph in content.split("\n\n"):
        cleaned = paragraph.strip()
        if cleaned:
            document.add_paragraph(cleaned)
    document.save(path)
    return str(path)

