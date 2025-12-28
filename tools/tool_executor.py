import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from .ast_analyzer import ASTAnalyzer
from .dependency_graph import DependencyGraph

class ToolExecutor:
    
    def __init__(self, root_path: str = "."):
        self.root_path = root_path
        self.analyzer = ASTAnalyzer()
        self.dep_graph = DependencyGraph()
        self.graph_built = False
    
    def execute(self, tool_name: str, args: Dict) -> Dict:
        if tool_name == "read_file":
            return self.read_file(args.get("path"))

        elif tool_name == "read_file_with_dependencies":
            return self.read_file_with_dependencies(args.get("path"), args.get("depth", 1))

        elif tool_name == "search_symbol":
            return self.search_symbol(args.get("symbol"), args.get("path", "."))

        elif tool_name == "apply_patch":
            return self.apply_patch(args.get("path"), args.get("old_content"), args.get("new_content"))

        elif tool_name == "run_tests":
            return self.run_tests(args.get("test_path"))

        elif tool_name == "analyze_file":
            return self.analyze_file(args.get("path"))

        elif tool_name == "get_dependencies":
            return self.get_dependencies(args.get("module"))

        elif tool_name == "get_dependents":
            return self.get_dependents(args.get("module"))

        elif tool_name == "find_references":
            return self.find_references(args.get("symbol"))

        elif tool_name == "list_files":
            return self.list_files(args.get("path", "."))

        elif tool_name == "get_related_files":
            return self.get_related_files(args.get("path"), args.get("depth", 2))

        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def read_file(self, path: str) -> Dict:
        full_path = os.path.join(self.root_path, path) if not os.path.isabs(path) else path
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        return {
            "path": path,
            "content": content,
            "lines": len(content.split('\n'))
        }
    
    def search_symbol(self, symbol: str, path: str = ".") -> Dict:
        search_path = os.path.join(self.root_path, path) if not os.path.isabs(path) else path
        results = []
        
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c')):
                    filepath = os.path.join(root, file)
                    
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if symbol in line:
                                results.append({
                                    "file": filepath,
                                    "line": i + 1,
                                    "content": line.strip()
                                })
        
        return {"symbol": symbol, "results": results, "count": len(results)}
    
    def apply_patch(self, path: str, old_content: str, new_content: str) -> Dict:
        full_path = os.path.join(self.root_path, path) if not os.path.isabs(path) else path
        
        with open(full_path, 'r') as f:
            current = f.read()
        
        if old_content not in current:
            return {"error": "Old content not found in file", "success": False}
        
        updated = current.replace(old_content, new_content)
        
        with open(full_path, 'w') as f:
            f.write(updated)
        
        diff = self._create_diff(old_content, new_content)
        
        return {
            "success": True,
            "path": path,
            "diff": diff,
            "changes": len(new_content) - len(old_content)
        }
    
    def _create_diff(self, old: str, new: str) -> str:
        old_lines = old.split('\n')
        new_lines = new.split('\n')
        
        diff = f"@@ -{len(old_lines)} +{len(new_lines)} @@\n"
        
        for line in old_lines:
            diff += f"- {line}\n"
        
        for line in new_lines:
            diff += f"+ {line}\n"
        
        return diff
    
    def run_tests(self, test_path: Optional[str] = None) -> Dict:
        cmd = ["python", "-m", "pytest"]
        
        if test_path:
            cmd.append(test_path)
        
        result = subprocess.run(
            cmd,
            cwd=self.root_path,
            capture_output=True,
            text=True
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def analyze_file(self, path: str) -> Dict:
        full_path = os.path.join(self.root_path, path) if not os.path.isabs(path) else path
        
        analysis = self.analyzer.analyze_file(full_path)
        
        return {
            "path": path,
            "symbols": analysis["symbols"],
            "imports": analysis["imports"],
            "calls": analysis["calls"],
            "classes": analysis["classes"],
            "functions": analysis["functions"]
        }
    
    def get_dependencies(self, module: str) -> Dict:
        if not self.graph_built:
            self.dep_graph.build_project_graph(self.root_path)
            self.graph_built = True
        
        deps = self.dep_graph.get_dependencies(module)
        
        return {
            "module": module,
            "dependencies": deps,
            "count": len(deps)
        }
    
    def get_dependents(self, module: str) -> Dict:
        if not self.graph_built:
            self.dep_graph.build_project_graph(self.root_path)
            self.graph_built = True
        
        dependents = self.dep_graph.get_dependents(module)
        
        return {
            "module": module,
            "dependents": dependents,
            "count": len(dependents)
        }
    
    def find_references(self, symbol: str) -> Dict:
        results = []
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                    filepath = os.path.join(root, file)
                    
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if symbol in line:
                                results.append({
                                    "file": filepath,
                                    "line": i + 1,
                                    "content": line.strip()
                                })
        
        return {"symbol": symbol, "references": results, "count": len(results)}
    
    def list_files(self, path: str = ".") -> Dict:
        search_path = os.path.join(self.root_path, path) if not os.path.isabs(path) else path

        files = []
        for entry in os.listdir(search_path):
            full_path = os.path.join(search_path, entry)
            files.append({
                "name": entry,
                "type": "directory" if os.path.isdir(full_path) else "file",
                "path": full_path
            })

        return {"path": path, "files": files, "count": len(files)}

    def read_file_with_dependencies(self, path: str, depth: int = 1) -> Dict:
        """Read a file and all its related files from the dependency graph."""
        if not self.graph_built:
            print(f"[DEP_GRAPH] Building dependency graph for: {self.root_path}")
            self.dep_graph.build_project_graph(self.root_path)
            self.graph_built = True
            print(f"[DEP_GRAPH] Graph built. Total modules: {len(self.dep_graph.module_graph.nodes)}")

        # Read the main file
        main_file = self.read_file(path)

        # Get the module name from path
        module_name = Path(path).stem
        print(f"[DEP_GRAPH] Looking for dependencies of module: {module_name}")

        # Get related modules
        related_modules = self.dep_graph.get_related_modules(module_name, depth)
        print(f"[DEP_GRAPH] Found {len(related_modules)} related modules: {related_modules}")

        # Read all related files
        related_files = {}
        for module in related_modules:
            if module == module_name:
                continue  # Skip the main file

            # Find the file path for this module
            module_path = self._find_module_path(module)
            if module_path and os.path.exists(module_path):
                try:
                    with open(module_path, 'r') as f:
                        related_files[module] = {
                            "path": module_path,
                            "content": f.read()
                        }
                    print(f"[DEP_GRAPH] Loaded: {module} -> {module_path}")
                except Exception as e:
                    print(f"[DEP_GRAPH] Failed to load {module}: {e}")
            else:
                print(f"[DEP_GRAPH] Module not found: {module}")

        print(f"[DEP_GRAPH] Total files loaded: {len(related_files) + 1}")

        return {
            "main_file": main_file,
            "related_files": related_files,
            "module": module_name,
            "related_count": len(related_files)
        }

    def get_related_files(self, path: str, depth: int = 2) -> Dict:
        """Get list of files related through dependency graph."""
        if not self.graph_built:
            self.dep_graph.build_project_graph(self.root_path)
            self.graph_built = True

        module_name = Path(path).stem
        related_modules = self.dep_graph.get_related_modules(module_name, depth)

        related_info = []
        for module in related_modules:
            module_path = self._find_module_path(module)
            if module_path:
                deps = self.dep_graph.get_dependencies(module)
                dependents = self.dep_graph.get_dependents(module)
                related_info.append({
                    "module": module,
                    "path": module_path,
                    "dependencies": deps,
                    "dependents": dependents
                })

        return {
            "module": module_name,
            "related_modules": related_info,
            "count": len(related_info)
        }

    def _find_module_path(self, module_name: str) -> Optional[str]:
        """Find the file path for a given module name."""
        # Check if it's in the module graph
        if module_name in self.dep_graph.module_graph.nodes:
            node_data = self.dep_graph.module_graph.nodes[module_name]
            if 'filepath' in node_data:
                return node_data['filepath']

        # Search for the file in the project
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for file in files:
                if file == f"{module_name}.py":
                    return os.path.join(root, file)

        return None
