import re
from .helper.sanitizer import sanitize_filename

def find_denial_entitied(text, insurance):
    """
    Based on the extracted ocr text and insurnace type from determine_insurance, get the patient info.
    For each insurance there is its own regex for patient info.
    """

    patient_name = None
    patient_dob = None
    patient_drug = None

    match insurance:
        case "Fidelis Care":
            patient_name_match = re.search(r'Member:\s*([A-Za-z\s\-]+)\s+1D', text) or re.search(r'Member:\s*([A-Za-z\s\-]+)\s+ID', text)
            patient_dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Question:\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'Service:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)

        case "Aetna":
            patient_name_match = re.search(r'Re:\s*([A-Za-z\s\-]+)\s+DOB', text)
            patient_dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'request for coverage of (.+?) for you', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Horizon":
            patient_name_match = re.search(r'Dear\s+([A-Z\s\-]+):', text)
            patient_dob_match = re.search(r'Date of Birth:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'request for (.+?) services', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

            # extra case
            if not patient_name and not patient_dob:
                match = re.search(r"RE:\s*([A-Z]+\s+[A-Z]+)\s+(\d{2}/\d{2}/\d{4})", text)
                patient_drug_match = re.search(r'authorization for (.+?). If', text)
                if match:
                    patient_name = match.group(1)
                    patient_dob = match.group(2)
                if patient_drug_match:
                    patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "CVS Caremark":
            patient_name_match = re.search(r'Dear\s+([A-Z\s\-]+):', text)
            patient_drug_match = re.search(r'request for coverage of (.+?) Dear', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Prime Therapeutics":
            patient_name_match = re.search(r'regarding:\s+([A-Z\s\-]+)\sDrug', text)
            patient_dob_match = re.search(r'Requested:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Drug: (.+?) Date', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

    # print(f"[Approval analyzator] Patient info\nName: {patient_name}\nDOB: {patient_dob}\nDrug: {patient_drug}")
    return sanitize_filename(patient_name), sanitize_filename(patient_dob), sanitize_filename(patient_drug)
