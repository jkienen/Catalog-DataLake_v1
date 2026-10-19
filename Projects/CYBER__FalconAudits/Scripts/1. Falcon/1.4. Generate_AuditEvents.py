#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import json
import requests
import datetime
import pandas as pd
from falconpy import OAuth2, EventStreams, UserManagement, Hosts

# ----------------------------------------->

# Results
PROJECT = "FalconAudits"

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

# Local time of the reports (UTC-3) and the previous calendar month window, bounds at 00:00 local time in epoch milliseconds
LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=-3))
first_day_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
first_day_prev_month = (first_day_month - datetime.timedelta(days=1)).replace(day=1)
start_ms = int(first_day_prev_month.replace(tzinfo=LOCAL_TZ).timestamp() * 1000)
end_ms = int(first_day_month.replace(tzinfo=LOCAL_TZ).timestamp() * 1000)

# The stream is read from the oldest event it keeps (about 34 days) and stops one day after the window closes, so late events still arrive
STOP_MS = end_ms + 24 * 60 * 60 * 1000
APP_ID = "FalconAudits"
STREAM_TIMEOUT = (10, 30)

# Hosts and users per lookup
LOOKUP_SIZE = 100
PAGE_SIZE = 500

# Access events (AuditLogV3Event action -> readable text)
LOGIN_ACTIONS = {"userAuthenticate": "Login", "twoFactorAuthenticate": "Two-Factor", "assert": "SSO", "customer_switch": "Tenant Switch"}

# Changes kept: API clients, user roles and the uninstall protection of sensor update policies (AuditLogV3Event action -> readable text)
API_CLIENT_ACTIONS = {"CreateAPIClient": "Create", "UpdateAPIClient": "Update", "DeleteAPIClients": "Delete", "ResetAPIClientSecret": "Reset Secret"}
ROLE_ACTIONS = {"grantUserRoles": "Grant", "revokeUserRoles": "Revoke"}



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

            # Define falcon request (one token shared by every service)
            auth = OAuth2(client_id=CLIENT_ID, client_secret=SECRET_ID)
            falcon_streams = EventStreams(auth_object=auth)
            falcon_users = UserManagement(auth_object=auth)
            falcon_hosts = Hosts(auth_object=auth)



            #################################### Part 3: Obtaining Audit Events ->

            # First call proves the credentials: the stream partitions of the tenant
            response = falcon_streams.list_available_streams(app_id=APP_ID, format="json")

            if response["status_code"] != 200:
                print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                raise SystemExit(1)

            # Only the events this script reports are kept: access and changes in the new audit format, uninstall tokens in the activity format
            # (the same action is written in both formats, so each one is read from a single format)
            access_events, change_events, token_events, events_read, oldest_ms = [], [], [], 0, None
            for feed in response["body"]["resources"]:
                stream_headers = {"Authorization": f"Token {feed['sessionToken']['token']}", "Accept": "application/json"}
                with requests.get(feed["dataFeedURL"] + "&offset=0", headers=stream_headers, stream=True, timeout=STREAM_TIMEOUT) as stream:
                    try:
                        for line in stream.iter_lines():
                            if not line: continue
                            event = json.loads(line)
                            events_read += 1
                            created_ms = event["metadata"]["eventCreationTime"]
                            oldest_ms = created_ms if oldest_ms is None else min(oldest_ms, created_ms)
                            if created_ms >= STOP_MS: break

                            body = event.get("event") or {}
                            event_type = event["metadata"].get("eventType")
                            if event_type == "AuditLogV3Event":
                                if body.get("Action") in LOGIN_ACTIONS: access_events.append(body)
                                elif body.get("Action") in API_CLIENT_ACTIONS or body.get("Action") in ROLE_ACTIONS: change_events.append(body)
                                elif body.get("Category") == "sensor_update_policy" and body.get("Action") == "update_policy": change_events.append(body)
                            elif event_type == "UserActivityAuditEvent" and body.get("OperationName") == "reveal_token": token_events.append(body)

                    # The stream holds the connection open once it reaches the newest event: the read timeout means it was read to the end
                    except requests.exceptions.RequestException: pass

            print(f"Event stream: {events_read} events read")

            # A stream that no longer keeps the start of the window gives a partial month: said out loud, never silently
            if oldest_ms and oldest_ms > start_ms:
                print(f"The stream keeps events only from {datetime.datetime.fromtimestamp(oldest_ms / 1000, tz=LOCAL_TZ):%Y-%m-%d}: the month is partial. Run this script in the first days of the month.")



            #################################### Part 4: Obtaining Users and Hosts ->

            empty = "-"

            # E-mail of every user of the tenant, by UUID (a role change names its target user only by UUID when the user is not in the event)
            user_ids, offset = [], 0
            while True:
                response = falcon_users.query_users(limit=PAGE_SIZE, offset=offset)
                page = response["body"].get("resources") or []
                user_ids += page
                offset += len(page)
                if not page or offset >= response["body"]["meta"]["pagination"]["total"]: break

            emails = {}
            for start in range(0, len(user_ids), LOOKUP_SIZE):
                for user in falcon_users.retrieve_users(ids=user_ids[start:start + LOOKUP_SIZE])["body"].get("resources") or []:
                    emails[user["uuid"]] = user.get("uid") or empty

            # Returns the key/value pairs of an activity audit event as a dict
            def key_values(body):
                return {pair.get("Key"): pair.get("ValueString") for pair in body.get("AuditKeyValues") or []}

            # Hosts of the uninstall tokens (a lookup with ids that no longer exist answers 404 and still returns the rest)
            hosts = {}
            device_ids = list({key_values(body).get("device_id") for body in token_events} - {None, ""})
            for start in range(0, len(device_ids), LOOKUP_SIZE):
                response = falcon_hosts.get_device_details(ids=device_ids[start:start + LOOKUP_SIZE])
                for host in response["body"].get("resources") or []:
                    hosts[host["device_id"]] = host



            #################################### Part 5: Extracting Fields ->

            # Returns an epoch timestamp in milliseconds as a local datetime
            def local_time(milliseconds):
                return datetime.datetime.fromtimestamp(milliseconds / 1000, tz=LOCAL_TZ)

            # Returns True when an epoch timestamp in milliseconds falls inside the previous calendar month
            def in_window(milliseconds):
                return milliseconds is not None and start_ms <= milliseconds < end_ms

            # Returns the result of an audit event as readable text
            def result(value):
                if str(value).lower() in ("success", "true"): return "Success"
                if str(value).lower() in ("failed", "false"): return "Failed"
                return empty

            # Returns the uninstall protection of a policy setting ('{"uninstall_protection":"MAINTENANCE_MODE"}' -> "Maintenance Mode")
            def uninstall_protection(value):
                if not value: return empty
                return json.loads(value).get("uninstall_protection", empty).replace("_", " ").title()

            # Returns a text with its whitespace collapsed, or "-" when there is none
            def text(value):
                return " ".join(str(value).split()) if value else empty

            # Returns the date and time columns of an event
            def event_time(milliseconds):
                moment = local_time(milliseconds)
                return {"Event Date": moment.strftime("%Y-%m-%d"), "Event Time": moment.strftime("%H:%M:%S")}

            # Access: one record per login, two-factor, SSO or tenant switch
            logins = []
            for body in access_events:
                if not in_window(body.get("ActionTimestamp")): continue
                extensions = body.get("Extensions") or {}
                logins.append({
                    **event_time(body["ActionTimestamp"]),
                    "User": body["ActorID"],
                    "Action": LOGIN_ACTIONS[body["Action"]],
                    "Result": result(extensions.get("success")),
                    "Source IP": body.get("ActorIP") or empty,
                    "City": body.get("GeoCity") or empty,
                    "Country": body.get("GeoCountry") or empty,
                })

            # Uninstall tokens: one record per token revealed (the activity format carries the time in seconds)
            tokens = []
            for body in token_events:
                milliseconds = body["UTCTimestamp"] * 1000
                if not in_window(milliseconds): continue
                values = key_values(body)
                host = hosts.get(values.get("device_id"), {})
                tokens.append({
                    **event_time(milliseconds),
                    "User": body.get("UserId") or empty,
                    "Host Name": host.get("hostname") or empty,
                    "Host Id": values.get("device_id") or empty,
                    "Host Platform": host.get("platform_name") or empty,
                    "Host Type": host.get("product_type_desc") or empty,
                    "Message": text(values.get("message")),
                })

            # Changes: API clients, user roles and uninstall protection
            changes = []
            for body in change_events:
                if not in_window(body.get("ActionTimestamp")): continue
                extensions = body.get("Extensions") or {}
                action = body["Action"]

                if action in API_CLIENT_ACTIONS:
                    change_type, label, target, before = "API Client", API_CLIENT_ACTIONS[action], extensions.get("name"), empty
                    after = text(extensions.get("scope(s)") or extensions.get("new_scope(s)") or extensions.get("new_name"))
                elif action in ROLE_ACTIONS:
                    change_type, label = "User Role", ROLE_ACTIONS[action]
                    target = extensions.get("target_name") or emails.get(extensions.get("target_user_uuid"), extensions.get("target_user_uuid"))
                    before, after = text(extensions.get("previous_roles")), f"{'Granted' if label == 'Grant' else 'Revoked'}: {text(extensions.get('roles'))}"
                else:
                    before = uninstall_protection(extensions.get("old_policy_settings_UninstallProtection"))
                    after = uninstall_protection(extensions.get("policy_settings_UninstallProtection"))
                    if before == after: continue
                    change_type, label, target = "Uninstall Protection", "Policy Update", extensions.get("policy_name")

                changes.append({
                    **event_time(body["ActionTimestamp"]),
                    "Change Type": change_type,
                    "Action": label,
                    "Actor": body["ActorID"],
                    "Target": target or empty,
                    "Before": before,
                    "After": after,
                    # Policy services report no result: the new audit format writes "false" for every policy event, successful or not
                    "Result": empty if change_type == "Uninstall Protection" else result(extensions.get("success")),
                    "Source IP": body.get("ActorIP") or empty,
                    "Country": body.get("GeoCountry") or empty,
                })

            print(f"Logins: {len(logins)} | Uninstall tokens: {len(tokens)} | Changes: {len(changes)}")



            #################################### Part 6: Saving the information ->

            # Save a list of records to a CSV, oldest first (adds the reference stamp columns last)
            def save_csv(records, dir, project):
                if not records: return
                dataframe = pd.DataFrame(records).fillna(empty).sort_values(["Event Date", "Event Time"])

                # Reference stamp columns — always last
                dataframe["Reference Month"] = current_date.strftime("%m")
                dataframe["Reference Year"] = current_date.strftime("%Y")
                dataframe["Reference Date"] = current_date.strftime("%Y-%m-%d")

                dataframe.to_csv(os.path.join(dir, f"{project}.csv"), index=False, encoding="utf-8-sig")

            # Saving data
            save_csv(logins, dir_to_save_csv, f"{PROJECT}-Logins")
            save_csv(tokens, dir_to_save_csv, f"{PROJECT}-UninstallTokens")
            save_csv(changes, dir_to_save_csv, f"{PROJECT}-Changes")


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
