from typing import Annotated, Sequence, TypedDict, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    """State that gets passed between nodes in the graph"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_token: Optional[str]
    context: Optional[Dict[str, Any]]
    user_role: Optional[str]  # For permission-based tool access