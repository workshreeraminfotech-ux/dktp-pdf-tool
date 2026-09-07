import os
import re
import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from backend.app.core.parser.normalizer import TagNormalizer

@dataclass
class ConfigParameter:
    name: str
    value: str
    raw_value: str
    param_type: str # "INPUT", "OUTPUT", "TIMER", "SETPOINT", "LOGIC", "ATTRIBUTE"
    line_start: int
    line_end: int
    normalized_value: str = ""

@dataclass
class ConfigBlock:
    name: str
    block_type: str
    compound: Optional[str] = None
    description: Optional[str] = None
    loop_id: Optional[str] = None
    parameters: Dict[str, ConfigParameter] = field(default_factory=dict)
    inputs: List[ConfigParameter] = field(default_factory=list)
    outputs: List[ConfigParameter] = field(default_factory=list)
    timers: List[ConfigParameter] = field(default_factory=list)
    setpoints: List[ConfigParameter] = field(default_factory=list)
    logic_steps: List[ConfigParameter] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0
    raw_text: str = ""

@dataclass
class ParsedConfigFile:
    filename: str
    format_type: str # "FOXBORO_DCS", "GENERIC_BLOCK", "CSV", "JSON", "XML", "KEY_VALUE"
    total_lines: int
    blocks: Dict[str, ConfigBlock] = field(default_factory=dict)
    all_signals: List[ConfigParameter] = field(default_factory=list)

class UniversalConfigParser:
    """
    Universal Configuration Parser.
    Automatically detects DCS/PLC export formats (Foxboro, ABB, Siemens, CSV, JSON, XML, Key-Value)
    and extracts structured blocks, parameters, connections, timers, and line-level evidence.
    """

    INPUT_PARAM_PATTERNS = [r'^BI\d+$', r'^RI\d+$', r'^II\d+$', r'^IN\d+$', r'^I\d+$', r'^INPUT\d*$', r'^INP_.*']
    OUTPUT_PARAM_PATTERNS = [r'^BO\d+$', r'^RO\d+$', r'^IO\d+$', r'^OUT\d+$', r'^O\d+$', r'^OUTPUT\d*$', r'^OUT_.*']
    TIMER_PARAM_PATTERNS = [r'^TIM_.*', r'^TIME_.*', r'^DELAY.*', r'^PERIOD$', r'^TON.*', r'^TOFF.*', r'^DON.*', r'^DOFF.*', r'^PULSE.*']
    SETPOINT_PATTERNS = [r'^SPT.*', r'^HLIM.*', r'^LLIM.*', r'^HHAL.*', r'^LLAL.*', r'^SETPT.*', r'^LIMIT.*', r'^DEADB.*']
    LOGIC_PATTERNS = [r'^M\d+$', r'^STEP\d+$', r'^EQN\d*$', r'^CALC\d*$', r'^LOGIC\d*$']

    def __init__(self, normalizer: Optional[TagNormalizer] = None):
        self.normalizer = normalizer or TagNormalizer()

    def parse_file(self, file_path: str) -> ParsedConfigFile:
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".json":
            return self._parse_json(file_path, filename)
        elif ext in [".csv", ".tsv"]:
            return self._parse_csv(file_path, filename, delimiter=',' if ext == ".csv" else '\t')
        elif ext == ".xml":
            return self._parse_xml(file_path, filename)
        else:
            # For .txt or unknown text files, parse text blocks
            return self._parse_text_config(file_path, filename)

    def _classify_param_type(self, param_name: str, value: str) -> str:
        name_up = param_name.strip().upper()
        for pat in self.INPUT_PARAM_PATTERNS:
            if re.match(pat, name_up):
                return "INPUT"
        for pat in self.OUTPUT_PARAM_PATTERNS:
            if re.match(pat, name_up):
                return "OUTPUT"
        for pat in self.TIMER_PARAM_PATTERNS:
            if re.match(pat, name_up):
                return "TIMER"
        for pat in self.SETPOINT_PATTERNS:
            if re.match(pat, name_up):
                return "SETPOINT"
        for pat in self.LOGIC_PATTERNS:
            if re.match(pat, name_up):
                return "LOGIC"
        return "ATTRIBUTE"

    def _parse_text_config(self, file_path: str, filename: str) -> ParsedConfigFile:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        result = ParsedConfigFile(
            filename=filename,
            format_type="FOXBORO_DCS" if any("NAME   =" in l or "TYPE   =" in l for l in lines[:100]) else "GENERIC_BLOCK",
            total_lines=len(lines)
        )

        current_block: Optional[ConfigBlock] = None
        block_lines: List[str] = []
        block_start_line = 1

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            
            # Check for block starter e.g. "NAME   = BLOCK_NAME" or "BLOCK BLOCK_NAME"
            name_match = re.match(r'^(?:NAME\s*=\s*|BLOCK\s+)([A-Za-z0-9_:\-\/]+)', line, re.IGNORECASE)
            
            if name_match:
                # Save previous block
                if current_block:
                    current_block.line_end = idx - 1
                    current_block.raw_text = "".join(block_lines)
                    result.blocks[current_block.name] = current_block

                block_name = name_match.group(1).strip()
                compound = None
                if ":" in block_name:
                    parts = block_name.split(":", 1)
                    compound = parts[0]
                
                current_block = ConfigBlock(
                    name=block_name,
                    block_type="UNKNOWN",
                    compound=compound,
                    line_start=idx
                )
                block_lines = [raw_line]
                continue

            # Check for block terminator
            if line == "END" or line == "END_BLOCK":
                if current_block:
                    block_lines.append(raw_line)
                    current_block.line_end = idx
                    current_block.raw_text = "".join(block_lines)
                    result.blocks[current_block.name] = current_block
                    current_block = None
                    block_lines = []
                continue

            if current_block:
                block_lines.append(raw_line)
                # Parse Key = Value
                kv_match = re.match(r'^([A-Za-z0-9_]+)\s*[:=]\s*(.*)$', line)
                if kv_match:
                    p_name = kv_match.group(1).strip().upper()
                    p_val = kv_match.group(2).strip()

                    if p_name == "TYPE":
                        current_block.block_type = p_val
                    elif p_name == "DESCRP" or p_name == "DESCRIPTION":
                        current_block.description = p_val
                    elif p_name == "LOOPID":
                        current_block.loop_id = p_val

                    p_type = self._classify_param_type(p_name, p_val)
                    norm_val = self.normalizer.normalize(p_val) if not self.normalizer.is_spare_or_unused(p_val) else ""

                    param_obj = ConfigParameter(
                        name=p_name,
                        value=p_val,
                        raw_value=p_val,
                        param_type=p_type,
                        line_start=idx,
                        line_end=idx,
                        normalized_value=norm_val
                    )

                    current_block.parameters[p_name] = param_obj

                    if p_type == "INPUT":
                        current_block.inputs.append(param_obj)
                        result.all_signals.append(param_obj)
                    elif p_type == "OUTPUT":
                        current_block.outputs.append(param_obj)
                        result.all_signals.append(param_obj)
                    elif p_type == "TIMER":
                        current_block.timers.append(param_obj)
                    elif p_type == "SETPOINT":
                        current_block.setpoints.append(param_obj)
                    elif p_type == "LOGIC":
                        current_block.logic_steps.append(param_obj)

        if current_block:
            current_block.line_end = len(lines)
            current_block.raw_text = "".join(block_lines)
            result.blocks[current_block.name] = current_block

        return result

    def _parse_csv(self, file_path: str, filename: str, delimiter: str = ',') -> ParsedConfigFile:
        result = ParsedConfigFile(filename=filename, format_type="CSV", total_lines=0)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for idx, row in enumerate(reader, start=2):
                block_name = row.get("Block", row.get("BLOCK", row.get("Tag", f"ROW_{idx}"))).strip()
                tag = row.get("Tag", row.get("TAG", row.get("Signal", ""))).strip()
                val = row.get("Value", row.get("VALUE", tag)).strip()
                
                block = result.blocks.get(block_name)
                if not block:
                    block = ConfigBlock(name=block_name, block_type="CSV_ENTRY", line_start=idx, line_end=idx)
                    result.blocks[block_name] = block
                
                param = ConfigParameter(
                    name=f"PARAM_{idx}",
                    value=val,
                    raw_value=val,
                    param_type="INPUT" if "IN" in tag.upper() else "OUTPUT",
                    line_start=idx,
                    line_end=idx,
                    normalized_value=self.normalizer.normalize(val)
                )
                block.parameters[param.name] = param
                result.all_signals.append(param)
        result.total_lines = len(result.all_signals) + 1
        return result

    def _parse_json(self, file_path: str, filename: str) -> ParsedConfigFile:
        result = ParsedConfigFile(filename=filename, format_type="JSON", total_lines=0)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle dict of blocks or list of objects
        if isinstance(data, dict):
            for block_name, b_data in data.items():
                block = ConfigBlock(name=block_name, block_type=str(b_data.get("type", "JSON_BLOCK")), line_start=1, line_end=1)
                for k, v in b_data.items():
                    val_str = str(v)
                    p_type = self._classify_param_type(k, val_str)
                    param = ConfigParameter(
                        name=k,
                        value=val_str,
                        raw_value=val_str,
                        param_type=p_type,
                        line_start=1,
                        line_end=1,
                        normalized_value=self.normalizer.normalize(val_str)
                    )
                    block.parameters[k] = param
                    if p_type in ["INPUT", "OUTPUT"]:
                        result.all_signals.append(param)
                result.blocks[block_name] = block
        return result

    def _parse_xml(self, file_path: str, filename: str) -> ParsedConfigFile:
        result = ParsedConfigFile(filename=filename, format_type="XML", total_lines=0)
        tree = ET.parse(file_path)
        root = tree.getroot()
        for idx, elem in enumerate(root.iter()):
            name = elem.attrib.get("name", elem.attrib.get("Name", elem.tag))
            if elem.attrib:
                block = ConfigBlock(name=name, block_type=elem.tag, line_start=idx+1, line_end=idx+1)
                for k, v in elem.attrib.items():
                    p_type = self._classify_param_type(k, v)
                    param = ConfigParameter(
                        name=k,
                        value=v,
                        raw_value=v,
                        param_type=p_type,
                        line_start=idx+1,
                        line_end=idx+1,
                        normalized_value=self.normalizer.normalize(v)
                    )
                    block.parameters[k] = param
                    if p_type in ["INPUT", "OUTPUT"]:
                        result.all_signals.append(param)
                result.blocks[name] = block
        return result
