from datetime import datetime, timedelta
from dumpers.text_dumper import text_extracting
from dumpers.json_dumper import dump_json
import time

# TODO: refresh and assign token using local storage
# For that use selenium (login/scrapper)

# TODO: before fetching faxes, validate the authorization (look for code 401)

# yesterday date format mm-dd-yyyy
date = (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y")

start_time = time.perf_counter()

dump_json(date=date)
# text_extracting(date=date)

end_time = time.perf_counter()

execution_time = end_time - start_time

print (f"Program ran in {execution_time/60} minutes")