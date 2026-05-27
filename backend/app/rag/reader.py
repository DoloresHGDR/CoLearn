import fitz
import docx
import os

# Lee archivos PDF, DOCX y TXT y devuelve su contenido como texto plano
def read_file(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    # PDF
    if extension == ".pdf":
        text = ""
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        return text

    # DOCX
    elif extension == ".docx":
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    # TXT
    elif extension == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    # ERROR
    else:
        raise ValueError("Formato no soportado")