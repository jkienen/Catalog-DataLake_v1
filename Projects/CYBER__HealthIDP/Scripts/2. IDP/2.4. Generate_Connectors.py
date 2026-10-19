#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import re
import requests
import datetime
import pandas as pd
from falconpy import IdentityProtection

# ----------------------------------------->

# Results
PROJECT = "HealthIDP-Connectors"

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

# Connectors are only exposed as timeline events -> read the whole history
HISTORY_START = "2020-01-01T00:00:00Z"

# Failure events carry the technical connector type; configuration events carry the connector name
FAILURE_TYPE_TO_CONNECTOR = {
    "AZURE": "Entra",
    "OIDC": "Microsoft MFA (OIDC)",
}

# GraphQL query: connector configuration changes and failures, oldest first
CONNECTORS_QUERY = """
query ($start: DateTimeInput, $after: Cursor) {
  timeline(types: [CONNECTOR_CONFIGURATION_ADDED, CONNECTOR_CONFIGURATION_MODIFIED, CONNECTOR_CONFIGURATION_DELETED, CONNECTOR_FAILURE],
           startTime: $start, first: 1000, after: $after, sortOrder: ASCENDING) {
    nodes {
      eventType timestamp
      ... on TimelineConnectorConfigurationEvent { type category systemUser { displayName } }
      ... on TimelineConnectorFailureEvent { connectorType connectorStatus errorDetails { message } state { resolved dismissed lastUpdateTime } }
    }
    pageInfo { hasNextPage endCursor }
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

            # Define falcon request
            falcon = IdentityProtection(client_id=CLIENT_ID, client_secret=SECRET_ID)



            #################################### Part 3: Obtaining Connector Events ->

            # Every configuration / failure event, oldest first, paginated by cursor
            events, after = [], None
            while True:
                response = falcon.graphql(query=CONNECTORS_QUERY, variables={"start": HISTORY_START, "after": after})

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                if response["body"].get("errors"): print(f"GraphQL errors: {response['body']['errors']}"); break
                data = response["body"]["data"]["timeline"]
                events += data.get("nodes") or []
                if not data["pageInfo"]["hasNextPage"]: break
                after = data["pageInfo"]["endCursor"]



            #################################### Part 4: Rebuilding Current Connectors ->

            empty = "-"

            # Replay configuration events: a connector exists while its last ADDED is newer than its last DELETED
            connectors = {}
            for event in events:
                if not event["eventType"].startswith("CONNECTOR_CONFIGURATION"): continue

                name = event.get("type") or empty
                connector = connectors.setdefault(name, {"category": event.get("category") or empty, "active": False})
                action = event["eventType"].replace("CONNECTOR_CONFIGURATION_", "")

                if action == "ADDED": connector.update(active=True, added=event["timestamp"])
                if action == "DELETED": connector.update(active=False)
                connector.update(modified=event["timestamp"], modified_by=(event.get("systemUser") or {}).get("displayName") or empty)

            current = {name: c for name, c in connectors.items() if c["active"]}

            # Failures grouped by connector name (unmapped technical types keep their own name)
            failures = {}
            for event in events:
                if event["eventType"] != "CONNECTOR_FAILURE": continue
                name = FAILURE_TYPE_TO_CONNECTOR.get(event.get("connectorType"), event.get("connectorType") or empty)
                failures.setdefault(name, []).append(event)

            # An open error (not resolved, not dismissed) for a connector that is not in the current list still gets its own row
            for name, connector_failures in failures.items():
                if name not in current and any(not f["state"]["resolved"] and not f["state"]["dismissed"] for f in connector_failures):
                    current[name] = {"category": empty}



            #################################### Part 5: Defining Function Fields ->

            # Readable label: AUTHENTICATION_ERROR -> Authentication Error
            def label(value): return " ".join(w.capitalize() for w in str(value).replace("_", " ").split())

            # Categories already come readable ("Cloud MFA (protocol based)"), except the IDaaS code
            def category_label(value): return "IDaaS" if value == "IDAAS" else value

            # Convert GraphQL ISO datetime to local date (UTC-3)
            def format_date(value):
                if not value: return empty
                date = datetime.datetime.fromisoformat(value.replace("Z", "+00:00")) - datetime.timedelta(hours=3)
                return date.strftime("%Y-%m-%d")

            # Keep the meaningful part of the raw error (Azure AADSTS message when present), without trace ids
            def clean_message(message):
                if not message: return empty
                aadsts = re.search(r"AADSTS\d+:.*?(?=\s+Trace ID:|$)", message)
                text = aadsts.group(0) if aadsts else message.split("Exception: ")[-1]
                return text.strip()[:300]

            # Failures opened in the last 30 days (an ongoing error keeps its original open date)
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
            def recent(failure): return datetime.datetime.fromisoformat(failure["timestamp"].replace("Z", "+00:00")) >= cutoff

            # One row per current connector
            def connector_row(name, connector):
                connector_failures = failures.get(name, [])
                open_failure = next((f for f in reversed(connector_failures) if not f["state"]["resolved"] and not f["state"]["dismissed"]), None)

                # An open failure keeps being updated while the error persists -> its last update is the latest occurrence
                last_failure = max((f["state"]["lastUpdateTime"] if f is open_failure else f["timestamp"] for f in connector_failures), default=None)

                return {
                    "Connector": name,
                    "Category": category_label(connector["category"]),
                    "Status": "Error" if open_failure else "Active",
                    "Error Status": label(open_failure["connectorStatus"]) if open_failure else empty,
                    "Error Message": clean_message(open_failure["errorDetails"]["message"]) if open_failure else empty,
                    "Error Last Seen": format_date(open_failure["state"]["lastUpdateTime"]) if open_failure else empty,
                    "New Failures (30d)": sum(recent(f) for f in connector_failures),
                    "Last Failure": format_date(last_failure),
                    "Added At": format_date(connector.get("added")),
                    "Last Modified": format_date(connector.get("modified")),
                    "Last Modified By": connector.get("modified_by", empty),
                    "Item: Connector Active": "Attention" if open_failure else "Ok",
                }

            records = [connector_row(name, connector) for name, connector in current.items()]



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
            save_csv(records, PROJECT)


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
