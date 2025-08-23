from typing import List, Dict, Any
from langchain_cerebras import ChatCerebras
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ExtractedAction(BaseModel):
    type: str = Field(description="Type of action: task, meeting_item, github_action, calendar_event, idea, decision")
    description: str = Field(description="Clear description of the action")
    confidence: float = Field(description="Confidence score between 0 and 1")

class ActionsList(BaseModel):
    actions: List[ExtractedAction]

class ActionExtractionService:
    def __init__(self):
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
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI assistant that extracts actionable items from transcribed text.
            
Identify and extract the following types of actions:
- task: Specific to-do items or tasks mentioned
- meeting_item: Agenda items or topics to discuss in meetings
- github_action: GitHub-related actions like creating PRs, commits, issues
- calendar_event: Events or appointments to schedule
- idea: Creative ideas or brainstorming points
- decision: Important decisions that were made or need to be made

For each action, provide:
1. The action type
2. A clear, concise description
3. A confidence score (0-1) indicating how certain you are this is an actionable item

Focus on explicit mentions and clear intent. Avoid inferring actions that aren't clearly stated.

{format_instructions}"""),
            ("user", "Extract actionable items from this text: {text}")
        ])
    
    async def extract_actions(self, text: str) -> Dict[str, Any]:
        try:
            if not self.llm:
                return {
                    "actions": [],
                    "error": "Cerebras API key not configured"
                }
            
            chain = self.prompt | self.llm | self.parser
            
            result = await chain.ainvoke({
                "text": text,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting actions: {e}")
            return {
                "actions": [],
                "error": str(e)
            }