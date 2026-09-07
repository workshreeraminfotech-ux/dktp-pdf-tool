import os
import re
import pymupdf
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image
import io
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from backend.app.schemas.types import BoundingBox
from backend.app.core.parser.normalizer import TagNormalizer

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPID_OCR = True
    ocr_engine = RapidOCR()
except Exception as e:
    HAS_RAPID_OCR = False
    ocr_engine = None

@dataclass
class PDFWord:
    text: str
    bbox: BoundingBox
    page_number: int
    confidence: float = 1.0

@dataclass
class PDFExtractedObject:
    object_id: str
    object_type: str # "SIGNAL", "BLOCK", "GATE", "TIMER", "SETPOINT", "INPUT", "OUTPUT", "EQUIPMENT", "NOTE"
    raw_text: str
    normalized_text: str
    page_number: int
    bbox: BoundingBox
    associated_block: Optional[str] = None
    pin_number: Optional[str] = None
    value: Optional[str] = None
    confidence: float = 1.0

@dataclass
class PDFPageResult:
    page_number: int
    width: float
    height: float
    is_scanned: bool
    text_content: str
    words: List[PDFWord] = field(default_factory=list)
    objects: List[PDFExtractedObject] = field(default_factory=list)
    image_count: int = 0
    drawing_count: int = 0

class PDFUnderstandingEngine:
    """
    Multi-Level PDF Understanding & Extraction Engine.
    Layer 1: Native PDF text & bounding box extraction
    Layer 2: Vector & logic symbol object recognition
    Layer 3: Scanned page detection & RapidOCR fallback with coordinate projection
    Layer 4: Signal, Gate, Timer, and Setpoint entity extraction
    """

    LOGIC_GATE_KEYWORDS = ["AND", "OR", "NOT", "NAND", "NOR", "XOR", "SR", "RS", "FLIP-FLOP", "LATCH"]
    TIMER_REGEX = r'(?:TON|TOFF|DON|DOFF|TIMER|DELAY)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:S|SEC|MS|MIN|HR)?|(\d+(?:\.\d+)?)\s*(?:SEC|SECS|SECONDS|MS|MIN)\b'
    SETPOINT_REGEX = r'(?:HIGH|LOW|TRIP|SETPOINT|SPT|ALARM|HLIM|LLIM)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)'
    TAG_REGEX = r'\b([A-Z0-9]{2,12}(?:[-_:][A-Z0-9]{2,12})+|[A-Z]{2,6}\d{3,8}[A-Z0-9]*)\b'

    def __init__(self, normalizer: Optional[TagNormalizer] = None):
        self.normalizer = normalizer or TagNormalizer()

    def process_pdf(self, pdf_path: str, max_pages: Optional[int] = None) -> List[PDFPageResult]:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        pages_to_process = min(total_pages, max_pages) if max_pages else total_pages

        page_results: List[PDFPageResult] = []
        for page_idx in range(pages_to_process):
            p = doc[page_idx]
            res = self._process_single_page(p, page_idx + 1)
            page_results.append(res)

        doc.close()
        return page_results

    def _process_single_page(self, page: pymupdf.Page, page_num: int) -> PDFPageResult:
        rect = page.rect
        width, height = rect.width, rect.height
        
        # Extract native words
        raw_words = page.get_text("words") # (x0, y0, x1, y1, word, block_no, line_no, word_no)
        images = page.get_images()
        drawings = page.get_drawings()
        
        is_scanned = len(raw_words) < 5 and len(images) > 0

        words_list: List[PDFWord] = []
        full_text_lines: List[str] = []

        if is_scanned and HAS_RAPID_OCR and ocr_engine and page_num <= 5:
            # Render page to image with optimized scaling (0.65x) for ultra-fast OCR (~45 DPI)
            zoom = 0.65
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            pil_img = Image.open(io.BytesIO(img_bytes))
            np_img = np.array(pil_img)

            ocr_results, _ = ocr_engine(np_img)
            if ocr_results:
                for line in ocr_results:
                    dt_box, text, score = line
                    x_coords = [p[0] / zoom for p in dt_box]
                    y_coords = [p[1] / zoom for p in dt_box]
                    bx0, bx1 = min(x_coords), max(x_coords)
                    by0, by1 = min(y_coords), max(y_coords)

                    full_text_lines.append(text)
                    words_list.append(PDFWord(
                        text=text.strip(),
                        bbox=BoundingBox(x0=bx0, y0=by0, x1=bx1, y1=by1, width=bx1-bx0, height=by1-by0),
                        page_number=page_num,
                        confidence=float(score)
                    ))
        else:
            for w in raw_words:
                text = w[4].strip()
                if not text:
                    continue
                bbox = BoundingBox(x0=w[0], y0=w[1], x1=w[2], y1=w[3], width=w[2]-w[0], height=w[3]-w[1])
                words_list.append(PDFWord(
                    text=text,
                    bbox=bbox,
                    page_number=page_num,
                    confidence=1.0
                ))
            full_text_lines = [page.get_text("text")]

        # Group words into engineering objects
        objects = self._extract_engineering_objects(words_list, page_num, width, height)

        return PDFPageResult(
            page_number=page_num,
            width=width,
            height=height,
            is_scanned=is_scanned,
            text_content="\n".join(full_text_lines),
            words=words_list,
            objects=objects,
            image_count=len(images),
            drawing_count=len(drawings)
        )

    def _extract_engineering_objects(self, words: List[PDFWord], page_num: int, page_w: float, page_h: float) -> List[PDFExtractedObject]:
        objects: List[PDFExtractedObject] = []
        obj_count = 0

        # Pass 1: Scan for individual words matching tags, gates, setpoints
        for idx, w in enumerate(words):
            text_up = w.text.strip().upper()
            
            # Logic Gates
            if text_up in self.LOGIC_GATE_KEYWORDS:
                obj_count += 1
                objects.append(PDFExtractedObject(
                    object_id=f"P{page_num}_OBJ_{obj_count}",
                    object_type="GATE",
                    raw_text=w.text,
                    normalized_text=text_up,
                    page_number=page_num,
                    bbox=w.bbox,
                    value=text_up,
                    confidence=w.confidence
                ))
                continue

            # Check if text is a Tag / Signal (e.g. DIR38125, ACWP-2, 10PAB50, BI04, BO01)
            tag_matches = re.findall(self.TAG_REGEX, text_up)
            if tag_matches or any(c.isalnum() for c in text_up) and len(text_up) >= 3:
                norm = self.normalizer.normalize(text_up)
                if norm and not self.normalizer.is_spare_or_unused(text_up):
                    obj_count += 1
                    sem = self.normalizer.classify_semantics(text_up)
                    objects.append(PDFExtractedObject(
                        object_id=f"P{page_num}_OBJ_{obj_count}",
                        object_type="SIGNAL" if not sem else f"SIGNAL_{sem}",
                        raw_text=w.text,
                        normalized_text=norm,
                        page_number=page_num,
                        bbox=w.bbox,
                        value=text_up,
                        confidence=w.confidence
                    ))

        # Pass 2: Merge adjacent words on same line for multi-word labels (e.g. "STANDBY SELECTED", "120 SEC", "TRIP HIGH")
        for i in range(len(words) - 1):
            w1 = words[i]
            w2 = words[i+1]
            # If same horizontal line and close proximity
            if abs(w1.bbox.y0 - w2.bbox.y0) < 5 and 0 <= (w2.bbox.x0 - w1.bbox.x1) < 15:
                combo_text = f"{w1.text} {w2.text}".strip()
                combo_up = combo_text.upper()
                merged_bbox = BoundingBox(
                    x0=min(w1.bbox.x0, w2.bbox.x0),
                    y0=min(w1.bbox.y0, w2.bbox.y0),
                    x1=max(w1.bbox.x1, w2.bbox.x1),
                    y1=max(w1.bbox.y1, w2.bbox.y1),
                    width=max(w1.bbox.x1, w2.bbox.x1) - min(w1.bbox.x0, w2.bbox.x0),
                    height=max(w1.bbox.y1, w2.bbox.y1) - min(w1.bbox.y0, w2.bbox.y0)
                )

                # Check timer
                timer_m = re.search(self.TIMER_REGEX, combo_up)
                if timer_m:
                    obj_count += 1
                    t_val = timer_m.group(1) or timer_m.group(2)
                    objects.append(PDFExtractedObject(
                        object_id=f"P{page_num}_OBJ_{obj_count}",
                        object_type="TIMER",
                        raw_text=combo_text,
                        normalized_text=f"{t_val}S",
                        page_number=page_num,
                        bbox=merged_bbox,
                        value=t_val,
                        confidence=min(w1.confidence, w2.confidence)
                    ))

                # Check setpoint
                spt_m = re.search(self.SETPOINT_REGEX, combo_up)
                if spt_m:
                    obj_count += 1
                    s_val = spt_m.group(1)
                    objects.append(PDFExtractedObject(
                        object_id=f"P{page_num}_OBJ_{obj_count}",
                        object_type="SETPOINT",
                        raw_text=combo_text,
                        normalized_text=s_val,
                        page_number=page_num,
                        bbox=merged_bbox,
                        value=s_val,
                        confidence=min(w1.confidence, w2.confidence)
                    ))

                # Check multi-word semantics (e.g. STANDBY SELECTED, RUN FEEDBACK, TRIP SIGNAL)
                sem = self.normalizer.classify_semantics(combo_up)
                if sem:
                    obj_count += 1
                    objects.append(PDFExtractedObject(
                        object_id=f"P{page_num}_OBJ_{obj_count}",
                        object_type=f"SIGNAL_{sem}",
                        raw_text=combo_text,
                        normalized_text=self.normalizer.normalize(combo_up),
                        page_number=page_num,
                        bbox=merged_bbox,
                        value=combo_up,
                        confidence=min(w1.confidence, w2.confidence)
                    ))

        return objects
