from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from backend.app.core.parser.normalizer import TagNormalizer
from backend.app.core.parser.pdf_parser import PDFExtractedObject
from backend.app.core.parser.config_parser import ConfigParameter, ConfigBlock

@dataclass
class MatchResult:
    pdf_obj: PDFExtractedObject
    config_param: Optional[ConfigParameter]
    config_block: Optional[ConfigBlock]
    match_type: str # "EXACT", "NORMALIZED", "ALIAS", "SEMANTIC", "UNMATCHED"
    confidence: float # 0.0 - 1.0
    notes: str = ""

class MultiStrategyMatcher:
    """
    Multi-Strategy Matching Engine.
    Correlates PDF engineering objects with configuration parameters
    across multiple levels: exact, normalized, alias, alphanumeric, and semantic.
    """

    def __init__(self, normalizer: Optional[TagNormalizer] = None):
        self.normalizer = normalizer or TagNormalizer()

    def match(
        self,
        pdf_objects: List[PDFExtractedObject],
        config_blocks: Dict[str, ConfigBlock],
        config_signals: List[ConfigParameter]
    ) -> List[MatchResult]:
        results: List[MatchResult] = []

        # Index config signals by normalized value and raw value for fast O(1) lookup
        config_norm_map: Dict[str, List[Tuple[ConfigParameter, Optional[ConfigBlock]]]] = {}
        config_raw_map: Dict[str, List[Tuple[ConfigParameter, Optional[ConfigBlock]]]] = {}

        # Pre-index active parameters and exact lookup maps
        active_config_params = []
        for block_name, block in config_blocks.items():
            for p_name, param in block.parameters.items():
                if param.normalized_value:
                    config_norm_map.setdefault(param.normalized_value, []).append((param, block))
                raw_up = param.raw_value.strip().upper()
                if raw_up:
                    config_raw_map.setdefault(raw_up, []).append((param, block))
                if param.value and not self.normalizer.is_spare_or_unused(param.value):
                    active_config_params.append((raw_up, param, block))

        for pdf_obj in pdf_objects:
            raw_pdf = pdf_obj.raw_text.strip().upper()
            norm_pdf = pdf_obj.normalized_text.strip().upper()

            # 1. Exact Raw Match
            if raw_pdf in config_raw_map:
                param, block = config_raw_map[raw_pdf][0]
                results.append(MatchResult(
                    pdf_obj=pdf_obj,
                    config_param=param,
                    config_block=block,
                    match_type="EXACT",
                    confidence=1.0,
                    notes=f"Exact match on tag '{raw_pdf}'"
                ))
                continue

            # 2. Normalized Match
            if norm_pdf in config_norm_map:
                param, block = config_norm_map[norm_pdf][0]
                results.append(MatchResult(
                    pdf_obj=pdf_obj,
                    config_param=param,
                    config_block=block,
                    match_type="NORMALIZED",
                    confidence=0.95,
                    notes=f"Normalized match on '{norm_pdf}'"
                ))
                continue

            # 3. Fuzzy / Semantic / Partial Tag Match on active parameters
            best_match: Optional[Tuple[ConfigParameter, ConfigBlock, float, str]] = None
            for p_val_up, param, block in active_config_params[:500]:
                is_match, conf, m_type = self.normalizer.match_tags(raw_pdf, p_val_up)
                if is_match and (best_match is None or conf > best_match[2]):
                    best_match = (param, block, conf, m_type)
                    if conf >= 0.90:
                        break

            if best_match and best_match[2] >= 0.70:
                param, block, conf, m_type = best_match
                results.append(MatchResult(
                    pdf_obj=pdf_obj,
                    config_param=param,
                    config_block=block,
                    match_type=m_type,
                    confidence=conf,
                    notes=f"Matched via {m_type} with confidence {int(conf*100)}%"
                ))
                continue

            # 4. Unmatched PDF Object
            results.append(MatchResult(
                pdf_obj=pdf_obj,
                config_param=None,
                config_block=None,
                match_type="UNMATCHED",
                confidence=0.0,
                notes="No corresponding configuration parameter found"
            ))

        return results
