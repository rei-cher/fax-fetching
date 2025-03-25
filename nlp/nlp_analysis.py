import re, os, shutil, string

approval_patterns = [
    r"\byour request has been approved\b",
    r"\bcoverage is approved\b",
    r"\bthe prior authorization is approved\b",
    r"\bwe have approved\b",
    r"\bdrug has been approved\b",
    r"\bhas been approved\b",
]

fake_aproval_patterns = [
    r"\brequest for approval\b",
    r"\bpending approval\b",
    r"\bsubmit for approval\b",
    r"\bcomplete a pa for approval\b",
]

denial_patterns = [
    r"\byour request has been denied\b",
    r"\bthe prior authorization is denied\b",
    r"\bwe have denied\b",
]

# name_patterns = [
#     r"dear\s*[:, ]?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", # regex for names after 'dear'
#     r"patient(?:\s*name)?\s*[:, ]?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", # regex for names after 'patient'
#     r"last\s*name\s*[:, ]?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", # regex for names after 'last name'
#     r"member\s*name\s*[:, ]?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", # regex for names after 'last name'
#     r"member\s*[:, ]?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", # regex for names after 'last name'
#     r"name\s*[:, ]?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})", # regex for names after 'last name'
# ]

def determine_letter_type(text: str):
    """
    Determine if the extracted text is from an approval or denial letter

    The function checks for the keywords such as 'approval' or 'approved'
    and 'denial' or 'denied'. If none are found, it return 'unknown'

    Args:
        text (str): the full text extracted from the pdf

    Return:
        str: 'approval', 'denial' or 'unknown'
    """

    text_lower = text.lower() # all text to lowercase

    # check for approval patterns
    for pattern in approval_patterns:
        if re.search(pattern, text_lower):
            # check if there are 'fake' for patterns
            # for fake_pattern in fake_aproval_patterns:
            #     if re.search(fake_pattern, text_lower):
            #         return "unknown"
            return "approval"
            
    # check for denial patterns
    for pattern in denial_patterns:
        if re.search(pattern, text_lower):
            return "denial"
        
    # default 'unknown'
    return "unknown"

def extract_patient(text: str):
    """
    Extract patient name, dob, and medication details from the text

    Uses regex to extract info assuming:
        Patient Name: name of the patient
        DOB: patient dob
        medication: medication name

    (?) For medication: maybe better also to have a list and run it through text to find if matches
    
    Args:
        text (str): the extracted text from the pdf
    
    Returns:
        dict: A dictionary with keys 'name', 'dob', and 'medication'
    """

    # TODO: analyze results to adjust regex 
    name_match = re.search(r'(Dear | Member)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)', text)
    # name = "Unknown"
    # for pattern in name_patterns:
    #     match = re.search(pattern, text, re.IGNORECASE)
    #     if match:
    #         name = match.group(1).strip()
    #         break
    dob_match = re.search(r'\bDOB\b\s*:\s*([\d\/\-\.\s]+)', text, re.IGNORECASE)

    medication_match = re.search(r'\bMedication\b\s*:\s*(.+)', text, re.IGNORECASE)
    
    info = {
        "name": name_match.group(1).strip() if name_match else "Unknown",
        # "name": name,
        "dob": dob_match.group(1).strip() if dob_match else "Unknown",
        "medication": medication_match.group(1).strip() if medication_match else "Unknown"
    }
    
    return info

def rename_and_move_pdf(pdf_path: str, letter_type: str, patient_info: dict, base_path: str, id) -> str:
    """
    Renames the pdf based on letter type, patient name, dob, and medication
    Then moves it to the appropriate folder ('approvals', 'denials', or 'unknown')
    """

    # Helper to sanitize filenames
    def clean_str(s):
        return re.sub(r'\W+', '_', s).strip('_')

    # Clean up patient info for filename
    cleaned_name = clean_str(patient_info.get("name", "Unknown"))
    cleaned_dob = clean_str(patient_info.get("dob", "Unknown"))
    cleaned_med = clean_str(patient_info.get("medication", "Unknown"))

    # Decide on folder
    if letter_type == "approval":
        folder = os.path.join(base_path, "approvals")
    elif letter_type == "denial":
        folder = os.path.join(base_path, "denials")
    else:
        folder = os.path.join(base_path, "unknown")

    # Make sure folder exists
    os.makedirs(folder, exist_ok=True)

    # Create new filename
    new_filename = f"{letter_type.capitalize()}_{cleaned_name}_{cleaned_dob}_{cleaned_med}_{id}.pdf"
    new_pdf_path = os.path.join(folder, new_filename)

    # Move/rename the file
    shutil.move(pdf_path, new_pdf_path)

    return new_pdf_path