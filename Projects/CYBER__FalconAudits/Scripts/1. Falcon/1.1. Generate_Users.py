#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import requests
import datetime
import pandas as pd
from falconpy import UserManagement

# ----------------------------------------->

# Results
PROJECT = "FalconAudits-Users"

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

# Local time of the reports (UTC-3)
LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=-3))

# A user without a login inside this many days is inactive
INACTIVITY_DAYS = 45

# User Management page sizes (user ids per query, users per lookup, grants per user)
PAGE_SIZE = 500
LOOKUP_SIZE = 100

# Words kept in capitals when an API enum becomes readable text
ACRONYMS = {"CID"}



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
            falcon = UserManagement(client_id=CLIENT_ID, client_secret=SECRET_ID)



            #################################### Part 3: Obtaining Users ->

            # First call proves the credentials: every user id of the tenant
            user_ids, offset = [], 0
            while True:
                response = falcon.query_users(limit=PAGE_SIZE, offset=offset)

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                page = response["body"].get("resources") or []
                user_ids += page
                offset += len(page)
                if not page or offset >= response["body"]["meta"]["pagination"]["total"]: break

            # User records (name, e-mail, status, dates)
            users = []
            for start in range(0, len(user_ids), LOOKUP_SIZE):
                users += falcon.retrieve_users(ids=user_ids[start:start + LOOKUP_SIZE])["body"].get("resources") or []

            # Role grants of every user, or None when the call fails
            grants = {}
            for user in users:
                response = falcon.get_user_grants(user_uuid=user["uuid"], limit=PAGE_SIZE)
                if response["status_code"] != 200:
                    print(f"User Management returned status code {response['status_code']} for the roles of a user.")
                    grants[user["uuid"]] = None
                else: grants[user["uuid"]] = response["body"].get("resources") or []



            #################################### Part 4: Extracting Fields ->

            empty = "-"

            # Returns a UTC timestamp as a local datetime, or None when there is none
            def local_time(value):
                if not value: return None
                return datetime.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(LOCAL_TZ)

            # Returns an API enum as readable text, keeping acronyms in capitals
            def label(value):
                if not value: return empty
                return " ".join(word if word in ACRONYMS else word.capitalize() for word in str(value).upper().split("_"))

            # Returns the distinct values of a list sorted and joined by "; ", or "-" when there is none (sorted, so one set has one spelling)
            def join(values):
                values = sorted({value for value in values if value})
                return "; ".join(values) if values else empty

            records = []
            for user in users:
                created = local_time(user.get("created_at"))
                last_login = local_time(user.get("last_login_at"))
                days = (current_date.date() - last_login.date()).days if last_login else empty
                user_grants = grants[user["uuid"]]

                records.append({
                    "User Name": " ".join(name for name in (user.get("first_name"), user.get("last_name")) if name) or empty,
                    "User Email": user.get("uid", empty),
                    "User UUID": user["uuid"],
                    "Status": label(user.get("status")),
                    "Created": created.strftime("%Y-%m-%d") if created else empty,
                    "Last Login": last_login.strftime("%Y-%m-%d") if last_login else empty,
                    "Days Since Last Login": days,
                    "Roles": join(grant.get("role_name") for grant in user_grants) if user_grants is not None else empty,
                    "Roles Total": len({grant.get("role_id") for grant in user_grants}) if user_grants is not None else empty,
                    "Grant Type": join(label(grant.get("grant_type")) for grant in user_grants) if user_grants is not None else empty,
                    "Falcon Administrator": any(grant.get("role_id") == "falconhost_admin" for grant in user_grants) if user_grants is not None else empty,
                    "Item: Activity": "Ok" if last_login and days <= INACTIVITY_DAYS else "Attention",
                })

            print(f"Users: {len(records)}")



            #################################### Part 5: Saving the information ->

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
