from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.core.mcp_registry import MCPManager, MCPServer
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_mcp_status() -> Dict[str, Any]:
    """
    Get status of all registered MCP servers.
    Shows which are enabled, configured, and their capabilities.
    """
    try:
        status = MCPManager.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enabled")
async def get_enabled_mcps():
    """
    Get list of enabled MCP servers with their configurations.
    """
    try:
        enabled = MCPManager.get_enabled_servers()
        return {
            "count": len(enabled),
            "servers": [
                {
                    "name": mcp.name,
                    "display_name": mcp.display_name,
                    "description": mcp.description,
                    "capabilities": mcp.capabilities
                }
                for mcp in enabled
            ]
        }
    except Exception as e:
        logger.error(f"Error getting enabled MCPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/registry")
async def get_mcp_registry():
    """
    Get the complete MCP registry with all available servers.
    """
    try:
        all_servers = MCPManager.get_all_servers()
        return {
            "total": len(all_servers),
            "servers": [
                {
                    "name": mcp.name,
                    "display_name": mcp.display_name,
                    "description": mcp.description,
                    "transport": mcp.transport,
                    "capabilities": mcp.capabilities,
                    "enabled": mcp.is_enabled(),
                    "configured": mcp.get_config() is not None
                }
                for mcp in all_servers
            ]
        }
    except Exception as e:
        logger.error(f"Error getting MCP registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/env-template")
async def get_env_template():
    """
    Generate a .env template with all MCP configuration options.
    """
    try:
        template = MCPManager.generate_env_template()
        return {
            "template": template,
            "instructions": "Copy this template to your .env file and fill in the required values"
        }
    except Exception as e:
        logger.error(f"Error generating env template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/{mcp_name}")
async def test_mcp_connection(mcp_name: str):
    """
    Test connection to a specific MCP server.
    """
    try:
        # Find the MCP in registry
        mcp_server = None
        for mcp in MCPManager.get_all_servers():
            if mcp.name == mcp_name:
                mcp_server = mcp
                break
        
        if not mcp_server:
            raise HTTPException(status_code=404, detail=f"MCP '{mcp_name}' not found in registry")
        
        if not mcp_server.is_enabled():
            return {
                "status": "disabled",
                "message": f"MCP '{mcp_name}' is not enabled. Set {mcp_server.enable_env_var}=true"
            }
        
        config = mcp_server.get_config()
        if not config:
            missing_vars = []
            for var in mcp_server.required_env_vars:
                import os
                if not os.getenv(var):
                    missing_vars.append(var)
            
            return {
                "status": "not_configured",
                "message": f"MCP '{mcp_name}' is missing required configuration",
                "missing_vars": missing_vars
            }
        
        # Try to initialize MCP connection
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError:
            try:
                from langchain_mcp_adapters import MultiServerMCPClient
            except ImportError:
                return {
                    "status": "error",
                    "message": "langchain_mcp_adapters not properly installed"
                }
        
        test_config = {mcp_name: config}
        client = MultiServerMCPClient(test_config)
        
        # Try to get tools
        tools = await client.get_tools()
        
        return {
            "status": "connected",
            "message": f"Successfully connected to {mcp_name}",
            "tools_count": len(tools),
            "tools": [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools[:5]]  # First 5 tools
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing MCP {mcp_name}: {e}")
        return {
            "status": "error",
            "message": f"Failed to connect to {mcp_name}: {str(e)}"
        }