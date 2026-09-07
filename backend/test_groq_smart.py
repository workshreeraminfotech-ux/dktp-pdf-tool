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
    raw_lines = f.readlines()

all_deviations = []

# Chunk text config into 150-line chunks so TPM never exceeds 4,000 tokens per call
chunk_size = 150
total_chunks = min(3, (len(raw_lines) + chunk_size - 1) // chunk_size)

for c_idx in range(total_chunks):
    start_line = c_idx * chunk_size
    end_line = min(len(raw_lines), (c_idx + 1) * chunk_size)
    chunk_lines = [f"Line {i+1}: {l.strip()}" for i, l in enumerate(raw_lines[start_line:end_line], start=start_line)]
    cfg_chunk_str = "\n".join(chunk_lines)

    prompt = f"""You are a Lead DCS & Thermal Power Plant Control Systems Engineer.
Audit this chunk of Master DCS Text Configuration against the Drawing PDF content.
Identify missing operations, blocks, permissive gates, trip signals, or setpoint mismatches.

Return ONLY a JSON array:
[
  {{
    "line_number": <exact integer line number in text file>,
    "operation_name": "<tag or gate name>",
    "deviation_type": "MISSING_IN_PDF" | "LOGIC_MISMATCH" | "TIMER_MISMATCH" | "SETPOINT_MISMATCH" | "UNASSIGNED_INPUT",
    "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
    "text_file_content": "<exact text line content>",
    "drawing_expected": "<what drawing should show>",
    "explanation": "<clear explanation>",
    "drawing_page_number": 1
  }}
]

DRAWING PDF SUMMARY:
{pdf_txt[:2500]}

DCS CONFIGURATION CHUNK (Lines {start_line+1} to {end_line}):
{cfg_chunk_str}
"""

    print(f"Calling Groq AI for Chunk {c_idx+1}/{total_chunks} (Lines {start_line+1}-{end_line})...")
    try:
        res = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a specialized TPP Control Systems Logic Verification Engineer. You MUST output valid JSON array ONLY."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2048
        )
        content = res.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        parsed = json.loads(content.strip())
        print(f"Chunk {c_idx+1}: Found {len(parsed)} deviations from AI!")
        all_deviations.extend(parsed)
    except Exception as e:
        print(f"Chunk {c_idx+1} Error:", e)

print(f"\nTOTAL PURE AI DEVIATIONS: {len(all_deviations)}")
if all_deviations:
    print("Sample deviation:", json.dumps(all_deviations[0], indent=2))
