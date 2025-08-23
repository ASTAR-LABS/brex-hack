"""Google Calendar Integration Service"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Scopes required for Google Calendar
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]


class GoogleCalendarIntegration:
    def __init__(self, token_path: Optional[str] = None):
        """Initialize Google Calendar integration.
        
        Args:
            token_path: Path to store user tokens (defaults to tokens/{user_id}.json)
        """
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        self.token_path = token_path or "tokens"
        self.service = None
        self.credentials = None
        
        # Ensure token directory exists
        if not os.path.exists(self.token_path):
            os.makedirs(self.token_path)
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """Get OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not configured")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=SCOPES
        )
        flow.redirect_uri = self.redirect_uri
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )
        
        return auth_url
    
    async def handle_callback(self, code: str, user_id: str) -> Dict[str, Any]:
        """Handle OAuth callback and save credentials.
        
        Args:
            code: Authorization code from callback
            user_id: User/session ID for token storage
            
        Returns:
            User info and success status
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Save credentials
            token_file = os.path.join(self.token_path, f"{user_id}.json")
            with open(token_file, 'w') as token:
                token.write(credentials.to_json())
            
            # Get user info
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return {
                "success": True,
                "email": user_info.get('email'),
                "name": user_info.get('name'),
                "picture": user_info.get('picture')
            }
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return {"success": False, "error": str(e)}
    
    def load_credentials(self, user_id: str) -> Optional[Credentials]:
        """Load saved credentials for a user.
        
        Args:
            user_id: User/session ID
            
        Returns:
            Credentials object or None
        """
        token_file = os.path.join(self.token_path, f"{user_id}.json")
        
        if not os.path.exists(token_file):
            return None
        
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            return creds
            
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None
    
    def get_calendar_service(self, user_id: str):
        """Get authenticated Calendar service.
        
        Args:
            user_id: User/session ID
            
        Returns:
            Google Calendar service object
        """
        creds = self.load_credentials(user_id)
        if not creds:
            raise ValueError("No valid credentials found. Please authenticate first.")
        
        return build('calendar', 'v3', credentials=creds)
    
    async def create_event(
        self,
        user_id: str,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = 60,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """Create a calendar event.
        
        Args:
            user_id: User/session ID
            title: Event title
            start_time: Event start time
            end_time: Event end time (or use duration_minutes)
            duration_minutes: Duration if end_time not provided
            description: Event description
            location: Event location
            attendees: List of attendee emails
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            Created event details
        """
        try:
            service = self.get_calendar_service(user_id)
            
            # Calculate end time if not provided
            if not end_time:
                end_time = start_time + timedelta(minutes=duration_minutes or 60)
            
            # Build event
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if description:
                event['description'] = description
            
            if location:
                event['location'] = location
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Create event
            result = service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates='all' if attendees else 'none'
            ).execute()
            
            return {
                'success': True,
                'event_id': result['id'],
                'html_link': result['htmlLink'],
                'start': result['start'],
                'end': result['end']
            }
            
        except HttpError as e:
            logger.error(f"Calendar API error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_events(
        self,
        user_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """Get calendar events.
        
        Args:
            user_id: User/session ID
            time_min: Start of time range
            time_max: End of time range
            max_results: Maximum events to return
            calendar_id: Calendar ID
            
        Returns:
            List of events
        """
        try:
            service = self.get_calendar_service(user_id)
            
            # Default to next 7 days if not specified
            if not time_min:
                time_min = datetime.now()
            if not time_max:
                time_max = time_min + timedelta(days=7)
            
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return [
                {
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location'),
                    'description': event.get('description'),
                    'attendees': [a['email'] for a in event.get('attendees', [])]
                }
                for event in events
            ]
            
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    async def check_availability(
        self,
        user_id: str,
        date: datetime,
        duration_minutes: int = 30,
        time_min: Optional[str] = "09:00",
        time_max: Optional[str] = "17:00",
        calendar_id: str = 'primary'
    ) -> List[Dict[str, str]]:
        """Check calendar availability for a date.
        
        Args:
            user_id: User/session ID
            date: Date to check
            duration_minutes: Slot duration needed
            time_min: Start of working hours
            time_max: End of working hours
            calendar_id: Calendar ID
            
        Returns:
            List of available time slots
        """
        try:
            service = self.get_calendar_service(user_id)
            
            # Parse time boundaries
            start_hour, start_min = map(int, time_min.split(':'))
            end_hour, end_min = map(int, time_max.split(':'))
            
            day_start = date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            day_end = date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
            
            # Get busy times
            body = {
                "timeMin": day_start.isoformat() + 'Z',
                "timeMax": day_end.isoformat() + 'Z',
                "items": [{"id": calendar_id}]
            }
            
            freebusy_result = service.freebusy().query(body=body).execute()
            busy_times = freebusy_result['calendars'][calendar_id].get('busy', [])
            
            # Find free slots
            available_slots = []
            current_time = day_start
            
            for busy in busy_times:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                
                # Add free time before this busy period
                while current_time + timedelta(minutes=duration_minutes) <= busy_start:
                    slot_end = current_time + timedelta(minutes=duration_minutes)
                    available_slots.append({
                        'start': current_time.strftime('%H:%M'),
                        'end': slot_end.strftime('%H:%M')
                    })
                    current_time = slot_end
                
                current_time = busy_end
            
            # Add remaining time after last busy period
            while current_time + timedelta(minutes=duration_minutes) <= day_end:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                available_slots.append({
                    'start': current_time.strftime('%H:%M'),
                    'end': slot_end.strftime('%H:%M')
                })
                current_time = slot_end
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return []
    
    async def delete_event(
        self,
        user_id: str,
        event_id: str,
        send_updates: bool = True,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """Delete a calendar event.
        
        Args:
            user_id: User/session ID
            event_id: Event ID to delete
            send_updates: Whether to notify attendees
            calendar_id: Calendar ID
            
        Returns:
            Success status
        """
        try:
            service = self.get_calendar_service(user_id)
            
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates='all' if send_updates else 'none'
            ).execute()
            
            return {'success': True, 'message': f'Event {event_id} deleted'}
            
        except HttpError as e:
            if e.resp.status == 404:
                return {'success': False, 'error': 'Event not found'}
            logger.error(f"Error deleting event: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return {'success': False, 'error': str(e)}