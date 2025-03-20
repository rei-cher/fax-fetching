import requests, json, os
from dotenv import load_dotenv

# load env
load_dotenv()

# TODO: move path to env

def dump_json(date):
    # file path for saving extracted faxes
    filepath = f"C:\\Users\\OFFICE\\Documents\\dump\\dump-{date}.json"
    # print(date)
    # print(os.path.isdir(filepath))

    if (os.path.exists(filepath)):
        print(f"Json for the {date} already exists")
    else:
    # getting and saving faxes info into json 
        try:
            response = requests.get(f"{os.getenv('URL_REQUEST')}?recipient=&sender=&start={date}&end={date}", headers={
                'Authorization' : f'Bearer {os.getenv("AUTHORIZATION")}',
                'Location-id': os.getenv("LOCATION_ID"),
            })

            if (response.ok):
                # new_json = os.open(f'{filepath}\\dump.json', 'x')
                with open(filepath, 'w') as f:
                    json.dump(response.json(), f, indent=4)
                print(f"Data successfully written to {filepath}")
            else:
                print(response.text)
        except Exception as e:
            print(f"Error getting response: {e}")