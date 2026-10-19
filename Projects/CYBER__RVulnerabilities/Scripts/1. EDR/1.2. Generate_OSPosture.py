#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import requests
import datetime
import pandas as pd
from falconpy import OAuth2, Hosts, ZeroTrustAssessment, SpotlightVulnerabilities

# ----------------------------------------->

# Results
PROJECT = "RVulnerabilities-OSPosture"

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

# Hosts query: Windows hosts only (the OS signals and the installed patches exist only for Windows)
HOSTS_FILTER = "platform_name:'Windows'"
HOSTS_PAGE_SIZE = 5000

# Batch of hosts per Zero Trust call and page size of the installed patches call (500 answers 400)
ZTA_BATCH = 100
PATCHES_LIMIT = 100

# Zero Trust signal result -> check passed
MEETS_CRITERIA = {"yes": True, "no": False}



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

            # Define falcon requests (one token shared by the three services)
            auth = OAuth2(client_id=CLIENT_ID, client_secret=SECRET_ID)
            hosts = Hosts(auth_object=auth)
            zta = ZeroTrustAssessment(auth_object=auth)
            spotlight = SpotlightVulnerabilities(auth_object=auth)



            #################################### Part 3: Obtaining Hosts ->

            # First call proves the credentials: every Windows host id, following the offset until the total
            host_ids, offset = [], None
            while True:
                parameters = {"filter": HOSTS_FILTER, "limit": HOSTS_PAGE_SIZE}
                if offset: parameters["offset"] = offset
                response = hosts.query_devices_by_filter_scroll(**parameters)

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                host_ids += response["body"]["resources"]
                offset = response["body"]["meta"]["pagination"]["offset"]
                if len(host_ids) >= response["body"]["meta"]["pagination"]["total"]: break

            # Identity of every host (a 404 marks ids removed in between - the rest of the answer is still used)
            devices = []
            for i in range(0, len(host_ids), HOSTS_PAGE_SIZE):
                response = hosts.get_device_details(ids=host_ids[i:i + HOSTS_PAGE_SIZE])

                if response["status_code"] not in (200, 404):
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                devices += response["body"].get("resources") or []



            #################################### Part 4: Obtaining Zero Trust Assessments ->

            # OS assessment of every host, in batches (a 404 inside the answer marks the hosts without assessment - the rest is still used)
            assessments = {}
            for i in range(0, len(host_ids), ZTA_BATCH):
                response = zta.get_assessment(ids=host_ids[i:i + ZTA_BATCH])

                if response["status_code"] not in (200, 404):
                    print(f"Zero Trust Assessment returned status code {response['status_code']}, its columns left as '-'.")
                    assessments = {}
                    break

                for assessment in response["body"].get("resources") or []:
                    assessments[assessment["aid"]] = assessment



            #################################### Part 5: Obtaining Installed Patches ->

            # Patch summary of every host, one call per host (a failed call leaves that host's patch columns as "-")
            patches, failed = {}, []
            for host_id in host_ids:
                response = spotlight.query_installed_patches_combined(filter=f"aid:'{host_id}'", limit=PATCHES_LIMIT)
                resources = response["body"].get("resources") or []

                if response["status_code"] != 200: failed.append(response["status_code"])
                elif resources: patches[host_id] = resources[0]

            if failed: print(f"Installed patches failed for {len(failed)} hosts (status {sorted(set(failed))}), their patch columns left as '-'.")



            #################################### Part 6: Extracting Fields ->

            empty = "-"
            records = []

            # Returns a UTC timestamp as a local date (%Y-%m-%d)
            def format_date(value):
                if not value: return empty
                return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(LOCAL_TZ).strftime("%Y-%m-%d")

            # Returns "Ok" when a check passes, "Attention" when it fails and "-" when it was not assessed
            def item(passed):
                return empty if passed is None else ("Ok" if passed else "Attention")

            # Every OS signal found in the assessments, generated from the data and sorted by name
            signal_names = sorted({signal["signal_name"] for assessment in assessments.values() for signal in assessment.get("assessment_items", {}).get("os_signals", [])})

            for device in devices:
                host_id = device["device_id"]
                assessment = assessments.get(host_id, {})
                patch = patches.get(host_id, {})
                signals = {signal["signal_name"]: MEETS_CRITERIA.get(signal.get("meets_criteria")) for signal in assessment.get("assessment_items", {}).get("os_signals", [])}

                record = {
                    "Host Id": host_id,
                    "Host Name": device.get("hostname", empty),
                    "Host Ip": device.get("local_ip", empty),
                    "Host Type": device.get("product_type_desc", empty),
                    "Host System": device.get("os_version", empty),
                    "Active Patches": patch.get("active_patches", empty),
                    "Pending Patches": patch.get("pending_patches", empty),
                    "Last Patch Confirmed": format_date(patch.get("last_patch_confirmed")),
                    "Last Assessment": format_date(assessment.get("modified_time")),
                    "OS Score": assessment.get("assessment", {}).get("os", empty),
                    "Item: Reboot Pending": item(not patch["reboot_required"]) if patch else empty,
                }

                for name in signal_names:
                    record[f"Item: {name}"] = item(signals.get(name))

                records.append(record)



            #################################### Part 7: Saving the information ->

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
