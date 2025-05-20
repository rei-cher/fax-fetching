# ==== List of different insurances ====
insurance_types = [
    "Healthfirst",
    "Wellpoint",
    "Fidelis Care",
    "Prime Therapeutics",    # Private horizon
    "Clover Health",
    "UnitedHealthcare",    # UnitedHealthCare
    "Express Scripts",
    "WellCare",
    "Aetna",
    "Horizon",
    "CVS Caremark",
    "Anthem"
]

def determine_insurance(text):
    """
    From the extracted ocr text, matching the words with the list of pre-exist insurances.
    If there is a match, returns the name of the insurance.
    """
    return next((insurance for insurance in insurance_types if insurance.lower() in text.lower()), None)