"""
MCP Registry - Centralized catalog of available MCP servers
This makes it easy to add new MCPs without modifying code
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum
import os
import json

class TransportType(str, Enum):
    STDIO = "stdio"
    HTTP = "streamable_http"
    SSE = "sse"

class MCPServer(BaseModel):
    """Definition of an MCP server"""
    name: str
    display_name: str
    description: str
    transport: TransportType
    
    # For stdio transport
    command: Optional[str] = None
    args: Optional[List[str]] = None
    
    # For HTTP transport
    url_env_var: Optional[str] = None  # Environment variable containing URL
    
    # Environment variables needed
    required_env_vars: List[str] = []
    optional_env_vars: List[str] = []
    
    # Capabilities
    capabilities: List[str] = []
    
    # Enable flag env var
    enable_env_var: str
    
    def is_enabled(self) -> bool:
        """Check if this MCP is enabled"""
        return os.getenv(self.enable_env_var, "false").lower() == "true"
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """Get configuration for this MCP server"""
        if not self.is_enabled():
            return None
        
        config: Dict[str, Any] = {
            "transport": self.transport.value
        }
        
        if self.transport == TransportType.STDIO:
            config["command"] = self.command or "npx"
            config["args"] = self.args or []
            
        elif self.transport in [TransportType.HTTP, TransportType.SSE]:
            if self.url_env_var:
                url = os.getenv(self.url_env_var)
                if url:
                    config["url"] = url
                else:
                    return None  # URL not configured
        
        # Add environment variables
        env = {}
        for var in self.required_env_vars:
            value = os.getenv(var)
            if not value:
                return None  # Required var missing
            env[var] = value
        
        for var in self.optional_env_vars:
            value = os.getenv(var)
            if value:
                env[var] = value
        
        if env:
            config["env"] = env
        
        return config

# MCP Server Registry - Add new servers here!
MCP_REGISTRY: List[MCPServer] = [
    
    # Google Calendar
    MCPServer(
        name="google_calendar",
        display_name="Google Calendar",
        description="Manage Google Calendar events, check availability, schedule meetings",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-google-calendar"],
        enable_env_var="ENABLE_GOOGLE_CALENDAR_MCP",
        required_env_vars=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        optional_env_vars=["GOOGLE_REDIRECT_URI"],
        capabilities=["calendar.read", "calendar.write", "calendar.availability"]
    ),
    
    # GitHub
    MCPServer(
        name="github",
        display_name="GitHub",
        description="Create issues, PRs, manage repositories",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-github"],
        enable_env_var="ENABLE_GITHUB_MCP",
        required_env_vars=["GITHUB_TOKEN"],
        optional_env_vars=["GITHUB_OWNER", "GITHUB_REPO"],
        capabilities=["issues.create", "pr.create", "pr.comment", "repo.read"]
    ),
    
    # Slack
    MCPServer(
        name="slack",
        display_name="Slack",
        description="Send messages, read channels, manage workspace",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-slack"],
        enable_env_var="ENABLE_SLACK_MCP",
        required_env_vars=["SLACK_BOT_TOKEN"],
        optional_env_vars=["SLACK_APP_TOKEN", "SLACK_DEFAULT_CHANNEL"],
        capabilities=["message.send", "channel.read", "file.upload"]
    ),
    
    # Filesystem
    MCPServer(
        name="filesystem",
        display_name="File System",
        description="Read, write, and manage local files",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-filesystem"],
        enable_env_var="ENABLE_FILESYSTEM_MCP",
        optional_env_vars=["FILESYSTEM_ROOT"],
        capabilities=["file.read", "file.write", "file.delete", "directory.list"]
    ),
    
    # PostgreSQL
    MCPServer(
        name="postgres",
        display_name="PostgreSQL",
        description="Execute SQL queries, manage database",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-postgres"],
        enable_env_var="ENABLE_POSTGRES_MCP",
        required_env_vars=["POSTGRES_CONNECTION_STRING"],
        capabilities=["query.execute", "schema.read", "data.write"]
    ),
    
    # Notion
    MCPServer(
        name="notion",
        display_name="Notion",
        description="Create pages, manage databases, search workspace",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-notion"],
        enable_env_var="ENABLE_NOTION_MCP",
        required_env_vars=["NOTION_API_KEY"],
        optional_env_vars=["NOTION_DEFAULT_DATABASE"],
        capabilities=["page.create", "database.query", "search"]
    ),
    
    # Google Drive
    MCPServer(
        name="google_drive",
        display_name="Google Drive",
        description="Upload, download, and manage Google Drive files",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-google-drive"],
        enable_env_var="ENABLE_GOOGLE_DRIVE_MCP",
        required_env_vars=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        capabilities=["file.upload", "file.download", "file.search", "folder.create"]
    ),
    
    # Linear
    MCPServer(
        name="linear",
        display_name="Linear",
        description="Create and manage Linear issues, projects, and cycles",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-linear"],
        enable_env_var="ENABLE_LINEAR_MCP",
        required_env_vars=["LINEAR_API_KEY"],
        optional_env_vars=["LINEAR_DEFAULT_TEAM"],
        capabilities=["issue.create", "issue.update", "project.manage", "cycle.track"]
    ),
    
    # Jira
    MCPServer(
        name="jira",
        display_name="Jira",
        description="Create and manage Jira issues, sprints, and projects",
        transport=TransportType.STDIO,
        command="npx",
        args=["@modelcontextprotocol/server-jira"],
        enable_env_var="ENABLE_JIRA_MCP",
        required_env_vars=["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"],
        optional_env_vars=["JIRA_DEFAULT_PROJECT"],
        capabilities=["issue.create", "issue.update", "sprint.manage", "board.read"]
    ),
    
    # Custom HTTP MCP Example
    MCPServer(
        name="custom_api",
        display_name="Custom API",
        description="Your custom MCP server",
        transport=TransportType.HTTP,
        url_env_var="CUSTOM_MCP_URL",
        enable_env_var="ENABLE_CUSTOM_MCP",
        optional_env_vars=["CUSTOM_MCP_TOKEN"],
        capabilities=["custom.action"]
    ),
]

class MCPManager:
    """Manages MCP server configurations"""
    
    @staticmethod
    def get_enabled_servers() -> List[MCPServer]:
        """Get list of enabled MCP servers"""
        return [mcp for mcp in MCP_REGISTRY if mcp.is_enabled()]
    
    @staticmethod
    def get_all_servers() -> List[MCPServer]:
        """Get all registered MCP servers"""
        return MCP_REGISTRY
    
    @staticmethod
    def get_mcp_config() -> Dict[str, Any]:
        """Get configuration for all enabled MCP servers"""
        config = {}
        
        for mcp in MCP_REGISTRY:
            if mcp.is_enabled():
                mcp_config = mcp.get_config()
                if mcp_config:
                    config[mcp.name] = mcp_config
                else:
                    print(f"Warning: MCP {mcp.name} is enabled but not properly configured")
        
        return config
    
    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Get status of all MCP servers"""
        status = {
            "total": len(MCP_REGISTRY),
            "enabled": len([m for m in MCP_REGISTRY if m.is_enabled()]),
            "servers": []
        }
        
        for mcp in MCP_REGISTRY:
            server_status = {
                "name": mcp.name,
                "display_name": mcp.display_name,
                "enabled": mcp.is_enabled(),
                "configured": mcp.get_config() is not None,
                "capabilities": mcp.capabilities
            }
            
            # Check missing requirements
            if not server_status["configured"] and mcp.is_enabled():
                missing = []
                for var in mcp.required_env_vars:
                    if not os.getenv(var):
                        missing.append(var)
                server_status["missing_vars"] = missing
            
            status["servers"].append(server_status)
        
        return status
    
    @staticmethod
    def add_server(server: MCPServer):
        """Add a new server to the registry"""
        MCP_REGISTRY.append(server)
    
    @staticmethod
    def generate_env_template() -> str:
        """Generate .env template for all MCPs"""
        lines = ["# MCP Server Configuration\n# Generated from MCP Registry\n"]
        
        for mcp in MCP_REGISTRY:
            lines.append(f"\n# {mcp.display_name} - {mcp.description}")
            lines.append(f"{mcp.enable_env_var}=false  # Set to true to enable")
            
            if mcp.required_env_vars:
                lines.append("# Required:")
                for var in mcp.required_env_vars:
                    lines.append(f"{var}=")
            
            if mcp.optional_env_vars:
                lines.append("# Optional:")
                for var in mcp.optional_env_vars:
                    lines.append(f"# {var}=")
            
            if mcp.url_env_var:
                lines.append(f"{mcp.url_env_var}=http://localhost:8000/mcp/")
        
        return "\n".join(lines)

# Update the existing get_mcp_servers_config to use the registry
def get_mcp_servers_config() -> Dict[str, Any]:
    """Get MCP configuration from the registry"""
    return MCPManager.get_mcp_config()