def extract_pdf_text(file_path):
    import fitz

    doc = fitz.open(file_path)
    chunks = []
    for page in doc:
        chunks.append(page.get_text())
    doc.close()
    return "".join(chunks)
