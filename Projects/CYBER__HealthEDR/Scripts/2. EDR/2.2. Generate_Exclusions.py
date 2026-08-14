#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import re
import requests
import datetime
import pandas as pd
from falconpy import IOAExclusions, SensorVisibilityExclusions, MLExclusions

# ----------------------------------------->

# Results
PROJECT = "HealthEDR-Exclusions"

# Getting current date in format (MM-YYYY)
current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%m-%Y")

# Getting current path for file saving
current_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_dir, f"../.env")

# Define saving directory
dir_to_save_csv = os.path.join(current_dir, f"../../Datas/{formatted_date}")

# Auto create DIR
if not os.path.exists(dir_to_save_csv):
    os.makedirs(dir_to_save_csv)



#################################### Part 1: Obtaining Authorization Token ->

# Data obtained from project file
from dotenv import load_dotenv
if os.path.exists(env_path):

    load_dotenv(env_path)

    # Get .env variables
    BASE_URL = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRET_ID = os.getenv("SECRET_ID")
    IDENTITY = "crowdstrike_sample"

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



        #################################### Part 3: Obtaining Exclusions ->

        # Init extract data
        try:

            # Define local variables
            CLIENT_ID = secret["CLIENT_ID"]
            SECRET_ID = secret["SECRET_ID"]

            empty = "-"

            # Fetch every exclusion of a type: query the ids, then pull their details
            def get_all_exclusions(service):
                api = service(client_id=CLIENT_ID, client_secret=SECRET_ID)
                ids = api.query_exclusions(limit=500)["body"]["resources"] or []
                return api.get_exclusions(ids=ids)["body"]["resources"] or [] if ids else []

            ioa_raw = get_all_exclusions(IOAExclusions)
            sve_raw = get_all_exclusions(SensorVisibilityExclusions)
            ml_raw = get_all_exclusions(MLExclusions)



            #################################### Part 4: Defining Function Fields ->

            # Collect the values from every group's assignment_rule (all quoted entries; only values are quoted, keys never are)
            def group_values(exclusion):
                values = []
                for group in exclusion.get("groups", []):
                    rule = group.get("assignment_rule", "")
                    values.extend(re.findall(r"'([^']*)'", rule))
                return ", ".join(values) if values else empty

            # Sensor Visibility exclusions
            def sve_exclusion_row(exclusion):
                return {
                    "Exception ID": exclusion.get("id", empty),
                    "Exception Value": exclusion.get("value", empty),
                    "Applied For": group_values(exclusion),
                    "Applied Globally": exclusion.get("applied_globally", False),
                    "Created Date": exclusion.get("created_on", empty),
                    "Created By": exclusion.get("created_by", empty),
                }

            # ML exclusions add the engines the exclusion applies to (excluded_from)
            def ml_exclusion_row(exclusion):
                return {
                    "Exception ID": exclusion.get("id", empty),
                    "Exception Value": exclusion.get("value", empty),
                    "Excluded From": ", ".join(exclusion.get("excluded_from", [])) or empty,
                    "Applied For": group_values(exclusion),
                    "Applied Globally": exclusion.get("applied_globally", False),
                    "Created Date": exclusion.get("created_on", empty),
                    "Created By": exclusion.get("created_by", empty),
                }

            # IOA carries a different shape (pattern + regexes) -> its own list
            def ioa_exclusion_row(exclusion):
                return {
                    "Exception ID": exclusion.get("id", empty),
                    "Exception Name": exclusion.get("name", empty),
                    "Exception Description": exclusion.get("description", empty),
                    "Exclusion Pattern": exclusion.get("pattern_name", empty),
                    "Exclusion Image": exclusion.get("ifn_regex", empty),
                    "Exclusion Commandline": exclusion.get("cl_regex", empty),
                    "Applied For": group_values(exclusion),
                    "Applied Globally": exclusion.get("applied_globally", False),
                    "Created Date": exclusion.get("created_on", empty),
                    "Created By": exclusion.get("created_by", empty),
                }

            sve_exclusions = [sve_exclusion_row(e) for e in sve_raw]
            ml_exclusions = [ml_exclusion_row(e) for e in ml_raw]
            ioa_exclusions = [ioa_exclusion_row(e) for e in ioa_raw]



            #################################### Part 5: Saving the information ->

            # Save a list of records to a CSV (adds the reference stamp columns last)
            def save_csv(records, name):
                if not records: return
                dataframe = pd.DataFrame(records).fillna(empty)

                # Reference stamp columns — always last
                dataframe["Reference Month"] = current_date.strftime("%m")
                dataframe["Reference Year"] = current_date.strftime("%Y")
                dataframe["Reference Date"] = current_date.strftime("%Y-%m-%d")

                dataframe.to_csv(os.path.join(dir_to_save_csv, f"{PROJECT}_{name}.csv"), index=False, encoding="utf-8")

            # Saving data
            save_csv(sve_exclusions, "SVE")
            save_csv(ml_exclusions, "ML")
            save_csv(ioa_exclusions, "IOA")


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
