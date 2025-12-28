from .agent_state import AgentState
from typing import Dict, List

class ContextBuilder:
    
    def __init__(self):
        self.max_context_size = 8000
    
    def build_context(self, state: AgentState) -> str:
        sections = []
        
        sections.append(self._build_goal_section(state))
        sections.append(self._build_plan_section(state))
        sections.append(self._build_open_files_section(state))
        sections.append(self._build_errors_section(state))
        sections.append(self._build_diffs_section(state))
        sections.append(self._build_graph_section(state))
        
        context = "\n\n".join(filter(None, sections))
        
        if len(context) > self.max_context_size:
            context = self._compress_context(context, state)
        
        return context
    
    def _build_goal_section(self, state: AgentState) -> str:
        return f"""GOAL:
{state.goal}

ITERATION: {state.iteration}/{state.max_iterations}
STATUS: {state.status}"""
    
    def _build_plan_section(self, state: AgentState) -> str:
        if not state.plan:
            return ""
        
        plan_text = "PLAN:\n"
        for i, step in enumerate(state.plan):
            marker = "✓" if i < state.iteration else "○"
            plan_text += f"{marker} {i+1}. {step}\n"
        
        return plan_text
    
    def _build_open_files_section(self, state: AgentState) -> str:
        if not state.open_files:
            return ""

        files_text = f"AVAILABLE FILES - YOU CAN EDIT ANY OF THESE ({len(state.open_files)} files loaded):\n"
        files_text += "These files were automatically loaded based on dependencies.\n"
        files_text += "You can read, analyze, and MODIFY any of these files using apply_patch.\n\n"

        # List all available files first
        files_text += "FILES YOU CAN MODIFY:\n"
        for path in state.open_files.keys():
            files_text += f"  ✓ {path}\n"
        files_text += "\n"

        # Then show the content
        for path, content in state.open_files.items():
            files_text += f"\n=== FILE: {path} ===\n"
            lines = content.split('\n')
            if len(lines) > 50:
                files_text += '\n'.join(lines[:25]) + "\n... [truncated] ...\n" + '\n'.join(lines[-25:])
            else:
                files_text += content
            files_text += f"\n=== END OF {path} ===\n"

        return files_text
    
    def _build_errors_section(self, state: AgentState) -> str:
        if not state.last_errors:
            return ""
        
        errors_text = "RECENT ERRORS:\n"
        for error in state.last_errors[-3:]:
            errors_text += f"- {error}\n"
        
        return errors_text
    
    def _build_diffs_section(self, state: AgentState) -> str:
        if not state.recent_diffs:
            return ""
        
        diffs_text = "RECENT CHANGES:\n"
        for diff in state.recent_diffs[-5:]:
            diffs_text += f"{diff}\n"
        
        return diffs_text
    
    def _build_graph_section(self, state: AgentState) -> str:
        if not state.import_graph and not state.symbol_table:
            return ""
        
        graph_text = "CODE STRUCTURE:\n"
        
        if state.symbol_table:
            graph_text += "Symbols:\n"
            for file, symbols in list(state.symbol_table.items())[:5]:
                graph_text += f"  {file}: {', '.join(symbols[:10])}\n"
        
        if state.import_graph:
            graph_text += "\nImports:\n"
            for module, imports in list(state.import_graph.items())[:5]:
                graph_text += f"  {module} → {', '.join(imports)}\n"
        
        return graph_text
    
    def _compress_context(self, context: str, state: AgentState) -> str:
        sections = context.split('\n\n')
        
        compressed_sections = []
        for section in sections:
            if section.startswith('GOAL:') or section.startswith('RECENT ERRORS:'):
                compressed_sections.append(section)
            elif section.startswith('OPEN FILES:'):
                lines = section.split('\n')
                compressed_sections.append('\n'.join(lines[:30]))
            else:
                compressed_sections.append(section)
        
        return '\n\n'.join(compressed_sections)
    
    def build_tool_context(self) -> str:
        return """AVAILABLE TOOLS:

1. read_file(path: str) -> str
   Read the contents of a single file

2. read_file_with_dependencies(path: str, depth: int = 1) -> Dict
   Read a file AND all its related files from dependency graph
   Returns main file + all imported/importing files
   Use this to get full context when analyzing code

3. get_related_files(path: str, depth: int = 2) -> Dict
   Get list of files related through dependency graph
   Shows dependencies and dependents for each file

4. search_symbol(symbol: str, path: str = ".") -> List[Dict]
   Search for a symbol (function/class/variable) in the codebase

5. apply_patch(path: str, old_content: str, new_content: str) -> bool
   Apply changes to ANY file in the AVAILABLE FILES list
   You can modify file_b.py even if you started with file_a.py
   All loaded files are editable!

6. run_tests(test_path: str = None) -> Dict
   Run tests and return results

7. analyze_file(path: str) -> Dict
   Get AST analysis: symbols, imports, calls, classes, functions

8. get_dependencies(module: str) -> List[str]
   Get modules that this module imports

9. get_dependents(module: str) -> List[str]
   Get modules that import this module

10. find_references(symbol: str) -> List[Dict]
    Find all references to a symbol

RESPONSE FORMAT:
You must respond with valid JSON:

{
  "thought": "Your reasoning about what to do next",
  "action": "tool_name",
  "args": {"param": "value"},
  "next_step": "What you plan to do after this"
}

OR if task is complete:

{
  "thought": "Task completed successfully",
  "action": "DONE",
  "args": {},
  "summary": "What was accomplished"
}

RULES:
- ALL files in "AVAILABLE FILES" section are already loaded and ready to edit
- You can modify ANY file in the available files list using apply_patch
- If file_a.py imports file_b.py, BOTH files are available - you can edit both!
- Don't ask to open files - they're already open if they're in the available files list
- Use apply_patch on any available file directly
- When analyzing code, all imported and importing files are already loaded
- Inspect files before editing
- Use search_symbol and analyze_file to understand code structure
- Make small, focused changes
- Verify changes with tests when possible
- Check the "FILES YOU CAN MODIFY" list to see what's available"""
