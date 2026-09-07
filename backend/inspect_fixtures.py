import os
import fitz # PyMuPDF
import json

pdf_dir = r"C:\Users\karsa\Downloads\dktp pdf files"
txt_dir = r"C:\Users\karsa\Downloads\dktp text files"

print("--- Inspecting Sample Files ---")
sample_pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
sample_txts = [f for f in os.listdir(txt_dir) if f.endswith('.txt')]

print(f"Found {len(sample_pdfs)} PDFs: {sample_pdfs[:6]}")
print(f"Found {len(sample_txts)} TXTs: {sample_txts[:6]}")

# Inspect CP100R.pdf
sample_pdf_path = os.path.join(pdf_dir, "CP100R.pdf")
if os.path.exists(sample_pdf_path):
    doc = fitz.open(sample_pdf_path)
    print(f"\n[PDF CP100R] Page count: {len(doc)}")
    for page_idx in range(min(3, len(doc))):
        page = doc[page_idx]
        text = page.get_text("text")
        words = page.get_text("words") # x0, y0, x1, y1, word, block_no, line_no, word_no
        drawings = page.get_drawings()
        print(f"Page {page_idx+1}: {len(words)} words, {len(drawings)} vector drawing shapes, rect={page.rect}")
        # Sample first few words with coordinates
        print(f"  First 10 words with coords:")
        for w in words[:10]:
            print(f"    '{w[4]}' bbox=({w[0]:.1f}, {w[1]:.1f}, {w[2]:.1f}, {w[3]:.1f})")
        print(f"  Sample page text snippet:\n{text[:300]}")

# Inspect CP100R.txt
sample_txt_path = os.path.join(txt_dir, "CP100R.txt")
if os.path.exists(sample_txt_path):
    with open(sample_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    print(f"\n[TXT CP100R] Total lines: {len(lines)}")
    # Count blocks
    block_names = []
    for line in lines:
        if line.strip().startswith("NAME   ="):
            block_names.append(line.strip().split("=")[1].strip())
    print(f"Found {len(block_names)} blocks in CP100R.txt. Sample blocks: {block_names[:10]}")
