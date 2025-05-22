from datetime import datetime
from dotenv import load_dotenv
from login import get_token, get_last_faxes
from processing import copy_and_rename_pdf
from dumpers import download_pdf
import time, os, json, threading

# ========== Globla load env =============
# will be used to pass env variables as a parameters into functions
load_dotenv()

def main(interval: int):
    # Local variables
    token = None
    current_fax_id = None
    new_faxes_set = set()

    while True:
        date = datetime.now().strftime("%m-%d-%Y")
        # Getting token and validating it
        response_last_faxes = get_last_faxes(token=token)
        if not token or response_last_faxes.status_code == 403 or response_last_faxes.status_code == 401:
            try:
                token = get_token(
                        username=os.getenv("USERNAME_ENV"),
                        password=os.getenv("PASSWORD_ENV")
                    )
            except Exception as e:
                print(f"Error getting token: {e}")
            if token:
                response_last_faxes = get_last_faxes(token=token)

        data = response_last_faxes.json()

        fax_list = data.get("faxes", [])

        # Add new fax IDs to the set until reaching current_fax_id
        new_faxes_added = False
        for fax in fax_list:
            fax_id = fax.get("id")
            if not fax_id:
                continue
            if fax_id == current_fax_id:
                break
            if fax_id not in new_faxes_set:
                new_faxes_set.add(fax_id)
                new_faxes_added = True

        # Update current_fax_id to the latest seen one
        if new_faxes_added and fax_list:
            top_fax_id = fax_list[0].get("id")
            if top_fax_id:
                current_fax_id = top_fax_id
                print(f"Updated current_fax_id to {current_fax_id}")

        # make folder for the dedicated date
        date_location = f"{os.getenv("DUMP_LOCATION")}\\{date}"
        if(not os.path.exists(date_location)):
            os.mkdir(date_location)

        # download faxes in the set
        for fax_id in list(new_faxes_set):
            pdf_url = f"{os.getenv('URL_REQUEST')}/{fax_id}"

            try:
                pdf_response = download_pdf(
                    pdf_url = pdf_url, 
                    token = token, 
                    location = os.getenv("LOCATION_ID")
                )
        
                if (pdf_response.status_code !=200):
                    print(f"Error with {fax_id}, status code: {pdf_response.status_code}")
                    new_faxes_set.remove(fax_id)
                    continue

                new_faxes_set.remove(fax_id)
                print(f"Downloaded and analyzed {fax_id}")
            except Exception as e:
                print(f"Failed to download {fax_id}: {e}")

            temp_pdf_path = os.path.join(date_location, f"pdf-{fax_id}.pdf")
            with open(temp_pdf_path, 'wb') as pdf_file:
                pdf_file.write(pdf_response.content)

            if os.path.exists(temp_pdf_path):
                result = copy_and_rename_pdf(
                    src_path=temp_pdf_path, 
                    poppler_path=os.getenv("POPPLER_LOCATION"), 
                    file_name=fax_id, 
                    dest_root=date_location, 
                    pytesseract_path=os.getenv("TESSERACT_CMD"),
                    date=date
                )

        time.sleep(interval)

# ========== Calling the main function ============
# ========== VERSION 0.3.0 ===========
if __name__ == "__main__":
    listener_thread = threading.Thread(target=main(interval=10))
    listener_thread.daemon = True
    listener_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program stopped")