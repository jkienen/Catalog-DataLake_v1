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
PROJECT_PARENT = "GVulnerabilities-Assets"

PROJECT = "GVulnerabilities-Vulns"
PROJECT_CHILD_01 = "GVulnerabilities-Vulns(Fixed)"
PROJECT_CHILD_02 = "(Unwatched)_GVulnerabilities-Vulns"

# Getting current date in format (MM-YYYY)
current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%m-%Y")

# Getting current path for file saving
current_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_dir, f"../.env")

# Define saving directories
dir_to_save_csv = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT}_{formatted_date}.csv")
dir_to_save_json = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT}_{formatted_date}.json")

# Define fixed vulns directories
dir_to_save_csv_fixed = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT_CHILD_01}_{formatted_date}.csv")
dir_to_save_json_fixed = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT_CHILD_01}_{formatted_date}.json")

# Define unwatched assets
dir_to_save_csv_unwatched = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/Unwatched/{PROJECT_CHILD_02}_{formatted_date}.csv")
dir_to_save_json_unwatched = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/Unwatched/{PROJECT_CHILD_02}_{formatted_date}.json")

# Define auto create DIR
parent_directory = os.path.dirname(dir_to_save_csv_unwatched)
if not os.path.exists(parent_directory):
    os.makedirs(parent_directory)

# Check if comparison files exist, if so, they will be read
dir_entry_json = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT_PARENT}_{formatted_date}.json")
dir_entry_csv = os.path.join(current_dir, f"../../Datas/{formatted_date}/{PROJECT_PARENT}_{formatted_date}.csv")
if os.path.exists(dir_entry_csv) and os.path.exists(dir_entry_json): 
    with open(dir_entry_json, encoding="utf-8") as file: data_assets = json.load(file)
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
 
     

        #################################### Part 3: Obtaining Tenable Active Vulns ->

        # Init extract data
        try:
            
            # Define local variables
            CLIENT_ID = secret["CLIENT_ID"]
            SECRET_ID = secret["SECRET_ID"]

            # Authentication with pyTenable
            from tenable.io import TenableIO
            tio = TenableIO(CLIENT_ID, SECRET_ID)

            # Compute previous calendar month date range
            today = datetime.datetime.now()
            first_day_prev_month = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
            last_day_prev_month  = (today.replace(day=1) - datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)

            # Cancel any queued/running vuln exports to free up slots (max 10 allowed)
            try:
                for job in tio.exports.jobs("vulns"):
                    if job.get("status") in ("QUEUED", "PROCESSING"): tio.exports.cancel("vulns", job["uuid"])
            except Exception as cancel_err: pass
            
            # Performs the query filtering
            active_vulns = tio.exports.vulns(
                severity=["low", "medium", "high", "critical"],
                source=["AGENT", "NESSUS"],
                state=["OPEN", "REOPENED"],
                num_assets=5000,
                timeout=3000,
                adopt_existing=False
            ); active_vulns_tenable = []

            for vuln in active_vulns:
                active_vulns_tenable.append(vuln)
  
            # Performs the query filtering (fixed vulns from previous calendar month)
            fixed_vulns = tio.exports.vulns(
                last_fixed=first_day_prev_month,
                severity=["low", "medium", "high", "critical"],
                source=["AGENT", "NESSUS"],
                state=["FIXED"],
                num_assets=5000,
                timeout=3000,
                adopt_existing=False
            ); fixed_vulns_tenable = []

            for vuln in fixed_vulns:
                vuln_last_fixed = vuln.get("last_fixed")
                if vuln_last_fixed:
                    if isinstance(vuln_last_fixed, str):
                        vuln_last_fixed = datetime.datetime.fromisoformat(vuln_last_fixed.replace("Z", "+00:00")).replace(tzinfo=None)
                    if vuln_last_fixed <= last_day_prev_month:
                        fixed_vulns_tenable.append(vuln)
            

            
            #################################### Part 4: Data Processing ->

            active_vulns = []
            fixed_vulns  = []
            empty = "-"

            # Function for date normalization
            def format_date(date):
                if date is not empty:
                    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
                        try:
                            date = datetime.datetime.strptime(date, fmt).strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                return date

            # Perform data standardization
            for i in active_vulns_tenable + fixed_vulns_tenable:

                # Nested objects
                asset = i.get("asset", {})
                plugin = i.get("plugin", {})
                vpr = plugin.get("vpr", {})
                vpr_v2 = plugin.get("vpr_v2", {})

                # Asset fields
                server_id  = asset.get("uuid", empty)
                server_name = asset.get("hostname", empty)
                server_ip = asset.get("ipv4", empty)
                os_raw = asset.get("operating_system", empty)
                server_system = os_raw[0] if isinstance(os_raw, list) and os_raw else os_raw

                # Finding fields
                finding_id = i.get("finding_id", empty)
                vuln_state = i.get("state", empty)
                vuln_source = i.get("source", empty)
                vuln_severity = (vpr_v2.get("vpr_severity") or i.get("severity", empty)).capitalize()
                risk_state = i.get("severity_modification_type", empty)
                resurfaced_data = i.get("resurfaced_data")
                first_seen = format_date(resurfaced_data if resurfaced_data else i.get("first_found", empty))
                last_fixed = format_date(i.get("last_fixed", empty))

                # Plugin fields
                vuln_group = plugin.get("id", empty)
                vuln_name = plugin.get("name", empty)
                vuln_family = plugin.get("family", empty)
                vuln_resume = plugin.get("synopsis", empty)
                vuln_solution = plugin.get("solution", empty)
                vuln_cves = plugin.get("cve", empty)

                # VPR fields
                vpr_score = vpr.get("score", empty)
                vuln_age = (datetime.datetime.now() - datetime.datetime.strptime(first_seen, "%Y-%m-%d")).days if first_seen is not empty else empty

                # VPR v2 fields
                vpr2_score = vpr_v2.get("score", empty)
                vpr2_percentile = vpr_v2.get("vpr_percentile", empty)
                on_cisa_kev = vpr_v2.get("on_cisa_kev", empty)
                exploit_code_maturity = vpr_v2.get("exploit_code_maturity", empty)

                # Prioritization fields
                exploit_available = plugin.get("exploit_available", empty)
                exploitability_ease = plugin.get("exploitability_ease", empty)
                epss_score = plugin.get("epss_score", empty)
                exploited_by_malware = plugin.get("exploited_by_malware", empty)
                exploited_by_nessus = plugin.get("exploited_by_nessus", empty)

                record = {
                    "Department": empty,
                    "Severity": vuln_severity,
                    "Server Id": server_id,
                    "Server VM": empty,
                    "Server Name": server_name,
                    "Server Ip": server_ip,
                    "Server Type": empty,
                    "Server System": server_system,
                    "Vuln Age-in-days": vuln_age,
                    "Vuln Group": vuln_group,
                    "Vuln Id": finding_id,
                    "Vuln Name": vuln_name,
                    "Vuln Family": vuln_family,
                    "Vuln Resume": vuln_resume,
                    "Vuln Solution": vuln_solution,
                    "Vuln CVEs": vuln_cves,
                    "Vuln Source": vuln_source,
                    "Vuln State": vuln_state,
                    "Risk State": risk_state,
                    "First Seen": first_seen,
                    "Last Fixed": last_fixed,
                    "VPR": vpr_score,
                    "VPR v2": vpr2_score,
                    "VPR v2 Percentile": vpr2_percentile,
                    "EPSS Score": epss_score,
                    "Exploit Available": exploit_available,
                    "Exploit Maturity": exploit_code_maturity,
                    "Exploitability Ease": exploitability_ease,
                    "Exploited By Malware": exploited_by_malware,
                    "Exploited By Nessus": exploited_by_nessus,
                    "On CISA KEV": on_cisa_kev,
                    "Reference Month": datetime.datetime.now().strftime("%m"),
                    "Reference Year": datetime.datetime.now().strftime("%Y"),
                    "Reference Date": datetime.datetime.now().strftime("%Y-%m-%d")
                }

                if vuln_state == "FIXED": fixed_vulns.append(record)
                else: active_vulns.append(record)


            
            #################################### Part 5: Departments Updating ->

            # Build lookup: server_id -> asset record from tenable-assets JSON
            assets_by_id = {asset["Server Id"]: asset for asset in data_assets}

            # 1. Feed Department in fixed_vulns (all records)
            for vuln in fixed_vulns:
                asset = assets_by_id.get(vuln["Server Id"])
                if asset:
                    vuln["Department"] = asset["Department"]
                    vuln["Server VM"] = asset["Server VM"]
                    vuln["Server Type"] = asset["Server Type"]

            # 1 & 3. Feed Department in active_vulns + remove unmatched
            active_vulns_matched = []
            active_vulns_unmatched = []
            for vuln in active_vulns:
                asset = assets_by_id.get(vuln["Server Id"])
                if asset:
                    vuln["Department"] = asset["Department"]
                    vuln["Server VM"] = asset["Server VM"]
                    vuln["Server Type"] = asset["Server Type"]
                    active_vulns_matched.append(vuln)
                else:
                    active_vulns_unmatched.append(vuln)
            active_vulns = active_vulns_matched

            # 2. Count active vulns by severity per asset and update dir_entry records
            for asset in data_assets:
                asset["Vulns Critical"] = 0
                asset["Vulns High"] = 0
                asset["Vulns Medium"] = 0
                asset["Vulns Low"] = 0

            for vuln in active_vulns:
                if vuln.get("Risk State") == "ACCEPTED":
                    continue
                asset = assets_by_id.get(vuln["Server Id"])
                if asset:
                    sev = vuln.get("Severity", empty)
                    key = f"Vulns {sev}"
                    if key in asset:
                        asset[key] += 1

            for asset in data_assets:
                asset["Vulns Total"] = asset["Vulns Critical"] + asset["Vulns High"] + asset["Vulns Medium"] + asset["Vulns Low"]

            # --------------------------------- Part 5.1: Saving updated asset records (with vuln counts) back to dir_entry

            # Create Data Frame
            df_assets = pd.DataFrame(data_assets)

            # Data Storing
            df_assets.to_csv(dir_entry_csv, index=False, encoding="utf-8")
            df_assets.to_json(dir_entry_json, orient="records")

            # --------------------------------- ->


            # --------------------------------- Part 5.1: Saving to Other Audit: Unwatched Vulns ->

            # Create Data Frame
            df_unmatched  = pd.DataFrame(active_vulns_unmatched)

            # Data Storing
            df_unmatched.to_csv(dir_to_save_csv_unwatched, index=False, encoding="utf-8")
            df_unmatched.to_json(dir_to_save_json_unwatched, orient="records")

            # --------------------------------- ->



            #################################### Part 6: Data Saving ->

            # Create Data Frames
            df_active = pd.DataFrame(active_vulns).drop(columns=["Last Fixed"])
            df_fixed  = pd.DataFrame(fixed_vulns).drop(columns=["Vuln Age-in-days", "Risk State"])

            # Data Storing
            df_active.to_csv(dir_to_save_csv, index=False, encoding="utf-8")
            df_active.to_json(dir_to_save_json, orient="records")

            df_fixed.to_csv(dir_to_save_csv_fixed, index=False, encoding="utf-8")
            df_fixed.to_json(dir_to_save_json_fixed, orient="records")
            

        except Exception as err: print(err)
        
    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")