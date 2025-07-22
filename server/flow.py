#
# Copyright (c) 2024, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import datetime
from pathlib import Path
from typing import List, TypedDict, Optional

from loguru import logger

# Google Calendar imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pipecat_flows import (
    ContextStrategy,
    ContextStrategyConfig,
    FlowArgs,
    FlowConfig,
    FlowResult,
)

# Google Calendar Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']

class DateUtility:
    """Utility class for date operations and conversions."""
    
    @staticmethod
    def get_current_date_info():
        """Get current date information in user-friendly format."""
        today = datetime.date.today()
        return {
            "today_formatted": today.strftime('%A %B %d, %Y'),  # "Friday July 19, 2025"
            "today_iso": today.strftime('%Y-%m-%d'),            # For internal use
            "day_name": today.strftime('%A'),
            "month_name": today.strftime('%B'),
            "year": today.year,
            "month": today.month,
            "day": today.day
        }
    
    @staticmethod
    def format_date_user_friendly(date_str: str) -> str:
        """Convert YYYY-MM-DD format to user-friendly format like 'Friday July 18th, 2025'."""
        try:
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            # Add ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
            day = date_obj.day
            if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]
            
            return date_obj.strftime(f'%A %B {day}{suffix}, %Y')
        except ValueError:
            return date_str  # Return as-is if can't parse

class CalendarManager:
    """Manages Google Calendar operations."""
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        creds = None
        token_path = Path(__file__).parent / 'token.json'
        credentials_path = Path(__file__).parent / 'credentials.json'
        
        # Load existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        f"credentials.json not found at {credentials_path}. "
                        "Please follow the setup guide in CALENDAR_SETUP.md"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def get_available_slots(self, date_str: str, duration_minutes: int = 30) -> List[str]:
        """Get available appointment slots for a given date."""
        try:
            # Parse the date
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            
            # Define business hours (9 AM - 5 PM)
            start_time = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
            
            # Get existing events for the day
            start_time_iso = start_time.isoformat() + 'Z'
            end_time_iso = end_time.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time_iso,
                timeMax=end_time_iso,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Generate all possible slots
            available_slots = []
            current_time = start_time
            
            while current_time + datetime.timedelta(minutes=duration_minutes) <= end_time:
                slot_end = current_time + datetime.timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any existing event
                is_available = True
                for event in events:
                    event_start = datetime.datetime.fromisoformat(
                        event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00')
                    ).replace(tzinfo=None)
                    event_end = datetime.datetime.fromisoformat(
                        event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00')
                    ).replace(tzinfo=None)
                    
                    # Check for overlap
                    if (current_time < event_end and slot_end > event_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(current_time.strftime('%H:%M'))
                
                # Move to next slot (every 30 minutes)
                current_time += datetime.timedelta(minutes=30)
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
    
    def schedule_appointment(self, date_str: str, time_str: str, patient_name: str, 
                           patient_email: str = None, duration_minutes: int = 30, description: str = "") -> bool:
        """Schedule an appointment in Google Calendar."""
        try:
            # Parse date and time
            appointment_datetime = datetime.datetime.strptime(
                f"{date_str} {time_str}", '%Y-%m-%d %H:%M'
            )
            end_datetime = appointment_datetime + datetime.timedelta(minutes=duration_minutes)
            
            # Validate patient email is provided
            if not patient_email:
                logger.error("Cannot schedule appointment: patient_email is required")
                return False
            
            # Create event
            attendees = [{'email': patient_email, 'responseStatus': 'needsAction'}]
            event = {
                'summary': f'Appointment with {patient_name}',
                'description': description,
                'start': {
                    'dateTime': appointment_datetime.isoformat(),
                    'timeZone': 'America/New_York',  # Change this to your timezone
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/New_York',  # Change this to your timezone
                },
                'attendees': attendees,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'guestsCanSeeOtherGuests': False,
            }
            
            logger.info(f"Creating calendar event with attendees: {attendees}")
            
            # Create the event and send invitations
            event = self.service.events().insert(
                calendarId='primary', 
                body=event,
                sendUpdates='all'  # This ensures invitations are sent to all attendees
            ).execute()
            logger.info(f'Event created: {event.get("htmlLink")}')
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling appointment: {e}")
            return False

# Initialize calendar manager
calendar_manager = CalendarManager()

def normalize_time(time_str: str) -> str:
    """Convert various time formats to HH:MM format."""
    time_str = time_str.lower().strip()
    
    # Handle common patterns
    if 'am' in time_str or 'pm' in time_str:
        # Parse 12-hour format
        try:
            # Clean up the string
            time_str = time_str.replace(' ', '')
            if ':' not in time_str:
                # Handle cases like "2pm" -> "2:00pm"
                time_str = time_str.replace('am', ':00am').replace('pm', ':00pm')
            
            # Parse and convert to 24-hour format
            time_obj = datetime.datetime.strptime(time_str, '%I:%M%p')
            return time_obj.strftime('%H:%M')
        except ValueError:
            pass
    
    # Handle 24-hour format or already normalized
    try:
        # Try to parse as HH:MM
        time_obj = datetime.datetime.strptime(time_str, '%H:%M')
        return time_str
    except ValueError:
        pass
    
    # Handle just hour numbers
    try:
        hour = int(time_str)
        if 9 <= hour <= 17:  # Business hours
            return f"{hour:02d}:00"
    except ValueError:
        pass
    
    return time_str  # Return as-is if can't normalize


# Type definitions
class Prescription(TypedDict):
    medication: str
    dosage: str


class Allergy(TypedDict):
    name: str


class Condition(TypedDict):
    name: str


class VisitReason(TypedDict):
    name: str


# Result types for each handler
class PatientInfoResult(FlowResult):
    name: str
    birthday: str


class PrescriptionRecordResult(FlowResult):
    count: int


class AllergyRecordResult(FlowResult):
    count: int


class ConditionRecordResult(FlowResult):
    count: int


class VisitReasonRecordResult(FlowResult):
    count: int


# Calendar scheduling result types
class DateInfoResult(FlowResult):
    current_date_formatted: str
    current_date_iso: str
    day_name: str


class DateCheckResult(FlowResult):
    date: str
    date_formatted: str
    available_slots: List[str]
    preferred_time: Optional[str]


class AppointmentScheduleResult(FlowResult):
    scheduled: bool
    appointment_date: str
    appointment_date_formatted: str
    appointment_time: str


# Function handlers
async def collect_patient_info(args: FlowArgs) -> tuple[PatientInfoResult, str]:
    """Handler for collecting patient name and birthday."""
    name = args["name"].strip()
    birthday = args["birthday"]
    
    # Basic validation
    if not name or len(name) < 2:
        raise ValueError("Name must be at least 2 characters long")
    
    # In a real app, this would store in patient records and possibly verify against existing records
    return PatientInfoResult(name=name, birthday=birthday), "get_prescriptions"


async def record_prescriptions(args: FlowArgs) -> tuple[PrescriptionRecordResult, str]:
    """Handler for recording prescriptions."""
    prescriptions: List[Prescription] = args["prescriptions"]
    # In a real app, this would store in patient records
    return PrescriptionRecordResult(count=len(prescriptions)), "get_allergies"


async def record_allergies(args: FlowArgs) -> tuple[AllergyRecordResult, str]:
    """Handler for recording allergies."""
    allergies: List[Allergy] = args["allergies"]
    # In a real app, this would store in patient records
    return AllergyRecordResult(count=len(allergies)), "get_conditions"


async def record_conditions(args: FlowArgs) -> tuple[ConditionRecordResult, str]:
    """Handler for recording medical conditions."""
    conditions: List[Condition] = args["conditions"]
    # In a real app, this would store in patient records
    return ConditionRecordResult(count=len(conditions)), "get_visit_reasons"


async def record_visit_reasons(args: FlowArgs) -> tuple[VisitReasonRecordResult, str]:
    """Handler for recording visit reasons."""
    visit_reasons: List[VisitReason] = args["visit_reasons"]
    # In a real app, this would store in patient records
    return VisitReasonRecordResult(count=len(visit_reasons)), "verify"


async def revise_information(args: FlowArgs) -> tuple[None, str]:
    """Handler to restart the information-gathering process."""
    return None, "get_prescriptions"


async def confirm_information(args: FlowArgs) -> tuple[None, str]:
    """Handler to confirm all collected information."""
    return None, "confirm"


async def complete_intake(args: FlowArgs) -> tuple[None, str]:
    """Handler to complete the intake process."""
    return None, "schedule_date"


# Calendar scheduling handlers
async def get_current_date(args: FlowArgs) -> tuple[DateInfoResult, str]:
    """Handler to get current date information."""
    # Get current date info
    date_info = DateUtility.get_current_date_info()
    
    return DateInfoResult(
        current_date_formatted=date_info["today_formatted"],
        current_date_iso=date_info["today_iso"],
        day_name=date_info["day_name"]
    ), "schedule_date"


async def check_availability(args: FlowArgs) -> tuple[DateCheckResult, str]:
    """Handler for checking appointment availability for a given date."""
    date = args["date"].strip()
    preferred_time = args.get("preferred_time", "").strip()
    
    # Validate date format - expect YYYY-MM-DD from AI conversion
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")
    
    # Check if date is in the future
    today = datetime.date.today()
    requested_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    
    if requested_date <= today:
        raise ValueError("Please select a future date")
    
    # Get available slots
    available_slots = calendar_manager.get_available_slots(date)
    
    # If user specified a preferred time, check if it's available
    if preferred_time:
        # Normalize the preferred time to HH:MM format
        normalized_time = normalize_time(preferred_time)
        if normalized_time in available_slots:
            # Move preferred time to the front of the list
            available_slots.remove(normalized_time)
            available_slots.insert(0, normalized_time)
    
    return DateCheckResult(
        date=date, 
        date_formatted=DateUtility.format_date_user_friendly(date),
        available_slots=available_slots, 
        preferred_time=preferred_time
    ), "schedule_time"


async def schedule_appointment_handler(args: FlowArgs) -> tuple[AppointmentScheduleResult, str]:
    """Handler for scheduling an appointment using patient info from intake."""
    date = args["date"]
    time = args["time"]
    patient_email = args["email"]  # Email collected directly as parameter
    
    # Get patient info from context - this will be available from the previous steps
    patient_name = args.get("patient_name", "Patient")
    visit_reasons = args.get("visit_reasons", ["General consultation"])
    
    # Validate that patient email exists
    if not patient_email:
        logger.error("No patient email provided - this is required for scheduling")
        raise ValueError("Patient email is required to schedule appointment and send calendar invitation")
    
    logger.info(f"Scheduling appointment for {patient_name} with email: {patient_email}")
    
    # Create description from visit reasons
    if isinstance(visit_reasons, list) and visit_reasons:
        reasons_text = ", ".join([reason['name'] if isinstance(reason, dict) else str(reason) for reason in visit_reasons])
    else:
        reasons_text = "General consultation"
    
    # Schedule the appointment
    success = calendar_manager.schedule_appointment(
        date_str=date,
        time_str=time,
        patient_name=patient_name,
        patient_email=patient_email,
        description=f"Reason for visit: {reasons_text}"
    )
    
    if success:
        return AppointmentScheduleResult(
            scheduled=True,
            appointment_date=date,
            appointment_date_formatted=DateUtility.format_date_user_friendly(date),
            appointment_time=time
        ), "confirm_appointment"
    else:
        return AppointmentScheduleResult(
            scheduled=False,
            appointment_date=date,
            appointment_date_formatted=DateUtility.format_date_user_friendly(date),
            appointment_time=time
        ), "reschedule_appointment"


async def reschedule_appointment(args: FlowArgs) -> tuple[None, str]:
    """Handler to restart the scheduling process."""
    return None, "schedule_date"


async def confirm_final_appointment(args: FlowArgs) -> tuple[None, str]:
    """Handler to confirm the appointment and end."""
    return None, "end"


def get_current_datetime_context() -> str:
    """Generate current date and time context for system prompts."""
    now = datetime.datetime.now(datetime.timezone.utc)
    day_name = now.strftime('%A')
    month_name = now.strftime('%B')
    day = now.day
    year = now.year
    time_str = now.strftime('%I:%M %p UTC')
    
    # Add ordinal suffix to day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    
    return f"Today is {day_name}, {month_name} {day}{suffix}, {year}. The current time is {time_str}. Use this information when interpreting relative date requests like 'tomorrow', 'next week', etc."


# Flow Configuration - Patient Intake with Calendar Scheduling
#
# This configuration defines a medical intake system with the following states:
#
# 1. collect_info (INITIAL STATE)
#    - Initial state where system collects patient's name and birthday
#    - Functions:
#      * collect_patient_info (collects and validates name and birthday)
#    - Pre-action: Initial greeting from Jessica
#    - Expected flow: Greet -> Ask for name and birthday -> Validate -> Transition to prescriptions
#
# 2. get_prescriptions
#    - Collects information about patient's current medications
#    - Functions:
#      * record_prescriptions (node function, collects medication name and dosage)
#      * get_allergies (transitions to allergy collection)
#    - Expected flow: Ask about prescriptions -> Record details -> Transition to allergies
#
# 3. get_allergies
#    - Collects information about patient's allergies
#    - Functions:
#      * record_allergies (node function, records allergy information)
#      * get_conditions (transitions to medical conditions)
#    - Expected flow: Ask about allergies -> Record details -> Transition to conditions
#
# 4. get_conditions
#    - Collects information about patient's medical conditions
#    - Functions:
#      * record_conditions (node function, records medical conditions)
#      * get_visit_reasons (transitions to visit reason collection)
#    - Expected flow: Ask about conditions -> Record details -> Transition to visit reasons
#
# 5. get_visit_reasons
#    - Collects information about why patient is visiting
#    - Functions:
#      * record_visit_reasons (node function, records visit reasons)
#      * verify_information (transitions to verification)
#    - Expected flow: Ask about visit reason -> Record details -> Transition to verification
#
# 6. verify
#    - Reviews all collected information with patient
#    - Functions:
#      * revise_information (returns to prescriptions if changes needed)
#      * confirm_information (transitions to confirmation after approval)
#    - Expected flow: Review all info -> Confirm accuracy -> End or revise
#
# 7. confirm
#    - Confirms all information and prepares for scheduling
#    - Functions:
#      * complete_intake (transitions to scheduling)
#    - Expected flow: Final confirmation -> Begin scheduling
#
# 8. schedule_date
#    - Collects preferred appointment date
#    - Functions:
#      * get_current_date (gets current date context)
#      * check_availability (checks available slots for date)
#    - Expected flow: Ask for date -> Check availability -> Show available times
#
# 9. schedule_time
#    - Shows available times and collects time preference
#    - Functions:
#      * schedule_appointment_handler (schedules appointment with patient info)
#    - Expected flow: Show times -> Collect preference -> Schedule appointment
#
# 10. reschedule_appointment
#     - Handles scheduling errors
#     - Functions:
#       * reschedule_appointment (restarts scheduling process)
#     - Expected flow: Error -> Restart scheduling
#
# 11. confirm_appointment
#     - Confirms successful appointment scheduling
#     - Functions:
#       * confirm_final_appointment (ends conversation)
#     - Expected flow: Confirm details -> End
#
# 12. end
#     - Final state that closes the conversation
#     - No functions available
#     - Pre-action: Thank you message
#     - Post-action: Ends conversation

flow_config: FlowConfig = {
    "initial_node": "collect_info",
    "nodes": {
        "collect_info": {
            "role_messages": [
                {
                    "role": "system",
                    "content": "You are Jessica, an agent for Newcast Health Services. You must ALWAYS use one of the available functions to progress the conversation. Be professional but friendly.",
                }
            ],
            "task_messages": [
                {
                    "role": "system",
                    "content": "Start by introducing yourself and explaining that you'll be conducting a patient intake. Ask for the patient's full name and date of birth. When they provide their birthday in any format, convert it to YYYY-MM-DD format before calling the collect_patient_info function.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "collect_patient_info",
                        "handler": collect_patient_info,
                        "description": "Collect the patient's name and birthday. Both fields are required and will be validated. Once collected, proceed to prescription collection.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "The patient's full name",
                                },
                                "birthday": {
                                    "type": "string",
                                    "description": "The patient's birthdate converted to YYYY-MM-DD format",
                                }
                            },
                            "required": ["name", "birthday"],
                        },
                    },
                },
            ],
        },
        "get_prescriptions": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "This step is for collecting prescriptions. Ask them what prescriptions they're taking, including the dosage. After recording prescriptions (or confirming none), proceed to allergies.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "record_prescriptions",
                        "handler": record_prescriptions,
                        "description": "Record the user's prescriptions. Once confirmed, the next step is to collect allergy information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prescriptions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "medication": {
                                                "type": "string",
                                                "description": "The medication's name",
                                            },
                                            "dosage": {
                                                "type": "string",
                                                "description": "The prescription's dosage",
                                            },
                                        },
                                        "required": ["medication", "dosage"],
                                    },
                                }
                            },
                            "required": ["prescriptions"],
                        },
                    },
                },
            ],
        },
        "get_allergies": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "Collect allergy information. Ask about any allergies they have. After recording allergies (or confirming none), proceed to medical conditions.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "record_allergies",
                        "handler": record_allergies,
                        "description": "Record the user's allergies. Once confirmed, then next step is to collect medical conditions.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "allergies": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "description": "What the user is allergic to",
                                            },
                                        },
                                        "required": ["name"],
                                    },
                                }
                            },
                            "required": ["allergies"],
                        },
                    },
                },
            ],
        },
        "get_conditions": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "Collect medical condition information. Ask about any medical conditions they have. After recording conditions (or confirming none), proceed to visit reasons.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "record_conditions",
                        "handler": record_conditions,
                        "description": "Record the user's medical conditions. Once confirmed, the next step is to collect visit reasons.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "conditions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "description": "The user's medical condition",
                                            },
                                        },
                                        "required": ["name"],
                                    },
                                }
                            },
                            "required": ["conditions"],
                        },
                    },
                },
            ],
        },
        "get_visit_reasons": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "Collect information about the reason for their visit. Ask what brings them to the doctor today. After recording their reasons, proceed to verification.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "record_visit_reasons",
                        "handler": record_visit_reasons,
                        "description": "Record the reasons for their visit. Once confirmed, the next step is to verify all information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "visit_reasons": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "description": "The user's reason for visiting",
                                            },
                                        },
                                        "required": ["name"],
                                    },
                                }
                            },
                            "required": ["visit_reasons"],
                        },
                    },
                },
            ],
        },
        "verify": {
            "task_messages": [
                {
                    "role": "system",
                    "content": """Review all collected information with the patient. Follow these steps:
1. State their legal name and birth date
2. Then summarize their prescriptions, allergies, conditions, and visit reasons
3. Ask if everything is correct
4. Use the appropriate function based on their response

Format the summary clearly and be thorough in reviewing all details. Wait for explicit confirmation.""",
                }
            ],
            "context_strategy": ContextStrategyConfig(
                strategy=ContextStrategy.RESET_WITH_SUMMARY,
                summary_prompt=(
                    "Summarize the patient intake conversation in the following structured format:\n\n"
                    "PATIENT INFORMATION:\n"
                    "- Legal Name: [patient's full name]\n"
                    "- Date of Birth: [patient's birth date]\n\n"
                    "MEDICAL INFORMATION:\n"
                    "- Prescriptions: [list all medications and dosages, or 'None' if no prescriptions]\n"
                    "- Allergies: [list all allergies, or 'None' if no allergies]\n"
                    "- Medical Conditions: [list all conditions, or 'None' if no conditions]\n"
                    "- Reason for Visit: [list all visit reasons]\n\n"
                    "Focus on providing complete and accurate information for each section."
                ),
            ),
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "revise_information",
                        "handler": revise_information,
                        "description": "Return to prescriptions to revise information",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "confirm_information",
                        "handler": confirm_information,
                        "description": "Proceed with confirmed information",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
            ],
        },
        "confirm": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "Thank them for providing their medical information. Explain that the final step is to schedule their appointment. Use the complete_intake function to proceed to scheduling.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "complete_intake",
                        "handler": complete_intake,
                        "description": "Complete the intake process and proceed to appointment scheduling",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
            ],
        },
        "schedule_date": {
            "role_messages": [
                {
                    "role": "system",
                    "content": f"You are Jessica, a scheduling assistant for Newcast Health Services. You've completed the patient intake and now need to schedule their appointment. Be professional but friendly and helpful.\n\nIMPORTANT: {get_current_datetime_context()}",
                }
            ],
            "task_messages": [
                {
                    "role": "system",
                    "content": "Now that we have completed your medical intake, let's schedule your appointment. Ask when they would like to schedule their appointment. When they mention any date (like 'tomorrow', 'next Monday', 'June 15th', etc.), you should:\n\n1. First call get_current_date to know what today is\n2. Then convert their date request to YYYY-MM-DD format using your understanding of dates\n3. Always present dates back to the user in friendly format like 'Friday July 18th, 2025' (never show YYYY-MM-DD to users)\n4. Use check_availability with the YYYY-MM-DD format",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_current_date",
                        "handler": get_current_date,
                        "description": "Get the current date information. Call this first when user mentions any date to understand what today is, then you can convert their relative date expressions to specific dates.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "check_availability",
                        "handler": check_availability,
                        "description": "Check available appointment slots for a given date. You must convert any natural language date to YYYY-MM-DD format before calling this function, but always present dates to users in friendly format like 'Friday July 18th, 2025'.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date": {
                                    "type": "string",
                                    "description": "The desired appointment date in YYYY-MM-DD format (converted by you from user's natural language)",
                                },
                                "preferred_time": {
                                    "type": "string",
                                    "description": "The preferred time if mentioned by the user (e.g., '10:00', '2pm', '14:30'). Leave empty if no time was specified.",
                                },
                            },
                            "required": ["date"],
                        },
                    },
                },
            ],
        },
        "schedule_time": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "You now have the available time slots for the requested date. The date_formatted field contains the proper user-friendly format to show to the patient. Present the available times to the patient in a friendly way and ask them to choose their preferred time. After they select a time, ask for their email address so we can send them a calendar invitation. Once you have both the time and email, schedule the appointment. Use the date_formatted field when mentioning the date to users (never show YYYY-MM-DD format).",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "schedule_appointment_handler",
                        "handler": schedule_appointment_handler,
                        "description": "Schedule an appointment with the selected date and time using the patient information from the intake. Convert any time format to HH:MM 24-hour format.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date": {
                                    "type": "string",
                                    "description": "The appointment date in YYYY-MM-DD format",
                                },
                                "time": {
                                    "type": "string",
                                    "description": "The appointment time converted to HH:MM format (24-hour)",
                                },
                                "email": {
                                    "type": "string",
                                    "description": "The patient's email address for calendar invitation",
                                },
                                "patient_name": {
                                    "type": "string",
                                    "description": "The patient's full name from the intake",
                                },
                                "visit_reasons": {
                                    "type": "array",
                                    "description": "The visit reasons from the intake",
                                    "items": {"type": "string"}
                                },
                            },
                            "required": ["date", "time", "email"],
                        },
                    },
                },
            ],
        },
        "reschedule_appointment": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "There was an issue scheduling the appointment. Apologize for the inconvenience and offer to try scheduling for a different date or time. Use the reschedule function to start over.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "reschedule_appointment",
                        "handler": reschedule_appointment,
                        "description": "Start the scheduling process over from the beginning",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
            ],
        },
        "confirm_appointment": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "The appointment has been successfully scheduled! Confirm the appointment details with the patient using the appointment_date_formatted field for the date (never show YYYY-MM-DD to users). Include the date, time, and remind them of their visit reason. Provide any final instructions and use the confirm_final_appointment function to end the conversation.",
                }
            ],
            "functions": [
                {
                    "type": "function",
                    "function": {
                        "name": "confirm_final_appointment",
                        "handler": confirm_final_appointment,
                        "description": "Confirm the appointment and end the conversation",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
            ],
        },
        "end": {
            "task_messages": [
                {
                    "role": "system",
                    "content": "Thank them for completing both the intake and scheduling their appointment. Remind them to arrive 15 minutes early and bring a valid ID. End the conversation politely.",
                }
            ],
            "post_actions": [{"type": "end_conversation"}],
        },
    },
}
