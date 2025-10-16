#!/usr/bin/env python3
"""
ADK Development Portal
A simple web interface for managing and monitoring the AI Code Review Multi-Agent system.
"""

import os
import sys
import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Basic configuration
ADK_WORKSPACE = os.getenv('ADK_WORKSPACE', '/app/adk-workspace')
API_HOST = os.getenv('ADK_DEV_PORTAL_HOST', '0.0.0.0')
API_PORT = int(os.getenv('ADK_DEV_PORTAL_PORT', '8200'))

# Create FastAPI app
app = FastAPI(
    title="ADK Development Portal",
    description="Development portal for AI Code Review Multi-Agent system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Simple HTML templates
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADK Development Portal</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status.running { background: #d4edda; color: #155724; }
        .status.stopped { background: #f8d7da; color: #721c24; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #dee2e6;
        }
        .card h3 {
            margin-top: 0;
            color: #495057;
        }
        .list {
            list-style: none;
            padding: 0;
        }
        .list li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .list li:last-child {
            border-bottom: none;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #0056b3;
        }
        .log-viewer {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 ADK Development Portal</h1>
            <p>AI Code Review Multi-Agent System Development Environment</p>
            <span class="status running">System Running</span>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📊 System Status</h3>
                <ul class="list">
                    <li><strong>Environment:</strong> {{ environment }}</li>
                    <li><strong>ADK Workspace:</strong> {{ workspace }}</li>
                    <li><strong>API Status:</strong> <span class="status running">Running</span></li>
                    <li><strong>Portal Started:</strong> {{ start_time }}</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>🔧 Quick Actions</h3>
                <ul class="list">
                    <li><a href="/api/health" class="btn">Check API Health</a></li>
                    <li><a href="/api/docs" class="btn">API Documentation</a></li>
                    <li><a href="/workspace" class="btn">Browse Workspace</a></li>
                    <li><a href="/logs" class="btn">View Logs</a></li>
                </ul>
            </div>
            
            <div class="card">
                <h3>📁 Workspace Structure</h3>
                <ul class="list">
                    <li>📂 agents/ - Agent configurations</li>
                    <li>📂 sessions/ - Active sessions</li>
                    <li>📂 tools/ - Tool integrations</li>
                    <li>📂 workflows/ - Workflow definitions</li>
                    <li>📂 reports/ - Generated reports</li>
                    <li>📂 data/ - Analysis data</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>🚀 Development Tools</h3>
                <ul class="list">
                    <li><a href="http://localhost:8000" target="_blank">Main API (Port 8000)</a></li>
                    <li><a href="http://localhost:8081" target="_blank">Redis Commander</a></li>
                    <li><a href="http://localhost:8082" target="_blank">File Browser</a></li>
                    <li><a href="/metrics" class="btn">System Metrics</a></li>
                </ul>
            </div>
        </div>
        
        <div class="card">
            <h3>📋 Recent Activity</h3>
            <div class="log-viewer" id="logs">
                Loading recent activity...
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh logs every 5 seconds
        function refreshLogs() {
            fetch('/api/recent-logs')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('logs').innerHTML = data.logs.join('\\n');
                })
                .catch(error => {
                    document.getElementById('logs').innerHTML = 'Error loading logs: ' + error;
                });
        }
        
        // Initial load and setup auto-refresh
        refreshLogs();
        setInterval(refreshLogs, 5000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard page."""
    return HTML_TEMPLATE.replace(
        "{{ environment }}", os.getenv('ENVIRONMENT', 'development')
    ).replace(
        "{{ workspace }}", ADK_WORKSPACE
    ).replace(
        "{{ start_time }}", datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "workspace": ADK_WORKSPACE,
        "version": "1.0.0"
    }

@app.get("/api/workspace")
async def get_workspace_info():
    """Get workspace information."""
    workspace_path = Path(ADK_WORKSPACE)
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    def scan_directory(path: Path) -> Dict[str, Any]:
        """Recursively scan directory structure."""
        result = {
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": path.stat().st_size if path.is_file() else 0,
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        }
        
        if path.is_dir():
            try:
                result["children"] = [
                    scan_directory(child) 
                    for child in sorted(path.iterdir())
                    if not child.name.startswith('.')
                ]
            except PermissionError:
                result["children"] = []
        
        return result
    
    return {
        "workspace": ADK_WORKSPACE,
        "structure": scan_directory(workspace_path)
    }

@app.get("/api/recent-logs")
async def get_recent_logs():
    """Get recent log entries."""
    logs = [
        f"[{datetime.now().strftime('%H:%M:%S')}] ADK Development Portal started",
        f"[{datetime.now().strftime('%H:%M:%S')}] Workspace: {ADK_WORKSPACE}",
        f"[{datetime.now().strftime('%H:%M:%S')}] Environment: {os.getenv('ENVIRONMENT', 'development')}",
        f"[{datetime.now().strftime('%H:%M:%S')}] All systems operational"
    ]
    
    # Try to read actual log files if they exist
    log_dirs = ['/app/logs', f'{ADK_WORKSPACE}/logs']
    for log_dir in log_dirs:
        log_path = Path(log_dir)
        if log_path.exists():
            for log_file in log_path.glob('*.log'):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()[-10:]  # Last 10 lines
                        logs.extend([line.strip() for line in lines if line.strip()])
                except Exception:
                    continue
    
    return {"logs": logs[-20:]}  # Return last 20 log entries

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics."""
    import psutil
    
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent
        },
        "workspace_size": sum(
            f.stat().st_size for f in Path(ADK_WORKSPACE).rglob('*') if f.is_file()
        ) if Path(ADK_WORKSPACE).exists() else 0
    }

@app.get("/workspace")
async def workspace_browser():
    """Simple workspace file browser."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Workspace Browser</title>
        <style>
            body { font-family: monospace; padding: 20px; }
            .file { margin: 5px 0; }
            .directory { font-weight: bold; color: #0066cc; }
        </style>
    </head>
    <body>
        <h1>📁 Workspace Browser</h1>
        <div id="content">Loading...</div>
        <script>
            fetch('/api/workspace')
                .then(response => response.json())
                .then(data => {
                    function renderStructure(item, level = 0) {
                        const indent = '  '.repeat(level);
                        if (item.type === 'directory') {
                            let html = `<div class="file directory">${indent}📁 ${item.name}/</div>`;
                            if (item.children) {
                                for (const child of item.children) {
                                    html += renderStructure(child, level + 1);
                                }
                            }
                            return html;
                        } else {
                            return `<div class="file">${indent}📄 ${item.name} (${Math.round(item.size/1024)}KB)</div>`;
                        }
                    }
                    document.getElementById('content').innerHTML = renderStructure(data.structure);
                })
                .catch(error => {
                    document.getElementById('content').innerHTML = 'Error: ' + error;
                });
        </script>
    </body>
    </html>
    """)

def main():
    """Main entry point."""
    global ADK_WORKSPACE  # Declare global at the beginning
    
    parser = argparse.ArgumentParser(description='ADK Development Portal')
    parser.add_argument('--host', default=API_HOST, help='Host to bind to')
    parser.add_argument('--port', type=int, default=API_PORT, help='Port to bind to')
    parser.add_argument('--workspace', default=ADK_WORKSPACE, help='ADK workspace path')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    # Update global workspace path
    ADK_WORKSPACE = args.workspace
    
    print(f"🚀 Starting ADK Development Portal")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Workspace: {args.workspace}")
    print(f"   Portal URL: http://{args.host}:{args.port}")
    
    # Start the server
    uvicorn.run(
        "adk-dev-portal:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        access_log=False
    )

if __name__ == "__main__":
    main()