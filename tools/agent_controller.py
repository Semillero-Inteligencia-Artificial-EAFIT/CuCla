import json
from typing import Dict, Optional
from .agent_state import AgentState
from .context_builder import ContextBuilder
from .tool_executor import ToolExecutor
from .llm_client import LLMChat

class AgentController:
    
    def __init__(self, root_path: str = "."):
        self.root_path = root_path
        self.state: Optional[AgentState] = None
        self.context_builder = ContextBuilder()
        self.tool_executor = ToolExecutor(root_path)
    
    def initialize(self, goal: str, current_file: Optional[str] = None) -> AgentState:
        self.state = AgentState(
            goal=goal,
            current_file=current_file,
            status="running"
        )

        if current_file:
            # Read file with its dependencies from the graph
            file_with_deps = self.tool_executor.read_file_with_dependencies(current_file, depth=2)

            # Add main file
            self.state.open_files[current_file] = file_with_deps["main_file"]["content"]

            # Add related files
            loaded_files = [current_file]
            for module, file_data in file_with_deps["related_files"].items():
                file_path = file_data["path"]
                self.state.open_files[file_path] = file_data["content"]
                loaded_files.append(file_path)

            # Log what was loaded
            print(f"[INIT] Loaded {len(loaded_files)} files:")
            for f in loaded_files:
                print(f"  - {f}")

            # Analyze main file
            analysis = self.tool_executor.analyze_file(current_file)
            self.state.symbol_table[current_file] = analysis["symbols"]

            # Build import graph for context
            self._build_import_graph(current_file)

            # Also analyze related files to build complete symbol table
            for file_path in loaded_files:
                if file_path != current_file:
                    try:
                        analysis = self.tool_executor.analyze_file(file_path)
                        self.state.symbol_table[file_path] = analysis["symbols"]
                    except:
                        pass

        self.state.plan = self._generate_initial_plan(goal)

        return self.state
    
    def _generate_initial_plan(self, goal: str) -> list:
        goal_lower = goal.lower()
        
        if "refactor" in goal_lower:
            return [
                "Analyze current implementation",
                "Identify code to refactor",
                "Apply refactoring",
                "Verify changes"
            ]
        elif "add" in goal_lower or "implement" in goal_lower:
            return [
                "Locate relevant files",
                "Understand existing structure",
                "Implement changes",
                "Test implementation"
            ]
        elif "fix" in goal_lower or "bug" in goal_lower:
            return [
                "Identify bug location",
                "Understand root cause",
                "Apply fix",
                "Verify fix works"
            ]
        elif "find" in goal_lower or "search" in goal_lower:
            return [
                "Search for relevant code",
                "Analyze findings",
                "Report results"
            ]
        else:
            return [
                "Understand requirement",
                "Locate relevant code",
                "Make changes",
                "Verify"
            ]

    def _build_import_graph(self, file_path: str):
        """Build import graph for the current file and its dependencies."""
        try:
            analysis = self.tool_executor.analyze_file(file_path)
            module_name = file_path.replace('.py', '').replace('/', '.')

            if analysis.get("imports"):
                self.state.import_graph[module_name] = analysis["imports"]
        except Exception as e:
            pass  # Skip if analysis fails

    def execute_loop(self, provider: str, api_key: str, model: str = None, base_url: str = None) -> list:
        logs = []

        while self.state.iteration < self.state.max_iterations and self.state.status == "running":
            self.state.increment_iteration()

            logs.append({
                "iteration": self.state.iteration,
                "type": "info",
                "message": f"Starting iteration {self.state.iteration}/{self.state.max_iterations}"
            })

            context = self.context_builder.build_context(self.state)
            tool_context = self.context_builder.build_tool_context()

            full_prompt = f"""{tool_context}

{context}

Based on the above context, decide your next action. Respond with JSON only."""

            logs.append({
                "iteration": self.state.iteration,
                "type": "llm_call",
                "message": "Calling LLM for next action"
            })

            llm_response = self._call_llm(provider, api_key, model, full_prompt, base_url)
            
            logs.append({
                "iteration": self.state.iteration,
                "type": "llm_response",
                "message": llm_response[:200]
            })
            
            action = None
            parse_error = None
            parsed_json = llm_response.strip()
            
            if parsed_json.startswith("```json"):
                parsed_json = parsed_json[7:]
            if parsed_json.startswith("```"):
                parsed_json = parsed_json[3:]
            if parsed_json.endswith("```"):
                parsed_json = parsed_json[:-3]
            parsed_json = parsed_json.strip()
            
            if parsed_json:
                action = json.loads(parsed_json)
            
            if not action or "action" not in action:
                logs.append({
                    "iteration": self.state.iteration,
                    "type": "error",
                    "message": f"Failed to parse LLM response: {parse_error or 'Invalid format'}"
                })
                self.state.add_error(f"Parse error: {parse_error or 'Invalid format'}")
                continue
            
            if action["action"] == "DONE":
                logs.append({
                    "iteration": self.state.iteration,
                    "type": "success",
                    "message": f"Task completed: {action.get('summary', 'Done')}"
                })
                self.state.status = "completed"
                break
            
            logs.append({
                "iteration": self.state.iteration,
                "type": "action",
                "message": f"Executing: {action['action']}",
                "thought": action.get("thought", "")
            })
            
            result = None
            exec_error = None
            result = self._execute_action(action)
            
            logs.append({
                "iteration": self.state.iteration,
                "type": "result",
                "message": str(result)[:200] if result else f"Error: {exec_error}"
            })
            
            if result:
                self.state.add_action(action["action"], action.get("args", {}), result)
                
                if "error" in result:
                    self.state.add_error(str(result["error"]))
                
                if action["action"] == "apply_patch" and "diff" in result:
                    self.state.add_diff(result["diff"])
            else:
                self.state.add_error(f"Tool execution failed: {exec_error}")
        
        if self.state.iteration >= self.state.max_iterations:
            self.state.status = "max_iterations_reached"
            logs.append({
                "iteration": self.state.iteration,
                "type": "warning",
                "message": "Maximum iterations reached"
            })
        
        return logs
    
    def _call_llm(self, provider: str, api_key: str, model: Optional[str], prompt: str, base_url: Optional[str] = None) -> str:
        if not model:
            model = self._get_default_model(provider)

        if provider == "demo" or not api_key or api_key == "demo":
            return self._demo_llm_response(prompt)

        if provider == "claude":
            return LLMChat.claude(prompt, api_key, model)
        elif provider == "chatgpt":
            return LLMChat.chatgpt(prompt, api_key, model)
        elif provider == "gemini":
            return LLMChat.gemini(prompt, api_key, model)
        elif provider == "llmstudio":
            if not base_url:
                return "{\"error\": \"LLM Studio requires a base_url parameter\"}"
            return LLMChat.llmstudio(prompt, base_url, api_key or "not-needed", model)
        else:
            return "{\"error\": \"Unknown provider\"}"
    
    def _demo_llm_response(self, prompt: str) -> str:
        if "find" in self.state.goal.lower() or "search" in self.state.goal.lower():
            symbol = "parse"
            for word in self.state.goal.split():
                if len(word) > 3 and word not in ["find", "search", "the", "all", "for"]:
                    symbol = word
                    break
            
            if self.state.iteration == 1:
                return json.dumps({
                    "thought": f"I need to search for '{symbol}' in the codebase",
                    "action": "search_symbol",
                    "args": {"symbol": symbol, "path": "."},
                    "next_step": "Analyze the results"
                })
            else:
                return json.dumps({
                    "thought": "Search completed, task done",
                    "action": "DONE",
                    "args": {},
                    "summary": f"Found occurrences of '{symbol}'"
                })
        
        elif "analyze" in self.state.goal.lower():
            if self.state.current_file and self.state.iteration == 1:
                return json.dumps({
                    "thought": "Analyzing the current file",
                    "action": "analyze_file",
                    "args": {"path": self.state.current_file},
                    "next_step": "Report findings"
                })
            else:
                return json.dumps({
                    "thought": "Analysis complete",
                    "action": "DONE",
                    "args": {},
                    "summary": "File analyzed successfully"
                })
        
        elif "read" in self.state.goal.lower():
            if self.state.current_file and self.state.iteration == 1:
                return json.dumps({
                    "thought": "Reading the file",
                    "action": "read_file",
                    "args": {"path": self.state.current_file},
                    "next_step": "Display content"
                })
            else:
                return json.dumps({
                    "thought": "File read complete",
                    "action": "DONE",
                    "args": {},
                    "summary": "File contents retrieved"
                })
        
        else:
            if self.state.iteration == 1 and self.state.current_file:
                return json.dumps({
                    "thought": "Let me analyze the current file first",
                    "action": "analyze_file",
                    "args": {"path": self.state.current_file},
                    "next_step": "Understand the code structure"
                })
            elif self.state.iteration == 2:
                return json.dumps({
                    "thought": "Searching for relevant code",
                    "action": "search_symbol",
                    "args": {"symbol": "function", "path": "."},
                    "next_step": "Review findings"
                })
            else:
                return json.dumps({
                    "thought": "Task exploration complete",
                    "action": "DONE",
                    "args": {},
                    "summary": "Completed exploratory analysis"
                })
    
    
    def _get_default_model(self, provider: str) -> str:
        models = {
            "claude": "claude-sonnet-4-20250514",
            "chatgpt": "gpt-4",
            "gemini": "gemini-pro"
        }
        return models.get(provider, "claude-sonnet-4-20250514")
    
    def _parse_action(self, llm_response: str) -> Optional[Dict]:
        cleaned = llm_response.strip()
        
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        if not cleaned:
            return None
        
        if cleaned.lower() == "done" or "done" in cleaned.lower():
            return {"action": "DONE", "thought": "Task completed", "args": {}}
        
        parsed = json.loads(cleaned)
        return parsed
    
    def _execute_action(self, action: Dict) -> Dict:
        tool_name = action.get("action")
        args = action.get("args", {})

        # Automatically expand read_file to read_file_with_dependencies
        if tool_name == "read_file":
            tool_name = "read_file_with_dependencies"
            if "depth" not in args:
                args["depth"] = 1

        result = self.tool_executor.execute(tool_name, args)

        # Handle read_file_with_dependencies results
        if "main_file" in result and "related_files" in result:
            # Add main file
            main_file = result["main_file"]
            if main_file.get("path") and main_file.get("content"):
                self.state.open_files[main_file["path"]] = main_file["content"]

            # Add all related files to state (will be included in LLM context)
            related_count = 0
            related_paths = []
            for module, file_data in result.get("related_files", {}).items():
                if file_data.get("path") and file_data.get("content"):
                    self.state.open_files[file_data["path"]] = file_data["content"]
                    related_paths.append(file_data["path"])
                    related_count += 1

            # Log what was loaded
            print(f"[EXEC] read_file expanded to {related_count + 1} files:")
            print(f"  Main: {main_file.get('path')}")
            for path in related_paths:
                print(f"  Related: {path}")
            print(f"  Total files in context: {len(self.state.open_files)}")

            # Create enhanced result showing what was loaded
            enhanced_result = {
                "path": main_file.get("path"),
                "content": main_file.get("content"),
                "lines": main_file.get("lines"),
                "related_files_loaded": related_count,
                "related_files": related_paths,
                "total_files_in_context": len(self.state.open_files)
            }

            return enhanced_result

        # Handle regular read_file results
        if "content" in result and len(result["content"]) > 0:
            path = result.get("path")
            if path and path not in self.state.open_files:
                self.state.open_files[path] = result["content"]

        if "symbols" in result:
            path = result.get("path")
            if path:
                self.state.symbol_table[path] = result["symbols"]

        if "dependencies" in result:
            module = result.get("module")
            if module:
                self.state.import_graph[module] = result["dependencies"]
        
        return result
    
    def get_state(self) -> Dict:
        if self.state:
            return self.state.to_dict()
        return {}