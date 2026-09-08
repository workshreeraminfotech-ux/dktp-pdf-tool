# pyrefly: ignore [missing-import]
import pymupdf
import numpy as np
from PIL import Image
import io
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()
doc = pymupdf.open(r"C:\Users\karsa\Downloads\dktp pdf files\CP100P.pdf")
print("Total pages in CP100P.pdf:", len(doc))

for pno in [0, 3, 4, 5, 6, 7]:
    if pno < len(doc):
        page = doc[pno]
        pix = page.get_pixmap(dpi=100)
        pil_img = Image.open(io.BytesIO(pix.tobytes("png")))
        np_img = np.array(pil_img)
        res, _ = ocr(np_img)
        texts = [r[1] for r in res] if res else []
        print(f"\n--- PAGE {pno+1} OCR ({len(texts)} words) ---")
        print(" ".join(texts[:20]))
