import requests, json, os

# TODO: move path to env

def dump_json(url, token, location, path, date):
    # file path for saving extracted faxes
    filepath = f"{path}\\dump-{date}.json"
    # print(date)
    # print(os.path.isdir(filepath))

    if (os.path.exists(filepath)):
        print(f"Json for the {date} already exists")
    else:
    # getting and saving faxes info into json 
        try:
            response = requests.get(url, headers={
                'Authorization' : f'Bearer {token}',
                'Location-id': location,
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