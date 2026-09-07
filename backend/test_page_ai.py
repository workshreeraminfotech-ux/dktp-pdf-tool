import pymupdf, json, os, re
from rapidocr_onnxruntime import RapidOCR
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('.env')

groq_key = os.getenv('GROQ_API_KEY')
client = OpenAI(base_url='https://api.groq.com/openai/v1', api_key=groq_key)

ocr = RapidOCR()
pdf_path = 'backend/storage/uploads/CP100P.pdf'
txt_path = 'backend/storage/uploads/CP100P.txt'

doc = pymupdf.open(pdf_path)
with open(txt_path, 'r', errors='ignore') as f:
    cfg_text = f.read()

print(f'PDF Pages: {len(doc)}, Config Size: {len(cfg_text)} bytes')

# Test pages 4, 5, 8
for pno in [3, 4, 7]:
    page = doc[pno]
    pix = page.get_pixmap(dpi=150)
    res, _ = ocr(pix.tobytes('png'))
    words = [r[1] for r in res] if res else []
    page_ocr_text = ' '.join(words)
    
    # Match config blocks
    matching_lines = []
    for line in cfg_text.splitlines():
        if any(k in line for k in ['ACWP', 'CWP', 'DON', 'M01', 'M06', 'M08', 'STOP', 'TRIP', 'FLOW', 'VALVE', 'BEAR']):
            matching_lines.append(line.strip())
            if len(matching_lines) >= 80:
                break
                
    cfg_snippet = '\n'.join(matching_lines[:80])
    
    prompt = f"""You are a Lead DCS & Thermal Power Plant Control Systems Logic Engineer.
Analyze Drawing PDF Page {pno+1} against the DCS Master Configuration.

DRAWING PAGE {pno+1} CONTENT:
{page_ocr_text}

DCS MASTER TEXT CONFIGURATION:
{cfg_snippet}

Identify every deviation, missing gate, timer difference (DON), setpoint (M01), or signal discrepancy on this page.

Return ONLY a JSON array of objects with the exact schema:
[
  {{
    "page_number": {pno+1},
    "deviation": "<Block or Tag Name, e.g. ACWP2T>",
    "deviation_description": "<Clear explanation of the deviation comparing Drawing vs TXT>",
    "deviation_solution": "<Exact action/fix required to resolve the deviation>"
  }}
]
"""
    try:
        ai_res = client.chat.completions.create(
            model='openai/gpt-oss-120b',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1
        )
        content = ai_res.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        items = json.loads(content.strip())
        print(f"\n================ PAGE {pno+1} RESULT ({len(items)} items) ================")
        for it in items:
            p_no = it.get('page_number')
            dev = it.get('deviation', '').encode('ascii', errors='replace').decode('ascii')
            desc = it.get('deviation_description', '').encode('ascii', errors='replace').decode('ascii')
            sol = it.get('deviation_solution', '').encode('ascii', errors='replace').decode('ascii')
            print(f"Page: {p_no} | Deviation: {dev}")
            print(f"Description: {desc}")
            print(f"Solution:    {sol}\n")
    except Exception as e:
        print(f"Error on page {pno+1}: {e}")
