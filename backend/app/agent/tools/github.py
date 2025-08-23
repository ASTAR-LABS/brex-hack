from langchain_core.tools import tool, ToolException
from typing import Optional, List
import os
import logging

logger = logging.getLogger(__name__)

# Default configuration from environment
DEFAULT_TOKEN = os.getenv("GITHUB_TOKEN", "")
DEFAULT_OWNER = os.getenv("GITHUB_OWNER", "")
DEFAULT_REPO = os.getenv("GITHUB_REPO", "")


def _get_github_client(repo: Optional[str] = None):
    """Helper to get GitHub integration with proper repo"""
    from app.integrations.github_integration import GitHubIntegration
    
    if repo and '/' in repo:
        owner, repo_name = repo.split('/', 1)
    else:
        owner = DEFAULT_OWNER
        repo_name = repo or DEFAULT_REPO
    
    if not DEFAULT_TOKEN:
        raise ToolException("GitHub token not configured")
    
    return GitHubIntegration(token=DEFAULT_TOKEN, owner=owner, repo=repo_name)


@tool
async def create_github_issue(title: str, body: str, repo: Optional[str] = None, labels: Optional[List[str]] = None) -> str:
    """Create a GitHub issue in the specified repository.
    
    Args:
        title: Issue title
        body: Issue description/body
        repo: Repository in format 'owner/repo' (optional, uses default if not provided)
        labels: List of labels to add (optional)
    
    Returns:
        Success message with issue URL
    """
    try:
        gh = _get_github_client(repo)
        result = await gh.create_issue(title=title, body=body, labels=labels)
        
        if "error" in result:
            raise ToolException(f"Failed to create issue: {result['error']}")
        
        return f"✅ Created issue #{result['number']}: {result['html_url']}"
    except Exception as e:
        raise ToolException(f"Error creating issue: {str(e)}")


@tool
async def get_github_issues(repo: Optional[str] = None, state: str = "open", limit: int = 10) -> str:
    """Get GitHub issues from a repository.
    
    Args:
        repo: Repository in format 'owner/repo' (optional, uses default if not provided)
        state: Issue state - 'open', 'closed', or 'all' (default: 'open')
        limit: Maximum number of issues to return (default: 10)
    
    Returns:
        Formatted list of issues
    """
    try:
        gh = _get_github_client(repo)
        issues = await gh.list_issues(state=state, limit=limit)
        
        if not issues:
            return f"No {state} issues found in {gh.owner}/{gh.repo}"
        
        result = f"Found {len(issues)} {state} issues in {gh.owner}/{gh.repo}:\n\n"
        for issue in issues:
            result += f"• #{issue['number']}: {issue['title']}"
            if issue.get('labels'):
                labels = [l['name'] for l in issue['labels']]
                result += f" [{', '.join(labels)}]"
            result += f"\n  State: {issue['state']}, Created: {issue['created_at'][:10]}"
            if issue.get('assignee'):
                result += f", Assigned to: @{issue['assignee']['login']}"
            result += "\n"
        
        return result
    except Exception as e:
        raise ToolException(f"Error getting issues: {str(e)}")


@tool
async def update_github_issue(
    issue_number: int,
    repo: Optional[str] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None
) -> str:
    """Update a GitHub issue.
    
    Args:
        issue_number: Issue number to update
        repo: Repository in format 'owner/repo' (optional, uses default if not provided)
        title: New title (optional)
        body: New body/description (optional)
        state: New state - 'open' or 'closed' (optional)
        labels: New labels to set (optional, replaces existing labels)
    
    Returns:
        Success message
    """
    try:
        gh = _get_github_client(repo)
        
        # Build update kwargs
        update_data = {}
        if title: update_data['title'] = title
        if body: update_data['body'] = body
        if state: update_data['state'] = state
        if labels is not None: update_data['labels'] = labels
        
        if not update_data:
            return "No updates provided"
        
        result = await gh.update_issue(issue_number, **update_data)
        
        if "error" in result:
            raise ToolException(f"Failed to update issue: {result['error']}")
        
        updates_made = ", ".join(update_data.keys())
        return f"✅ Updated issue #{issue_number} in {gh.owner}/{gh.repo} - Modified: {updates_made}"
    except Exception as e:
        raise ToolException(f"Error updating issue: {str(e)}")


@tool
async def add_github_issue_comment(issue_number: int, comment: str, repo: Optional[str] = None) -> str:
    """Add a comment to a GitHub issue.
    
    Args:
        issue_number: Issue number to comment on
        comment: Comment text to add
        repo: Repository in format 'owner/repo' (optional, uses default if not provided)
    
    Returns:
        Success message
    """
    try:
        gh = _get_github_client(repo)
        result = await gh.add_issue_comment(issue_number, comment)
        
        if "error" in result:
            raise ToolException(f"Failed to add comment: {result['error']}")
        
        return f"✅ Added comment to issue #{issue_number} in {gh.owner}/{gh.repo}"
    except Exception as e:
        raise ToolException(f"Error adding comment: {str(e)}")


@tool
async def create_github_pull_request(
    title: str,
    body: str,
    head: str,
    base: str = "main",
    repo: Optional[str] = None
) -> str:
    """Create a GitHub pull request.
    
    Args:
        title: PR title
        body: PR description
        head: Branch to merge from (e.g., 'feature-branch' or 'username:branch')
        base: Branch to merge into (default: 'main')
        repo: Repository in format 'owner/repo' (optional, uses default if not provided)
    
    Returns:
        Success message with PR URL
    """
    try:
        gh = _get_github_client(repo)
        result = await gh.create_pull_request(title=title, body=body, head=head, base=base)
        
        if "error" in result:
            raise ToolException(f"Failed to create PR: {result['error']}")
        
        return f"✅ Created PR #{result['number']}: {result['html_url']}"
    except Exception as e:
        raise ToolException(f"Error creating pull request: {str(e)}")


@tool
async def get_github_pull_requests(repo: Optional[str] = None, state: str = "open", limit: int = 10) -> str:
    """Get GitHub pull requests from a repository.
    
    Args:
        repo: Repository in format 'owner/repo' (optional, uses default if not provided)
        state: PR state - 'open', 'closed', or 'all' (default: 'open')
        limit: Maximum number of PRs to return (default: 10)
    
    Returns:
        Formatted list of pull requests
    """
    try:
        gh = _get_github_client(repo)
        prs = await gh.list_pull_requests(state=state, limit=limit)
        
        if not prs:
            return f"No {state} pull requests found in {gh.owner}/{gh.repo}"
        
        result = f"Found {len(prs)} {state} pull requests in {gh.owner}/{gh.repo}:\n\n"
        for pr in prs:
            result += f"• #{pr['number']}: {pr['title']}"
            result += f"\n  Author: @{pr['user']['login']}, State: {pr['state']}"
            result += f"\n  Base: {pr['base']['ref']} ← Head: {pr['head']['ref']}"
            result += f"\n  Created: {pr['created_at'][:10]}"
            if pr.get('draft'):
                result += " [DRAFT]"
            result += "\n"
        
        return result
    except Exception as e:
        raise ToolException(f"Error getting pull requests: {str(e)}")


@tool
async def close_github_issue(issue_number: int, repo: Optional[str] = None, comment: Optional[str] = None) -> str:
    """Close a GitHub issue with an optional comment.
    
    Args:
        issue_number: Issue number to close
        repo: Repository in format 'owner/repo' (optional, uses default if not provided)
        comment: Optional closing comment
    
    Returns:
        Success message
    """
    try:
        gh = _get_github_client(repo)
        
        # Add comment if provided
        if comment:
            await gh.add_issue_comment(issue_number, comment)
        
        # Close the issue
        result = await gh.update_issue(issue_number, state="closed")
        
        if "error" in result:
            raise ToolException(f"Failed to close issue: {result['error']}")
        
        return f"✅ Closed issue #{issue_number} in {gh.owner}/{gh.repo}"
    except Exception as e:
        raise ToolException(f"Error closing issue: {str(e)}")