from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json

@dataclass
class AgentState:
    goal: str
    iteration: int = 0
    max_iterations: int = 10
    open_files: Dict[str, str] = field(default_factory=dict)
    recent_diffs: List[str] = field(default_factory=list)
    last_errors: List[str] = field(default_factory=list)
    plan: List[str] = field(default_factory=list)
    actions_taken: List[Dict] = field(default_factory=list)
    symbol_table: Dict[str, List[str]] = field(default_factory=dict)
    import_graph: Dict[str, List[str]] = field(default_factory=dict)
    call_graph: Dict[str, List[str]] = field(default_factory=dict)
    status: str = "initialized"
    current_file: Optional[str] = None
    
    def to_dict(self):
        return {
            "goal": self.goal,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "open_files": self.open_files,
            "recent_diffs": self.recent_diffs,
            "last_errors": self.last_errors,
            "plan": self.plan,
            "actions_taken": self.actions_taken,
            "symbol_table": self.symbol_table,
            "import_graph": self.import_graph,
            "call_graph": self.call_graph,
            "status": self.status,
            "current_file": self.current_file
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    def add_action(self, action_type: str, params: Dict, result: any):
        self.actions_taken.append({
            "iteration": self.iteration,
            "type": action_type,
            "params": params,
            "result": str(result)[:200]
        })
    
    def add_error(self, error: str):
        self.last_errors.append(error)
        if len(self.last_errors) > 5:
            self.last_errors = self.last_errors[-5:]
    
    def add_diff(self, diff: str):
        self.recent_diffs.append(diff)
        if len(self.recent_diffs) > 10:
            self.recent_diffs = self.recent_diffs[-10:]
    
    def increment_iteration(self):
        self.iteration += 1
