import shutil, os, json
from nlp import analyze_and_extract

# file_name is fax_id
def copy_and_rename_pdf(
        src_path: str, 
        poppler_path: str, 
        dest_root: str, 
        file_name: str, 
        pytesseract_path: str, 
        date: str
    ):
    """
    Copy the PDF at src_path into a subfolder of dest_root named for its letter_type,
    and rename it to include letter_type, patient_name, dob, and drug,
    replacing any None with 'Unknown'. If file already exists in the folder (ex: with 'Unknown', then add to the name a fax_id - file_name).
    """

    file_result = analyze_and_extract(
        file_path=src_path, 
        poppler_path=poppler_path, 
        file=file_name, 
        pytesseract_path = pytesseract_path
    )

    # pull out and normalize each component, defaulting to 'Unknown'
    lt = (file_result.get("letter_type") or "Unknown").replace(" ", "-")
    ins = (file_result.get("insurance") or "Unknown").replace(" ", "-")

    # check if the letter type is 'Other'
    # if so, then move to the sharable folder creating the date folder
    # name as fax_{fax_id}.pdf

    if lt == "Other":
        dest_dir = os.path.join("S:\\Folders\\FAXES", f"{date}")
        os.makedirs(dest_dir, exist_ok=True)
        file_name = f"fax_{file_name}.pdf"
        dest_path = os.path.join(dest_dir, file_name)
    
    else:
        # unpack extracted_entities tuple if present
        name, dob, drug = ("Unknown", "Unknown", "Unknown")
        if file_result.get("extracted_entities"):
            ent = file_result["extracted_entities"]
            name = (ent[0] or "Unknown").replace(" ", "-")
            dob  = (ent[1] or "Unknown").replace(" ", "-")
            drug = (ent[2] or "Unknown").replace(" ", "-")

        # print(f"[Process file] Patient info\nName: {name}\nDOB: {dob}\nDrug: {drug}")
        # build destination directory and filename
        dest_dir = os.path.join(dest_root, lt)
        os.makedirs(dest_dir, exist_ok=True)
        new_fname = f"{lt}_{name}_{dob}_{drug}.pdf"
        dest_path = os.path.join(dest_dir, new_fname)

        # check if the file already exists in the directory
        if os.path.exists(dest_path):
            new_fname = f"{lt}_{name}_{dob}_{drug}_{file_name}.pdf"
            dest_path = os.path.join(dest_dir, new_fname)
    
    # copy
    shutil.move(src_path, dest_path)
    # os.remove(src_path)

    return file_result