# All options for the medication wizard live here (one source of truth)

MEDICATION_FORMS = [
    {"value": "pill", "label": "Pill"},
    {"value": "injection", "label": "Injection"},
    {"value": "liquid", "label": "Liquid"},
    {"value": "drops", "label": "Drops"},
    {"value": "inhaler", "label": "Inhaler"},
    {"value": "powder", "label": "Powder"},
    {"value": "other", "label": "Other"},
]

# Asked only when the form is "other"
MEDICATION_ROUTES = [
    {"value": "mouth", "label": "By mouth"},
    {"value": "nose", "label": "In the nose"},
    {"value": "ears", "label": "In the ears"},
    {"value": "injection", "label": "Injection"},
    {"value": "vaginal", "label": "Vaginal"},
    {"value": "inhaled", "label": "Inhaled"},
]

FOOD_INSTRUCTIONS = [
    {"value": "before_meal", "label": "Before eating"},
    {"value": "with_meal", "label": "While eating"},
    {"value": "after_meal", "label": "After eating"},
    {"value": "any", "label": "Doesn't matter"},
]

# Icon names. Change this list when the designer decides the final icons.
MEDICATION_ICONS = [
    {"value": "pill_white", "label": "White pill"},
    {"value": "pill_blue", "label": "Blue pill"},
    {"value": "pill_pink", "label": "Pink pill"},
    {"value": "capsule", "label": "Capsule"},
    {"value": "liquid", "label": "Liquid"},
    {"value": "drops", "label": "Drops"},
    {"value": "injection", "label": "Injection"},
    {"value": "inhaler", "label": "Inhaler"},
    {"value": "powder", "label": "Powder"},
]

# Monday = 0 ... Sunday = 6 (same numbers the schedule API uses)
DAYS_OF_WEEK = [
    {"value": 0, "label": "Monday"},
    {"value": 1, "label": "Tuesday"},
    {"value": 2, "label": "Wednesday"},
    {"value": 3, "label": "Thursday"},
    {"value": 4, "label": "Friday"},
    {"value": 5, "label": "Saturday"},
    {"value": 6, "label": "Sunday"},
]

# "extra" values are merged into the final request body by the app
FREQUENCY_OPTIONS = [
    {"value": "daily", "label": "Every day"},
    {
        "value": "interval",
        "label": "Every other day",
        "extra": {"schedule.interval_days": 2},
    },
    {"value": "weekly", "label": "Specific days of the week"},
]

TIMES_PER_DAY_OPTIONS = [
    {"value": "1", "label": "Once a day"},
    {"value": "2", "label": "Twice a day"},
    {"value": "3", "label": "3 times a day"},
    {"value": "hourly", "label": "Every few hours"},
]

HOURS_BETWEEN_OPTIONS = [
    {"value": 2, "label": "Every 2 hours"},
    {"value": 3, "label": "Every 3 hours"},
    {"value": 4, "label": "Every 4 hours"},
    {"value": 6, "label": "Every 6 hours"},
    {"value": 8, "label": "Every 8 hours"},
    {"value": 12, "label": "Every 12 hours"},
]

DURATION_OPTIONS = [
    {"value": "no_end", "label": "No end date"},
    {"value": "end_date", "label": "Until a date"},
]


def get_option_values(options):
    # Returns only the "value" of each option, for example ["pill", "injection"]
    values = []
    for option in options:
        values.append(option["value"])
    return values