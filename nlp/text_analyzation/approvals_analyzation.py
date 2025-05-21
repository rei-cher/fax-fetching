import re
from .helper.sanitizer import sanitize_filename

def find_approval_entities(text, insurance):
    """
    Based on the extracted ocr text and insurnace type from determine_insurance, get the patient info.
    For each insurance there is its own regex for patient info.
    """

    patient_name = None
    patient_dob = None
    patient_drug = None

    # print(f"[Find approval called] Insurance: {insurance}")

    match insurance:
        case "Healthfirst":
            patient_name_match = re.search(r'Member Name:\s*(.*?)\s+Member\b', text) or re.search(r'Dear ([A-Z ]+):', text)
            patient_drug_match = re.search(r'drug\(s\):\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'approved your ([A-Za-z0-9 %]+)\.', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Wellpoint":
            patient_info_match = re.search(r'Member:\s*\d+,\s*([A-Za-z\s]+),\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'follows:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_info_match:
                patient_name = patient_info_match.group(1).strip().replace(" ", "-")
                patient_dob = patient_info_match.group(2).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)

        case "Fidelis Care":
            patient_name_match = re.search(r'Member:\s*([A-Za-z\s\-]+)\s+ID', text) or re.search(r'Member Name:\s*([A-Za-z\s\-]+)\s+Member', text)
            patient_dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Question:\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'Service:\s*\n*\s*([A-Z][A-Z0-9]+)', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)
        
        case "Horizon":
            pattern = re.search(r'(?:has|hag)\s+(?:requested|requosted)\s+([\w\s\-]+?)\s+for\s+([A-Z\s]+?),\s*(?:ID|1D|LD|\[D)\s*#\s*\d+,\s*DOB\s*(\d{1,2}/\d{1,2}/\d{4})', text)
            if pattern:
                patient_name = pattern.group(2).replace('\n', ' ').strip().replace(" ", "-")
                patient_dob = pattern.group(3).strip().replace("/", "-")
                patient_drug = pattern.group(1).strip().split(" ")[0]
        
        case "Prime Therapeutics":
            patterns = [
                r'regarding:\s+([A-Z ]+?)\s+Drug:\s+(.+?)\s+Date of Birth:.*?(\b\d{1,2}/\d{1,2}/\d{4}\b)',
                r'Name:\s+(.+?)\s+First Name:\s+([A-Za-z\-]+)\s+Strength:.*?Last Name:\s+([A-Za-z\-]+).*?Date of Birth:\s+(\d{1,2}/\d{1,2}/\d{4})',
                r'Re:\s*([A-Z\s\-]+?)\s+Member\s*DOB:\s*(\d{1,2}/\d{1,2}/\d{4}).*?Why we are writing:\s*([A-Z0-9 .%/-]+?)\s+has been'
            ]

            for pattern in patterns:
                result = re.search(pattern, text)
                if result:
                    if pattern.startswith('regarding:'):
                        patient_name = result.group(1).strip().replace(" ", "-")
                        patient_drug = result.group(2).strip().split(" ")[0]
                        patient_dob = result.group(3).strip().replace("/", "-")

                    elif pattern.startswith('Re:'):
                        patient_name = result.group(1).strip().replace(" ", "-")
                        patient_dob = result.group(2).strip().replace("/", "-")
                        patient_drug = result.group(3).strip().split(" ")[0]

                    elif pattern.startswith('Name'):  # Last pattern (drug name first, then first/last name, then DOB)
                        first_name = result.group(2).strip()
                        last_name = result.group(3).strip()
                        patient_name = f"{first_name}-{last_name}"
                        patient_drug = result.group(1).strip().split(" ")[0]
                        patient_dob = result.group(4).strip().replace("/", "-")
        
        case "Clover Health" | "CVS Caremark":
            patient_name_match = re.search(r'Member Name:\s*([A-Za-z\s\-]+)\s+Member', text)
            patient_drug_match = re.search(r'prescription drug\(s\):\s*\n*\s*([A-Z][A-Z0-9]+)', text) or re.search(r'for coverage of (.*?)\.\s+Dear', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)
        
        case "UnitedHealthcare":
            patient_name_match = re.search(r'Member Name_ \| ([A-Za-z]+(?: [A-Za-z]+)+)', text) or re.search(r'Patient:\s*([A-Za-z\s\-]+)\s+Case', text)
            patient_dob_match = re.search(r'Member DOB (\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'Drug Name (.+?) Approval', text) or re.search(r'inform you that the (.+?) requested', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Express Scripts":
            name_patterns = [
                r'Patient:\s*([A-Za-z\s\-]+)\s+Physician',
                r'Memver name:\s*([A-Za-z\s\-]+)\s+Member',
                r'Member name:\s*([A-Za-z\s\-]+)\s+Member',
            ]
            # loop over patterns for patient name within express script insurance
            for pattern in name_patterns:
                patient_name_match = re.search(pattern, text)
                if patient_name_match:
                    patient_name = patient_name_match.group(1).strip().replace(" ", "-")
                    break
            
            patient_dob_match = re.search(r'Patient DOB: (\d{1,2}/\d{1,2}/\d{4})', text)
            patient_drug_match = re.search(r'request for your patient to obtain coverage for (.+?) under', text) or re.search(r'your request for (.+?) has', text)
            
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "WellCare":
            patient_name_match = re.search(r'Dear\s+([A-Z][a-z]+(?:[-\s][A-Z]?[a-z]+)*):', text)
            patient_drug_match = re.search(r'request from you or your doctor for (.+?)\.', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1).split(" ")[0]

        case "Aetna":
            pass

        case "Anthem":
            patient_name_match = re.search(r'Member Name:\s*(.*?)\s*Member\b', text)
            patient_dob_match = re.search(r'Member date of birth:\s*(\d{2}/\d{2}/\d{4})', text)
            patient_drug_match = re.search(r'request as follaws:\s*(.+?)\s+quantity', text)
            if patient_name_match:
                patient_name = patient_name_match.group(1).strip().replace(" ", "-")
            if patient_dob_match:
                patient_dob = patient_dob_match.group(1).replace("/", "-")
            if patient_drug_match:
                patient_drug = patient_drug_match.group(1)

    # if "-" in patient_drug:
    #     patient_drug = patient_drug.replace("-", " ")

    # print(f"[Approval analyzator] Patient info\nName: {patient_name}\nDOB: {patient_dob}\nDrug: {patient_drug}")
    return sanitize_filename(patient_name), sanitize_filename(patient_dob), sanitize_filename(patient_drug)
