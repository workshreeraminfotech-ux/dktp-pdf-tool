import os
import json
import base64
import re
from typing import List, Dict, Optional, Any
from pathlib import Path
import pymupdf
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "backend" / ".env")

class TPPLogicAIEngine:
    """
    Thermal Power Plant (TPP) Intelligent Logic & Deviation AI Engine.
    Uses Groq Cloud LLMs (openai/gpt-oss-120b) to audit DCS/PLC text files against Drawing PDFs,
    identifying genuine logic discrepancies with page numbers and block names.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.groq_api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.client = None

        if self.groq_api_key:
            try:
                import openai
                self.client = openai.OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=self.groq_api_key,
                    timeout=30.0
                )
            except Exception as e:
                print(f"[AI_ENGINE] Groq client init error: {e}")

    def is_available(self) -> bool:
        return bool(self.client and self.groq_api_key)

    def analyze_tpp_drawing_vs_config(
        self,
        pdf_path: str,
        config_text_path: str,
        max_pages: Optional[int] = None,
        pdf_pages: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Runs full AI comparison between Drawing PDF pages and Text Configuration file.
        Produces structured deviations with PDF Page, Block/Area, and detailed Deviation description.
        """
        if not self.is_available():
            print("[AI_ENGINE] Groq API key not configured or client unavailable. Using rule-based engine.")
            return []

        # 1. Extract text from PDF pages
        pdf_pages_extracted = []

        if pdf_pages and len(pdf_pages) > 0:
            for idx, p in enumerate(pdf_pages):
                if max_pages and idx >= max_pages:
                    break
                p_words = " ".join([w.text for w in getattr(p, "words", []) if getattr(w, "text", "")])
                if p_words:
                    pdf_pages_extracted.append(f"--- DRAWING PDF PAGE {idx+1} ---\n{p_words[:500]}")

        if not pdf_pages_extracted:
            try:
                doc = pymupdf.open(pdf_path)
                total_pages = len(doc)
                for idx in range(total_pages):
                    if max_pages and idx >= max_pages:
                        break
                    page = doc[idx]
                    page_text = page.get_text().strip()
                    if page_text:
                        pdf_pages_extracted.append(f"--- DRAWING PDF PAGE {idx+1} ---\n{page_text[:500]}")
                doc.close()
            except Exception as e:
                print(f"[AI_ENGINE] Error opening PDF: {e}")

        pdf_txt = "\n\n".join(pdf_pages_extracted[:15])

        # 2. Extract block definitions & significant lines from Text Configuration
        try:
            with open(config_text_path, "r", encoding="utf-8", errors="replace") as f:
                all_raw_lines = f.readlines()
            
            cfg_samples = []
            for i, l in enumerate(all_raw_lines):
                line_str = l.strip()
                if not line_str:
                    continue
                if any(k in line_str for k in ["NAME", "TYPE", "DON", "OSP", "BI0", "BO0", "M01", "M06", "M08", "TRIP", "STOP", "START", "FLOW", "VALVE"]):
                    cfg_samples.append(f"Line {i+1}: {line_str}")
                elif len(cfg_samples) < 150:
                    cfg_samples.append(f"Line {i+1}: {line_str}")
                
                if len(cfg_samples) >= 200:
                    break

            cfg_str = "\n".join(cfg_samples[:200])
        except Exception as e:
            print(f"[AI_ENGINE] Error reading config file: {e}")
            return []

        prompt = f"""You are an Expert Lead DCS & Thermal Power Plant (TPP) Control Systems Logic Engineer.
Compare the following Engineering Drawing PDF pages against the DCS Master Text Configuration file.

Analyze every PDF page and identify all deviations, missing blocks/gates, timer mismatches (e.g. DON 120, DON 5), parameter thresholds (e.g. M01=7, M01=12, M01=90), trip/stop signals (e.g. MOTOR STOP CMD, INTERLOCK NOT ACTION, TRIP CONDITIONS), and valve feedback signals (e.g. 20% open, 90% closed).

Return ONLY a JSON array of objects with the exact schema:
[
  {{
    "page_number": <integer PDF Page number, e.g. 1, 2, 3, 4>,
    "deviation": "<Block or Tag Name, e.g. ACWP2T, ACWP2F1, CWP2A, HYDR PMP-2>",
    "deviation_description": "<Detailed, clear deviation description comparing Drawing vs TXT configuration>",
    "deviation_solution": "<Clear engineering solution / remediation to fix and align this deviation>",
    "line_number": <estimated integer line number in Text file or 1>,
    "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  }}
]

ENGINEERING DRAWING PDF CONTENT (BY PAGE):
{pdf_txt}

DCS MASTER TEXT CONFIGURATION SNIPPET:
{cfg_str}
"""

        # Primary model is openai/gpt-oss-120b which is validated and supported
        models_to_try = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama3-70b-8192"]
        
        for model_name in models_to_try:
            content = ""
            try:
                print(f"[AI_ENGINE] Requesting Groq AI analysis ({model_name})...")
                res = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a specialized TPP Control Systems Logic Verification Engineer. You MUST output ONLY valid JSON array with no extra markdown formatting or conversational text."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=4096
                )
                content = res.choices[0].message.content.strip()

                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]

                deviations = json.loads(content.strip())
                if isinstance(deviations, list) and len(deviations) > 0:
                    print(f"[AI_ENGINE] Successfully parsed {len(deviations)} pure AI deviations using {model_name}!")
                    return deviations
            except Exception as e:
                print(f"[AI_ENGINE] Model {model_name} failed: {e}")
                if content:
                    try:
                        match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                        if match:
                            deviations = json.loads(match.group(0))
                            print(f"[AI_ENGINE] Extracted {len(deviations)} deviations via regex")
                            return deviations
                    except Exception as e2:
                        print(f"[AI_ENGINE] Regex fallback failed: {e2}")

        return []
