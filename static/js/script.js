let file_path;
let agentState = null;

const editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
    mode: 'python',
    theme: 'dracula',
    lineNumbers: true,
    autoCloseBrackets: true,
    matchBrackets: true
});

async function fetchFileTree(path = null) {
    const response = await fetch(`/tree${path ? `?path=${encodeURIComponent(path)}` : ''}`);
    if (response.ok) {
        const fileTree = await response.json();
        displayFileTree(fileTree, document.getElementById('fileTree'), path);
    }
}

function displayFileTree(tree, container, currentPath) {
    container.innerHTML = '';

    if (currentPath) {
        const upElement = document.createElement('div');
        upElement.className = 'up-nav';
        upElement.textContent = '⬆️ Up';
        upElement.onclick = () => {
            const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/'));
            fetchFileTree(parentPath || null);
        };
        container.appendChild(upElement);
    }

    tree.forEach(item => {
        const element = document.createElement('div');
        element.className = item.type === 'directory' ? 'dir-item' : 'file-item';
        element.textContent = item.name;
        element.onclick = () => {
            if (item.type === 'directory') {
                fetchFileTree(item.path);
            } else {
                loadFile(item.path);
            }
        };
        container.appendChild(element);
    });
}

async function loadFile(filePath) {
    file_path = filePath;
    const response = await fetch(`/load-file?file_path=${encodeURIComponent(filePath)}`);
    if (response.ok) {
        const data = await response.json();
        editor.setValue(data.content);
        editor.setOption("mode", data.mode);
        addLog(`Loaded file: ${filePath}`);
    }
}

async function saveCode() {
    const code = editor.getValue();
    const response = await fetch("/save-file/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: file_path, content: code })
    });

    if (response.ok) {
        const result = await response.json();
        addLog(result.message);
    }
}

async function runAgent() {
    const task = document.getElementById('agentTask').value;
    const provider = document.getElementById('llmProvider').value;
    const apiKey = document.getElementById('apiKey').value;

    if (!task) {
        addLog("Error: Please specify a task", "error");
        return;
    }

    if (!apiKey && provider !== "demo" && provider !== "llmstudio") {
        addLog("Error: Please provide an API key", "error");
        return;
    }

    addLog("Initializing agent...", "info");
    addLog(`Task: ${task}`, "info");
    if (provider === "demo") {
        addLog("Running in DEMO MODE - simulated responses", "info");
    }
    if (provider === "llmstudio") {
        addLog("Connecting to LLM Studio at http://localhost:1234/v1", "info");
    }

    // Set appropriate default API key based on provider
    let defaultApiKey = "demo";
    if (provider === "llmstudio") {
        defaultApiKey = "not-needed";
    }

    const requestBody = {
        task,
        provider,
        api_key: apiKey || defaultApiKey,
        model: getDefaultModel(provider),
        current_file: file_path,
        root_path: "."
    };

    if (provider === "llmstudio") {
        requestBody.base_url = "http://localhost:1234/v1";
    }

    const response = await fetch("/agent/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
    });

    if (response.ok) {
        const result = await response.json();

        addLog(`Agent execution completed`, "success");
        addLog(`Status: ${result.state.status}`, "info");

        if (result.logs) {
            result.logs.forEach(log => {
                const type = log.type || "info";
                let message = log.message;

                if (log.thought) {
                    message = `💭 ${log.thought}\n${message}`;
                }

                addLog(message, type);
            });
        }

        if (result.state.open_files) {
            const files = Object.keys(result.state.open_files);
            if (files.length > 0) {
                addLog(`Files accessed: ${files.join(', ')}`, "info");
            }
        }

        if (result.state.recent_diffs && result.state.recent_diffs.length > 0) {
            addLog("Changes made to files", "success");
        }
    } else {
        addLog("Agent execution failed", "error");
    }
}

function addLog(message, type = "info") {
    const output = document.getElementById('agentOutput');
    const entry = document.createElement('div');
    entry.className = 'log-entry';

    if (type === "error") {
        entry.style.borderLeftColor = "#ff4444";
        entry.style.background = "rgba(255, 68, 68, 0.1)";
    } else if (type === "success") {
        entry.style.borderLeftColor = "#00ff9d";
        entry.style.background = "rgba(0, 255, 157, 0.1)";
    } else if (type === "action") {
        entry.style.borderLeftColor = "#8a2be2";
        entry.style.background = "rgba(138, 43, 226, 0.1)";
    }

    const time = document.createElement('div');
    time.className = 'log-time';
    time.textContent = new Date().toLocaleTimeString();

    const content = document.createElement('div');
    content.innerHTML = message.replace(/\n/g, '<br>');

    entry.appendChild(time);
    entry.appendChild(content);
    output.appendChild(entry);
    output.scrollTop = output.scrollHeight;
}

function getDefaultModel(provider) {
    const models = {
        'claude': 'claude-sonnet-4-20250514',
        'chatgpt': 'gpt-4',
        'gemini': 'gemini-pro',
        'llmstudio': 'local-model'
    };
    return models[provider];
}

document.getElementById('llmProvider').addEventListener('change', function() {
    const apiKeyGroup = document.getElementById('apiKeyGroup');

    if (this.value === 'llmstudio' || this.value === 'demo') {
        // Hide API key field for LLM Studio and Demo Mode
        apiKeyGroup.style.display = 'none';
    } else {
        // Show API key field for Claude, ChatGPT, and Gemini
        apiKeyGroup.style.display = 'flex';
    }
});

document.addEventListener('DOMContentLoaded', () => fetchFileTree());
