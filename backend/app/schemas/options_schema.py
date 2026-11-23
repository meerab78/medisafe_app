from pydantic import BaseModel


class WizardOption(BaseModel):
    value: str | int
    label: str
    # Fixed values that the app adds to the final body when this option is chosen
    extra: dict | None = None


class WizardCondition(BaseModel):
    # Show the step only when the answer of this step matches
    step: str
    equals: str | int | None = None
    not_equals: str | int | None = None


class WizardStep(BaseModel):
    id: str
    # Where the answer goes in the final body. None means it is only used for the flow.
    field: str | None = None
    type: str
    # "main" steps come one by one, "extras" are the optional settings
    section: str
    title: str
    hint: str | None = None
    required: bool = True
    default: str | int | None = None
    options: list[WizardOption] | None = None
    show_when: WizardCondition | None = None
    # For the "times" step: how many time pickers to show
    count_from: str | None = None


class MedicationWizardResponse(BaseModel):
    version: int
    steps: list[WizardStep]