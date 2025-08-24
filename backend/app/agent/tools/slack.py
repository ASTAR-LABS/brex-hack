from langchain_core.tools import tool, ToolException
from typing import Optional, List, Dict, Any
import os
import httpx
import logging

logger = logging.getLogger(__name__)

# Slack configuration from environment - using bot token
SLACK_BOT_TOKEN = os.getenv("SLACK_MCP_XOXB_TOKEN", "")
SLACK_DEFAULT_CHANNEL = os.getenv("SLACK_DEFAULT_CHANNEL", "general")


# Helper functions for Slack API calls
def _get_slack_headers() -> Dict[str, str]:
    """Get headers for Slack API requests with bot token."""
    if not SLACK_BOT_TOKEN:
        raise ToolException("Slack bot token not configured")

    return {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }


async def _slack_api_call(
    client: httpx.AsyncClient, method: str, url: str, **kwargs
) -> Dict[str, Any]:
    """Make a Slack API call and handle common errors."""
    headers = _get_slack_headers()

    if method.upper() == "GET":
        response = await client.get(url, headers=headers, **kwargs)
    elif method.upper() == "POST":
        response = await client.post(url, headers=headers, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    result = response.json()

    if not result.get("ok"):
        error_msg = result.get("error", "Unknown error")
        raise ToolException(f"Slack API error: {error_msg}")

    return result


def _format_channel(channel: str) -> str:
    """Ensure channel has proper format."""
    if not channel.startswith("C") and not channel.startswith("#"):
        return f"#{channel}"
    return channel


@tool
async def send_slack_message(channel: str, message: str) -> str:
    """Send a message to a Slack channel.

    Args:
        channel: Channel name (without #) or channel ID
        message: Message text to send

    Returns:
        Success message with timestamp
    """
    try:
        channel = _format_channel(channel)

        async with httpx.AsyncClient() as client:
            await _slack_api_call(
                client,
                "POST",
                "https://slack.com/api/chat.postMessage",
                json={"channel": channel, "text": message},
            )

            return f"✅ Message sent to {channel}"
    except ToolException:
        raise
    except Exception as e:
        raise ToolException(f"Error sending Slack message: {str(e)}")


@tool
async def send_slack_dm(user_name: str, message: str) -> str:
    """Send a direct message to a Slack user.

    Args:
        user_name: Username or display name of the user (e.g., "Erik", "John Doe")
        message: Message text to send

    Returns:
        Success message
    """
    try:
        async with httpx.AsyncClient() as client:
            # Get list of users
            result = await _slack_api_call(
                client, "GET", "https://slack.com/api/users.list"
            )

            # Find user by name (case insensitive)
            user_id = None
            user_name_lower = user_name.lower()
            for member in result.get("members", []):
                real_name = member.get("real_name", "").lower()
                display_name = member.get("profile", {}).get("display_name", "").lower()
                name = member.get("name", "").lower()

                if (
                    user_name_lower in [real_name, display_name, name]
                    or user_name_lower in real_name
                    or user_name_lower in display_name
                ):
                    user_id = member["id"]
                    break

            if not user_id:
                raise ToolException(f"Could not find user with name '{user_name}'")

            # Open conversation
            conv_result = await _slack_api_call(
                client,
                "POST",
                "https://slack.com/api/conversations.open",
                json={"users": user_id},
            )

            channel_id = conv_result["channel"]["id"]

            # Send message
            await _slack_api_call(
                client,
                "POST",
                "https://slack.com/api/chat.postMessage",
                json={"channel": channel_id, "text": message},
            )

            return f"✅ DM sent to {user_name}"
    except ToolException:
        raise
    except Exception as e:
        raise ToolException(f"Error sending Slack DM: {str(e)}")


@tool
async def search_slack_messages(query: str, limit: int = 10) -> str:
    """Search for messages in Slack.

    Args:
        query: Search query text
        limit: Maximum number of results to return (default: 10)

    Returns:
        Formatted search results
    """
    try:
        async with httpx.AsyncClient() as client:
            result = await _slack_api_call(
                client,
                "GET",
                "https://slack.com/api/search.messages",
                params={
                    "query": query,
                    "count": limit,
                    "sort": "timestamp",
                    "sort_dir": "desc",
                },
            )

            messages = result.get("messages", {}).get("matches", [])

            if not messages:
                return f"No messages found matching '{query}'"

            output = f"Found {len(messages)} messages matching '{query}':\n\n"
            for msg in messages[:limit]:
                user = msg.get("username", "Unknown")
                text = msg.get("text", "")
                channel = msg.get("channel", {}).get("name", "Unknown")

                output += f"• [{channel}] @{user}: {text[:100]}{'...' if len(text) > 100 else ''}\n"

            return output

    except ToolException:
        raise
    except Exception as e:
        raise ToolException(f"Error searching Slack: {str(e)}")
