from langchain.tools import BaseTool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta
import pytz
from pydantic import BaseModel, Field
from typing import Optional, Any
import dateparser
from dateutil.relativedelta import relativedelta

class GoogleCalendarTool(BaseTool):
    name = "google_calendar"
    description = """A tool for managing Google Calendar events. Available operations:
                    1. Create events: Input should be a JSON string with: 
                       operation: "create",
                       title, start_time, end_time, attendees (list of emails), 
                       description (optional), location (optional).
                       Times should be in natural language (e.g., 'tomorrow at 2pm', 'next Monday at 3pm')
                    2. List events: Input should be a JSON string with:
                       operation: "list",
                       start_time (optional), end_time (optional), max_results (optional, default 10)"""
    
    service: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_credentials()

    def _setup_credentials(self):
        """Set up Google Calendar API credentials."""
        # Load credentials from file
        creds_file = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE")
        token_file = os.getenv("GOOGLE_CALENDAR_TOKEN_FILE")
        scopes = [os.getenv("GOOGLE_CALENDAR_SCOPES")]

        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)

    def _parse_datetime(self, time_str: str) -> str:
        """Parse natural language time string to RFC3339 format."""
        try:
            # Parse the natural language time with dateparser
            settings = {
                'PREFER_DATES_FROM': 'future',
                'RETURN_AS_TIMEZONE_AWARE': True,
                'TIMEZONE': 'Asia/Singapore'  # Set default timezone to Singapore
            }
            dt = dateparser.parse(time_str, settings=settings)
            
            if dt is None:
                raise ValueError(f"Could not parse time: {time_str}")
            
            # Ensure the datetime is in Singapore timezone
            sgt = pytz.timezone('Asia/Singapore')
            if dt.tzinfo is None:
                dt = sgt.localize(dt)
            else:
                dt = dt.astimezone(sgt)
            
            # Format as RFC3339 with Singapore timezone
            return dt.isoformat()
        except Exception as e:
            raise ValueError(f"Could not parse time: {time_str}. Error: {str(e)}")

    def _list_events(self, params: dict) -> str:
        """List calendar events in a structured format."""
        try:
            # Set default parameters
            now = datetime.now(pytz.timezone('Asia/Singapore'))
            start_time = params.get('start_time', now.isoformat())
            end_time = params.get('end_time', (now + timedelta(days=7)).isoformat())
            max_results = params.get('max_results', 10)

            # Parse time strings if provided
            if isinstance(start_time, str):
                start_time = self._parse_datetime(start_time)
            if isinstance(end_time, str):
                end_time = self._parse_datetime(end_time)

            # Get events
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time,
                timeMax=end_time,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            
            if not events:
                return "No events found in the specified time range."

            # Format list
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse and format times
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                start_dt = start_dt.astimezone(pytz.timezone('Asia/Singapore'))
                end_dt = end_dt.astimezone(pytz.timezone('Asia/Singapore'))
                
                event_info = {
                    "id": event['id'],
                    "title": event['summary'],
                    "start": start_dt.strftime('%Y-%m-%d %H:%M'),
                    "end": end_dt.strftime('%H:%M'),
                    "location": event.get('location', ''),
                    "description": event.get('description', ''),
                    "attendees": [attendee['email'] for attendee in event.get('attendees', [])]
                }
                event_list.append(event_info)

            # Convert to JSON string for output
            return json.dumps(event_list, indent=2)
        except Exception as e:
            return f"Error listing events: {str(e)}"

    def _run(self, input_str: str) -> str:
        """Handle calendar operations based on input."""
        try:
            # Parse input JSON
            data = json.loads(input_str)
            
            # Get operation type
            operation = data.get("operation")
            if not operation:
                return "Error: Operation type not specified. Please include 'operation' field with value 'create' or 'list'"
            
            # Handle operation based on type
            if operation == "create":
                return self._create_event(data)
            elif operation == "list":
                return self._list_events(data)
            else:
                return f"Error: Invalid operation '{operation}'. Must be one of: create, list"
                
        except Exception as e:
            return f"Error: {str(e)}"

    def _create_event(self, event_data: dict) -> str:
        """Create a calendar event."""
        try:
            # Validate required fields
            if not event_data.get("title"):
                return "Error: Event title is required"
            if not event_data.get("start_time"):
                return "Error: Start time is required"
            
            # Parse start time
            start_time = self._parse_datetime(event_data["start_time"])
            if not start_time:
                return "Error: Could not parse start time"
            
            # Set default end time if not provided
            if not event_data.get("end_time"):
                # Parse start time again to get datetime object
                start_dt = dateparser.parse(event_data["start_time"], settings={'TIMEZONE': 'Asia/Singapore'})
                if start_dt:
                    # Add 1 hour to start time
                    end_dt = start_dt + timedelta(hours=1)
                    # Format in RFC3339 with Singapore timezone
                    end_time = end_dt.astimezone(pytz.timezone('Asia/Singapore')).strftime('%Y-%m-%dT%H:%M:%S%z')
                else:
                    return "Error: Could not parse start time for default end time"
            else:
                # Parse provided end time
                end_time = self._parse_datetime(event_data["end_time"])
                if not end_time:
                    return "Error: Could not parse end time"
            
            # Create event
            event = {
                'summary': event_data["title"],
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'Asia/Singapore',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'Asia/Singapore',
                },
                'description': event_data.get("description", ""),
                'location': event_data.get("location", ""),
            }
            
            # Add attendees if provided
            if event_data.get("attendees"):
                event['attendees'] = [{'email': email} for email in event_data["attendees"]]
            
            # Create the event
            event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            
            return f"Event created: {event.get('htmlLink')}"
        except Exception as e:
            return f"Error creating event: {str(e)}"

    async def _arun(self, query: str) -> str:
        """Async version of _run."""
        return self._run(query) 