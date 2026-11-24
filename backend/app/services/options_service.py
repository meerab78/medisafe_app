from app.core import appointment_options, medication_options
from app.schemas.options_schema import (
    AppointmentWizardResponse,
    MedicationWizardResponse,
)

# Increase this number whenever the wizard changes, so the app knows to refresh
WIZARD_VERSION = 1


def build_medication_wizard():
    steps = []

    # ---------------- Main steps ----------------

    steps.append(
        {
            "id": "name",
            "field": "name",
            "type": "text",
            "section": "main",
            "title": "What is the name of the medicine?",
            "hint": "Example: Paracetamol",
            "required": True,
        }
    )

    steps.append(
        {
            "id": "form",
            "field": "medication_type",
            "type": "single_choice",
            "section": "main",
            "title": "What form is it?",
            "required": True,
            "options": medication_options.MEDICATION_FORMS,
        }
    )

    steps.append(
        {
            "id": "route",
            "field": "route",
            "type": "single_choice",
            "section": "main",
            "title": "How do you take it?",
            "required": True,
            "options": medication_options.MEDICATION_ROUTES,
            "show_when": {"step": "form", "equals": "other"},
        }
    )

    steps.append(
        {
            "id": "dosage",
            "field": "dosage",
            "type": "text",
            "section": "main",
            "title": "What is the strength or amount?",
            "hint": "Example: 500 mg or 5 ml",
            "required": True,
        }
    )

    steps.append(
        {
            "id": "reason",
            "field": "reason",
            "type": "text",
            "section": "main",
            "title": "What are you taking it for?",
            "hint": "You can skip this",
            "required": False,
        }
    )

    steps.append(
        {
            "id": "frequency",
            "field": "schedule.schedule_type",
            "type": "single_choice",
            "section": "main",
            "title": "How often do you take it?",
            "required": True,
            "options": medication_options.FREQUENCY_OPTIONS,
        }
    )

    steps.append(
        {
            "id": "days",
            "field": "schedule.days_of_week",
            "type": "multi_choice",
            "section": "main",
            "title": "On which days?",
            "required": True,
            "options": medication_options.DAYS_OF_WEEK,
            "show_when": {"step": "frequency", "equals": "weekly"},
        }
    )

    steps.append(
        {
            "id": "times_per_day",
            "field": None,
            "type": "single_choice",
            "section": "main",
            "title": "How many times a day?",
            "required": True,
            "options": medication_options.TIMES_PER_DAY_OPTIONS,
        }
    )

    steps.append(
        {
            "id": "hours_between",
            "field": "schedule.hours_between",
            "type": "single_choice",
            "section": "main",
            "title": "How many hours between doses?",
            "required": True,
            "options": medication_options.HOURS_BETWEEN_OPTIONS,
            "show_when": {"step": "times_per_day", "equals": "hourly"},
        }
    )

    steps.append(
        {
            "id": "first_dose_time",
            "field": "schedule.first_dose_time",
            "type": "time",
            "section": "main",
            "title": "When is the first dose of the day?",
            "required": True,
            "show_when": {"step": "times_per_day", "equals": "hourly"},
        }
    )

    steps.append(
        {
            "id": "times",
            "field": "schedule.times",
            "type": "times",
            "section": "main",
            "title": "When do you take it?",
            "hint": "Each time has a time_of_day and a dose_amount (default 1)",
            "required": True,
            "count_from": "times_per_day",
            "show_when": {"step": "times_per_day", "not_equals": "hourly"},
        }
    )

    # ---------------- Extra (optional) settings ----------------

    steps.append(
        {
            "id": "start_date",
            "field": "start_date",
            "type": "date",
            "section": "extras",
            "title": "When do you start?",
            "required": False,
            "default": "today",
        }
    )

    steps.append(
        {
            "id": "duration",
            "field": None,
            "type": "single_choice",
            "section": "extras",
            "title": "How long will you take it?",
            "required": False,
            "default": "no_end",
            "options": medication_options.DURATION_OPTIONS,
        }
    )

    steps.append(
        {
            "id": "end_date",
            "field": "end_date",
            "type": "date",
            "section": "extras",
            "title": "Until which date?",
            "required": True,
            "show_when": {"step": "duration", "equals": "end_date"},
        }
    )

    steps.append(
        {
            "id": "stock_quantity",
            "field": "stock_quantity",
            "type": "number",
            "section": "extras",
            "title": "How many do you have right now?",
            "required": False,
            "default": 0,
        }
    )

    steps.append(
        {
            "id": "low_stock_threshold",
            "field": "low_stock_threshold",
            "type": "number",
            "section": "extras",
            "title": "Remind me to refill when this many are left",
            "required": False,
            "default": 5,
        }
    )

    steps.append(
        {
            "id": "icon",
            "field": "icon",
            "type": "single_choice",
            "section": "extras",
            "title": "Choose an icon",
            "required": False,
            "options": medication_options.MEDICATION_ICONS,
        }
    )

    steps.append(
        {
            "id": "food_instruction",
            "field": "food_instruction",
            "type": "single_choice",
            "section": "extras",
            "title": "Any instructions about food?",
            "required": False,
            "default": "any",
            "options": medication_options.FOOD_INSTRUCTIONS,
        }
    )

    steps.append(
        {
            "id": "instructions",
            "field": "instructions",
            "type": "text",
            "section": "extras",
            "title": "Add a note",
            "hint": "Example: Take with a full glass of water",
            "required": False,
        }
    )

    return MedicationWizardResponse(version=WIZARD_VERSION, steps=steps)

APPOINTMENT_WIZARD_VERSION = 1


def build_appointment_wizard():
    steps = []

    # ---------------- Main steps ----------------

    steps.append(
        {
            "id": "title",
            "field": "title",
            "type": "text",
            "section": "main",
            "title": "What is the name of the appointment?",
            "hint": "Example: Dentist visit",
            "required": True,
        }
    )

    steps.append(
        {
            "id": "appointment_at",
            "field": "appointment_at",
            "type": "datetime",
            "section": "main",
            "title": "What is the date and time of the appointment?",
            "hint": "Send the time in the user's own timezone, for example 2026-12-05T16:30:00",
            "required": True,
        }
    )

    steps.append(
        {
            "id": "remind_before_minutes",
            "field": "remind_before_minutes",
            "type": "single_choice",
            "section": "main",
            "title": "When would you like to be reminded?",
            "required": False,
            "default": 60,
            "options": appointment_options.APPOINTMENT_REMINDERS,
        }
    )

    # ---------------- Extra (optional) settings ----------------

    steps.append(
        {
            "id": "doctor_name",
            "field": "doctor_name",
            "type": "text",
            "section": "extras",
            "title": "Doctor's name",
            "required": False,
        }
    )

    steps.append(
        {
            "id": "location",
            "field": "location",
            "type": "text",
            "section": "extras",
            "title": "Where is it?",
            "required": False,
        }
    )

    steps.append(
        {
            "id": "notes",
            "field": "notes",
            "type": "text",
            "section": "extras",
            "title": "Add a note",
            "hint": "Example: Bring old reports",
            "required": False,
        }
    )

    return AppointmentWizardResponse(version=APPOINTMENT_WIZARD_VERSION, steps=steps)