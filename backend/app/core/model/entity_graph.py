from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from backend.app.schemas.types import BoundingBox

@dataclass
class EngineeringSignal:
    id: str
    name: str
    raw_name: str
    normalized_name: str
    source: str # "PDF" or "CONFIG"
    page_number: Optional[int] = None
    line_number: Optional[int] = None
    block_name: Optional[str] = None
    pin_name: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    is_spare: bool = False
    semantic_role: Optional[str] = None
    confidence: float = 1.0

@dataclass
class LogicNode:
    id: str
    node_type: str # "AND", "OR", "NOT", "NAND", "NOR", "XOR", "CALCA", "TIMER", "SETPOINT", "BLOCK"
    operator: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    timer_value_sec: Optional[float] = None
    setpoint_value: Optional[float] = None
    source: str = "PDF" # "PDF" or "CONFIG"
    page_number: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    bbox: Optional[BoundingBox] = None

@dataclass
class LogicConnection:
    from_node_id: str
    to_node_id: str
    signal_name: str
    connection_type: str = "DIRECT"

class EngineeringGraphModel:
    """
    Unified Graph & Object representation for both PDF and Configuration files.
    """
    def __init__(self):
        self.signals: Dict[str, EngineeringSignal] = {}
        self.nodes: Dict[str, LogicNode] = {}
        self.connections: List[LogicConnection] = []
        self.blocks: Dict[str, Dict[str, Any]] = {}

    def add_signal(self, sig: EngineeringSignal):
        self.signals[sig.id] = sig

    def add_node(self, node: LogicNode):
        self.nodes[node.id] = node

    def add_connection(self, conn: LogicConnection):
        self.connections.append(conn)

    def find_signals_by_normalized_name(self, norm_name: str) -> List[EngineeringSignal]:
        return [s for s in self.signals.values() if s.normalized_name == norm_name]

    def find_nodes_by_type(self, node_type: str) -> List[LogicNode]:
        return [n for n in self.nodes.values() if n.node_type == node_type]
