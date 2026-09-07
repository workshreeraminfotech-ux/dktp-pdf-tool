# Deviation Intelligence 🔍⚡
### Automated Industrial Control-System Deviation Detection & PDF Highlighting Platform

**Deviation Intelligence** is a production-quality, generic engineering platform that eliminates the manual burden of comparing engineering drawings (PDFs) against control system configuration export files (TXT, CSV, JSON, XML).

The system extracts spatial text, symbols, logic gates, setpoints, and connections from drawings, parses structured DCS/PLC configurations (Foxboro/EcoStruxure, ABB, Siemens, Emerson DeltaV, etc.), executes 24+ industrial deviation detectors, and draws interactive, color-coded visual highlights **directly onto the original PDF**.

---

## 🌟 Key Capabilities

1. **Non-Destructive PDF Visual Highlighting**: Renders color-coded vector bounding boxes and `[DEV-001]` badges directly onto the original PDF.
2. **24+ Industrial Deviation Detectors**:
   - Missing / Extra Signals
   - Logic Gate Mismatches (`AND` vs `OR`, `NOT`, latches)
   - Timer Duration Discrepancies (e.g., 120s vs 60s, delay / debounce)
   - Setpoint & Alarm Limits (High, Low, Trip limits)
   - Standby / Duty Selection Differences (e.g., Standby selected in drawing vs unassigned `0` in configuration)
   - Spare vs Configured Channel Inconsistencies
   - Permissive & Interlock Mismatches
3. **Multi-Level PDF Understanding**: Native PyMuPDF spatial vector extraction with automatic RapidOCR fallback for scanned drawings.
4. **Universal Configuration Parser**: Generic key-value, block compound, XML, JSON, and CSV parser preserving exact line numbers for 100% traceability.
5. **Interactive Split-Screen SaaS Viewer**:
   - Page thumbnails with deviation count badges
   - Zoom, pan, and prev/next deviation navigation
   - Side-by-side evidence inspector with 180 DPI visual snippet crops
   - Human-in-the-loop audit actions (Confirm, Reject, Mark for Review, Add Comments)
6. **Executive Audit Reporting**:
   - Downloadable PDF Audit Report with executive statistics and risk charts
   - Formatted Excel (XLSX) workbook & CSV export
   - High-resolution annotated PDF export
   - Secure signed share links (`/share/[token]`)

---

## 🛠️ Architecture

- **Backend**: FastAPI, Python 3.11, PyMuPDF (fitz), RapidOCR ONNX, ReportLab, OpenPyXL, Pillow, OpenCV.
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, Lucide Icons.

---

## 🚀 Quick Start Guide

### 1. Start the Backend API Server

```bash
cd backend
# Activate virtual environment
.\.venv\Scripts\activate

# Run FastAPI server on port 8000
python app/main.py
```

API Documentation will be available at `http://127.0.0.1:8000/docs`.

### 2. Start the Frontend Application

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in your web browser.

---

## 🧪 Running Automated Tests

```bash
backend\.venv\Scripts\python.exe -m pytest backend\tests\test_pipeline.py -v
```
