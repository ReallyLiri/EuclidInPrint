def use_pdf2image():
    import pytesseract
    from pdf2image import convert_from_path

    pages = convert_from_path("EiP.pdf", 600)
    text_data = ''

    for i in range(len(pages)):
        text = pytesseract.image_to_string(pages[i])
        text_data += text + '\n'
        print(text)

    with open('EiP_v2.txt', 'w') as f:
        f.write(text_data)


def use_pypdf2():
    from PyPDF2 import PdfReader
    reader = PdfReader("EiP.pdf")
    text_data = ''
    for page in reader.pages:
        print(page.extract_text())
        text_data += page.extract_text() + '\n'

    with open('EiP_v1.txt', 'w') as f:
        f.write(text_data)


# use_pdf2image()
use_pypdf2()
