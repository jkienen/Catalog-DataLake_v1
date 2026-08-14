#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import sys
import json
import requests
import datetime
import pandas as pd

# ----------------------------------------->

# Results
PROJECT = "GVulnerabilities-Assets"
PROJECT_CHILD_01 = "(Unwatched)_GVulnerabilities-Assets"

# Getting current date in format (MM-YYYY)
current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%m-%Y")

# Getting current path for file saving
current_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_dir, f"../.env")

# Define saving directories
dir_to_save_csv = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT}_{formatted_date}.csv")
dir_to_save_json = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT}_{formatted_date}.json")

# Define unwatched assets
dir_to_save_csv_unwatched = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/Unwatched/{PROJECT_CHILD_01}_{formatted_date}.csv")
dir_to_save_json_unwatched = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/Unwatched/{PROJECT_CHILD_01}_{formatted_date}.json")

# Define auto create DIR
parent_directory = os.path.dirname(dir_to_save_csv_unwatched)
if not os.path.exists(parent_directory):
    os.makedirs(parent_directory)

# Check if comparison files exist, if so, they will be read
dir_entry = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/vcenter-assets_{formatted_date}.json")
if os.path.exists(dir_entry):
    with open(dir_entry, encoding="utf-8") as file: data_vcenter = json.load(file)
else: print("Pending files!"); sys.exit(1)



#################################### Part 1: Obtaining Authorization Token ->

# Data obtained from project file
from dotenv import load_dotenv
if os.path.exists(env_path):

    load_dotenv(env_path)

    # Get .env variables
    BASE_URL = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRET_ID = os.getenv("SECRET_ID")
    IDENTITY = "tenable_sample"
    
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

        secret = {}
        secrets = requests.get(url, headers=headers).json()["application"]["secrets"]
        for i in secrets:
            if i["identity"] == IDENTITY: secret = i["data"][0]
 
        

        #################################### Part 3: Obtaining Tenable Assets ->
   
        # Init extract data
        try:
            
            # Define local variables
            CLIENT_ID = secret["CLIENT_ID"]
            SECRET_ID = secret["SECRET_ID"]

            # Authentication with pyTenable
            from tenable.io import TenableIO
            tio = TenableIO(CLIENT_ID, SECRET_ID)

            # Performs the query filtering
            assets = tio.exports.assets(
                sources=["NESSUS_AGENT", "NESSUS_SCAN"]
            )

            hosts_tenable = []

            for asset in assets:
                hosts_tenable.append(asset)


            
            #################################### Part 4: Data Processing ->

            hosts = []
            empty = "-"

            # Function for date normalization
            def format_date(date):
                if date is not empty:
                    date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    date = date.strftime("%Y-%m-%d")
                return date

            # Perform data standardization
            for i in hosts_tenable:

                # Asset fields
                server_id = i.get("id", empty)
                server_name = (i.get("agent_names") or [empty])[0]
                mac_address = list({
                    mac
                    for iface in i.get("network_interfaces", [])
                    for mac in iface.get("mac_addresses", [])
                }) or i.get("mac_addresses") or [empty]

                # Classification fields
                department = next((d["value"] for d in i.get("tags", []) if d["key"] == "SETOR"), empty)
                server_type = next((d["value"] for d in i.get("tags", []) if d["key"] == "TYPE"), empty)

                # Rating fields
                score_aes = i.get("ratings", {}).get("aes", {}).get("score") or 0
                score_acr = i.get("ratings", {}).get("acr", {}).get("score") or 0

                # Activity fields
                last_seen = format_date(i.get("last_seen", empty))
                has_agent = i.get("has_agent", False)
                softwares = [s.split(":")[3] for s in i.get("installed_software", [])] or empty

                hosts.append({
                    "Department": department,
                    "Server Id": server_id,
                    "Server VM": empty,
                    "Server Name": server_name,
                    "Server Type": server_type,
                    "Score ACR": score_acr,
                    "Score AES": score_aes,
                    "Vulns Critical": empty,
                    "Vulns High": empty,
                    "Vulns Medium": empty,
                    "Vulns Low": empty,
                    "Vulns Total": empty,
                    "Mac Address": mac_address,
                    "Last Seen": last_seen,
                    "Last Department": empty,
                    "Department Changed": False,
                    "Server Has Agent?": has_agent,
                    "Server Installed Softwares": softwares,
                    "Reference Month": datetime.datetime.now().strftime("%m"),
                    "Reference Year": datetime.datetime.now().strftime("%Y"),
                    "Reference Date": datetime.datetime.now().strftime("%Y-%m-%d")
                })


            
            #################################### Part 5: Departments Updating ->

            # Build a lookup: mac_address -> vcenter record
            vcenter_by_mac = {}
            for v in data_vcenter:
                for mac in v.get("Mac Address", []):
                    if mac != "-":
                        vcenter_by_mac[mac.lower()] = v

            unmatched_hosts = []

            for i in hosts:
                macs = i.get("Mac Address", [])
                vcenter = next((vcenter_by_mac[m.lower()] for m in macs if m.lower() in vcenter_by_mac), None)

                if vcenter:
                    old_dept = i["Department"]
                    new_dept = vcenter.get("Setor", old_dept)
                    i["Last Department"] = old_dept if old_dept != new_dept else empty
                    i["Department Changed"] = old_dept != new_dept
                    i["Department"] = new_dept
                    i["Server VM"] = vcenter.get("Asset VM")
                else: unmatched_hosts.append(i)

            assets = [i for i in hosts if i not in unmatched_hosts]

            # --------------------------------- Part 5.1: Saving to Other Audit: Unwatched Assets ->

            # Create Data Frames
            df_unmatched = pd.DataFrame(unmatched_hosts)

            # Data Storing
            df_unmatched.to_csv(dir_to_save_csv_unwatched, index=False, encoding="utf-8")
            df_unmatched.to_json(dir_to_save_json_unwatched, orient="records")

            # print(f"\nTotal: {len(hosts)} | Matched: {len(hosts) - len(unmatched_hosts)} | Unmatched: {len(unmatched_hosts)}")

            # --------------------------------- ->

            

            #################################### Part 6: Data Saving ->

            # Create Data Frames 
            df = pd.DataFrame(assets)

            # Data Storing
            df.to_csv(dir_to_save_csv, index=False, encoding="utf-8")
            df.to_json(dir_to_save_json, orient="records")
            

        except Exception as err: print(err)
        
    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")