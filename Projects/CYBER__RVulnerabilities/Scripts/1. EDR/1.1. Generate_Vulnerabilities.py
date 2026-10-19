#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import requests
import datetime
import pandas as pd
from falconpy import SpotlightVulnerabilities

# ----------------------------------------->

# Results
PROJECT = "RVulnerabilities"

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

# Spotlight queries: active vulnerabilities as a snapshot, fixed and expired inside the previous calendar month
FILTERS = {
    "Active": "status:['open','reopen']",
    "Fixed": f"status:'closed'+closed_timestamp:>='{start_utc}'+closed_timestamp:<'{end_utc}'",
    "Expired": f"status:'expired'+updated_timestamp:>='{start_utc}'+updated_timestamp:<'{end_utc}'"
}
FACETS = ["cve", "host_info", "remediation"]
PAGE_SIZE = 5000

# Spotlight exploit status -> exploit maturity
EXPLOIT_STATUS = {0: "Unproven", 30: "Available", 60: "Easily Accessible", 90: "Actively Used"}

# CVSS remediation level -> readable text
REMEDIATION_LEVEL = {"O": "Official Fix", "T": "Temporary Fix", "W": "Workaround", "U": "Unavailable"}

# Words kept in capitals when an API enum becomes readable text
ACRONYMS = {"KB", "CPE"}

# Columns whose values arrive in more than one spelling (differing only in case)
ONE_SPELLING = ["Vuln Product", "Vuln Solution", "Solution Reference"]



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
            falcon = SpotlightVulnerabilities(client_id=CLIENT_ID, client_secret=SECRET_ID)



            #################################### Part 3: Obtaining Vulnerabilities ->

            # First calls prove the credentials and count each dataset
            totals = {}
            for variant, fql in FILTERS.items():
                response = falcon.query_vulnerabilities(filter=fql, limit=1)

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                totals[variant] = response["body"]["meta"]["pagination"]["total"]

            # Yields one page of vulnerabilities at a time, following the after token until the last page
            # (pages are turned into records as they arrive in Part 4, so the raw responses never pile up in memory)
            def fetch_pages(fql):
                after = None
                while True:
                    parameters = {"filter": fql, "facet": FACETS, "limit": PAGE_SIZE}
                    if after: parameters["after"] = after
                    response = falcon.query_vulnerabilities_combined(**parameters)

                    if response["status_code"] != 200:
                        print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                        raise SystemExit(1)

                    yield response["body"].get("resources") or []
                    after = response["body"]["meta"]["pagination"].get("after")
                    if not after: break



            #################################### Part 4: Extracting Fields ->

            empty = "-"
            today = current_date.strftime("%Y-%m-%d")

            # Returns a UTC timestamp as a local date (%Y-%m-%d)
            def format_date(value):
                if not value: return empty
                return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(LOCAL_TZ).strftime("%Y-%m-%d")

            # Returns the calendar day of a catalog date (CVE publication, CISA due date), with no timezone shift
            def format_day(value):
                return value[:10] if value else empty

            # Returns an API enum as readable text, keeping acronyms in capitals
            def label(value):
                if not value: return empty
                return " ".join(word if word in ACRONYMS else word.capitalize() for word in str(value).upper().split("_"))

            # Returns the distinct values of a list joined by "; ", or "-" when there is none
            def join(values):
                values = list(dict.fromkeys(value for value in values if value))
                return "; ".join(map(str, values)) if values else empty

            # Returns the record of one vulnerability for the dataset of its variant (Active, Fixed or Expired)
            def build_record(item, variant):
                cve = item.get("cve", {})
                host = item.get("host_info", {})
                apps = item.get("apps", [])
                cisa = cve.get("cisa_info", {})
                suppression = item.get("suppression_info", {})
                exploit_status = cve.get("exploit_status")
                on_kev = cisa.get("is_cisa_kev", False)
                first_seen = format_date(item.get("created_timestamp"))

                record = {
                    "Severity": label(cve.get("severity")),
                    "Host Id": item.get("aid", empty),
                    "Host Name": host.get("hostname", empty),
                    "Host Ip": host.get("local_ip", empty),
                    "Host Type": host.get("product_type_desc", empty),
                    "Host Platform": host.get("platform", empty),
                    "Host System": host.get("os_version", empty),
                    "Internet Exposure": host.get("internet_exposure", empty),
                }

                if variant == "Active":
                    record["Vuln Age-in-days"] = (current_date.date() - datetime.date.fromisoformat(first_seen)).days

                record.update({
                    "Vuln Group": item.get("vulnerability_id", empty),
                    "Vuln Id": item.get("id", empty),
                    "Vuln Name": cve.get("name") or empty,
                    "Vuln Family": join(cve.get("types", [])),
                    "Vuln Resume": " ".join(cve.get("description", empty).split()),
                })

                # Recommended remediation of each affected application (Spotlight clears it once the vulnerability closes or expires)
                if variant == "Active":
                    recommended_ids = {app.get("remediation_info", {}).get("recommended_id") for app in apps}
                    solutions = [entity for entity in item.get("remediation", {}).get("entities", []) if entity.get("id") in recommended_ids]
                    record.update({
                        "Vuln Solution": join(entity.get("action") for entity in solutions),
                        "Solution Type": join(label(entity.get("type")) for entity in solutions if entity.get("type")),
                        "Solution Reference": join(entity.get("reference") for entity in solutions),
                    })

                record.update({
                    "Vuln Product": join(app.get("product_name_version") for app in apps),
                    "Vuln Vendor": join(app.get("vendor_normalized") for app in apps),
                    "Vuln CVEs": cve.get("id", empty),
                    "Vuln Source": join(provider.get("provider") for provider in item.get("data_providers", [])),
                    "Vuln State": label(item.get("status")),
                })

                if variant == "Active":
                    record["Risk State"] = "None" if not suppression.get("is_suppressed") else label(suppression.get("reason"))

                record["First Seen"] = first_seen

                if variant == "Fixed":
                    record["Last Fixed"] = format_date(item.get("closed_timestamp"))

                if variant == "Expired":
                    record["Last Expired"] = format_date(item.get("updated_timestamp"))
                    record["Host Last Seen"] = format_date(host.get("host_last_seen_timestamp"))

                record.update({
                    "CVE Published": format_day(cve.get("published_date")),
                    "CVSS Score": cve.get("base_score", empty),
                    "ExPRT Rating": label(cve.get("exprt_rating")),
                    "Remediation Level": REMEDIATION_LEVEL.get(cve.get("remediation_level"), empty),
                    "Exploit Available": exploit_status >= 30,
                    "Exploit Maturity": EXPLOIT_STATUS.get(exploit_status, empty),
                    "Exploitability Score": cve.get("exploitability_score", empty),
                    "Adversaries": join(cve.get("actors", [])),
                    "On CISA KEV": on_kev,
                    "CISA Due Date": format_day(cisa.get("due_date")),
                })

                if variant == "Active":
                    record["Item: CISA Due Date"] = empty if not on_kev else ("Attention" if format_day(cisa.get("due_date")) < today else "Ok")

                return record

            # Build every dataset page by page
            datasets = {}
            for variant, fql in FILTERS.items():
                frames = [pd.DataFrame([build_record(item, variant) for item in page]) for page in fetch_pages(fql) if page]
                datasets[variant] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
                print(f"{variant}: {totals[variant]} vulnerabilities")

            # One spelling per value: values that differ only in case take the spelling with the most capitals, the same in every file
            for dataframe in datasets.values():
                for column in ONE_SPELLING:
                    if column not in dataframe: continue
                    lower = dataframe[column].str.lower()
                    spelling = dataframe[column].groupby(lower).agg(lambda values: max(sorted(values.unique()), key=lambda value: sum(map(str.isupper, value))))
                    dataframe[column] = lower.map(spelling)



            #################################### Part 5: Saving the information ->

            # Save one dataset to a CSV (adds the reference stamp columns last)
            def save_csv(dataframe, dir, project):
                if dataframe.empty: return
                dataframe = dataframe.fillna(empty)

                # Reference stamp columns — always last
                dataframe["Reference Month"] = current_date.strftime("%m")
                dataframe["Reference Year"] = current_date.strftime("%Y")
                dataframe["Reference Date"] = current_date.strftime("%Y-%m-%d")

                dataframe.to_csv(os.path.join(dir, f"{project}.csv"), index=False, encoding="utf-8-sig")

            # Saving data
            for variant, dataframe in datasets.items():
                save_csv(dataframe, dir_to_save_csv, f"{PROJECT}-{variant}")


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
