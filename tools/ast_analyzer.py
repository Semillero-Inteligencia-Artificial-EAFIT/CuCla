import ast
from typing import Dict, List, Set
from pathlib import Path

class ASTAnalyzer:
    
    def __init__(self):
        self.symbol_table = {}
        self.import_graph = {}
        self.call_graph = {}
    
    def analyze_python_file(self, filepath: str, content: str = None) -> Dict:
        if content is None:
            with open(filepath, 'r') as f:
                content = f.read()
        
        tree = ast.parse(content)
        
        visitor = SymbolVisitor(filepath)
        visitor.visit(tree)
        
        return {
            "symbols": visitor.symbols,
            "imports": visitor.imports,
            "calls": visitor.calls,
            "classes": visitor.classes,
            "functions": visitor.functions
        }
    
    def analyze_javascript_file(self, filepath: str, content: str = None) -> Dict:
        if content is None:
            with open(filepath, 'r') as f:
                content = f.read()
        
        symbols = []
        imports = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
            elif 'function ' in line or 'const ' in line or 'let ' in line or 'var ' in line:
                symbols.append(line[:50])
        
        return {
            "symbols": symbols,
            "imports": imports,
            "calls": [],
            "classes": [],
            "functions": []
        }
    
    def analyze_file(self, filepath: str, content: str = None) -> Dict:
        ext = Path(filepath).suffix
        
        if ext == '.py':
            return self.analyze_python_file(filepath, content)
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            return self.analyze_javascript_file(filepath, content)
        else:
            return {
                "symbols": [],
                "imports": [],
                "calls": [],
                "classes": [],
                "functions": []
            }
    
    def find_symbol_definition(self, symbol: str, files: List[str]) -> List[Dict]:
        results = []
        
        for filepath in files:
            analysis = self.analyze_file(filepath)
            
            for func in analysis['functions']:
                if symbol in func:
                    results.append({
                        "file": filepath,
                        "type": "function",
                        "name": func,
                        "line": 0
                    })
            
            for cls in analysis['classes']:
                if symbol in cls:
                    results.append({
                        "file": filepath,
                        "type": "class",
                        "name": cls,
                        "line": 0
                    })
        
        return results
    
    def find_references(self, symbol: str, files: List[str]) -> List[Dict]:
        results = []
        
        for filepath in files:
            with open(filepath, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if symbol in line:
                        results.append({
                            "file": filepath,
                            "line": i + 1,
                            "content": line.strip()
                        })
        
        return results

class SymbolVisitor(ast.NodeVisitor):
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.symbols = []
        self.imports = []
        self.calls = []
        self.classes = []
        self.functions = []
    
    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.symbols.append(f"function:{node.name}")
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.functions.append(node.name)
        self.symbols.append(f"async_function:{node.name}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self.symbols.append(f"class:{node.name}")
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(f"import {alias.name}")
    
    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"from {module} import {alias.name}")
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)
        self.generic_visit(node)
