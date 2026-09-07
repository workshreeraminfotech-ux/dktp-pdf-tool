import os
import pymupdf

pdf_dir = r"C:\Users\karsa\Downloads\dktp pdf files"
sample_pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

for pdf_name in sample_pdfs:
    path = os.path.join(pdf_dir, pdf_name)
    doc = pymupdf.open(path)
    p0 = doc[0]
    words = p0.get_text("words")
    images = p0.get_images()
    drawings = p0.get_drawings()
    print(f"{pdf_name:35} | Pages: {len(doc):3} | P1 words: {len(words):4} | P1 images: {len(images):2} | P1 drawings: {len(drawings):4}")
    if len(words) > 0:
        print(f"   Sample text: {words[0][4]} ... {words[-1][4] if len(words)>1 else ''}")
