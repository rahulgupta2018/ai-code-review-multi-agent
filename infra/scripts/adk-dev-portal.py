#!/usr/bin/env python3
"""
Custom ADK Development Portal
Provides a web interface for ADK development and monitoring
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ADK imports
try:
    import google.cloud.aiplatform
    from vertexai.agent_engines.templates import adk
    ADK_AVAILABLE = True
except ImportError as e:
    print(f"ADK libraries not available: {e}")
    ADK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API versioning configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

app = FastAPI(
    title="ADK Development Portal", 
    version="1.0.0",
    description="Custom ADK Development Portal with versioned API endpoints"
)

# Configuration
ADK_WORKSPACE = os.getenv("ADK_WORKSPACE", "/app/adk-workspace")
ADK_DEV_PORTAL_PORT = int(os.getenv("ADK_DEV_PORTAL_PORT", "8200"))
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")


class ADKDevPortal:
    """ADK Development Portal backend"""
    
    def __init__(self):
        self.workspace_path = Path(ADK_WORKSPACE)
        self.sessions_path = self.workspace_path / "sessions"
        self.tools_path = self.workspace_path / "tools"
        self.logs_path = self.workspace_path / "logs"
        self.cache_path = self.workspace_path / "cache"
        
        # Ensure directories exist
        for path in [self.sessions_path, self.tools_path, self.logs_path, self.cache_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "adk_available": ADK_AVAILABLE,
            "adk_version": self._get_adk_version(),
            "workspace": str(self.workspace_path),
            "project_id": GOOGLE_CLOUD_PROJECT_ID,
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_adk_version(self) -> str:
        """Get ADK version"""
        try:
            if ADK_AVAILABLE:
                return adk.get_adk_version()
            return "Not available"
        except Exception as e:
            return f"Error: {e}"
    
    def get_workspace_status(self) -> Dict[str, Any]:
        """Get workspace status"""
        try:
            return {
                "workspace_path": str(self.workspace_path),
                "sessions_count": len(list(self.sessions_path.glob("*"))),
                "tools_count": len(list(self.tools_path.glob("*"))),
                "logs_count": len(list(self.logs_path.glob("*"))),
                "cache_size": self._get_dir_size(self.cache_path),
                "last_activity": self._get_last_activity()
            }
        except Exception as e:
            logger.error(f"Error getting workspace status: {e}")
            return {"error": str(e)}
    
    def _get_dir_size(self, path: Path) -> int:
        """Get directory size in bytes"""
        try:
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        except Exception:
            return 0
    
    def _get_last_activity(self) -> Optional[str]:
        """Get timestamp of last activity"""
        try:
            latest_file = max(
                self.workspace_path.rglob('*'),
                key=lambda x: x.stat().st_mtime if x.is_file() else 0,
                default=None
            )
            if latest_file:
                return datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
            return None
        except Exception:
            return None
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available ADK tools"""
        tools = []
        try:
            # Check our custom tools
            tools_dir = Path("/app/src/tools")
            if tools_dir.exists():
                for tool_dir in tools_dir.iterdir():
                    if tool_dir.is_dir() and not tool_dir.name.startswith('__'):
                        tools.append({
                            "name": tool_dir.name,
                            "type": "custom",
                            "path": str(tool_dir),
                            "files": [f.name for f in tool_dir.glob("*.py")]
                        })
            
            # Add ADK built-in tools if available
            if ADK_AVAILABLE:
                tools.append({
                    "name": "adk_core",
                    "type": "builtin", 
                    "description": "Core ADK functionality",
                    "version": self._get_adk_version()
                })
            
        except Exception as e:
            logger.error(f"Error getting tools: {e}")
        
        return tools
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        logs = []
        try:
            for log_file in self.logs_path.glob("*.log"):
                if log_file.is_file():
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-limit:]:
                            if line.strip():
                                logs.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "file": log_file.name,
                                    "message": line.strip()
                                })
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
        
        return logs[-limit:]


# Initialize portal
portal = ADKDevPortal()

# HTML template for the portal
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADK Development Portal</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .status-ok { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        .logs { background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace; max-height: 300px; overflow-y: auto; }
        h1, h2 { color: #333; margin: 0 0 15px 0; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ADK Development Portal</h1>
            <div>
                <span class="status-badge {{adk_status_class}}">ADK {{adk_status}}</span>
                <span style="margin-left: 10px;">Version: {{adk_version}}</span>
                <button class="refresh-btn" onclick="location.reload()">Refresh</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>📊 System Information</h2>
                <p><strong>Workspace:</strong> {{workspace}}</p>
                <p><strong>Project ID:</strong> {{project_id}}</p>
                <p><strong>Python:</strong> {{python_version}}</p>
                <p><strong>Last Updated:</strong> {{timestamp}}</p>
            </div>
            
            <div class="card">
                <h2>📁 Workspace Status</h2>
                <div id="workspace-status">Loading...</div>
            </div>
        </div>
        
        <div class="card">
            <h2>🛠️ Available Tools</h2>
            <div id="tools-list">Loading...</div>
        </div>
        
        <div class="card">
            <h2>📝 Recent Activity</h2>
            <div class="logs" id="logs">Loading...</div>
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                // Load workspace status
                const workspaceRes = await fetch('/api/v1/workspace/status');
                const workspaceData = await workspaceRes.json();
                document.getElementById('workspace-status').innerHTML = `
                    <p><strong>Sessions:</strong> ${workspaceData.sessions_count}</p>
                    <p><strong>Tools:</strong> ${workspaceData.tools_count}</p>
                    <p><strong>Log Files:</strong> ${workspaceData.logs_count}</p>
                    <p><strong>Cache Size:</strong> ${(workspaceData.cache_size / 1024).toFixed(1)} KB</p>
                `;
                
                // Load tools
                const toolsRes = await fetch('/api/v1/tools');
                const toolsData = await toolsRes.json();
                document.getElementById('tools-list').innerHTML = toolsData.map(tool => `
                    <div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        <strong>${tool.name}</strong> (${tool.type})
                        ${tool.files ? '<br><small>Files: ' + tool.files.join(', ') + '</small>' : ''}
                    </div>
                `).join('');
                
                // Load logs
                const logsRes = await fetch('/api/v1/logs');
                const logsData = await logsRes.json();
                document.getElementById('logs').innerHTML = logsData.map(log => 
                    `<div>${log.timestamp}: ${log.message}</div>`
                ).join('');
                
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        loadData();
        setInterval(loadData, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def portal_home():
    """Serve the portal homepage"""
    info = portal.get_system_info()
    
    template_vars = {
        "adk_status": "Available" if info["adk_available"] else "Not Available",
        "adk_status_class": "status-ok" if info["adk_available"] else "status-error",
        "adk_version": info["adk_version"],
        "workspace": info["workspace"],
        "project_id": info["project_id"] or "Not configured",
        "python_version": info["python_version"].split()[0],
        "timestamp": info["timestamp"]
    }
    
    html_content = HTML_TEMPLATE
    for key, value in template_vars.items():
        html_content = html_content.replace("{{" + key + "}}", str(value))
    
    return HTMLResponse(content=html_content)


@app.get(f"{API_PREFIX}/version")
async def api_version():
    """Get API version information"""
    return JSONResponse({
        "api_version": API_VERSION,
        "portal_version": app.version,
        "supported_endpoints": [
            f"{API_PREFIX}/system/info",
            f"{API_PREFIX}/workspace/status", 
            f"{API_PREFIX}/tools",
            f"{API_PREFIX}/logs",
            f"{API_PREFIX}/version"
        ],
        "deprecated_endpoints": [
            "/api/system/info",
            "/api/workspace/status",
            "/api/tools", 
            "/api/logs"
        ]
    })


@app.get(f"{API_PREFIX}/system/info")
async def api_system_info():
    """Get system information"""
    return JSONResponse(portal.get_system_info())


@app.get(f"{API_PREFIX}/workspace/status")
async def api_workspace_status():
    """Get workspace status"""
    return JSONResponse(portal.get_workspace_status())


@app.get(f"{API_PREFIX}/tools")
async def api_tools():
    """Get available tools"""
    return JSONResponse(portal.get_available_tools())


@app.get(f"{API_PREFIX}/logs")
async def api_logs():
    """Get recent logs"""
    return JSONResponse(portal.get_recent_logs())


# Legacy API endpoints (deprecated but maintained for backward compatibility)
@app.get("/api/system/info")
async def api_system_info_legacy():
    """Get system information (deprecated - use /api/v1/system/info)"""
    logger.warning("Using deprecated API endpoint /api/system/info - please use /api/v1/system/info")
    return JSONResponse(portal.get_system_info())


@app.get("/api/workspace/status")
async def api_workspace_status_legacy():
    """Get workspace status (deprecated - use /api/v1/workspace/status)"""
    logger.warning("Using deprecated API endpoint /api/workspace/status - please use /api/v1/workspace/status")
    return JSONResponse(portal.get_workspace_status())


@app.get("/api/tools")
async def api_tools_legacy():
    """Get available tools (deprecated - use /api/v1/tools)"""
    logger.warning("Using deprecated API endpoint /api/tools - please use /api/v1/tools")
    return JSONResponse(portal.get_available_tools())


@app.get("/api/logs")
async def api_logs_legacy():
    """Get recent logs (deprecated - use /api/v1/logs)"""
    logger.warning("Using deprecated API endpoint /api/logs - please use /api/v1/logs")
    return JSONResponse(portal.get_recent_logs())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    logger.info(f"Starting ADK Development Portal on port {ADK_DEV_PORTAL_PORT}")
    logger.info(f"Workspace: {ADK_WORKSPACE}")
    logger.info(f"ADK Available: {ADK_AVAILABLE}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ADK_DEV_PORTAL_PORT,
        log_level="info"
    )