"""OAuth Authentication Endpoints"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Optional, Dict, Any
import logging

from app.integrations.google_calendar import GoogleCalendarIntegration

logger = logging.getLogger(__name__)

router = APIRouter()

# HTML template for success/error pages
SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Successful</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .success { color: green; }
        .error { color: red; }
        button { padding: 10px 20px; margin: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <h1 class="success">✅ Google Calendar Connected!</h1>
    <p>You have successfully connected your Google Calendar.</p>
    <p>You can now close this window and use calendar features in the chat.</p>
    <button onclick="window.close()">Close Window</button>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Authentication Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .error { color: red; }
        button { padding: 10px 20px; margin: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <h1 class="error">❌ Authentication Failed</h1>
    <p>Error: {error}</p>
    <button onclick="window.location.href='/api/v1/auth/google/login'">Try Again</button>
</body>
</html>
"""


@router.get("/google/login")
async def google_login(user_id: Optional[str] = Query(default="default_user")):
    """Initiate Google OAuth flow.
    
    Args:
        user_id: Optional user identifier for multi-user support
    
    Returns:
        Redirect to Google OAuth consent screen
    """
    try:
        service = GoogleCalendarIntegration()
        auth_url = service.get_auth_url(state=user_id)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(default="default_user"),
    error: Optional[str] = Query(None)
):
    """Handle Google OAuth callback.
    
    Args:
        code: Authorization code from Google
        state: User ID passed through OAuth flow
        error: Error from OAuth flow if any
    
    Returns:
        Success or error page
    """
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"OAuth error: {error}")
            return HTMLResponse(content=ERROR_HTML.format(error=error))
        
        if not code:
            return HTMLResponse(content=ERROR_HTML.format(error="No authorization code received"))
        
        # Exchange code for tokens
        service = GoogleCalendarIntegration()
        result = await service.handle_callback(code=code, user_id=state)
        
        if result["success"]:
            logger.info(f"User {state} authenticated successfully: {result.get('email')}")
            return HTMLResponse(content=SUCCESS_HTML)
        else:
            error_msg = result.get("error", "Unknown error")
            return HTMLResponse(content=ERROR_HTML.format(error=error_msg))
            
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        return HTMLResponse(content=ERROR_HTML.format(error=str(e)))


@router.get("/google/status")
async def google_status(user_id: str = Query(default="default_user")):
    """Check Google Calendar authentication status.
    
    Args:
        user_id: User identifier
    
    Returns:
        Authentication status
    """
    try:
        service = GoogleCalendarIntegration()
        creds = service.load_credentials(user_id)
        
        if creds:
            # Try to get user info
            from googleapiclient.discovery import build
            oauth_service = build('oauth2', 'v2', credentials=creds)
            try:
                user_info = oauth_service.userinfo().get().execute()
                return {
                    "authenticated": True,
                    "email": user_info.get('email'),
                    "name": user_info.get('name'),
                    "picture": user_info.get('picture')
                }
            except:
                return {
                    "authenticated": True,
                    "email": "Unknown",
                    "name": "Unknown"
                }
        else:
            return {
                "authenticated": False,
                "auth_url": f"/api/v1/auth/google/login?user_id={user_id}"
            }
            
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {
            "authenticated": False,
            "error": str(e)
        }


@router.delete("/google/logout")
async def google_logout(user_id: str = Query(default="default_user")):
    """Revoke Google Calendar access.
    
    Args:
        user_id: User identifier
    
    Returns:
        Logout status
    """
    try:
        import os
        
        # Delete stored token
        token_path = f"tokens/{user_id}.json"
        if os.path.exists(token_path):
            os.remove(token_path)
            
        return {
            "success": True,
            "message": f"Google Calendar disconnected for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/test")
async def test_calendar_access(user_id: str = Query(default="default_user")):
    """Test Google Calendar access by fetching upcoming events.
    
    Args:
        user_id: User identifier
    
    Returns:
        Test results with events or error
    """
    try:
        service = GoogleCalendarIntegration()
        creds = service.load_credentials(user_id)
        
        if not creds:
            return {
                "success": False,
                "error": "Not authenticated",
                "auth_url": f"/api/v1/auth/google/login?user_id={user_id}"
            }
        
        # Try to fetch events
        from datetime import datetime, timedelta
        events = await service.get_events(
            user_id=user_id,
            time_min=datetime.now(),
            time_max=datetime.now() + timedelta(days=7),
            max_results=5
        )
        
        return {
            "success": True,
            "message": f"Successfully accessed calendar. Found {len(events)} upcoming events.",
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Error testing calendar access: {e}")
        return {
            "success": False,
            "error": str(e)
        }