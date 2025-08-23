from typing import Dict, Any, Optional
from app.models.action_state import Action, ActionState
from app.integrations.github_integration import GitHubIntegration
from datetime import datetime
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

class ActionExecutorService:
    def __init__(self):
        self.actions_store: Dict[str, Action] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task = None
    
    async def start(self):
        """Start the background worker"""
        if not self.worker_task:
            self.worker_task = asyncio.create_task(self._process_queue())
    
    async def stop(self):
        """Stop the background worker"""
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
    
    async def add_action(self, action_type: str, description: str, confidence: float, 
                         metadata: Dict[str, Any] = None) -> Action:
        """Add a new action to be executed"""
        action = Action(
            id=str(uuid.uuid4()),
            type=action_type,
            description=description,
            confidence=confidence,
            metadata=metadata or {}
        )
        
        self.actions_store[action.id] = action
        
        if confidence > 0.7:
            action.state = ActionState.QUEUED
            await self.execution_queue.put(action.id)
        
        return action
    
    async def execute_action(self, action_id: str, integration_config: Dict[str, Any] = None) -> Action:
        """Execute a specific action immediately"""
        action = self.actions_store.get(action_id)
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        action.state = ActionState.EXECUTING
        action.executed_at = datetime.now()
        
        try:
            result = await self._execute_single_action(action, integration_config)
            action.result = result
            action.state = ActionState.RESOLVED
            action.resolved_at = datetime.now()
        except Exception as e:
            logger.error(f"Action {action_id} failed: {e}")
            action.state = ActionState.FAILED
            action.error = str(e)
        
        action.updated_at = datetime.now()
        return action
    
    async def _process_queue(self):
        """Background worker to process queued actions"""
        while True:
            try:
                action_id = await self.execution_queue.get()
                await self.execute_action(action_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
    
    async def _execute_single_action(self, action: Action, integration_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the actual action based on its type"""
        config = integration_config or {}
        
        if action.type == "github_action":
            github = GitHubIntegration(
                token=config.get("github_token"),
                owner=config.get("github_owner"),
                repo=config.get("github_repo")
            )
            
            if "PR" in action.description or "pull request" in action.description.lower():
                pr_number = action.metadata.get("pr_number", 1)
                return await github.create_pr_comment(pr_number, action.description)
            
            elif "issue" in action.description.lower():
                return await github.create_issue(
                    title=action.metadata.get("title", "New Issue"),
                    body=action.description
                )
        
        elif action.type == "task":
            return {"status": "logged", "description": action.description}
        
        elif action.type == "calendar_event":
            return {"status": "calendar_not_implemented", "description": action.description}
        
        else:
            return {"status": "unknown_action_type", "type": action.type}
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Get action by ID"""
        return self.actions_store.get(action_id)
    
    def get_all_actions(self) -> list[Action]:
        """Get all actions"""
        return list(self.actions_store.values())