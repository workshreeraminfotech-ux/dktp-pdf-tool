import os
import json
import pymupdf
import openai
from dotenv import load_dotenv

load_dotenv()
groq_key = os.environ.get("GROQ_API_KEY", "")
client = openai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)

pdf_path = r"C:\Users\karsa\Downloads\dktp pdf files\CP100P.pdf"
txt_path = r"C:\Users\karsa\Downloads\dktp text files\CP100P.txt"

doc = pymupdf.open(pdf_path)
pdf_txt = ""
for idx, page in enumerate(doc):
    pdf_txt += f"\n--- DRAWING PAGE {idx+1} ---\n" + page.get_text()
doc.close()

with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
    raw_lines = f.readlines()[:400]

cfg_lines = [f"Line {i+1}: {l.strip()}" for i, l in enumerate(raw_lines)]
cfg_str = "\n".join(cfg_lines)

prompt = f"""You are a Lead DCS & Thermal Power Plant (TPP) Control Systems Engineer.
Audit the following Engineering Drawing PDF content against the DCS Master Text Configuration file.

Find every missing operation, missing gate, permissive, trip signal, timer mismatch, or unassigned tag that is in the Text file but omitted or deviating in the Drawing PDF.

Return ONLY a JSON array of objects with:
[
  {{
    "line_number": <exact integer line number in Text file>,
    "operation_name": "<tag or gate name>",
    "deviation_type": "MISSING_IN_PDF" | "LOGIC_MISMATCH" | "TIMER_MISMATCH" | "SETPOINT_MISMATCH" | "UNASSIGNED_INPUT",
    "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
    "text_file_content": "<the exact line content from Text file>",
    "drawing_expected": "<what drawing should show>",
    "explanation": "<clear explanation>",
    "drawing_page_number": <page 1-indexed>
  }}
]

ENGINEERING DRAWING PDF:
{pdf_txt}

DCS MASTER TEXT CONFIGURATION:
{cfg_str}
"""

print("Sending request to Groq openai/gpt-oss-120b...")
try:
    res = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a specialized TPP Control Systems Logic Verification Engineer. You MUST output valid JSON array ONLY."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=4096
    )
    content = res.choices[0].message.content.strip()
    print("GROQ RESPONSE LENGTH:", len(content))
    print(content[:500])

    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    parsed = json.loads(content.strip())
    print(f"Successfully parsed {len(parsed)} deviations from AI!")
    if parsed:
        print("Sample item 1:", json.dumps(parsed[0], indent=2))
except Exception as e:
    print("Error:", e)
