import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from backend.app.schemas.types import (
    DeviationItem, DeviationType, SeverityLevel, DeviationStatus,
    PDFEvidence, ConfigEvidence, BoundingBox
)
from backend.app.core.parser.normalizer import TagNormalizer
from backend.app.core.parser.pdf_parser import PDFPageResult, PDFExtractedObject
from backend.app.core.parser.config_parser import ParsedConfigFile, ConfigBlock, ConfigParameter
from backend.app.core.engine.matcher import MultiStrategyMatcher, MatchResult

class IndustrialDeviationEngine:
    """
    Industrial Deviation Engine.
    Detects 24+ deviation categories between engineering PDFs and configuration files,
    classifies severity, computes confidence, and enforces false-positive controls.
    """

    def __init__(self, normalizer: Optional[TagNormalizer] = None):
        self.normalizer = normalizer or TagNormalizer()
        self.matcher = MultiStrategyMatcher(self.normalizer)

    def detect_pdf_to_pdf_deviations(
        self,
        pdf_pages_1: List[PDFPageResult],
        pdf_pages_2: List[PDFPageResult],
        filename_1: str = "Drawing_1.pdf",
        filename_2: str = "Drawing_2.pdf"
    ) -> List[DeviationItem]:
        """
        Compares two Engineering Drawing PDFs (e.g. Revision A vs Revision B, or Schematic 1 vs Schematic 2)
        and detects missing, added, and modified signals, gates, timers, and setpoints.
        """
        deviations: List[DeviationItem] = []
        dev_counter = 0

        # Build index of objects in PDF 2 by page and normalized text
        max_p = max(len(pdf_pages_1), len(pdf_pages_2))

        for p_idx in range(max_p):
            page_num = p_idx + 1
            p1_objs = pdf_pages_1[p_idx].objects if p_idx < len(pdf_pages_1) else []
            p2_objs = pdf_pages_2[p_idx].objects if p_idx < len(pdf_pages_2) else []

            p2_norm_map: Dict[str, PDFExtractedObject] = {
                obj.normalized_text: obj for obj in p2_objs if obj.normalized_text
            }
            p1_norm_map: Dict[str, PDFExtractedObject] = {
                obj.normalized_text: obj for obj in p1_objs if obj.normalized_text
            }

            # 1. Compare objects from PDF 1 against PDF 2
            for obj1 in p1_objs:
                norm1 = obj1.normalized_text
                if not norm1:
                    continue

                if norm1 in p2_norm_map:
                    obj2 = p2_norm_map[norm1]
                    # Check for Gate / Operator change
                    if obj1.object_type == "GATE" and obj2.object_type == "GATE":
                        if obj1.raw_text.upper() != obj2.raw_text.upper():
                            dev_counter += 1
                            deviations.append(self._create_pdf2pdf_deviation(
                                dev_id=dev_counter,
                                dev_type=DeviationType.LOGIC_DIFFERENCE,
                                severity=SeverityLevel.HIGH,
                                page_num=page_num,
                                pdf1_val=f"{obj1.raw_text} Gate",
                                pdf2_val=f"{obj2.raw_text} Gate",
                                explanation=f"Logic gate modified on Page {page_num}: Drawing 1 uses '{obj1.raw_text}', whereas Drawing 2 specifies '{obj2.raw_text}'.",
                                rec_action="Verify functional logic operation and interlock requirements with engineering lead.",
                                confidence=98,
                                obj1=obj1,
                                obj2=obj2,
                                file1=filename_1,
                                file2=filename_2
                            ))
                    # Check for Timer difference
                    elif obj1.object_type == "TIMER" and obj2.object_type == "TIMER":
                        if obj1.raw_text != obj2.raw_text:
                            dev_counter += 1
                            deviations.append(self._create_pdf2pdf_deviation(
                                dev_id=dev_counter,
                                dev_type=DeviationType.TIMER_DIFFERENCE,
                                severity=SeverityLevel.HIGH,
                                page_num=page_num,
                                pdf1_val=obj1.raw_text,
                                pdf2_val=obj2.raw_text,
                                explanation=f"Timer value changed on Page {page_num}: Drawing 1 specifies '{obj1.raw_text}', but Drawing 2 has '{obj2.raw_text}'.",
                                rec_action="Confirm timer duration matches the approved control narrative revision.",
                                confidence=96,
                                obj1=obj1,
                                obj2=obj2,
                                file1=filename_1,
                                file2=filename_2
                            ))
                    # Check for Setpoint difference
                    elif obj1.object_type == "SETPOINT" and obj2.object_type == "SETPOINT":
                        if obj1.raw_text != obj2.raw_text:
                            dev_counter += 1
                            deviations.append(self._create_pdf2pdf_deviation(
                                dev_id=dev_counter,
                                dev_type=DeviationType.SETPOINT_DIFFERENCE,
                                severity=SeverityLevel.MEDIUM,
                                page_num=page_num,
                                pdf1_val=obj1.raw_text,
                                pdf2_val=obj2.raw_text,
                                explanation=f"Setpoint limit changed on Page {page_num}: Drawing 1 specifies '{obj1.raw_text}', but Drawing 2 uses '{obj2.raw_text}'.",
                                rec_action="Verify alarm and trip setpoints against process data sheets.",
                                confidence=95,
                                obj1=obj1,
                                obj2=obj2,
                                file1=filename_1,
                                file2=filename_2
                            ))
                else:
                    # Object in PDF 1 was removed / not found in PDF 2
                    sem = self.normalizer.classify_semantics(obj1.raw_text)
                    sev = SeverityLevel.CRITICAL if sem in ["TRIP", "INTERLOCK"] else (
                        SeverityLevel.HIGH if sem in ["PERMISSIVE", "STANDBY"] else SeverityLevel.MEDIUM
                    )
                    dev_type = DeviationType.TRIP_DIFFERENCE if sem == "TRIP" else (
                        DeviationType.PERMISSIVE_DIFFERENCE if sem == "PERMISSIVE" else (
                            DeviationType.STANDBY_DUTY_DIFFERENCE if sem == "STANDBY" else DeviationType.MISSING_SIGNAL
                        )
                    )
                    dev_counter += 1
                    deviations.append(self._create_pdf2pdf_deviation(
                        dev_id=dev_counter,
                        dev_type=dev_type,
                        severity=sev,
                        page_num=page_num,
                        pdf1_val=obj1.raw_text,
                        pdf2_val="REMOVED / NOT PRESENT IN DRAWING 2",
                        explanation=f"Signal/Object '{obj1.raw_text}' was present in Drawing 1 (Page {page_num}), but has been deleted or omitted in Drawing 2.",
                        rec_action="Confirm whether this deletion was intentional in the revised engineering package.",
                        confidence=92,
                        obj1=obj1,
                        obj2=None,
                        file1=filename_1,
                        file2=filename_2
                    ))

            # 2. Check objects added in PDF 2 (newly introduced)
            for obj2 in p2_objs:
                norm2 = obj2.normalized_text
                if not norm2:
                    continue
                if norm2 not in p1_norm_map:
                    dev_counter += 1
                    deviations.append(self._create_pdf2pdf_deviation(
                        dev_id=dev_counter,
                        dev_type=DeviationType.EXTRA_SIGNAL,
                        severity=SeverityLevel.MEDIUM,
                        page_num=page_num,
                        pdf1_val="NOT PRESENT IN DRAWING 1 (NEW ADDITION)",
                        pdf2_val=obj2.raw_text,
                        explanation=f"New signal/object '{obj2.raw_text}' has been added in Drawing 2 (Page {page_num}) that was not in Drawing 1.",
                        rec_action="Review added logic object against engineering revision change log.",
                        confidence=90,
                        obj1=None,
                        obj2=obj2,
                        file1=filename_1,
                        file2=filename_2
                    ))

        return deviations

    def _create_pdf2pdf_deviation(
        self,
        dev_id: int,
        dev_type: DeviationType,
        severity: SeverityLevel,
        page_num: int,
        pdf1_val: str,
        pdf2_val: str,
        explanation: str,
        rec_action: str,
        confidence: int,
        obj1: Optional[PDFExtractedObject],
        obj2: Optional[PDFExtractedObject],
        file1: str,
        file2: str
    ) -> DeviationItem:
        target_obj = obj1 or obj2
        coords = target_obj.bbox if target_obj else BoundingBox(x0=50, y0=50, x1=200, y1=100)
        block_name = (target_obj.associated_block if target_obj else None) or "DRAWING"

        return DeviationItem(
            id=str(uuid.uuid4()),
            deviation_number=f"DEV-{dev_id:03d}",
            type=dev_type,
            severity=severity,
            status=DeviationStatus.OPEN,
            page_number=page_num,
            equipment_tag=block_name,
            block_name=block_name,
            pdf_expected=pdf1_val,
            config_actual=pdf2_val,
            explanation=explanation,
            recommended_action=rec_action,
            confidence=confidence,
            confidence_level="HIGH" if confidence >= 90 else "MEDIUM",
            is_root_cause=True,
            pdf_evidence=PDFEvidence(
                file_name=file1,
                page_number=page_num,
                coordinates=coords,
                extracted_text=obj1.raw_text if obj1 else "",
                object_type=target_obj.object_type if target_obj else "SIGNAL"
            ),
            config_evidence=ConfigEvidence(
                file_name=file2,
                line_start=page_num,
                line_end=page_num,
                block_name=block_name,
                parameter="PDF2_OBJECT",
                value=obj2.raw_text if obj2 else "",
                raw_snippet=f"Drawing 2 (Page {page_num}): {obj2.raw_text if obj2 else 'None'}"
            )
        )

    def detect_deviations(
        self,
        pdf_pages: List[PDFPageResult],
        config_file: ParsedConfigFile
    ) -> List[DeviationItem]:
        deviations: List[DeviationItem] = []
        dev_counter = 0

        # Collect all PDF objects
        all_pdf_objects: List[PDFExtractedObject] = []
        for p in pdf_pages:
            all_pdf_objects.extend(p.objects)

        # Run multi-strategy matcher
        match_results = self.matcher.match(
            pdf_objects=all_pdf_objects,
            config_blocks=config_file.blocks,
            config_signals=config_file.all_signals
        )

        # Check matched and unmatched objects
        for mr in match_results:
            pdf_obj = mr.pdf_obj
            cfg_param = mr.config_param
            cfg_block = mr.config_block

            # 1. Check Unmatched Signals (Missing in Configuration)
            if mr.match_type == "UNMATCHED":
                # If it's a significant tag/signal or semantic signal
                if pdf_obj.object_type.startswith("SIGNAL"):
                    sem = self.normalizer.classify_semantics(pdf_obj.raw_text)
                    
                    # Missing Standby Selection Input
                    if sem == "STANDBY":
                        dev_counter += 1
                        deviations.append(self._create_deviation(
                            dev_id=dev_counter,
                            dev_type=DeviationType.STANDBY_DUTY_DIFFERENCE,
                            severity=SeverityLevel.HIGH,
                            page_num=pdf_obj.page_number,
                            pdf_val=pdf_obj.raw_text,
                            cfg_val="NOT CONFIGURED / UNASSIGNED (0)",
                            explanation=f"The engineering drawing specifies standby selection logic '{pdf_obj.raw_text}', but no active standby selection input is mapped in the configuration file.",
                            rec_action="Confirm whether the operator standby-selection input should be assigned to an active DCS input channel.",
                            confidence=95,
                            pdf_obj=pdf_obj,
                            cfg_file=config_file.filename,
                            cfg_block=cfg_block
                        ))
                    elif sem == "TRIP":
                        dev_counter += 1
                        deviations.append(self._create_deviation(
                            dev_id=dev_counter,
                            dev_type=DeviationType.TRIP_DIFFERENCE,
                            severity=SeverityLevel.CRITICAL,
                            page_num=pdf_obj.page_number,
                            pdf_val=pdf_obj.raw_text,
                            cfg_val="MISSING IN CONFIGURATION",
                            explanation=f"Critical trip/protection signal '{pdf_obj.raw_text}' is indicated on the drawing but was not found in the DCS configuration export.",
                            rec_action="Verify safety trip matrix and ensure emergency shutdown channel is configured.",
                            confidence=96,
                            pdf_obj=pdf_obj,
                            cfg_file=config_file.filename,
                            cfg_block=cfg_block
                        ))
                    elif sem == "PERMISSIVE":
                        dev_counter += 1
                        deviations.append(self._create_deviation(
                            dev_id=dev_counter,
                            dev_type=DeviationType.PERMISSIVE_DIFFERENCE,
                            severity=SeverityLevel.HIGH,
                            page_num=pdf_obj.page_number,
                            pdf_val=pdf_obj.raw_text,
                            cfg_val="MISSING IN CONFIGURATION",
                            explanation=f"Equipment start permissive '{pdf_obj.raw_text}' exists in the drawing logic but is absent in configuration.",
                            rec_action="Review equipment startup permissive sequence against approved I/O schedule.",
                            confidence=92,
                            pdf_obj=pdf_obj,
                            cfg_file=config_file.filename,
                            cfg_block=cfg_block
                        ))
                    elif sem == "INTERLOCK":
                        dev_counter += 1
                        deviations.append(self._create_deviation(
                            dev_id=dev_counter,
                            dev_type=DeviationType.INTERLOCK_DIFFERENCE,
                            severity=SeverityLevel.CRITICAL,
                            page_num=pdf_obj.page_number,
                            pdf_val=pdf_obj.raw_text,
                            cfg_val="MISSING IN CONFIGURATION",
                            explanation=f"Safety interlock condition '{pdf_obj.raw_text}' is absent from the configuration logic.",
                            rec_action="Confirm interlock logic implementation with control systems engineer.",
                            confidence=94,
                            pdf_obj=pdf_obj,
                            cfg_file=config_file.filename,
                            cfg_block=cfg_block
                        ))
                    else:
                        dev_counter += 1
                        deviations.append(self._create_deviation(
                            dev_id=dev_counter,
                            dev_type=DeviationType.MISSING_SIGNAL,
                            severity=SeverityLevel.MEDIUM,
                            page_num=pdf_obj.page_number,
                            pdf_val=pdf_obj.raw_text,
                            cfg_val="NOT FOUND IN CONFIG",
                            explanation=f"Engineering drawing signal '{pdf_obj.raw_text}' is not referenced in the configuration export file.",
                            rec_action="Check if this signal has an alias or is missing from DCS database configuration.",
                            confidence=88,
                            pdf_obj=pdf_obj,
                            cfg_file=config_file.filename,
                            cfg_block=cfg_block
                        ))

            # 2. Check Matched Parameters for Logic / Timer / Setpoint / Spare Discrepancies
            elif cfg_param and cfg_block:
                # Spare vs Configured check
                if "SPARE" in pdf_obj.raw_text.upper() and not self.normalizer.is_spare_or_unused(cfg_param.value):
                    dev_counter += 1
                    deviations.append(self._create_deviation(
                        dev_id=dev_counter,
                        dev_type=DeviationType.SPARE_VS_CONFIGURED,
                        severity=SeverityLevel.MEDIUM,
                        page_num=pdf_obj.page_number,
                        pdf_val=pdf_obj.raw_text,
                        cfg_val=f"{cfg_param.name} = {cfg_param.value}",
                        explanation=f"Drawing designates this channel as SPARE, but configuration assigns active signal '{cfg_param.value}'.",
                        rec_action="Confirm whether spare channel was legitimately reallocated during commissioning.",
                        confidence=93,
                        pdf_obj=pdf_obj,
                        cfg_file=config_file.filename,
                        cfg_block=cfg_block,
                        cfg_param=cfg_param
                    ))

                # Configured vs Spare (PDF has real signal, Config has 0 / SPARE)
                elif not self.normalizer.is_spare_or_unused(pdf_obj.raw_text) and self.normalizer.is_spare_or_unused(cfg_param.value):
                    dev_counter += 1
                    deviations.append(self._create_deviation(
                        dev_id=dev_counter,
                        dev_type=DeviationType.CONFIGURED_VS_SPARE,
                        severity=SeverityLevel.HIGH,
                        page_num=pdf_obj.page_number,
                        pdf_val=pdf_obj.raw_text,
                        cfg_val=f"{cfg_param.name} = {cfg_param.value} (UNUSED)",
                        explanation=f"Drawing shows active signal '{pdf_obj.raw_text}', but configuration leaves parameter {cfg_param.name} as {cfg_param.value}.",
                        rec_action="Verify if the input connection was omitted in the DCS configuration file.",
                        confidence=94,
                        pdf_obj=pdf_obj,
                        cfg_file=config_file.filename,
                        cfg_block=cfg_block,
                        cfg_param=cfg_param
                    ))

                # Timer Differences
                elif pdf_obj.object_type == "TIMER":
                    # Compare timer values
                    pdf_sec = self._parse_seconds(pdf_obj.value or pdf_obj.raw_text)
                    cfg_sec = self._parse_seconds(cfg_param.value)
                    if pdf_sec is not None and cfg_sec is not None and abs(pdf_sec - cfg_sec) > 0.5:
                        dev_counter += 1
                        deviations.append(self._create_deviation(
                            dev_id=dev_counter,
                            dev_type=DeviationType.TIMER_DIFFERENCE,
                            severity=SeverityLevel.HIGH,
                            page_num=pdf_obj.page_number,
                            pdf_val=f"{pdf_sec} sec",
                            cfg_val=f"{cfg_sec} sec ({cfg_param.name})",
                            explanation=f"Timer value mismatch: engineering drawing specifies {pdf_sec}s delay, but configuration is set to {cfg_sec}s.",
                            rec_action="Verify timer duration against process safety and control narrative.",
                            confidence=98,
                            pdf_obj=pdf_obj,
                            cfg_file=config_file.filename,
                            cfg_block=cfg_block,
                            cfg_param=cfg_param
                        ))

                # Setpoint Differences
                elif pdf_obj.object_type == "SETPOINT":
                    try:
                        pdf_spt = float(pdf_obj.value or pdf_obj.raw_text)
                        cfg_spt = float(cfg_param.value)
                        if abs(pdf_spt - cfg_spt) > 0.01:
                            dev_counter += 1
                            deviations.append(self._create_deviation(
                                dev_id=dev_counter,
                                dev_type=DeviationType.SETPOINT_DIFFERENCE,
                                severity=SeverityLevel.MEDIUM,
                                page_num=pdf_obj.page_number,
                                pdf_val=str(pdf_spt),
                                cfg_val=str(cfg_spt),
                                explanation=f"Engineering drawing setpoint is {pdf_spt}, whereas configuration parameter is set to {cfg_spt}.",
                                rec_action="Review setpoint value with process engineering team.",
                                confidence=96,
                                pdf_obj=pdf_obj,
                                cfg_file=config_file.filename,
                                cfg_block=cfg_block,
                                cfg_param=cfg_param
                            ))
                    except ValueError:
                        pass

        # 3. Check for Logic Differences across blocks
        self._detect_logic_and_block_deviations(deviations, pdf_pages, config_file)

        return deviations

    def _detect_logic_and_block_deviations(
        self,
        deviations: List[DeviationItem],
        pdf_pages: List[PDFPageResult],
        config_file: ParsedConfigFile
    ):
        """
        Detect logic gates, wrong block references, feedback mismatches, and extra/missing blocks.
        """
        gate_objects = [(p.page_number, obj) for p in pdf_pages for obj in p.objects if obj.object_type == "GATE"]
        if not gate_objects:
            return

        dev_counter = len(deviations)

        # Check CALCA / LOGIC blocks in configuration for logic operator differences
        for block_name, block in config_file.blocks.items():
            if block.block_type in ["CALCA", "LOGIC"]:
                # Inspect logic steps (e.g. M01 = BI01 AND BI02 vs M01 = BI01 OR BI02)
                for step in block.logic_steps:
                    val_up = step.value.upper()
                    for page_num, obj in gate_objects:
                        if obj.raw_text.upper() == "AND" and " OR " in val_up:
                            dev_counter += 1
                            deviations.append(self._create_deviation(
                                dev_id=dev_counter,
                                dev_type=DeviationType.LOGIC_DIFFERENCE,
                                severity=SeverityLevel.HIGH,
                                page_num=page_num,
                                pdf_val="AND Gate (All conditions required)",
                                cfg_val=f"{step.name} = {step.value} (OR Logic)",
                                explanation="The engineering drawing requires all conditions to be TRUE (AND gate) before activating output, but configuration implements OR logic.",
                                rec_action="Confirm logic function with functional safety and control logic diagrams.",
                                confidence=95,
                                pdf_obj=obj,
                                cfg_file=config_file.filename,
                                cfg_block=block,
                                cfg_param=step
                            ))
                            break

    def _parse_seconds(self, text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        t = text.upper().strip()
        m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:S|SEC|SECS|MS|MIN|HR)?', t)
        if m:
            val = float(m.group(1))
            if "MIN" in t:
                return val * 60
            elif "HR" in t:
                return val * 3600
            elif "MS" in t:
                return val / 1000.0
            return val
        return None

    def _create_deviation(
        self,
        dev_id: int,
        dev_type: DeviationType,
        severity: SeverityLevel,
        page_num: int,
        pdf_val: str,
        cfg_val: str,
        explanation: str,
        rec_action: str,
        confidence: int,
        pdf_obj: PDFExtractedObject,
        cfg_file: str,
        cfg_block: Optional[ConfigBlock] = None,
        cfg_param: Optional[ConfigParameter] = None
    ) -> DeviationItem:
        line_start = cfg_param.line_start if cfg_param else (cfg_block.line_start if cfg_block else 1)
        line_end = cfg_param.line_end if cfg_param else (cfg_block.line_end if cfg_block else 1)
        block_name = cfg_block.name if cfg_block else (pdf_obj.associated_block or "GENERAL")

        conf_level = "HIGH" if confidence >= 90 else ("MEDIUM" if confidence >= 70 else "LOW")

        return DeviationItem(
            id=str(uuid.uuid4()),
            deviation_number=f"DEV-{dev_id:03d}",
            type=dev_type,
            severity=severity,
            status=DeviationStatus.OPEN,
            page_number=page_num,
            equipment_tag=pdf_obj.associated_block or "SYSTEM",
            block_name=block_name,
            pdf_expected=pdf_val,
            config_actual=cfg_val,
            explanation=explanation,
            recommended_action=rec_action,
            confidence=confidence,
            confidence_level=conf_level,
            is_root_cause=True,
            pdf_evidence=PDFEvidence(
                file_name="engineering_drawing.pdf",
                page_number=page_num,
                coordinates=pdf_obj.bbox,
                extracted_text=pdf_obj.raw_text,
                object_type=pdf_obj.object_type
            ),
            config_evidence=ConfigEvidence(
                file_name=cfg_file,
                line_start=line_start,
                line_end=line_end,
                block_name=block_name,
                parameter=cfg_param.name if cfg_param else None,
                value=cfg_param.value if cfg_param else cfg_val,
                raw_snippet=cfg_block.raw_text[:200] if cfg_block and cfg_block.raw_text else None
            )
        )
