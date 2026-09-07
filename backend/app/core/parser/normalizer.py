import re
from typing import Dict, List, Optional, Tuple

class TagNormalizer:
    """
    Generic Tag & Signal Normalization Engine.
    Preserves raw values while extracting standard normalized tokens,
    stripping hierarchical prefixes/suffixes, and resolving project aliases.
    """
    
    # Common DCS / PLC signal suffixes
    SUFFIX_PATTERNS = [
        r'\.CIN$', r'\.COUT$', r'\.AIN$', r'\.AOUT$', r'\.PNT$', r'\.VAL$',
        r'\.BO\d+$', r'\.BI\d+$', r'\.RI\d+$', r'\.RO\d+$', r'\.II\d+$',
        r'\.IO\d+$', r'\.IN\d+$', r'\.OUT\d+$', r'\.PV$', r'\.SP$', r'\.OUT$'
    ]
    
    # Common DCS hierarchical prefixes (e.g., U10PDI:, 10PAB:, CP100R_ECB:)
    PREFIX_PATTERNS = [
        r'^[A-Za-z0-9_-]+:',
        r'^[A-Za-z0-9_-]+/',
        r'^[A-Za-z0-9_-]+\\'
    ]

    # Standard industrial signal semantics & keywords
    SEMANTIC_KEYWORDS = {
        "RUNNING": ["RUN", "RUNNING", "RUN_FB", "MTR_RUN", "STARTED", "STATUS_RUN", "RUN_IND"],
        "STOPPED": ["STOP", "STOPPED", "STOP_FB", "MTR_STOP", "STATUS_STOP"],
        "TRIP": ["TRIP", "TRIPPED", "FAULT", "E_TRIP", "MTR_TRIP", "EMERG_STOP", "ESD"],
        "PERMISSIVE": ["PERM", "PERMISSIVE", "START_PERM", "READY", "ENABLE"],
        "INTERLOCK": ["INTLK", "INTERLOCK", "PROTECT", "SAFE_INTLK", "ILK"],
        "STANDBY": ["STANDBY", "STBY", "STANDBY_SEL", "DUTY_STBY", "STANDBY_SELECTED", "AUTO_STBY"],
        "AUTO": ["AUTO", "AUTO_MODE", "AUTOMATIC", "REMOTE", "REM"],
        "MANUAL": ["MAN", "MANUAL", "LOCAL", "HAND"],
        "SPARE": ["SPARE", "UNUSED", "UNASSIGNED", "DUMMY", "NOT_USED", "RESERVED", "NC", "0", "NULL"]
    }

    def __init__(self, project_aliases: Optional[Dict[str, str]] = None):
        self.project_aliases = {k.upper().strip(): v.upper().strip() for k, v in (project_aliases or {}).items()}

    def normalize(self, raw_tag: str) -> str:
        """
        Produce a normalized, canonical representation of a tag or signal string.
        """
        if not raw_tag:
            return ""
        
        tag = raw_tag.strip().upper()
        
        # Check explicit aliases first
        if tag in self.project_aliases:
            tag = self.project_aliases[tag]

        # Strip prefixes like U10PDI: or U10RDI: or CP100R:
        for prefix_pat in self.PREFIX_PATTERNS:
            tag = re.sub(prefix_pat, '', tag)

        # Strip suffixes like .CIN, .BO01, .PNT
        for suffix_pat in self.SUFFIX_PATTERNS:
            tag = re.sub(suffix_pat, '', tag)

        # Normalize internal separators: replace consecutive delimiters with a single underscore
        tag = re.sub(r'[\s\-_\.\:\/\\]+', '_', tag).strip('_')

        return tag

    def is_spare_or_unused(self, value: str) -> bool:
        """Check if a signal value represents a spare, unused, or disconnected signal."""
        if not value:
            return True
        v = value.strip().upper()
        if v in ["0", "0.0", "NULL", "NONE", "FALSE", "NC", "N/C", "SPARE", "UNUSED", "UNASSIGNED", "RESERVED", "NOT USED"]:
            return True
        for spare_kw in self.SEMANTIC_KEYWORDS["SPARE"]:
            if spare_kw == v or f"_{spare_kw}" in v or f"{spare_kw}_" in v:
                return True
        return False

    def classify_semantics(self, text: str) -> Optional[str]:
        """
        Classify industrial signal concept (e.g. RUNNING, TRIP, PERMISSIVE, STANDBY, etc.)
        """
        if not text:
            return None
        t = text.strip().upper()
        for concept, kw_list in self.SEMANTIC_KEYWORDS.items():
            for kw in kw_list:
                if kw in t:
                    return concept
        return None

    def match_tags(self, tag1: str, tag2: str) -> Tuple[bool, float, str]:
        """
        Compare two tag strings using multi-level matching:
        1. Exact match (100%)
        2. Normalized match (95%)
        3. Core token containment / subset match (85%)
        4. Semantic match (75%)
        Returns (is_match, confidence, match_type)
        """
        if not tag1 or not tag2:
            return False, 0.0, "NONE"
        
        t1_raw = tag1.strip().upper()
        t2_raw = tag2.strip().upper()

        if t1_raw == t2_raw:
            return True, 1.0, "EXACT"

        t1_norm = self.normalize(t1_raw)
        t2_norm = self.normalize(t2_raw)

        if t1_norm and t2_norm and t1_norm == t2_norm:
            return True, 0.95, "NORMALIZED"

        # Check alphanumeric only match (e.g. DIR38125 vs DIR-38125 vs DIR_38125)
        clean1 = re.sub(r'[^A-Z0-9]', '', t1_raw)
        clean2 = re.sub(r'[^A-Z0-9]', '', t2_raw)
        if clean1 and clean2 and clean1 == clean2:
            return True, 0.92, "ALPHANUMERIC"

        # Check if one is a direct substring of another with strong length
        if clean1 and clean2:
            if len(clean1) >= 4 and len(clean2) >= 4:
                if clean1 in clean2 or clean2 in clean1:
                    ratio = min(len(clean1), len(clean2)) / max(len(clean1), len(clean2))
                    if ratio > 0.6:
                        return True, 0.80 * ratio, "SUBSTRING"

        # Check semantic concept match
        sem1 = self.classify_semantics(t1_raw)
        sem2 = self.classify_semantics(t2_raw)
        if sem1 and sem2 and sem1 == sem2 and sem1 != "SPARE":
            return True, 0.70, f"SEMANTIC_{sem1}"

        return False, 0.0, "NO_MATCH"
