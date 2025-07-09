import os
from nlp import analyze_and_extract
from fileshare import ensure_folder, upload_file

def copy_and_rename_pdf(
    src_path: str,
    poppler_path: str,
    file_name: str,
    pytesseract_path: str,
    date_folder_id: str,
    sf_token: dict
):
    """
    1) OCR + entity extraction via analyze_and_extract
    2) Determine letter_type folder name (lt)
    3) Build new remote filename
    4) ensure_folder(sf_token, date_folder_id, lt)
    5) upload_file(...) into that lt-folder under ShareFile
    6) delete local src_path
    """
    result = analyze_and_extract(
        file_path=src_path,
        poppler_path=poppler_path,
        file=file_name,
        pytesseract_path=pytesseract_path
    )

    lt = (result.get("letter_type") or "Unknown").replace(" ", "-")

    if lt == "Other":
        new_name = f"fax_{file_name}.pdf"
    else:
        ents = result.get("extracted_entities") or []
        name = (ents[0] or "Unknown").replace(" ", "-")
        dob  = (ents[1] or "Unknown").replace(" ", "-")
        drug = (ents[2] or "Unknown").replace(" ", "-")
        new_name = f"{lt}_{name}_{dob}_{drug}.pdf"

    lt_folder_id = ensure_folder(sf_token, date_folder_id, lt)

    upload_file(sf_token, lt_folder_id, src_path, remote_name=new_name)

    os.remove(src_path)

    return result
