# MCP Integration Guide

## Overview
This guide explains how to add new Model Context Protocol (MCP) servers to the Ultrathink application. The system is designed to be scalable and standardized, allowing easy integration of new MCP servers without modifying core code.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Frontend (Next.js)                 │
│                                              │
│  - Voice Input → WebSocket → Backend        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        Backend (FastAPI + LangGraph)        │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │   Agentic Orchestrator              │     │
│  │   - LangGraph ReAct Agent           │     │
│  │   - Memory Service (BaseMessages)   │     │
│  │   - MCP Client Manager              │     │
│  └──────────────┬─────────────────────┘     │
│                 │                            │
│  ┌──────────────▼─────────────────────┐     │
│  │   MultiServerMCPClient              │     │
│  │   - Manages multiple MCP servers    │     │
│  │   - Converts to LangChain tools     │     │
│  └──────────────┬─────────────────────┘     │
└─────────────────┼────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────┐
│            MCP Servers (External)            │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Google   │  │  Slack   │  │  Notion  │  │
│  │ Calendar │  │   MCP    │  │   MCP    │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ GitHub   │  │ Database │  │  Custom  │  │
│  │   MCP    │  │   MCP    │  │   MCP    │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────────────────────────┘
```

## How to Add a New MCP Server

### Step 1: Install or Locate the MCP Server

#### Option A: NPM Package (Recommended)
```bash
# Install globally
npm install -g @modelcontextprotocol/server-[name]

# Or use npx (no installation needed)
npx @modelcontextprotocol/server-[name]
```

#### Option B: Custom MCP Server
Create your own MCP server following the [MCP specification](https://modelcontextprotocol.io/docs).

### Step 2: Add Configuration to `mcp_config.py`

Edit `/backend/app/core/mcp_config.py`:

```python
def get_mcp_servers_config() -> Dict[str, Any]:
    config = {}
    
    # Your new MCP server
    if os.getenv("ENABLE_YOUR_MCP", "false").lower() == "true":
        config["your_mcp_name"] = {
            # For stdio transport (local executable)
            "command": "npx",
            "args": ["@modelcontextprotocol/server-your-mcp"],
            "transport": "stdio",
            "env": {
                # Any environment variables the MCP needs
                "YOUR_API_KEY": os.getenv("YOUR_API_KEY", ""),
                "YOUR_CONFIG": os.getenv("YOUR_CONFIG", ""),
            }
        }
    
    # OR for HTTP transport
    your_mcp_url = os.getenv("YOUR_MCP_URL")
    if your_mcp_url:
        config["your_mcp_name"] = {
            "url": your_mcp_url,
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {os.getenv('YOUR_MCP_TOKEN', '')}"
            }
        }
    
    return config
```

### Step 3: Add Environment Variables

Add to `.env`:

```bash
# Enable your MCP
ENABLE_YOUR_MCP=true

# MCP-specific configuration
YOUR_API_KEY=your_api_key_here
YOUR_CONFIG=your_config_here

# OR for HTTP-based MCP
YOUR_MCP_URL=http://localhost:8001/mcp/
YOUR_MCP_TOKEN=your_token_here
```

### Step 4: That's It! 🎉

The system will automatically:
1. Load your MCP configuration on startup
2. Connect to the MCP server
3. Convert MCP tools to LangChain tools
4. Make them available to the agent
5. Handle authentication and execution

## Available MCP Servers

### Official MCP Servers
- `@modelcontextprotocol/server-google-calendar` - Google Calendar integration
- `@modelcontextprotocol/server-filesystem` - File system operations
- `@modelcontextprotocol/server-github` - GitHub integration
- `@modelcontextprotocol/server-gitlab` - GitLab integration
- `@modelcontextprotocol/server-slack` - Slack integration
- `@modelcontextprotocol/server-postgres` - PostgreSQL database
- `@modelcontextprotocol/server-sqlite` - SQLite database
- `@modelcontextprotocol/server-google-drive` - Google Drive
- `@modelcontextprotocol/server-notion` - Notion workspace

### Community MCP Servers
Check [MCP Hub](https://github.com/modelcontextprotocol/hub) for community-contributed servers.

## Example: Adding Slack Integration

### 1. Install Slack MCP
```bash
npm install -g @modelcontextprotocol/server-slack
```

### 2. Update `mcp_config.py`
```python
# Slack MCP Server
if os.getenv("ENABLE_SLACK_MCP", "false").lower() == "true":
    config["slack"] = {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-slack"],
        "transport": "stdio",
        "env": {
            "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", ""),
            "SLACK_APP_TOKEN": os.getenv("SLACK_APP_TOKEN", ""),
        }
    }
```

### 3. Configure Environment
```bash
# .env
ENABLE_SLACK_MCP=true
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

### 4. Use It!
The agent can now:
- Send Slack messages
- Read channels
- Create threads
- Upload files
- And more...

## Testing Your MCP Integration

### 1. Verify MCP Connection
```python
# backend/test_mcp.py
import asyncio
from app.services.agentic_orchestrator import AgenticOrchestrator

async def test_mcp():
    orchestrator = AgenticOrchestrator()
    await orchestrator.initialize()
    
    tools = await orchestrator.get_available_tools()
    print(f"Available tools: {tools}")
    
    # Test a request
    result = await orchestrator.process_request(
        "What tools do you have available?",
        session_token="test"
    )
    print(f"Agent response: {result}")

asyncio.run(test_mcp())
```

### 2. Check Logs
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python backend/run.py
```

### 3. Test via API
```bash
curl -X POST http://localhost:8000/api/v1/actions/extract \
  -H "Content-Type: application/json" \
  -H "X-Session-Token: your-session-token" \
  -d '{"text": "Send a message to the team Slack channel"}'
```

## Advanced Configuration

### Custom Tool Mapping
If an MCP server provides tools with names that conflict or need mapping:

```python
# In agentic_orchestrator.py
async def initialize(self, ...):
    # Get MCP tools
    mcp_tools = await self.mcp_client.get_tools()
    
    # Custom mapping or filtering
    for tool in mcp_tools:
        if tool.name == "conflicting_name":
            tool.name = f"mcp_{tool.name}"
        self.tools.append(tool)
```

### Dynamic MCP Loading
For user-specific MCP servers:

```python
def get_user_mcp_config(user_id: str) -> Dict:
    """Load user-specific MCP configuration"""
    user_prefs = load_user_preferences(user_id)
    config = {}
    
    for mcp in user_prefs.enabled_mcps:
        config[mcp.name] = {
            "command": mcp.command,
            "args": mcp.args,
            "transport": mcp.transport,
            "env": mcp.env
        }
    
    return config
```

## Troubleshooting

### MCP Not Connecting
1. Check environment variables are set
2. Verify MCP server is installed: `npm list -g | grep mcp`
3. Test MCP directly: `npx @modelcontextprotocol/server-name --test`
4. Check logs for connection errors

### Tools Not Appearing
1. Ensure MCP config returns tools
2. Check `get_available_tools()` output
3. Verify transport method matches MCP server

### Authentication Issues
1. Verify API keys/tokens in `.env`
2. Check MCP server documentation for auth requirements
3. Test credentials directly with the service

## Best Practices

1. **Use Environment Variables**: Never hardcode credentials
2. **Lazy Loading**: Only connect to MCPs when needed
3. **Error Handling**: MCPs can fail; handle gracefully
4. **Tool Namespacing**: Prefix tools if conflicts arise
5. **Documentation**: Document each MCP's capabilities
6. **Testing**: Test each MCP integration separately
7. **Monitoring**: Log MCP usage for debugging

## Security Considerations

1. **Credentials**: Store securely, never commit to git
2. **Permissions**: Limit MCP access to necessary resources
3. **Validation**: Validate MCP responses before execution
4. **Sandboxing**: Run untrusted MCPs in isolated environments
5. **Audit**: Log all MCP tool executions

## Future Enhancements

### Planned Features
- [ ] Hot-reload MCP configuration
- [ ] Web UI for MCP management
- [ ] MCP marketplace integration
- [ ] Custom MCP builder tool
- [ ] MCP performance monitoring
- [ ] Automatic MCP discovery

### Contributing
To contribute a new MCP integration:
1. Follow the standard pattern in `mcp_config.py`
2. Document environment variables
3. Add example usage
4. Submit PR with tests

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [LangGraph Documentation](https://langchain.com/langgraph)
- [MCP Server Examples](https://github.com/modelcontextprotocol/servers)
- [Community MCP Hub](https://github.com/modelcontextprotocol/hub)

---

**Remember**: The beauty of MCP is that you don't need to write integration code. Just configure, connect, and let the agent handle the rest! 🚀