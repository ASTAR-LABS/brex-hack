from typing import Dict, Any, List, Optional

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError:
    try:
        from langchain_mcp_adapters import MultiServerMCPClient
    except ImportError:
        MultiServerMCPClient = None
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_cerebras import ChatCerebras
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.core.config import settings
from app.core.mcp_config import get_mcp_servers_config
from app.integrations.github_integration import GitHubIntegration
from app.services.memory_service import MemoryService
import logging
import json
import os

logger = logging.getLogger(__name__)


class AgenticOrchestrator:
    def __init__(self):
        self.mcp_client = None
        self.agent = None
        self.tools = []
        self.memory_service = MemoryService()
        self.github_integration = None

    async def initialize(
        self,
        session_token: Optional[str] = None,
        integration_config: Optional[Dict] = None,
    ):
        """Initialize the orchestrator with MCP servers and tools"""
        try:
            # Initialize GitHub as a native tool (until we have GitHub MCP)
            if integration_config and integration_config.get("github_token"):
                self.github_integration = GitHubIntegration(
                    token=integration_config.get("github_token"),
                    owner=integration_config.get("github_owner"),
                    repo=integration_config.get("github_repo"),
                )

            # Initialize MCP servers
            mcp_config = get_mcp_servers_config()

            if mcp_config and MultiServerMCPClient:
                try:
                    self.mcp_client = MultiServerMCPClient(mcp_config)
                    # Get tools from MCP servers
                    mcp_tools = await self.mcp_client.get_tools()
                    self.tools.extend(mcp_tools)
                except Exception as e:
                    logger.warning(f"Failed to initialize MCP client: {e}")
            elif not MultiServerMCPClient:
                logger.warning(
                    "langchain_mcp_adapters not properly installed - MCP features disabled"
                )

            # Add native tools
            native_tools = self._get_native_tools()
            self.tools.extend(native_tools)

            # Initialize the LLM
            if settings.cerebras_api_key:
                llm = ChatCerebras(
                    api_key=settings.cerebras_api_key,
                    model=settings.cerebras_model,
                    temperature=0.7,
                )
            elif os.getenv("OPENAI_API_KEY"):
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.7,
                )
            else:
                logger.error("No LLM API key configured")
                return

            # Create the ReAct agent with available tools
            if self.tools:
                self.agent = create_react_agent(llm, self.tools)
            else:
                # Fallback to simple LLM if no tools available
                self.agent = llm

            logger.info(f"Initialized orchestrator with {len(self.tools)} tools")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    def _get_native_tools(self) -> List:
        """Get native tools that aren't MCP servers yet"""
        tools = []

        # GitHub tools (until GitHub MCP is available)
        if self.github_integration:
            from langchain_core.tools import Tool

            tools.append(
                Tool(
                    name="create_github_issue",
                    description="Create a GitHub issue with a title and body",
                    func=lambda input: self._run_async_tool(
                        self.github_integration.create_issue, **json.loads(input)
                    ),
                )
            )

            tools.append(
                Tool(
                    name="create_pr_comment",
                    description="Add a comment to a GitHub pull request",
                    func=lambda input: self._run_async_tool(
                        self.github_integration.create_pr_comment, **json.loads(input)
                    ),
                )
            )

        return tools

    def _run_async_tool(self, async_func, **kwargs):
        """Helper to run async functions in sync context"""
        import asyncio
        import concurrent.futures
        
        # Use ThreadPoolExecutor to run async function in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, async_func(**kwargs))
            return future.result()

    async def process_request(
        self, text: str, session_token: str, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process a user request using the agent"""
        try:
            if not self.agent:
                return {"error": "Agent not initialized", "actions": []}

            # Get conversation history from memory service
            messages: List[BaseMessage] = await self.memory_service.get_messages(
                session_token
            )

            # Add system prompt if this is start of conversation
            if not messages:
                system_prompt = """You are an AI assistant that helps users by planning and executing tasks.
                When given a request, break it down into actionable steps and execute them using available tools.
                Be proactive in checking for conflicts, gathering necessary information, and confirming success.
                Always explain what you're doing and provide clear results."""
                messages.append(SystemMessage(content=system_prompt))

            # Add current request
            human_msg = HumanMessage(content=text)
            messages.append(human_msg)

            # Process with agent
            if hasattr(self.agent, "ainvoke"):
                # Full agent with tools
                result = await self.agent.ainvoke({"messages": messages})

                # Extract actions from the result
                actions = self._extract_actions_from_result(result)

                # Store conversation in memory
                if "messages" in result and result["messages"]:
                    # Add the human message and AI response to memory
                    new_messages = [human_msg]
                    if isinstance(result["messages"][-1], BaseMessage):
                        new_messages.append(result["messages"][-1])
                    await self.memory_service.add_messages(session_token, new_messages)

                return {
                    "actions": actions,
                    "result": (
                        result.get("messages", [])[-1].content
                        if "messages" in result
                        else str(result)
                    ),
                    "error": None,
                }
            else:
                # Fallback to simple LLM
                response = await self.agent.ainvoke(messages)

                # Store conversation in memory
                await self.memory_service.add_messages(
                    session_token, [human_msg, response]
                )

                return {"actions": [], "result": response.content, "error": None}

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {"error": str(e), "actions": []}

    def _extract_actions_from_result(self, result: Dict) -> List[Dict]:
        """Extract structured actions from agent result"""
        actions = []

        # Parse tool calls from the agent's execution
        if "messages" in result:
            for message in result["messages"]:
                if hasattr(message, "tool_calls"):
                    for tool_call in message.tool_calls:
                        actions.append(
                            {
                                "type": tool_call["name"],
                                "description": f"Called {tool_call['name']} with {tool_call.get('args', {})}",
                                "confidence": 1.0,
                                "status": "completed",
                            }
                        )

        return actions

    async def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return [
            tool.name if hasattr(tool, "name") else str(tool) for tool in self.tools
        ]

    async def clear_history(self, session_token: str):
        """Clear conversation history for a session"""
        history = self.memory_service.get_session_history(session_token)
        history.clear()
        logger.info(f"Cleared conversation history for session {session_token}")
