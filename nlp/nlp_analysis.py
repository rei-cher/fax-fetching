import re, os, shutil

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
    if "approved" in text_lower or "approval" in text_lower:
        return "approval"
    if "denied" in text_lower or "denial" in text_lower:
        return "denial"
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

    name_match = re.search(r'Patient Name\s*:\s*(.+)', text, re.IGNORECASE)
    dob_match = re.search(r'DOB\s*:\s*([\d\/\-\.\s]+)', text, re.IGNORECASE)
    medication_match = re.search(r'Medication\s*:\s*(.+)', text, re.IGNORECASE)
    
    info = {
        "name": name_match.group(1).strip() if name_match else "Unknown",
        "dob": dob_match.group(1).strip() if dob_match else "Unknown",
        "medication": medication_match.group(1).strip() if medication_match else "Unknown"
    }
    
    return info

def rename_and_move_pdf(pdf_path: str, letter_type: str, patient_info: dict, base_path: str) -> str:
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
    new_filename = f"{letter_type.capitalize()}_{cleaned_name}_{cleaned_dob}_{cleaned_med}.pdf"
    new_pdf_path = os.path.join(folder, new_filename)

    # Move/rename the file
    shutil.move(pdf_path, new_pdf_path)

    return new_pdf_path