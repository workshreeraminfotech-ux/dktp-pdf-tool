import os
import pymupdf
from typing import List, Dict, Optional
from PIL import Image
import io

from backend.app.schemas.types import DeviationItem, SeverityLevel
from backend.app.config import SNIPPETS_DIR, PROCESSED_DIR

class PDFVisualAnnotator:
    """
    PyMuPDF-powered PDF Visual Annotation & Snippet Cropping Engine.
    Draws non-destructive color-coded deviation highlights, badge tags (e.g. DEV-001),
    and crops high-resolution evidence snippets for split-screen inspection.
    """

    COLOR_MAP = {
        SeverityLevel.CRITICAL: (0.9, 0.1, 0.1),      # Crimson Red
        SeverityLevel.HIGH: (1.0, 0.45, 0.0),         # Vivid Orange
        SeverityLevel.MEDIUM: (0.85, 0.65, 0.0),      # Amber Gold
        SeverityLevel.LOW: (0.15, 0.55, 0.9),         # Blue
        SeverityLevel.INFO: (0.45, 0.45, 0.55)        # Neutral Slate
    }

    def annotate_pdf(
        self,
        input_pdf_path: str,
        output_pdf_path: str,
        deviations: List[DeviationItem],
        generate_snippets: bool = True
    ) -> Dict[str, str]:
        """
        Creates an annotated copy of the original PDF with visual bounding boxes,
        deviation IDs, and generates cropped image snippets.
        Returns a dict mapping deviation_id -> snippet_relative_path.
        """
        snippet_paths: Dict[str, str] = {}
        doc = pymupdf.open(input_pdf_path)

        # Group deviations by page number (1-indexed)
        devs_by_page: Dict[int, List[DeviationItem]] = {}
        for dev in deviations:
            p_num = dev.page_number
            devs_by_page.setdefault(p_num, []).append(dev)

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            if page_num not in devs_by_page:
                continue

            page = doc[page_idx]
            page_rect = page.rect
            page_devs = devs_by_page[page_num]

            # Render complete page pixmap once for both web viewer and snippet cropping
            page_png_path = os.path.join(str(PROCESSED_DIR), f"page_{os.path.splitext(os.path.basename(output_pdf_path))[0]}_{page_num}.png")
            page_pix = page.get_pixmap(dpi=144)
            page_pix.save(page_png_path)
            
            # Load page image into PIL for instant O(1) in-memory snippet crops
            scale = 144.0 / 72.0  # ratio of pixmap pixels to PDF points
            pil_page = Image.open(io.BytesIO(page_pix.tobytes("png")))

            for dev in page_devs:
                coords = dev.pdf_evidence.coordinates
                if not coords:
                    continue

                # Ensure valid rectangle within page boundaries
                x0 = max(0.0, coords.x0 - 4)
                y0 = max(0.0, coords.y0 - 4)
                x1 = min(page_rect.width, coords.x1 + 4)
                y1 = min(page_rect.height, coords.y1 + 4)
                
                # If width or height is too small, expand for visibility
                if (x1 - x0) < 20:
                    x1 = x0 + 25
                if (y1 - y0) < 12:
                    y1 = y0 + 15

                rect = pymupdf.Rect(x0, y0, x1, y1)
                color = self.COLOR_MAP.get(dev.severity, (1.0, 0.45, 0.0))

                # 1. Draw highlighting rectangle
                highlight = page.add_rect_annot(rect)
                highlight.set_colors(stroke=color)
                highlight.set_border(width=2.0)
                highlight.set_info(
                    title=f"[{dev.deviation_number}] {dev.type.value}",
                    content=f"Severity: {dev.severity.value}\nPDF: {dev.pdf_expected}\nConfig: {dev.config_actual}\n\n{dev.explanation}"
                )
                highlight.update()

                # 2. Draw badge text above the bounding box
                badge_text = f"[{dev.deviation_number}]"
                badge_point = pymupdf.Point(x0, max(12.0, y0 - 3))
                page.insert_text(
                    badge_point,
                    badge_text,
                    fontsize=8,
                    color=color,
                    render_mode=0
                )

                # 3. Generate high-resolution evidence snippet crop instantly from PIL page
                if generate_snippets:
                    snippet_filename = f"{dev.id}.png"
                    snippet_full_path = os.path.join(str(SNIPPETS_DIR), snippet_filename)
                    
                    crop_x0 = max(0, int((x0 - 40) * scale))
                    crop_y0 = max(0, int((y0 - 40) * scale))
                    crop_x1 = min(pil_page.width, int((x1 + 40) * scale))
                    crop_y1 = min(pil_page.height, int((y1 + 40) * scale))
                    
                    crop_img = pil_page.crop((crop_x0, crop_y0, crop_x1, crop_y1))
                    crop_img.save(snippet_full_path, format="PNG")
                    
                    dev.pdf_evidence.snippet_url = f"/api/files/snippets/{snippet_filename}"
                    snippet_paths[dev.id] = snippet_filename

        # Also render pages that didn't have deviations
        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page_png_path = os.path.join(str(PROCESSED_DIR), f"page_{os.path.splitext(os.path.basename(output_pdf_path))[0]}_{page_num}.png")
            if not os.path.exists(page_png_path):
                page = doc[page_idx]
                page_pix = page.get_pixmap(dpi=144)
                page_pix.save(page_png_path)

        # Save annotated PDF
        doc.save(output_pdf_path)
        doc.close()

        return snippet_paths
