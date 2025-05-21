import pymupdf


def extract_pdf_text(file_path):
    doc = pymupdf.open(file_path)
    text = ""
    for page in doc:
        text = page.get_text().encode("utf8")  # get plain text (is in UTF-8)
    doc.close()
    return text
