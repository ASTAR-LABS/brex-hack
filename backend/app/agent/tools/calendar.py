from langchain_core.tools import tool, ToolException
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

# Track authenticated users (in production, use proper session management)
_authenticated_users = {}


def _get_calendar_service():
    """Get or create Google Calendar service."""
    from app.integrations.google_calendar import GoogleCalendarIntegration
    return GoogleCalendarIntegration()


def _get_user_id() -> str:
    """Get current user ID from context (simplified for demo)."""
    # In production, get from session/context
    # For now, use a default user or environment variable
    return os.getenv("GOOGLE_USER_ID", "default_user")


@tool
async def create_calendar_event(
    title: str,
    start_time: str,
    duration_minutes: int = 60,
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """Create a calendar event in Google Calendar.
    
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
        
        # Get calendar service
        service = _get_calendar_service()
        user_id = _get_user_id()
        
        # Check if user is authenticated
        creds = service.load_credentials(user_id)
        if not creds:
            return "❌ Not authenticated with Google Calendar. Please visit /auth/google/login to connect your calendar."
        
        # Create the event
        result = await service.create_event(
            user_id=user_id,
            title=title,
            start_time=start,
            duration_minutes=duration_minutes,
            description=description,
            location=location,
            attendees=attendees
        )
        
        if result['success']:
            event_link = result.get('html_link', '')
            event_id = result.get('event_id', '')
            
            event_details = f"📅 Event created: {title}\n"
            event_details += f"⏰ Time: {start.strftime('%Y-%m-%d %H:%M')}\n"
            event_details += f"⏱️ Duration: {duration_minutes} minutes\n"
            
            if location:
                event_details += f"📍 Location: {location}\n"
            
            if attendees:
                event_details += f"👥 Attendees: {', '.join(attendees)}\n"
            
            if event_link:
                event_details += f"🔗 Link: {event_link}\n"
            
            return f"✅ {event_details}"
        else:
            raise ToolException(f"Failed to create event: {result.get('error', 'Unknown error')}")
            
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
        
        # Parse time range
        time_parts = time_range.split('-')
        time_min = time_parts[0] if len(time_parts) > 0 else "9:00"
        time_max = time_parts[1] if len(time_parts) > 1 else "17:00"
        
        # Get calendar service
        service = _get_calendar_service()
        user_id = _get_user_id()
        
        # Check if user is authenticated
        creds = service.load_credentials(user_id)
        if not creds:
            # Return mock data if not authenticated
            available_slots = [
                "09:00 - 10:00",
                "11:00 - 12:00",
                "14:00 - 15:30",
                "16:00 - 17:00"
            ]
            result = f"📅 Available slots on {date} ({duration_minutes} min slots):\n"
            result += "⚠️ Note: Not connected to Google Calendar. Showing sample slots.\n"
            for slot in available_slots:
                result += f"  • {slot}\n"
            return result
        
        # Get real availability
        slots = await service.check_availability(
            user_id=user_id,
            date=check_date,
            duration_minutes=duration_minutes,
            time_min=time_min,
            time_max=time_max
        )
        
        if not slots:
            return f"📅 No available {duration_minutes}-minute slots on {date} between {time_range}"
        
        result = f"📅 Available {duration_minutes}-minute slots on {date}:\n"
        for slot in slots:
            result += f"  • {slot['start']} - {slot['end']}\n"
        
        return result
        
    except ValueError as e:
        raise ToolException(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise ToolException(f"Error checking availability: {str(e)}")


@tool
async def get_upcoming_events(days_ahead: int = 7, max_events: int = 10) -> str:
    """Get upcoming calendar events from Google Calendar.
    
    Args:
        days_ahead: Number of days to look ahead (default: 7)
        max_events: Maximum number of events to return (default: 10)
    
    Returns:
        List of upcoming events
    """
    try:
        # Get calendar service
        service = _get_calendar_service()
        user_id = _get_user_id()
        
        # Check if user is authenticated
        creds = service.load_credentials(user_id)
        if not creds:
            # Return mock data if not authenticated
            today = datetime.now()
            events = [
                {
                    "summary": "Team Standup",
                    "start": (today + timedelta(days=1, hours=9)).isoformat(),
                },
                {
                    "summary": "Project Review",
                    "start": (today + timedelta(days=2, hours=14)).isoformat(),
                }
            ]
            result = f"📅 Upcoming events (next {days_ahead} days):\n"
            result += "⚠️ Note: Not connected to Google Calendar. Showing sample events.\n\n"
            for event in events:
                start_time = datetime.fromisoformat(event['start'])
                result += f"• {event['summary']}\n"
                result += f"  {start_time.strftime('%Y-%m-%d %H:%M')}\n"
            return result
        
        # Get real events
        time_min = datetime.now()
        time_max = time_min + timedelta(days=days_ahead)
        
        events = await service.get_events(
            user_id=user_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_events
        )
        
        if not events:
            return f"📅 No upcoming events in the next {days_ahead} days"
        
        result = f"📅 Upcoming events (next {days_ahead} days):\n\n"
        for event in events:
            # Parse start time
            start_str = event['start']
            if 'T' in start_str:
                start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                time_str = start_time.strftime('%Y-%m-%d %H:%M')
            else:
                time_str = start_str  # All-day event
            
            result += f"• {event['summary']}\n"
            result += f"  📅 {time_str}\n"
            
            if event.get('location'):
                result += f"  📍 {event['location']}\n"
            
            if event.get('attendees'):
                result += f"  👥 {len(event['attendees'])} attendees\n"
        
        return result
        
    except Exception as e:
        raise ToolException(f"Error getting events: {str(e)}")


@tool
async def cancel_calendar_event(event_id: str, notify_attendees: bool = True) -> str:
    """Cancel a Google Calendar event.
    
    Args:
        event_id: ID or title of the event to cancel
        notify_attendees: Whether to notify attendees (default: True)
    
    Returns:
        Success message
    """
    try:
        # Get calendar service
        service = _get_calendar_service()
        user_id = _get_user_id()
        
        # Check if user is authenticated
        creds = service.load_credentials(user_id)
        if not creds:
            return "❌ Not authenticated with Google Calendar. Please visit /auth/google/login to connect your calendar."
        
        # If event_id looks like a title, try to find the event
        if not event_id.startswith('_') and len(event_id) < 20:
            # Search for event by title
            events = await service.get_events(
                user_id=user_id,
                time_min=datetime.now() - timedelta(days=1),
                time_max=datetime.now() + timedelta(days=30),
                max_results=50
            )
            
            matching_event = None
            for event in events:
                if event['summary'].lower() == event_id.lower():
                    matching_event = event
                    break
            
            if matching_event:
                event_id = matching_event['id']
                event_title = matching_event['summary']
            else:
                return f"❌ Could not find event with title '{event_id}'"
        else:
            event_title = event_id
        
        # Delete the event
        result = await service.delete_event(
            user_id=user_id,
            event_id=event_id,
            send_updates=notify_attendees
        )
        
        if result['success']:
            notification = "with notification" if notify_attendees else "without notification"
            return f"✅ Event '{event_title}' cancelled {notification}"
        else:
            raise ToolException(f"Failed to cancel event: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        raise ToolException(f"Error cancelling event: {str(e)}")


@tool
async def authenticate_google_calendar() -> str:
    """Get the URL to authenticate with Google Calendar.
    
    Returns:
        Authentication URL or status message
    """
    try:
        service = _get_calendar_service()
        user_id = _get_user_id()
        
        # Check if already authenticated
        creds = service.load_credentials(user_id)
        if creds:
            return "✅ Already authenticated with Google Calendar"
        
        # Get auth URL
        auth_url = service.get_auth_url(state=user_id)
        
        return f"""🔗 Please authenticate with Google Calendar:
        
1. Visit this URL: {auth_url}
2. Sign in with your Google account
3. Grant calendar permissions
4. You'll be redirected back to the app

After authentication, you can use all calendar features!"""
        
    except Exception as e:
        raise ToolException(f"Error getting auth URL: {str(e)}")