
import os
import json
import time
import threading
from datetime import datetime
from dotenv import load_dotenv

from login import get_token, get_last_faxes
from dumpers import download_pdf

from fileshare import (
    authenticate as sf_authenticate,
    get_today_folder
)
from processing import copy_and_rename_pdf

load_dotenv()

def save_last_fax_id(fax_id, file_path="last_fax_id.json"):
    try:
        with open(file_path, "w") as f:
            json.dump({"last_fax_id": fax_id}, f)
    except Exception as e:
        print(f"Error saving last fax ID: {e}")

def load_last_fax_id(file_path="last_fax_id.json"):
    try:
        if os.path.exists(file_path):
            return json.load(open(file_path)).get("last_fax_id")
        return None
    except Exception as e:
        print(f"Error loading last fax ID: {e}")
        return None

def main(interval: int):
    fax_token = None
    current_fax_id = load_last_fax_id() or None
    new_faxes_set = set()

    while True:
        date = datetime.now().strftime("%m-%d-%Y")

        # fetch/update fax_token & last_faxes
        resp_faxes = get_last_faxes(token=fax_token)
        if not fax_token or resp_faxes is None or resp_faxes.status_code in (401,403):
            fax_token = get_token(
                username=os.getenv("USERNAME_ENV"),
                password=os.getenv("PASSWORD_ENV")
            )
            resp_faxes = get_last_faxes(token=fax_token)

        if not resp_faxes or resp_faxes.status_code != 200:
            print("Error fetching faxes, status:", getattr(resp_faxes, "status_code", None))
            time.sleep(interval)
            continue

        # Authenticate to ShareFile once
        sf_token = sf_authenticate(
            hostname = os.getenv("HOSTNAME"),
            client_id = "pF4cbpOFj7wTmvbnmLqPM3Jmi6VY0tHU",
            client_secret = "vTWymgKTgp7hU0XzfYz5OQihPMRaD34Mf08jYBIGlkZOCdHS",
            username = os.getenv("USERNAME"),
            password = os.getenv("PASSWORD"),
        )
        if not sf_token:
            raise RuntimeError("Failed to authenticate to ShareFile")

        data = resp_faxes.json().get("rows", [])
        # collect new IDs
        for fax in data:
            fid = fax.get("id")
            if not fid: continue
            if fid == current_fax_id:
                break
            new_faxes_set.add(fid)

        # update current_fax_id to the very newest
        if new_faxes_set:
            current_fax_id = data[0]["id"]
            save_last_fax_id(current_fax_id)

        # ensure today’s ShareFile folder exists
        try:
            date_folder_id = get_today_folder(sf_token, f'{date}')
        except Exception as e:
            print("Error accessing/creating date folder:", e)
            time.sleep(interval)
            continue

        # process each new fax
        for fax_id in list(new_faxes_set):
            try:
                pdf_url = f"{os.getenv('URL_REQUEST')}/{fax_id}"
                pdf_resp = download_pdf(pdf_url=pdf_url, token=fax_token, location=os.getenv("LOCATION_ID"))
                if pdf_resp.status_code != 200:
                    print(f"Download failed for {fax_id}: {pdf_resp.status_code}")
                    new_faxes_set.remove(fax_id)
                    continue

                # write raw PDF locally
                local_dir  = os.path.join(os.getenv("LOCAL_DUMP"), date)
                os.makedirs(local_dir, exist_ok=True)
                raw_path   = os.path.join(local_dir, f"pdf-{fax_id}.pdf")
                with open(raw_path, "wb") as f:
                    f.write(pdf_resp.content)

                # process & upload to ShareFile~~
                copy_and_rename_pdf(
                    src_path = raw_path,
                    poppler_path = os.getenv("POPPLER_LOCATION"),
                    file_name = fax_id,
                    pytesseract_path = os.getenv("TESSERACT_CMD"),
                    date_folder_id = date_folder_id,
                    sf_token = sf_token
                )
                print(f"Processed & uploaded fax {fax_id}")

                new_faxes_set.remove(fax_id)
            except Exception as e:
                print(f"Error handling fax {fax_id}:", e)
                continue

        time.sleep(interval)

# ========== Calling the main function ============
# ========== VERSION 0.4.0 ===========
if __name__ == "__main__":
    listener_thread = threading.Thread(target=main, args=(10,))
    listener_thread.daemon = True
    listener_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program stopped")