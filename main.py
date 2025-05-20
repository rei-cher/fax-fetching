from datetime import datetime, timedelta
from dumpers.json_dumper import dump_json
from login.login import get_token, validate_token
from dotenv import load_dotenv
from processing.process_file import copy_and_rename_pdf
from dumpers.pdf_dumper import download_pdf
import time, os, json

# ========== Globla load env =============
# will be used to pass env variables as a parameters into functions
load_dotenv()

def main(date=None):
    all_results = []
    # Local variables
    date = (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y")
    faxurl = f"{os.getenv("URL_REQUEST")}?recipient=&sender=&start={date}&end={date}"

    # Getting token and validating it
    try:
        token = get_token(
                username=os.getenv("USERNAME_ENV"),
                password=os.getenv("PASSWORD_ENV")
            )
        
        # print("\n\n", token, "\n\n")
        if (token):
            status = validate_token(
                    url=faxurl,
                    token=token,
                    location=os.getenv("LOCATION_ID")
                )
            if (status != 200):
                print(f"Token is not validated. Status code: {status}")
                return 0
    except Exception as e:
        print(f"Error: {e}")

    # make folder for the dedicated date
    date_location = f"{os.getenv("DUMP_LOCATION")}\\{date}"
    if(not os.path.exists(date_location)):
        os.mkdir(date_location)

    # Get json file with faxes and their ids
    json_path = dump_json(
        url=faxurl,
        token=token,
        location=os.getenv("LOCATION_ID"),
        path=date_location,
        date=date
    )

    with open (json_path, "r") as json_file:
        data = json.load(json_file)
        count = 0
        failed = 0
        for i, item in enumerate(data["data"]):
            fax_id = item.get("ID")
            pdf_url = f"{os.getenv('URL_REQUEST')}/{fax_id}"

            pdf_response = download_pdf(
                pdf_url = pdf_url, 
                token = token, 
                location = os.getenv("LOCATION_ID")
            )
        
            if (pdf_response.status_code !=200):
                print(f"Error with {fax_id}, status code: {pdf_response.status_code}")
                failed += 1
                continue

            temp_pdf_path = os.path.join(date_location, f"pdf-{fax_id}.pdf")
            with open(temp_pdf_path, 'wb') as pdf_file:
                pdf_file.write(pdf_response.content)

            if os.path.exists(temp_pdf_path):
                all_results.append(copy_and_rename_pdf(
                    src_path=temp_pdf_path, 
                    poppler_path=os.getenv("POPPLER_LOCATION"), 
                    file_name=fax_id, 
                    dest_root=date_location, 
                    pytesseract_path=os.getenv("TESSERACT_CMD"),
                    date=date
                ))

            count += 1

        with open("extract_results.json", "w") as file:
            json.dump(all_results, file, indent=4)
            
        print(f"Total: {count}\nPassed: {count-failed}\nFailed: {failed}")

# ========== Calling the main function ============
# ========== VERSION 0.2.1 ===========
if __name__ == "__main__":
    start_time = time.perf_counter()

    # for date in range(10, 12):
    #     main(date=f"05-{date}-2025")

    main()

    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print (f"Program ran in {execution_time/60:.2f} minutes")