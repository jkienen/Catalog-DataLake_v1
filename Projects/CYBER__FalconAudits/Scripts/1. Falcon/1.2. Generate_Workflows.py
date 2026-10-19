#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import requests
import datetime
import pandas as pd
from falconpy import Workflows

# ----------------------------------------->

# Results
PROJECT = "FalconAudits-Workflows"

# Getting current date in format (MM-YYYY)
current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%m-%Y")

# Getting current path for file saving
current_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_dir, f"../.env")

# Define saving directories
dir_to_save_csv = os.path.join(current_dir, f"../../Datas/{formatted_date}")

# Auto create DIR
if not os.path.exists(dir_to_save_csv):
    os.makedirs(dir_to_save_csv)

# Local time of the reports (UTC-3) and the previous calendar month window, bounds at 00:00 local time written in UTC
LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=-3))
first_day_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
first_day_prev_month = (first_day_month - datetime.timedelta(days=1)).replace(day=1)
start_utc = first_day_prev_month.replace(tzinfo=LOCAL_TZ).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
end_utc = first_day_month.replace(tzinfo=LOCAL_TZ).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Workflow executions started inside the previous calendar month
WINDOW = f"started_timestamp:>='{start_utc}'+started_timestamp:<'{end_utc}'"

# Workflows page size (the API maximum)
PAGE_SIZE = 100



#################################### Part 1: Obtaining Authorization Token ->

# Data obtained from project file
from dotenv import load_dotenv
if os.path.exists(env_path):

    load_dotenv(env_path)

    # Get .env variables
    BASE_URL = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRET_ID = os.getenv("SECRET_ID")
    IDENTITY = "crowdstrike_audits_sample"

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



        # Init extract data
        try:

            # Define local variables
            CLIENT_ID = secret["CLIENT_ID"]
            SECRET_ID = secret["SECRET_ID"]

            # Define falcon request
            falcon = Workflows(client_id=CLIENT_ID, client_secret=SECRET_ID)



            #################################### Part 3: Obtaining Workflows ->

            # First call proves the credentials: every workflow definition of the tenant
            definitions, offset = [], 0
            while True:
                response = falcon.search_definitions(limit=PAGE_SIZE, offset=offset)

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                page = response["body"].get("resources") or []
                definitions += page
                offset += len(page)
                if not page or offset >= response["body"]["meta"]["pagination"]["total"]: break



            #################################### Part 4: Obtaining Executions ->

            empty = "-"

            # Returns the number of executions matching a filter, or "-" when the call fails
            def count_executions(fql, workflow):
                response = falcon.search_executions(filter=fql, limit=1)
                if response["status_code"] != 200:
                    print(f"Workflows returned status code {response['status_code']} for the executions of {workflow}.")
                    return empty
                return response["body"]["meta"]["pagination"]["total"]

            # Returns the start of the most recent execution of a workflow, or None
            def last_execution(definition_id):
                response = falcon.search_executions(filter=f"definition_id:'{definition_id}'", sort="started_timestamp.desc", limit=1)
                executions = response["body"].get("resources") or []
                return executions[0].get("start_timestamp") if executions else None

            # Executions of every workflow inside the window: all of them, and the ones that succeeded
            executions = {}
            for definition in definitions:
                fql = f"definition_id:'{definition['id']}'+{WINDOW}"
                executions[definition["id"]] = {
                    "total": count_executions(fql, definition["name"]),
                    "succeeded": count_executions(f"{fql}+status:'Succeeded'", definition["name"]),
                    "last": last_execution(definition["id"]),
                }



            #################################### Part 5: Extracting Fields ->

            # Returns a UTC timestamp as a local date (%Y-%m-%d)
            def format_date(value):
                if not value: return empty
                return datetime.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(LOCAL_TZ).strftime("%Y-%m-%d")

            records = []
            for definition in definitions:
                trigger = definition.get("trigger") or {}
                runs = executions[definition["id"]]
                failed = runs["total"] - runs["succeeded"] if empty not in (runs["total"], runs["succeeded"]) else empty

                records.append({
                    "Workflow Name": definition["name"],
                    "Workflow Description": " ".join((definition.get("description") or empty).split()),
                    "Enabled": definition["enabled"],
                    "Trigger Type": trigger.get("type") or empty,
                    "Trigger Event": trigger.get("event") or empty,
                    "Version": definition.get("version", empty),
                    "Last Modified": format_date(definition.get("last_modified_timestamp")),
                    "Executions (Previous Month)": runs["total"],
                    "Failed Executions (Previous Month)": failed,
                    "Last Execution": format_date(runs["last"]),
                    "Item: Validation": "Attention" if definition.get("has_validation_errors") else "Ok",
                    "Item: Failures": empty if failed == empty else ("Attention" if failed else "Ok"),
                })

            print(f"Workflows: {len(records)} ({sum(1 for record in records if record['Enabled'])} enabled)")



            #################################### Part 6: Saving the information ->

            # Save a list of records to a CSV (adds the reference stamp columns last)
            def save_csv(records, dir, project):
                if not records: return
                dataframe = pd.DataFrame(records).fillna(empty)

                # Reference stamp columns — always last
                dataframe["Reference Month"] = current_date.strftime("%m")
                dataframe["Reference Year"] = current_date.strftime("%Y")
                dataframe["Reference Date"] = current_date.strftime("%Y-%m-%d")

                dataframe.to_csv(os.path.join(dir, f"{project}.csv"), index=False, encoding="utf-8-sig")

            # Saving data
            save_csv(records, dir_to_save_csv, PROJECT)


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
