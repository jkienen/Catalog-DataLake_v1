#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import re
import requests
import datetime
import pandas as pd
from falconpy import IdentityProtection, Alerts

# ----------------------------------------->

# Results
PROJECT = "HealthIDP-Exclusions"

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

# Detection exclusions are only exposed as change events -> read the whole timeline history
HISTORY_START = "2020-01-01T00:00:00Z"

# GraphQL query: every detection exclusion change (which detection, when, by whom)
EXCLUSION_CHANGES_QUERY = """
query ($start: DateTimeInput, $after: Cursor) {
  timeline(types: [ALERT_EXCEPTION_MODIFIED], startTime: $start, first: 1000, after: $after, sortOrder: DESCENDING) {
    nodes { timestamp ... on TimelineAlertExceptionModifiedEvent { patternId systemUser { displayName } } }
    pageInfo { hasNextPage endCursor }
  }
}
""".strip()

# GraphQL query: one past alert of a detection pattern carries its title and type
DETECTION_TITLE_QUERY = """
query ($start: DateTimeInput, $pattern: Int!) {
  timeline(types: [ALERT], startTime: $start, first: 1, alertQuery: { patternIds: [$pattern] }) {
    nodes { ... on TimelineAlertEvent { alertType eventLabel } }
  }
}
""".strip()



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



        # Init extract data
        try:

            # Define local variables
            CLIENT_ID = secret["CLIENT_ID"]
            SECRET_ID = secret["SECRET_ID"]

            # Define falcon requests
            falcon = IdentityProtection(client_id=CLIENT_ID, client_secret=SECRET_ID)
            falcon_alerts = Alerts(client_id=CLIENT_ID, client_secret=SECRET_ID)



            #################################### Part 3: Obtaining Detection Exclusion Changes ->

            # Every change event, newest first, paginated by cursor
            changes, after = [], None
            while True:
                response = falcon.graphql(query=EXCLUSION_CHANGES_QUERY, variables={"start": HISTORY_START, "after": after})

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                if response["body"].get("errors"): print(f"GraphQL errors: {response['body']['errors']}"); break
                data = response["body"]["data"]["timeline"]
                changes += data.get("nodes") or []
                if not data["pageInfo"]["hasNextPage"]: break
                after = data["pageInfo"]["endCursor"]

            # Group changes by detection pattern (newest first inside each group)
            changes_by_pattern = {}
            for change in changes: changes_by_pattern.setdefault(change["patternId"], []).append(change)



            #################################### Part 4: Resolving Detection Titles ->

            empty = "-"
            detections = {}

            for pattern_id in changes_by_pattern:

                # Title and type from the Identity Protection alert history
                response = falcon.graphql(query=DETECTION_TITLE_QUERY, variables={"start": HISTORY_START, "pattern": pattern_id})
                node = next(iter(((response["body"].get("data") or {}).get("timeline") or {}).get("nodes") or []), {})

                # MITRE tactic / technique from the latest alert of this pattern (only while alerts are retained)
                response = falcon_alerts.query_alerts_v2(filter=f"product:'idp'+pattern_id:{pattern_id}", limit=1, sort="created_timestamp.desc")
                alert_ids = response["body"].get("resources") or []
                alert = (falcon_alerts.get_alerts_v2(composite_ids=alert_ids)["body"].get("resources") or [{}])[0] if alert_ids else {}

                detections[pattern_id] = {
                    "title": node.get("eventLabel") or empty,
                    "type": node.get("alertType") or empty,
                    "tactic": alert.get("tactic") or empty,
                    "technique": alert.get("technique") or empty,
                }



            #################################### Part 5: Defining Function Fields ->

            # Readable label: PassTheHashAlert -> Pass The Hash, DcSyncAlert -> DC Sync (acronyms kept)
            acronyms = {"MFA", "AD", "RPC", "DC", "IP", "ML", "SMB", "LDAP", "LDAPS", "NTLM", "SPN", "VPN", "RDP", "API"}
            def label(value, suffix=""):
                words = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", str(value)).replace("_", " ").split()
                text = " ".join(w.upper() if w.upper() in acronyms else w.capitalize() for w in words)
                return text.removesuffix(suffix).strip() if suffix else text

            # Convert GraphQL ISO datetime to local date (UTC-3)
            def format_date(value):
                if not value: return empty
                date = datetime.datetime.fromisoformat(value.replace("Z", "+00:00")) - datetime.timedelta(hours=3)
                return date.strftime("%Y-%m-%d")

            # Detection exclusions: one row per detection whose exclusions were configured / modified
            def detection_row(pattern_id, pattern_changes):
                detection = detections.get(pattern_id, {})
                last = pattern_changes[0]
                last_user = last.get("systemUser") or {}
                return {
                    "Pattern Id": pattern_id,
                    "Detection": detection.get("title", empty),
                    "Detection Type": label(detection["type"], " Alert") if detection.get("type", empty) != empty else empty,
                    "Tactic": detection.get("tactic", empty),
                    "Technique": detection.get("technique", empty),
                    "Changes": len(pattern_changes),
                    "First Change": format_date(pattern_changes[-1].get("timestamp")),
                    "Last Change": format_date(last.get("timestamp")),
                    "Last Modified By": last_user.get("displayName") or empty,
                }

            detection_exclusions = sorted((detection_row(p, c) for p, c in changes_by_pattern.items()), key=lambda r: r["Last Change"], reverse=True)



            #################################### Part 6: Saving the information ->

            # Save a list of records to a CSV (adds the reference stamp columns last)
            def save_csv(records, project):
                if not records: return
                dataframe = pd.DataFrame(records).fillna(empty)

                # Reference stamp columns — always last
                dataframe["Reference Month"] = current_date.strftime("%m")
                dataframe["Reference Year"] = current_date.strftime("%Y")
                dataframe["Reference Date"] = current_date.strftime("%Y-%m-%d")

                dataframe.to_csv(os.path.join(dir_to_save_csv, f"{project}.csv"), index=False, encoding="utf-8-sig")

            # Saving data
            save_csv(detection_exclusions, PROJECT)


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
