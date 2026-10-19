#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import requests
import datetime
import pandas as pd
from falconpy import OAuth2, RealTimeResponseAudit, Hosts

# ----------------------------------------->

# Results
PROJECT = "FalconAudits-RTRSessions"

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

# Local time of the reports (UTC-3) and the previous calendar month window, bounds at 00:00 local time
LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=-3))
first_day_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
first_day_prev_month = (first_day_month - datetime.timedelta(days=1)).replace(day=1)

# Returns a local datetime written in UTC for an FQL filter
def to_utc(value):
    return value.replace(tzinfo=LOCAL_TZ).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# RTR sessions created inside the previous calendar month, one window per day
# (over the whole month the API cursor skips about 1% of the sessions; per day it returns every one)
DAY_WINDOWS = []
day = first_day_prev_month
while day < first_day_month:
    DAY_WINDOWS.append((day.strftime("%Y-%m-%d"), f"created_at:>='{to_utc(day)}'+created_at:<'{to_utc(day + datetime.timedelta(days=1))}'"))
    day += datetime.timedelta(days=1)

# RTR audit page size (the API maximum) and hosts per lookup
PAGE_SIZE = 1000
LOOKUP_SIZE = 100

# RTR session origin (the "source:" part of the origin field) -> readable text
ORIGINS = {"api": "API", "card": "Console - Host Card", "hosts": "Console - Hosts", "activity": "Console - Activity"}



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

            # Define falcon request (one token shared by both services)
            auth = OAuth2(client_id=CLIENT_ID, client_secret=SECRET_ID)
            falcon_rtr = RealTimeResponseAudit(auth_object=auth)
            falcon_hosts = Hosts(auth_object=auth)



            #################################### Part 3: Obtaining RTR Sessions ->

            # First call proves the credentials; each day follows the cursor the API returns in "next"
            sessions, total = [], 0
            for day_label, fql in DAY_WINDOWS:
                read, cursor = 0, None
                while True:
                    parameters = {"filter": fql, "limit": PAGE_SIZE, "with_command_info": True}
                    if cursor: parameters["offset"] = cursor
                    response = falcon_rtr.audit_sessions(**parameters)

                    if response["status_code"] != 200:
                        print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                        raise SystemExit(1)

                    page = response["body"].get("resources") or []
                    sessions += page
                    read += len(page)
                    day_total = response["body"]["meta"]["pagination"].get("total", 0)
                    cursor = response["body"]["meta"]["pagination"].get("next")
                    if not page or not cursor: break

                total += day_total
                if read != day_total: print(f"RTR audit returned {read} of {day_total} sessions for {day_label}.")



            #################################### Part 4: Obtaining Hosts ->

            empty = "-"

            # Host type of every host with a session (a lookup with ids that no longer exist answers 404 and still returns the rest)
            host_types = {}
            device_ids = list({session["device_id"] for session in sessions})
            for start in range(0, len(device_ids), LOOKUP_SIZE):
                response = falcon_hosts.get_device_details(ids=device_ids[start:start + LOOKUP_SIZE])
                for host in response["body"].get("resources") or []:
                    host_types[host["device_id"]] = host.get("product_type_desc") or empty



            #################################### Part 5: Extracting Fields ->

            # Returns a UTC timestamp as a local datetime, or None when there is none
            def local_time(value):
                if not value: return None
                return datetime.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(LOCAL_TZ)

            # Returns the origin of a session as readable text ("source:api,deviceId:..." -> "API")
            def origin(value):
                source = (value or "").split(",")[0].split(":")[-1]
                return ORIGINS.get(source, source.title() or empty)

            # One record per command; a session without commands is one record with "-" in the command columns
            records = []
            for session in sessions:
                created = local_time(session["created_at"])
                base = {
                    "Session Date": created.strftime("%Y-%m-%d"),
                    "Session Time": created.strftime("%H:%M:%S"),
                    "Session Id": session["id"],
                    "User": session.get("user_id") or empty,
                    "Origin": origin(session.get("origin")),
                    "Host Name": session.get("hostname") or empty,
                    "Host Id": session["device_id"],
                    "Host Type": host_types.get(session["device_id"], empty),
                    "Session Duration (s)": round(session["duration"], 1) if session.get("duration") is not None else empty,
                }
                for log in session.get("logs") or [{}]:
                    command_time = local_time(log.get("created_at"))
                    records.append({
                        **base,
                        "Command": log.get("base_command") or empty,
                        "Command Line": " ".join((log.get("command_string") or empty).split()),
                        "Command Time": command_time.strftime("%H:%M:%S") if command_time else empty,
                    })

            print(f"RTR sessions: {len(sessions)} of {total} reported by the API, {len(records)} records")



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
