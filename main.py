from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import json
from tools.agent_controller import AgentController
from tools.tool_executor import ToolExecutor

app = FastAPI()

# Mount the static directory to serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

active_agents = {}

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/tree")
def get_file_tree(path: str = None):
    def walk_directory(path):
        tree = []
        for entry in sorted(os.listdir(path)):
            if entry.startswith('.'):
                continue
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                tree.append({"name": entry, "type": "directory", "path": full_path})
            else:
                tree.append({"name": entry, "type": "file", "path": full_path})
        return tree

    path = path or str(Path.home())
    return JSONResponse(content=walk_directory(path))

@app.get("/load-file")
async def load_file(file_path: str):
    with open(file_path, "r") as f:
        content = f.read()

    extension = Path(file_path).suffix
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".html": "htmlmixed",
        ".css": "css",
        ".json": "application/json",
        ".java": "text/x-java",
        ".cpp": "text/x-c++src",
        ".c": "text/x-csrc",
        ".md": "markdown",
        ".xml": "xml",
        ".rb": "ruby",
        ".sh": "shell",
    }
    mode = language_map.get(extension, "plaintext")
    return {"content": content, "mode": mode, "file_path": file_path}

@app.post("/save-file/")
async def save_file(request: Request):
    data = await request.json()
    file_path = data.get("file_path")
    content = data.get("content")

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return {"message": "File saved successfully"}

@app.post("/agent/execute")
async def agent_execute(request: Request):
    data = await request.json()
    task = data.get("task")
    provider = data.get("provider")
    api_key = data.get("api_key")
    model = data.get("model")
    current_file = data.get("current_file")
    root_path = data.get("root_path", ".")
    base_url = data.get("base_url")

    agent_id = f"agent_{len(active_agents)}"

    controller = AgentController(root_path)
    state = controller.initialize(task, current_file)

    active_agents[agent_id] = controller

    logs = controller.execute_loop(provider, api_key, model, base_url)

    final_state = controller.get_state()

    return {
        "agent_id": agent_id,
        "state": final_state,
        "logs": logs
    }

@app.post("/agent/tool")
async def agent_tool(request: Request):
    data = await request.json()
    tool_name = data.get("tool")
    params = data.get("params", {})
    root_path = data.get("root_path", ".")
    
    executor = ToolExecutor(root_path)
    result = executor.execute(tool_name, params)
    
    return result

@app.get("/agent/state/{agent_id}")
async def get_agent_state(agent_id: str):
    if agent_id in active_agents:
        return active_agents[agent_id].get_state()
    return {"error": "Agent not found"}