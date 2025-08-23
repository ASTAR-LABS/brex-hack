from typing import Dict, Any, List, Optional
from langchain_core.tools import Tool, StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_cerebras import ChatCerebras
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from app.core.config import settings
from app.integrations.github_integration import GitHubIntegration
import logging
import os
import json

logger = logging.getLogger(__name__)


class SimpleAgent:
    def __init__(self):
        self.tools = []
        self.agent = None
        self.github_integration = None
        
    async def initialize(self):
        """Initialize the agent with native tools"""
        try:
            # Initialize GitHub integration if configured
            if os.getenv("GITHUB_TOKEN"):
                self.github_integration = GitHubIntegration(
                    token=os.getenv("GITHUB_TOKEN"),
                    owner=os.getenv("GITHUB_OWNER", ""),
                    repo=os.getenv("GITHUB_REPO", "")
                )
                
                # Create GitHub tools
                self.tools.extend(self._create_github_tools())
            
            # Add more tools as needed
            self.tools.extend(self._create_utility_tools())
            
            # Initialize LLM - try OpenAI first for better tool support
            if os.getenv("OPENAI_API_KEY"):
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.7,
                )
            elif settings.cerebras_api_key:
                # Try Cerebras with simplified tools
                llm = ChatCerebras(
                    api_key=settings.cerebras_api_key,
                    model=settings.cerebras_model,
                    temperature=0.7,
                )
            else:
                raise ValueError("No LLM API key configured")
            
            # Create agent with tools
            if self.tools:
                self.agent = create_react_agent(llm, self.tools)
                logger.info(f"Initialized simple agent with {len(self.tools)} tools")
            else:
                self.agent = llm
                logger.info("Initialized simple agent without tools")
                
        except Exception as e:
            logger.error(f"Failed to initialize simple agent: {e}")
            raise
    
    def _create_github_tools(self) -> List[Tool]:
        """Create GitHub-specific tools with flexible repo parameters"""
        tools = []
        
        if not self.github_integration:
            return tools
        
        default_owner = self.github_integration.owner
        default_repo = self.github_integration.repo
        token = self.github_integration.token
        
        # Create issue tool
        async def create_issue(title: str, body: str, repo: Optional[str] = None) -> str:
            """Create a GitHub issue in specified or default repository"""
            try:
                # Parse repo if provided (format: owner/repo)
                if repo and '/' in repo:
                    owner, repo_name = repo.split('/', 1)
                else:
                    owner = default_owner
                    repo_name = repo or default_repo
                
                gh = GitHubIntegration(token=token, owner=owner, repo=repo_name)
                result = await gh.create_issue(title=title, body=body)
                return f"Created issue #{result['number']} in {owner}/{repo_name}: {result['html_url']}"
            except Exception as e:
                return f"Error creating issue: {str(e)}"
        
        tools.append(
            StructuredTool.from_function(
                func=lambda title, body, repo=None: self._run_async(create_issue(title, body, repo)),
                name="create_github_issue",
                description="Create a GitHub issue. Optional repo param format: 'owner/repo'",
            )
        )
        
        # Get issues tool
        async def get_issues(repo: Optional[str] = None, state: str = "open", limit: int = 10) -> str:
            """Get GitHub issues from specified or default repository"""
            try:
                # Parse repo if provided
                if repo and '/' in repo:
                    owner, repo_name = repo.split('/', 1)
                else:
                    owner = default_owner
                    repo_name = repo or default_repo
                
                gh = GitHubIntegration(token=token, owner=owner, repo=repo_name)
                result = await gh.list_issues(state=state, limit=limit)
                
                if not result:
                    return f"No {state} issues found in {owner}/{repo_name}"
                
                issues_text = f"Found {len(result)} {state} issues in {owner}/{repo_name}:\n"
                for issue in result:
                    issues_text += f"- #{issue['number']}: {issue['title']}"
                    if issue.get('labels'):
                        labels = [l['name'] for l in issue['labels']]
                        issues_text += f" [{', '.join(labels)}]"
                    issues_text += "\n"
                return issues_text
            except Exception as e:
                return f"Error getting issues: {str(e)}"
        
        tools.append(
            StructuredTool.from_function(
                func=lambda repo=None, state="open", limit=10: self._run_async(get_issues(repo, state, limit)),
                name="get_github_issues",
                description="Get GitHub issues from a repository. Optional repo param format: 'owner/repo'",
            )
        )
        
        # Update issue tool
        async def update_issue(issue_number: int, repo: Optional[str] = None, 
                              title: Optional[str] = None, body: Optional[str] = None,
                              state: Optional[str] = None, labels: Optional[List[str]] = None) -> str:
            """Update a GitHub issue"""
            try:
                # Parse repo if provided
                if repo and '/' in repo:
                    owner, repo_name = repo.split('/', 1)
                else:
                    owner = default_owner
                    repo_name = repo or default_repo
                
                gh = GitHubIntegration(token=token, owner=owner, repo=repo_name)
                
                # Build update payload
                update_data = {}
                if title: update_data['title'] = title
                if body: update_data['body'] = body
                if state: update_data['state'] = state
                if labels: update_data['labels'] = labels
                
                result = await gh.update_issue(issue_number, **update_data)
                return f"Updated issue #{issue_number} in {owner}/{repo_name}"
            except Exception as e:
                return f"Error updating issue: {str(e)}"
        
        tools.append(
            StructuredTool.from_function(
                func=lambda issue_number, repo=None, title=None, body=None, state=None, labels=None: 
                    self._run_async(update_issue(issue_number, repo, title, body, state, labels)),
                name="update_github_issue",
                description="Update a GitHub issue. Optional repo param format: 'owner/repo'",
            )
        )
        
        # Add issue comment tool
        async def add_issue_comment(issue_number: int, comment: str, repo: Optional[str] = None) -> str:
            """Add a comment to a GitHub issue"""
            try:
                # Parse repo if provided
                if repo and '/' in repo:
                    owner, repo_name = repo.split('/', 1)
                else:
                    owner = default_owner
                    repo_name = repo or default_repo
                
                gh = GitHubIntegration(token=token, owner=owner, repo=repo_name)
                result = await gh.add_issue_comment(issue_number, comment)
                return f"Added comment to issue #{issue_number} in {owner}/{repo_name}"
            except Exception as e:
                return f"Error adding comment: {str(e)}"
        
        tools.append(
            StructuredTool.from_function(
                func=lambda issue_number, comment, repo=None: 
                    self._run_async(add_issue_comment(issue_number, comment, repo)),
                name="add_issue_comment",
                description="Add a comment to a GitHub issue. Optional repo param format: 'owner/repo'",
            )
        )
        
        # Create pull request tool
        async def create_pull_request(title: str, body: str, head: str, base: str = "main", 
                                     repo: Optional[str] = None) -> str:
            """Create a GitHub pull request"""
            try:
                # Parse repo if provided
                if repo and '/' in repo:
                    owner, repo_name = repo.split('/', 1)
                else:
                    owner = default_owner
                    repo_name = repo or default_repo
                
                gh = GitHubIntegration(token=token, owner=owner, repo=repo_name)
                result = await gh.create_pull_request(title=title, body=body, head=head, base=base)
                return f"Created PR #{result['number']} in {owner}/{repo_name}: {result['html_url']}"
            except Exception as e:
                return f"Error creating PR: {str(e)}"
        
        tools.append(
            StructuredTool.from_function(
                func=lambda title, body, head, base="main", repo=None: 
                    self._run_async(create_pull_request(title, body, head, base, repo)),
                name="create_pull_request",
                description="Create a GitHub pull request. Optional repo param format: 'owner/repo'",
            )
        )
        
        # Get pull requests tool
        async def get_pull_requests(repo: Optional[str] = None, state: str = "open", limit: int = 10) -> str:
            """Get GitHub pull requests from specified or default repository"""
            try:
                # Parse repo if provided
                if repo and '/' in repo:
                    owner, repo_name = repo.split('/', 1)
                else:
                    owner = default_owner
                    repo_name = repo or default_repo
                
                gh = GitHubIntegration(token=token, owner=owner, repo=repo_name)
                result = await gh.list_pull_requests(state=state, limit=limit)
                
                if not result:
                    return f"No {state} pull requests found in {owner}/{repo_name}"
                
                prs_text = f"Found {len(result)} {state} pull requests in {owner}/{repo_name}:\n"
                for pr in result:
                    prs_text += f"- #{pr['number']}: {pr['title']} (by @{pr['user']['login']})\n"
                return prs_text
            except Exception as e:
                return f"Error getting pull requests: {str(e)}"
        
        tools.append(
            StructuredTool.from_function(
                func=lambda repo=None, state="open", limit=10: 
                    self._run_async(get_pull_requests(repo, state, limit)),
                name="get_pull_requests",
                description="Get GitHub pull requests from a repository. Optional repo param format: 'owner/repo'",
            )
        )
        
        return tools
    
    def _create_utility_tools(self) -> List[Tool]:
        """Create general utility tools"""
        tools = []
        
        # Calculator tool
        def calculate(expression: str) -> str:
            """Evaluate a mathematical expression"""
            try:
                # Safe evaluation of math expressions
                allowed_names = {
                    k: v for k, v in __builtins__.items() 
                    if k in ['abs', 'round', 'min', 'max', 'sum', 'pow']
                }
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                return str(result)
            except Exception as e:
                return f"Error calculating: {str(e)}"
        
        tools.append(
            StructuredTool.from_function(
                func=calculate,
                name="calculator",
                description="Perform mathematical calculations",
            )
        )
        
        # Get current time tool
        def get_current_time() -> str:
            """Get the current time and date"""
            from datetime import datetime
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        tools.append(
            Tool(
                name="get_current_time",
                func=get_current_time,
                description="Get the current date and time",
            )
        )
        
        return tools
    
    def _run_async(self, coro):
        """Helper to run async functions in sync context"""
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    
    async def process(self, text: str) -> Dict[str, Any]:
        """Process a text request using the agent"""
        try:
            if not self.agent:
                return {"error": "Agent not initialized", "response": ""}
            
            # Build messages
            messages = [
                SystemMessage(content=f"""You are a helpful AI assistant with access to various tools.
                
Default GitHub repository: {self.github_integration.owner}/{self.github_integration.repo} if configured.
When asked to create issues or PRs without specifying a repo, use this default.

Be concise and clear in your responses."""),
                HumanMessage(content=text)
            ]
            
            # Process with agent
            if hasattr(self.agent, 'ainvoke'):
                result = await self.agent.ainvoke({"messages": messages})
                
                # Extract response
                if "messages" in result and result["messages"]:
                    response = result["messages"][-1].content
                else:
                    response = str(result)
                
                return {
                    "response": response,
                    "error": None
                }
            else:
                # Fallback to simple LLM
                response = await self.agent.ainvoke(messages)
                return {
                    "response": response.content,
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "error": str(e),
                "response": ""
            }