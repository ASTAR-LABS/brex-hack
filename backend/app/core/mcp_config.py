"""
MCP Configuration - Uses the centralized MCP Registry
"""
from app.core.mcp_registry import MCPManager

def get_mcp_servers_config():
    """
    Get MCP configuration from the registry.
    To add new MCPs, update mcp_registry.py instead of this file.
    """
    return MCPManager.get_mcp_config()

def get_mcp_setup_instructions() -> str:
    """Return instructions for setting up MCP servers"""
    return """
    # MCP Server Setup Instructions
    
    ## Google Calendar MCP
    1. Get Google OAuth credentials from https://console.cloud.google.com/
    2. Add to .env:
       ENABLE_GOOGLE_CALENDAR_MCP=true
       GOOGLE_CLIENT_ID=your_client_id
       GOOGLE_CLIENT_SECRET=your_client_secret
       GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
    
    ## Filesystem MCP
    1. Add to .env:
       ENABLE_FILESYSTEM_MCP=true
       FILESYSTEM_ROOT=/path/to/allowed/directory
    
    ## Available MCP Servers:
    - @modelcontextprotocol/server-google-calendar
    - @modelcontextprotocol/server-filesystem
    - @modelcontextprotocol/server-github
    - @modelcontextprotocol/server-gitlab
    - @modelcontextprotocol/server-slack
    - @modelcontextprotocol/server-postgres
    
    Install any server with: npm install -g @modelcontextprotocol/server-name
    Or use without installing: npx @modelcontextprotocol/server-name
    """