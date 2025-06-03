import re
from .helper.sanitizer import sanitize_filename

def find_request_entities(text):
    """
    Based on the extracted ocr text, get the request info.
    """
    patient_key = None
    patient_name = None
    patient_dob = None

    patient_key = re.search(r"Key:\s*([A-Za-z\s\-]+)\s+Patient", text)
    patient_name = re.search(r"Last Name:\s*([A-Za-z\s\-]+)\s+DOB", text)
    patient_dob = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text)

    return sanitize_filename(patient_key), sanitize_filename(patient_name), sanitize_filename(patient_dob)