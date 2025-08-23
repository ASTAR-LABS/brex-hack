from typing import Optional, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

class GitHubIntegration:
    def __init__(self, token: str = None, owner: str = None, repo: str = None):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        } if self.token else {}
    
    async def create_pr_comment(self, pr_number: int, body: str) -> Dict[str, Any]:
        """Add a comment to a pull request"""
        try:
            if not all([self.token, self.owner, self.repo]):
                return {"error": "GitHub credentials not configured"}
            
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json={"body": body}
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to create PR comment: {e}")
            return {"error": str(e)}
    
    async def create_issue(self, title: str, body: str, labels: list = None) -> Dict[str, Any]:
        """Create a new issue"""
        try:
            if not all([self.token, self.owner, self.repo]):
                return {"error": "GitHub credentials not configured"}
            
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
            
            data = {"title": title, "body": body}
            if labels:
                data["labels"] = labels
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return {"error": str(e)}
    
    async def get_pr(self, pr_number: int) -> Dict[str, Any]:
        """Get PR details"""
        try:
            if not all([self.token, self.owner, self.repo]):
                return {"error": "GitHub credentials not configured"}
            
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls/{pr_number}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get PR: {e}")
            return {"error": str(e)}
    
    async def test_connection(self) -> bool:
        """Test if GitHub credentials are valid"""
        try:
            if not self.token:
                return False
                
            url = f"{self.base_url}/user"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                return response.status_code == 200
                
        except Exception:
            return False