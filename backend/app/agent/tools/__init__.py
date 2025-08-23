"""Tool organization and categories"""
from typing import List, Dict, Any, Optional

# Import all tools
from .github import (
    create_github_issue,
    get_github_issues,
    update_github_issue,
    add_github_issue_comment,
    create_github_pull_request,
    get_github_pull_requests,
    close_github_issue
)

from .slack import (
    send_slack_message,
    send_slack_dm,
    create_slack_reminder
)

from .calendar import (
    create_calendar_event,
    check_calendar_availability,
    get_upcoming_events,
    cancel_calendar_event,
    authenticate_google_calendar
)

from .utility import (
    calculate,
    get_current_time,
    format_json,
    create_todo_list,
    convert_units,
    generate_uuid,
    search_web
)

# Group tools by category
GITHUB_TOOLS = [
    create_github_issue,
    get_github_issues,
    update_github_issue,
    add_github_issue_comment,
    create_github_pull_request,
    get_github_pull_requests,
    close_github_issue
]

SLACK_TOOLS = [
    send_slack_message,
    send_slack_dm,
    create_slack_reminder
]

CALENDAR_TOOLS = [
    create_calendar_event,
    check_calendar_availability,
    get_upcoming_events,
    cancel_calendar_event,
    authenticate_google_calendar
]

UTILITY_TOOLS = [
    calculate,
    get_current_time,
    format_json,
    create_todo_list,
    convert_units,
    generate_uuid,
    search_web
]

# Tool categories with metadata
TOOL_CATEGORIES = {
    "github": {
        "name": "GitHub",
        "tools": GITHUB_TOOLS,
        "description": "Create and manage GitHub issues, PRs, and repositories",
        "requires_auth": True
    },
    "slack": {
        "name": "Slack",
        "tools": SLACK_TOOLS,
        "description": "Send messages and create reminders in Slack",
        "requires_auth": True
    },
    "calendar": {
        "name": "Calendar",
        "tools": CALENDAR_TOOLS,
        "description": "Manage calendar events and check availability",
        "requires_auth": True
    },
    "utility": {
        "name": "Utilities",
        "tools": UTILITY_TOOLS,
        "description": "General utilities like calculations, time, and search",
        "requires_auth": False
    }
}


def get_tools(
    enabled_categories: Optional[List[str]] = None,
    allow_writes: bool = True,
    user_role: Optional[str] = None
) -> List:
    """Get tools based on enabled categories and permissions.
    
    Args:
        enabled_categories: List of category names to enable (default: all)
        allow_writes: Whether to allow write operations (default: True)
        user_role: User role for permission filtering (optional)
    
    Returns:
        List of tool functions
    """
    if enabled_categories is None:
        # Default to all categories
        enabled_categories = list(TOOL_CATEGORIES.keys())
    
    # Role-based filtering
    if user_role:
        role_permissions = {
            "admin": ["github", "slack", "calendar", "utility"],
            "user": ["github", "utility"],
            "guest": ["utility"]
        }
        allowed = role_permissions.get(user_role, ["utility"])
        enabled_categories = [c for c in enabled_categories if c in allowed]
    
    tools = []
    for category in enabled_categories:
        if category in TOOL_CATEGORIES:
            category_tools = TOOL_CATEGORIES[category]["tools"]
            
            # Filter out write operations if not allowed
            if not allow_writes:
                category_tools = [
                    t for t in category_tools
                    if not any(keyword in t.name for keyword in 
                              ["create", "update", "send", "cancel", "close", "add"])
                ]
            
            tools.extend(category_tools)
    
    return tools


def get_tool_descriptions() -> Dict[str, Any]:
    """Get descriptions of all available tools by category."""
    descriptions = {}
    
    for category_name, category_info in TOOL_CATEGORIES.items():
        descriptions[category_name] = {
            "name": category_info["name"],
            "description": category_info["description"],
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description
                }
                for tool in category_info["tools"]
            ]
        }
    
    return descriptions