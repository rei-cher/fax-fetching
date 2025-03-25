from datetime import datetime, timedelta
from dumpers.text_dumper import text_extracting
from dumpers.json_dumper import dump_json
from login.scrapper import extract_token
from login.tokenValidator import validate_token
from dotenv import load_dotenv
import time, os

# ========== Globla load env =============
# will be used to pass env variables as a parameters into functions
load_dotenv()

def main():
    # Local variables
    date = (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y")
    # date = "03-17-2025"
    faxurl = f"{os.getenv("URL_REQUEST")}?recipient=&sender=&start={date}&end={date}"

    # Getting token and validating it
    try:
        token = extract_token(
                username=os.getenv("USERNAME_ENV"),
                password=os.getenv("PASSWORD_ENV"),
                url=os.getenv("URL_LOGIN")
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

    start_time = time.perf_counter()

    # Get json file with faxes and their ids
    dump_json(
        url=faxurl,
        token=token,
        location=os.getenv("LOCATION_ID"),
        path=date_location,
        date=date
    )

    text_extracting(
        url=os.getenv("URL_REQUEST"),
        token=token,
        location=os.getenv("LOCATION_ID"),
        path=date_location,
        date=date,
        poppler_path=os.getenv("POPPLER_LOCATION")
    )

    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print (f"Program ran in {execution_time/60:.2f} minutes")



# ========== Calling the main function ============
main()