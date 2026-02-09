import PyPDF2
import docx


def extract_text(file_path):
    """
    Extract text from PDF, DOCX, or TXT files
    """
    text = ""

    if file_path.endswith(".pdf"):
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""

    elif file_path.endswith(".docx"):
        document = docx.Document(file_path)
        for para in document.paragraphs:
            text += para.text + "\n"

    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    return text.strip()
