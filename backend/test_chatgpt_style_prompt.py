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
pdf_summary_lines = []
for idx in range(len(doc)):
    page = doc[idx]
    txt = page.get_text().strip()
    if txt:
        pdf_summary_lines.append(f"[PAGE {idx+1}]: {txt[:300]}")
    else:
        # Drawing object count
        drawings = len(page.get_drawings())
        images = len(page.get_images())
        pdf_summary_lines.append(f"[PAGE {idx+1}]: Schematic Diagram Page (Drawings: {drawings}, Images: {images})")
doc.close()

pdf_summary_text = "\n".join(pdf_summary_lines)

with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
    raw_lines = f.readlines()[:300]

cfg_lines = [f"Line {i+1}: {l.strip()}" for i, l in enumerate(raw_lines)]
cfg_str = "\n".join(cfg_lines)

prompt = f"""You are a Lead DCS & Thermal Power Plant (TPP) Control Systems Engineer.
Audit the following Engineering Drawing PDF against the Master DCS Configuration Text File.

Analyze the logic page-by-page and find all deviations, including:
1. Timer differences (e.g. 120s, 5s, 4s, 2s, 30s delays)
2. Block parameters (e.g. M01=7, M01-M08=90, M01=12 thresholds)
3. Signal connections (e.g. MOTOR STOP CMD, INTERLOCK NOT ACTION, OPERATOR STOP, TRIP CONDITIONS -> BO08)
4. Valve feedback and permissives (e.g. 20% open, 90% closed feedback)
5. Missing logic blocks or unassigned gates

Return ONLY a JSON array of objects with:
[
  {{
    "drawing_page_number": <exact integer page number 1 to 25>,
    "operation_name": "<block or area name, e.g. ACWP2T, ACWP2F1, CWP2A, CWP2P, HYDR PMP-2>",
    "deviation_type": "LOGIC_MISMATCH" | "MISSING_IN_PDF" | "TIMER_MISMATCH" | "SETPOINT_MISMATCH" | "SIGNAL_MISMATCH",
    "severity": "CRITICAL" | "HIGH" | "MEDIUM",
    "text_file_content": "<exact line content from DCS text file>",
    "drawing_expected": "<what the drawing schematic shows or should show>",
    "explanation": "<detailed, comprehensive engineering explanation formatted like ChatGPT table>",
    "line_number": <exact integer line number in DCS text file>
  }}
]

DRAWING PDF PAGES OVERVIEW:
{pdf_summary_text}

DCS MASTER CONFIGURATION:
{cfg_str}
"""

print("Executing AI Logic Audit...")
try:
    res = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a Lead TPP Control Systems Engineer. Always output valid JSON array ONLY with detailed engineering deviation explanations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=4096
    )
    content = res.choices[0].message.content.strip()
    if content.startswith("```json"): content = content[7:]
    if content.startswith("```"): content = content[3:]
    if content.endswith("```"): content = content[:-3]
    
    parsed = json.loads(content.strip())
    print(f"\nSuccessfully generated {len(parsed)} deviations in ChatGPT table format!")
    print("\n| PDF Page | Block / Area | Deviation | Line in Text |")
    print("|---|---|---|---|")
    for d in parsed:
        print(f"| **{d.get('drawing_page_number')}** | **{d.get('operation_name')}** | {d.get('explanation')} | Line {d.get('line_number')} |")
except Exception as e:
    print("Error:", e)
