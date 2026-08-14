#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import json
import requests
import datetime
import pandas as pd

# ----------------------------------------->

# Getting current date in format (MM-YYYY)
current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%m-%Y")

# Getting current path for file saving
current_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_dir, f"../.env")

# Define saving directories
dir_to_save_csv = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/vcenter-assets_{formatted_date}.csv")
dir_to_save_json = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/vcenter-assets_{formatted_date}.json")

# Define auto create DIR
parent_directory = os.path.dirname(dir_to_save_csv)
if not os.path.exists(parent_directory):
    os.makedirs(parent_directory)



#################################### Part 1: Obtaining Authorization Token ->

# Data obtained from project file
from dotenv import load_dotenv
if os.path.exists(env_path):

    load_dotenv(env_path)

    # Get .env variables
    BASE_URL = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRET_ID = os.getenv("SECRET_ID")
    IDENTITY = "vcenter_sample"
    DEPTS = "default-depts-sample"
    
    # If valid itens
    if BASE_URL and CLIENT_ID and SECRET_ID:

        url = f"{BASE_URL}/api/oauth2/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": SECRET_ID
        }

        headers_auth = {"Content-Type": "application/x-www-form-urlencoded"}

        response_auth = requests.post(url, data=payload, headers=headers_auth).json()
        TOKEN = response_auth["access_token"]



        #################################### Part 2: Obtaining Authorization Secrets ->

        url = f"{BASE_URL}/iso/dapp/application"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }

        secret = {}; depts = {}
        secrets = requests.get(url, headers=headers).json()["application"]["secrets"]
        for i in secrets:
            if i["identity"] == IDENTITY: secret = i["data"][0]
            if i["identity"] == DEPTS: depts = i["data"][0]
 
        

        #################################### Part 3: Obtaining VCenter Authorization Token ->

        # Init extract data
        try:
            
            # Define local variables
            AUTH_URL = secret["AUTH_URL"]
            LIST_URL = secret["LIST_URL"]
            USER_ID = secret["CLIENT_ID"]
            PASS_ID = secret["SECRET_ID"]
            DEPTS = json.loads(depts["DEPTS"].strip("'"))

            # Define payload for token request
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            payload = {
                "username": USER_ID,
                "password": PASS_ID
            }

            # Request Token
            response = requests.post(AUTH_URL, headers=headers, data=json.dumps(payload))

            # Declare variable for access 
            access_token = response.json().get("access_token")

            # Validation of status
            if response.status_code != 200:
                print("Maybe, We failed to obtain the access token:", response.status_code)



            #################################### Part 4: Obtaining VCenter Assets ->
                
            # Declare permissions
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "authorization": f"Bearer {access_token}"
            }

            # Get initial response
            data = requests.get(LIST_URL, headers=headers).json()



            #################################### Part 5: Data Processing ->

            # Define lists
            assets = []
            empty = "-"
            hosts = [item["result"] for item in data]

            for id, host in enumerate(hosts):
                setor = host["metadata"].get("setor") or empty
                tenant = host["tenant"] or empty
                namevm = host["vmName"] or empty
                mac = host["macAddress"] or empty
                template = host["is_template"] or False
                
                # ----------------------------------------->

                # Organize Departments
                if setor in DEPTS: depart = setor
                elif setor not in DEPTS and "CYBER" in tenant: depart = "CYBER"
                else: depart = "TI-INFRA"

                if not template:
                    assets.append({
                        "Asset VM": namevm, 
                        "Mac Address": mac,
                        "Setor": depart,
                    })
            


            #################################### Part 6: Data Saving ->

            # Create Data Frames 
            df = pd.DataFrame(assets)

            # Data Storing
            df.to_csv(dir_to_save_csv, index=False, encoding="utf-8")
            df.to_json(dir_to_save_json, orient="records")


        except Exception as err: print(err)
        
    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")