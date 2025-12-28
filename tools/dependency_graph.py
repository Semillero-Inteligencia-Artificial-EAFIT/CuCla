import os
from pathlib import Path
from typing import Dict, List, Set
import networkx as nx
from .ast_analyzer import ASTAnalyzer

class DependencyGraph:
    
    def __init__(self):
        self.import_graph = nx.DiGraph()
        self.call_graph = nx.DiGraph()
        self.module_graph = nx.DiGraph()
        self.analyzer = ASTAnalyzer()
    
    def build_project_graph(self, root_path: str):
        python_files = []
        
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    python_files.append(filepath)
        
        for filepath in python_files:
            self._analyze_file(filepath)
        
        return {
            "import_graph": nx.node_link_data(self.import_graph),
            "call_graph": nx.node_link_data(self.call_graph),
            "module_graph": nx.node_link_data(self.module_graph),
            "files": python_files
        }
    
    def _analyze_file(self, filepath: str):
        analysis = self.analyzer.analyze_file(filepath)
        
        module_name = Path(filepath).stem
        self.module_graph.add_node(module_name, filepath=filepath)
        
        for imp in analysis['imports']:
            imported_module = self._extract_module_name(imp)
            if imported_module:
                self.import_graph.add_edge(module_name, imported_module)
                self.module_graph.add_edge(module_name, imported_module)
        
        for func in analysis['functions']:
            self.call_graph.add_node(f"{module_name}.{func}", type="function")
        
        for cls in analysis['classes']:
            self.call_graph.add_node(f"{module_name}.{cls}", type="class")
    
    def _extract_module_name(self, import_stmt: str) -> str:
        """Extract module name from import statement, handling relative imports."""
        if import_stmt.startswith('import '):
            module = import_stmt.replace('import ', '').split()[0]
        elif import_stmt.startswith('from '):
            parts = import_stmt.split()
            if len(parts) >= 2:
                module = parts[1]
            else:
                return ""
        else:
            return ""

        # Handle relative imports: .module or ..module
        if module.startswith('.'):
            module = module.lstrip('.')  # Remove leading dots

        # Filter out standard library and common external modules
        stdlib_modules = {
            'os', 'sys', 'json', 'pathlib', 'typing', 'dataclasses', 'abc',
            'ast', 'subprocess', 'io', 'collections', 'itertools', 're',
            'datetime', 'time', 'math', 'random', 'copy', 'functools',
            'anthropic', 'openai', 'google', 'networkx', 'fastapi'
        }

        # Get the root module name (before any dots)
        root_module = module.split('.')[0] if '.' in module else module

        # Filter out standard library and external modules
        if root_module in stdlib_modules:
            return ""

        # Return just the module name (not the full path)
        return root_module
    
    def get_dependencies(self, module: str) -> List[str]:
        if module in self.import_graph:
            return list(self.import_graph.successors(module))
        return []
    
    def get_dependents(self, module: str) -> List[str]:
        if module in self.import_graph:
            return list(self.import_graph.predecessors(module))
        return []
    
    def find_path(self, source: str, target: str) -> List[str]:
        if source in self.module_graph and target in self.module_graph:
            if nx.has_path(self.module_graph, source, target):
                return nx.shortest_path(self.module_graph, source, target)
        return []
    
    def get_related_modules(self, module: str, depth: int = 2) -> Set[str]:
        related = set()
        
        if module not in self.module_graph:
            return related
        
        related.add(module)
        
        deps = self.get_dependencies(module)
        for dep in deps:
            related.add(dep)
            if depth > 1:
                related.update(self.get_related_modules(dep, depth - 1))
        
        dependents = self.get_dependents(module)
        for dep in dependents:
            related.add(dep)
        
        return related
