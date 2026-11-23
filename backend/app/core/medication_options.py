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


def get_option_values(options):
    # Returns only the "value" of each option, for example ["pill", "injection"]
    values = []
    for option in options:
        values.append(option["value"])
    return values