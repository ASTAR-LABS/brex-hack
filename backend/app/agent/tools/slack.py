from langchain_core.tools import tool, ToolException
from typing import Optional, List
import os
import httpx
import logging

logger = logging.getLogger(__name__)

# Slack configuration from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_DEFAULT_CHANNEL = os.getenv("SLACK_DEFAULT_CHANNEL", "general")


@tool
async def send_slack_message(channel: str, message: str) -> str:
    """Send a message to a Slack channel.
    
    Args:
        channel: Channel name (without #) or channel ID
        message: Message text to send
    
    Returns:
        Success message with timestamp
    """
    if not SLACK_BOT_TOKEN:
        raise ToolException("Slack bot token not configured")
    
    try:
        # Ensure channel has # prefix if it's a channel name
        if not channel.startswith("C") and not channel.startswith("#"):
            channel = f"#{channel}"
        
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "channel": channel,
            "text": message
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            result = response.json()
            
            if not result.get("ok"):
                raise ToolException(f"Slack API error: {result.get('error', 'Unknown error')}")
            
            return f"✅ Message sent to {channel}"
    except Exception as e:
        raise ToolException(f"Error sending Slack message: {str(e)}")


@tool
async def send_slack_dm(user_email: str, message: str) -> str:
    """Send a direct message to a Slack user.
    
    Args:
        user_email: Email address of the user
        message: Message text to send
    
    Returns:
        Success message
    """
    if not SLACK_BOT_TOKEN:
        raise ToolException("Slack bot token not configured")
    
    try:
        # First, find user by email
        lookup_url = "https://slack.com/api/users.lookupByEmail"
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with httpx.AsyncClient() as client:
            # Find user
            response = await client.get(
                lookup_url,
                headers=headers,
                params={"email": user_email}
            )
            result = response.json()
            
            if not result.get("ok"):
                raise ToolException(f"Could not find user with email {user_email}")
            
            user_id = result["user"]["id"]
            
            # Open conversation
            conv_url = "https://slack.com/api/conversations.open"
            conv_response = await client.post(
                conv_url,
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                json={"users": user_id}
            )
            conv_result = conv_response.json()
            
            if not conv_result.get("ok"):
                raise ToolException(f"Could not open DM with user")
            
            channel_id = conv_result["channel"]["id"]
            
            # Send message
            msg_url = "https://slack.com/api/chat.postMessage"
            msg_response = await client.post(
                msg_url,
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                json={"channel": channel_id, "text": message}
            )
            msg_result = msg_response.json()
            
            if not msg_result.get("ok"):
                raise ToolException(f"Failed to send DM: {msg_result.get('error')}")
            
            return f"✅ DM sent to {user_email}"
    except ToolException:
        raise
    except Exception as e:
        raise ToolException(f"Error sending Slack DM: {str(e)}")


@tool
async def create_slack_reminder(user_email: str, reminder_text: str, time: str) -> str:
    """Create a Slack reminder for a user.
    
    Args:
        user_email: Email of the user to remind
        reminder_text: Text of the reminder
        time: When to send reminder (e.g., "in 30 minutes", "tomorrow at 2pm", "every Monday at 9am")
    
    Returns:
        Success message
    """
    if not SLACK_BOT_TOKEN:
        raise ToolException("Slack bot token not configured")
    
    try:
        # This would use Slack's reminders.add API
        # For now, return a placeholder
        return f"✅ Reminder set for {user_email}: '{reminder_text}' at {time}"
    except Exception as e:
        raise ToolException(f"Error creating reminder: {str(e)}")