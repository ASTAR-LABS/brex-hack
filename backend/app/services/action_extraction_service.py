from typing import List, Dict, Any, Optional
from langchain_cerebras import ChatCerebras
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)


class ExtractedAction(BaseModel):
    type: str = Field(
        description="Type of action: task, meeting_item, github_action, calendar_event, idea, decision, update_action"
    )
    description: str = Field(description="Clear description of the action")
    confidence: float = Field(description="Confidence score between 0 and 1")
    target_id: Optional[str] = Field(description="For update_action type: ID of action to update", default=None)
    updates: Optional[Dict[str, Any]] = Field(description="For update_action type: fields to update", default=None)


class ActionsList(BaseModel):
    actions: List[ExtractedAction]


class ActionExtractionService:
    def __init__(self):
        self.use_agent = os.getenv("USE_AGENTIC_MODE", "false").lower() == "true"
        
        if not self.use_agent:
            # Traditional extraction mode
            if not settings.cerebras_api_key:
                logger.warning("CEREBRAS_API_KEY not set - action extraction will not work")
                self.llm = None
            else:
                self.llm = ChatCerebras(
                    api_key=settings.cerebras_api_key,
                    model=settings.cerebras_model,
                    temperature=settings.cerebras_temperature,
                    max_tokens=settings.cerebras_max_tokens,
                )
            
            self.parser = JsonOutputParser(pydantic_object=ActionsList)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an AI assistant that extracts actionable items from voice transcriptions where users speak commands naturally.

Already executed actions in this session:
{executed_actions}

Determine if the user wants to:
1. CREATE a new action (not similar to any executed action)
2. UPDATE an existing action (references like "that", "it", "the issue", or mentioning something already done)

Action types:
- task: To-do items or tasks
- meeting_item: Agenda items or meeting topics
- github_action: GitHub issues, PRs, commits
- calendar_event: Events or appointments
- idea: Creative ideas or brainstorming
- decision: Important decisions
- update_action: Update to a previous action

For UPDATE actions, set:
- type: "update_action"
- target_id: "last" (for most recent) or specific ID if identifiable
- updates: dict of fields to update (e.g., {{"priority": "high", "labels": ["bug"]}})
- description: What the update does

Common voice patterns:
- "Create an issue about X" → New github_action
- "Add priority high to that" → update_action on last action
- "Actually make it critical" → update_action on last action
- "The issue should have label bug" → update_action if issue exists

IMPORTANT:
- DO NOT create duplicate actions - check executed_actions first
- Be proactive - if someone mentions a problem, they likely want an issue
- Recognize follow-up commands that modify recent actions
- Use high confidence (0.8+) for clear commands

{format_instructions}
""",
                ),
                ("user", "Extract actionable items from this text: {text}"),
            ]
        )
    
    # Agent initialization is no longer needed - we use the new agent API directly
    
    async def extract_actions(self, text: str, session_token: Optional[str] = None, integration_config: Optional[Dict] = None, executed_actions: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            # Use new agent endpoint if enabled
            if self.use_agent:
                import httpx
                agent_base_url = os.getenv("API_URL", "http://localhost:8000")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{agent_base_url}/api/v1/agent/chat",
                        json={
                            "message": text,
                            "categories": ["github", "utility"],
                            "model": "gpt-oss-120b",
                            "session_token": session_token
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            # Convert tools_used to actions format
                            actions = []
                            for tool in result.get("tools_used", []):
                                actions.append({
                                    "type": "github_action" if "github" in tool else "task",
                                    "description": f"Executed {tool}",
                                    "confidence": 1.0
                                })
                            
                            return {
                                "actions": actions,
                                "agent_response": result.get("response", ""),
                                "error": None
                            }
                        else:
                            return {
                                "actions": [],
                                "error": result.get("error", "Agent processing failed")
                            }
                    else:
                        return {
                            "actions": [],
                            "error": f"Agent API error: {response.status_code}"
                        }
            
            # Fallback to traditional extraction
            if not self.llm:
                return {"actions": [], "error": "Cerebras API key not configured"}

            # Format executed actions for context
            executed_context = "\n".join(executed_actions) if executed_actions else "None"

            chain = self.prompt | self.llm | self.parser

            result = await chain.ainvoke(
                {
                    "text": text,
                    "executed_actions": executed_context,
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )

            return result

        except Exception as e:
            logger.error(f"Error extracting actions: {e}")
            return {"actions": [], "error": str(e)}
