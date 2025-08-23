from langchain_core.tools import tool, ToolException
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)


@tool
async def create_calendar_event(
    title: str,
    start_time: str,
    duration_minutes: int = 60,
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """Create a calendar event.
    
    Args:
        title: Event title
        start_time: Start time in ISO format (e.g., "2024-01-15T14:00:00")
        duration_minutes: Duration in minutes (default: 60)
        attendees: List of attendee email addresses (optional)
        description: Event description (optional)
        location: Event location or meeting URL (optional)
    
    Returns:
        Success message with event details
    """
    try:
        # Parse the time
        start = datetime.fromisoformat(start_time)
        end = start + timedelta(minutes=duration_minutes)
        
        # In production, this would integrate with Google Calendar or Outlook
        event_details = f"📅 Event: {title}\n"
        event_details += f"⏰ Time: {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')}\n"
        
        if location:
            event_details += f"📍 Location: {location}\n"
        
        if attendees:
            event_details += f"👥 Attendees: {', '.join(attendees)}\n"
        
        if description:
            event_details += f"📝 Description: {description}\n"
        
        return f"✅ Calendar event created:\n{event_details}"
    except ValueError as e:
        raise ToolException(f"Invalid time format: {str(e)}")
    except Exception as e:
        raise ToolException(f"Error creating calendar event: {str(e)}")


@tool
async def check_calendar_availability(
    date: str,
    duration_minutes: int = 30,
    time_range: Optional[str] = "9:00-17:00"
) -> str:
    """Check calendar availability for a given date.
    
    Args:
        date: Date to check in YYYY-MM-DD format
        duration_minutes: Duration of time slot needed (default: 30)
        time_range: Time range to check (default: "9:00-17:00")
    
    Returns:
        Available time slots
    """
    try:
        # Parse date
        check_date = datetime.strptime(date, "%Y-%m-%d")
        
        # In production, this would check actual calendar
        # For demo, return mock available slots
        available_slots = [
            "09:00 - 10:00",
            "11:00 - 12:00",
            "14:00 - 15:30",
            "16:00 - 17:00"
        ]
        
        result = f"📅 Available slots on {date} ({duration_minutes} min slots):\n"
        for slot in available_slots:
            result += f"  • {slot}\n"
        
        return result
    except ValueError as e:
        raise ToolException(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise ToolException(f"Error checking availability: {str(e)}")


@tool
async def get_upcoming_events(days_ahead: int = 7, max_events: int = 10) -> str:
    """Get upcoming calendar events.
    
    Args:
        days_ahead: Number of days to look ahead (default: 7)
        max_events: Maximum number of events to return (default: 10)
    
    Returns:
        List of upcoming events
    """
    try:
        # In production, this would fetch from actual calendar
        # Mock data for demo
        today = datetime.now()
        
        events = [
            {
                "title": "Team Standup",
                "time": (today + timedelta(days=1, hours=9)).strftime("%Y-%m-%d %H:%M"),
                "duration": 30
            },
            {
                "title": "Project Review",
                "time": (today + timedelta(days=2, hours=14)).strftime("%Y-%m-%d %H:%M"),
                "duration": 60
            },
            {
                "title": "Client Call",
                "time": (today + timedelta(days=3, hours=15)).strftime("%Y-%m-%d %H:%M"),
                "duration": 45
            }
        ]
        
        result = f"📅 Upcoming events (next {days_ahead} days):\n\n"
        for event in events[:max_events]:
            result += f"• {event['title']}\n"
            result += f"  {event['time']} ({event['duration']} min)\n"
        
        return result
    except Exception as e:
        raise ToolException(f"Error getting events: {str(e)}")


@tool
async def cancel_calendar_event(event_id: str, notify_attendees: bool = True) -> str:
    """Cancel a calendar event.
    
    Args:
        event_id: ID or title of the event to cancel
        notify_attendees: Whether to notify attendees (default: True)
    
    Returns:
        Success message
    """
    try:
        notification = "with notification" if notify_attendees else "without notification"
        return f"✅ Event '{event_id}' cancelled {notification}"
    except Exception as e:
        raise ToolException(f"Error cancelling event: {str(e)}")