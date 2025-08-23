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
        self.orchestrator = None
        
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
    
    async def initialize_agent(self, session_token: Optional[str] = None, integration_config: Optional[Dict] = None):
        """Initialize the agentic orchestrator if in agent mode"""
        if self.use_agent and not self.orchestrator:
            from app.services.agentic_orchestrator import AgenticOrchestrator
            self.orchestrator = AgenticOrchestrator()
            await self.orchestrator.initialize(session_token, integration_config)
            logger.info("Initialized agentic orchestrator")
    
    async def extract_actions(self, text: str, session_token: Optional[str] = None, integration_config: Optional[Dict] = None, executed_actions: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            # Use agentic mode if enabled
            if self.use_agent:
                if not self.orchestrator:
                    await self.initialize_agent(session_token, integration_config)
                
                if self.orchestrator:
                    # Use the agent to process the request
                    result = await self.orchestrator.process_request(
                        text=text,
                        session_token=session_token or "anonymous"
                    )
                    
                    # Convert agent result to expected format
                    if "error" not in result or not result["error"]:
                        return {
                            "actions": result.get("actions", []),
                            "agent_response": result.get("result", ""),
                            "error": None
                        }
                    else:
                        return {
                            "actions": [],
                            "error": result.get("error")
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
