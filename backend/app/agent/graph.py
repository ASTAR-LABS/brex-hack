"""LangGraph agent with conditional routing"""
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_cerebras import ChatCerebras
from typing import Optional, List, Dict, Any
import os
import logging

from .state import GraphState
from .tools import get_tools, get_tool_descriptions

logger = logging.getLogger(__name__)


def create_llm(model: str = "gpt-oss-120b", temperature: float = 0.7):
    """Create LLM instance - using Cerebras."""
    from app.core.config import settings
    if not settings.cerebras_api_key:
        raise ValueError("CEREBRAS_API_KEY not configured")
    
    # Always use Cerebras
    return ChatCerebras(
        api_key=settings.cerebras_api_key,
        model=model,  # Use the specified model
        temperature=temperature
    )


def should_continue(state: GraphState) -> str:
    """Decide whether to call tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if LLM wants to use tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return END


def create_agent(
    enabled_categories: Optional[List[str]] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    user_role: Optional[str] = None
):
    """Create agent with tools bound."""
    llm = create_llm(model, temperature)
    tools = get_tools(enabled_categories, user_role=user_role)
    
    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm
    
    def agent(state: GraphState):
        """Agent node that processes messages."""
        try:
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"Agent error: {e}")
            error_msg = AIMessage(content=f"I encountered an error: {str(e)}")
            return {"messages": [error_msg]}
    
    return agent


def create_graph(
    enabled_categories: Optional[List[str]] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    user_role: Optional[str] = None
):
    """Create the complete graph with conditional routing."""
    # Get tools and create agent
    tools = get_tools(enabled_categories, user_role=user_role)
    agent = create_agent(enabled_categories, model, temperature, user_role)
    
    # Build graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("agent", agent)
    
    if tools:
        workflow.add_node("tools", ToolNode(tools))
        
        # Define flow with tools
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        workflow.add_edge("tools", "agent")
    else:
        # Simple flow without tools
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)
    
    # Compile
    return workflow.compile()


# High-level convenience functions
async def chat(
    message: str,
    categories: Optional[List[str]] = None,
    model: str = "gpt-oss-120b",
    system_prompt: Optional[str] = None,
    session_token: Optional[str] = None,
    user_role: Optional[str] = None
) -> Dict[str, Any]:
    """Process a chat message and return the response.
    
    Args:
        message: User message to process
        categories: Tool categories to enable (default: all)
        model: LLM model to use
        system_prompt: Custom system prompt (optional)
        session_token: Session identifier (optional)
        user_role: User role for permissions (optional)
    
    Returns:
        Dict with response and metadata
    """
    try:
        # Default categories if not specified
        if categories is None:
            categories = ["github", "utility"]  # Safe defaults
        
        graph = create_graph(
            enabled_categories=categories,
            model=model,
            user_role=user_role
        )
        
        # Build system prompt
        if not system_prompt:
            default_repo = os.getenv("GITHUB_REPO", "")
            default_owner = os.getenv("GITHUB_OWNER", "")
            
            system_prompt = f"""You are a helpful AI assistant with access to various tools.
Be concise and clear in your responses. Use tools when appropriate to help the user.

Default GitHub repository: {default_owner}/{default_repo}
When asked about GitHub operations without specifying a repo, use this default."""
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        # Invoke graph
        result = await graph.ainvoke({
            "messages": messages,
            "session_token": session_token,
            "user_role": user_role
        })
        
        # Extract response
        final_message = result["messages"][-1]
        
        # Check if tools were used
        tools_used = []
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tools_used.append(tool_call["name"])
        
        return {
            "response": final_message.content,
            "tools_used": tools_used,
            "session_token": session_token,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "response": f"I encountered an error: {str(e)}",
            "tools_used": [],
            "session_token": session_token,
            "success": False,
            "error": str(e)
        }


async def stream_response(
    message: str,
    categories: Optional[List[str]] = None,
    model: str = "gpt-4o-mini",
    system_prompt: Optional[str] = None,
    session_token: Optional[str] = None,
    user_role: Optional[str] = None
):
    """Stream responses token by token.
    
    Yields:
        Chunks of response text or tool events
    """
    try:
        if categories is None:
            categories = ["github", "utility"]
        
        graph = create_graph(
            enabled_categories=categories,
            model=model,
            user_role=user_role
        )
        
        if not system_prompt:
            default_repo = os.getenv("GITHUB_REPO", "")
            default_owner = os.getenv("GITHUB_OWNER", "")
            system_prompt = f"You are a helpful AI assistant. Default GitHub: {default_owner}/{default_repo}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=message)
        ]
        
        async for event in graph.astream_events(
            {"messages": messages, "session_token": session_token, "user_role": user_role},
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                if "content" in event["data"]["chunk"]:
                    yield event["data"]["chunk"]["content"]
            
            elif event["event"] == "on_tool_start":
                yield f"\n🔧 Using tool: {event['name']}\n"
            
            elif event["event"] == "on_tool_end":
                yield f"✅ Tool completed\n"
                
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"\n❌ Error: {str(e)}"