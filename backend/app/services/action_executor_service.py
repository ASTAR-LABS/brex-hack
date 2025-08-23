from typing import Dict, Any
from app.integrations.github_integration import GitHubIntegration
import logging

logger = logging.getLogger(__name__)

class ActionExecutorService:
    def __init__(self):
        pass
    
    async def start(self):
        """Start the service (no-op for now)"""
        pass
    
    async def stop(self):
        """Stop the service (no-op for now)"""
        pass
    
    async def execute_single_action(self, action_type: str, description: str, 
                                   metadata: Dict[str, Any] = None,
                                   integration_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a single action based on its type"""
        config = integration_config or {}
        metadata = metadata or {}
        
        if action_type == "github_action":
            github = GitHubIntegration(
                token=config.get("github_token"),
                owner=config.get("github_owner"),
                repo=config.get("github_repo")
            )
            
            if "PR" in description or "pull request" in description.lower():
                pr_number = metadata.get("pr_number", 1)
                return await github.create_pr_comment(pr_number, description)
            
            elif "issue" in description.lower():
                # Extract title from description or use default
                title = metadata.get("title", description[:50] if len(description) > 50 else description)
                return await github.create_issue(
                    title=title,
                    body=description
                )
        
        elif action_type == "task":
            return {"status": "logged", "description": description}
        
        elif action_type == "calendar_event":
            return {"status": "calendar_not_implemented", "description": description}
        
        else:
            return {"status": "unknown_action_type", "type": action_type}