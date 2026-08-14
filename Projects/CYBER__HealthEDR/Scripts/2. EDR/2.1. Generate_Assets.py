#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import sys
import json
import requests
import datetime
import pandas as pd
from falconpy import Hosts, ZeroTrustAssessment, PreventionPolicy, DeviceControlPolicies, SensorUpdatePolicy, ContentUpdatePolicies, FirewallPolicies

# ----------------------------------------->

# Results
PROJECT = "HealthEDR-Assets"
PROJECT_CHILD_01 = "(Unwatched)_HealthEDR-Assets"

# Getting current date in format (MM-YYYY)
current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%m-%Y")

# Getting current path for file saving
current_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(current_dir, f"../.env")

# Define saving directories
dir_to_save_csv = os.path.join(current_dir, f"../../Datas/{formatted_date}")
dir_to_save_csv_unwatched = os.path.join(current_dir, f"../../Datas/{formatted_date}/Unwatched")

# Auto create DIR
if not os.path.exists(dir_to_save_csv_unwatched):
    os.makedirs(dir_to_save_csv_unwatched)

# Check if comparison files exist, if so, they will be read
dir_entry = os.path.join(current_dir, f"../../Datas/{formatted_date}/Entry/vcenter-assets_{formatted_date}.json")
if os.path.exists(dir_entry):
    with open(dir_entry, encoding="utf-8") as file: data_vcenter = json.load(file)
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
 
        

        #################################### Part 3: Obtaining Assets ->
   
        # Init extract data
        try:
            
            # Define local variables
            CLIENT_ID = secret["CLIENT_ID"]
            SECRET_ID = secret["SECRET_ID"]

            # Define falcon request
            falcon = Hosts(client_id=CLIENT_ID, client_secret=SECRET_ID)

            # Prepare variables for [id] call
            filter_limit = 10000

            response = falcon.query_devices_by_filter_combined(limit=filter_limit)
            assets = response["body"]["resources"]



            #################################### Part 4: Extracting Fields ->

            # Create list with filter
            empty = "-"
            hosts = []

            # Build policy_id -> name maps (device data only carries the id, not the name)
            def policy_names(service, method):
                resources = getattr(service(client_id=CLIENT_ID, client_secret=SECRET_ID), method)(limit=5000)["body"]["resources"]
                return {p["id"]: p["name"] for p in (resources or [])}

            prevention_names = policy_names(PreventionPolicy, "query_combined_policies")
            device_control_names = policy_names(DeviceControlPolicies, "query_combined_policies")
            firewall_names = policy_names(FirewallPolicies, "query_combined_policies")
            sensor_update_names = policy_names(SensorUpdatePolicy, "query_combined_policies")
            content_update_names = policy_names(ContentUpdatePolicies, "query_policies_combined")

            # Resolve a host's assigned policy id to its name for a given policy type
            def policy_name(item, policy_type, name_map):
                pid = item.get("device_policies", {}).get(policy_type, {}).get("policy_id")
                return name_map.get(pid, empty)


            for item in assets:

                host_id = item["device_id"]
                host_name = item["hostname"] if "hostname" in item else empty
                host_type = item["product_type_desc"] if "product_type_desc" in item else empty
                host_os = item["platform_name"] if "platform_name" in item else empty
                host_os_version = item["os_version"] if "os_version" in item else empty
                kernel_version = item["kernel_version"] if "kernel_version" in item else empty
                host_state = item["host_hidden_status"].capitalize() if "host_hidden_status" in item else empty
                rfm = True if "reduced_functionality_mode" in item and item["reduced_functionality_mode"] == "yes" else False
                linux_mode = item["linux_sensor_mode"] if "linux_sensor_mode" in item else empty
                agent_version = item["agent_version"] if "agent_version" in item else empty
                uninstall_protection = item.get("device_policies", {}).get("sensor_update", {}).get("uninstall_protection", empty)
                mac_address = sorted({mac.replace("-", ":") for mac in (item.get("mac_address", ""), item.get("connection_mac_address", "")) if mac})
                last_seen = item["last_seen"] if "last_seen" in item else empty
                
                if last_seen is not empty: last_seen = (datetime.datetime.strptime(last_seen, "%Y-%m-%dT%H:%M:%SZ") - datetime.timedelta(hours=3)).strftime("%Y-%m-%d")

                # ->
                hosts.append({
                    "Department": empty,
                    "Server VM": empty,
                    "Last Seen": last_seen,
                    "Host Id": host_id,
                    "Host Name": host_name,
                    "Mac Address": mac_address,
                    "Host Type": host_type,
                    "Host OS": host_os,
                    "OS Version": host_os_version,
                    "Kernel Version": kernel_version,
                    "Host State": host_state,
                    "RFM": rfm,
                    "Linux Mode": linux_mode,
                    "Uninstall Protection": uninstall_protection.capitalize(),
                    "Prevention Policy": policy_name(item, "prevention", prevention_names),
                    "USB Device Policy": policy_name(item, "device_control", device_control_names),
                    "Firewall Policy": policy_name(item, "firewall", firewall_names),
                    "Sensor Update Policy": policy_name(item, "sensor_update", sensor_update_names),
                    "Content Policy": policy_name(item, "content-update", content_update_names),
                })
                


            #################################### Part 5: Extracting Sensor Health Checks ->

            # Perform the query
            falcon = ZeroTrustAssessment(client_id=CLIENT_ID, client_secret=SECRET_ID)

            def is_rfm(signal):
                name = signal["signal_name"].upper()
                return "REDUCED" in name or "RFM" in name

            # Index assessment results by aid (matches the device_id / Host Id from Part 3)
            assessments = {}
            id_list = [item["Host Id"] for item in hosts]

            # Falcon allows at most 1000 AIDs per assessment call — request in chunks
            for start in range(0, len(id_list), 1000):

                response = falcon.get_assessment(ids=id_list[start:start + 1000])

                for resource in (response["body"]["resources"] or []):

                    aid = resource["aid"]
                    sensor_signals = resource["assessment_items"]["sensor_signals"]
                    is_linux = resource["event_platform"] == "Lin"
                    host_score = resource.get("assessment", {}).get("sensor_config", empty)

                    # Host is in Reduced Functionality Mode if its RFM signal fails
                    in_rfm = any(is_rfm(s) and s["meets_criteria"] != "yes" for s in sensor_signals)

                    # "Host Score" comes before the item columns; then one column per sensor signal
                    signals = {"Host Score": host_score}
                    for signal in sensor_signals:
                        column_name = f"Item: {signal['signal_name']}"

                        # RFM signal itself: OK when in full functionality, ATTENTION (root cause) otherwise
                        if is_rfm(signal): value = "Ok" if signal["meets_criteria"] == "yes" else "Attention"

                        # Linux host in RFM: every other item points to the root cause, even passing ones
                        elif is_linux and in_rfm: value = "Check RFM"
                        elif signal["meets_criteria"] == "yes": value = "Ok"
                        else: value = "Attention"

                        signals[column_name] = value

                    assessments[aid] = signals

            # Link each host (Host Id) with its assessment (aid) and append the signal columns
            for item in hosts: item.update(assessments.get(item["Host Id"], {}))



            #################################### Part 6: Departments Population & Unwatched Separation ->

            # Build a lookup: mac_address -> vcenter record
            vcenter_by_mac = {}
            for v in data_vcenter:
                for mac in v.get("Mac Address", []):
                    if mac != empty:
                        vcenter_by_mac[mac.lower()] = v

            # Match each host to a vcenter record by MAC; matched hosts get their department, unmatched are set aside
            matched_hosts = []
            unmatched_hosts = []

            for item in hosts:

                # Workstations are always watched with a fixed department and their own hostname as VM
                if item["Host Type"] == "Workstation":
                    item["Department"] = "TI-SERVICEDESK"
                    item["Server VM"] = item["Host Name"]
                    matched_hosts.append(item)
                    continue

                macs = item.get("Mac Address", [])
                vcenter = next((vcenter_by_mac[m.lower()] for m in macs if m.lower() in vcenter_by_mac), None)

                if vcenter:
                    item["Department"] = vcenter.get("Setor", empty)
                    item["Server VM"] = vcenter.get("Asset VM", empty)
                    matched_hosts.append(item)
                else:
                    unmatched_hosts.append(item)



            #################################### Part 7: Saving the information ->

            # Only generate reports for these operating systems
            target_os = {"Linux", "Mac", "Windows"}

            # Save a set of host records as one CSV per Host OS
            def save_per_os(records, dir, project):
                if not records: return
                df = pd.DataFrame(records)

                # Keep "Linux Mode" only for Linux hosts
                df["Linux Mode"] = df["Linux Mode"].where(df["Host OS"] == "Linux")

                # Create a separate DataFrame per Host OS
                for host_os, dataframe in df.groupby("Host OS"):
                    if host_os not in target_os: continue

                    # Keep only the signal columns relevant to this OS, then fill remaining nulls with the empty marker
                    dataframe = dataframe.dropna(axis=1, how="all").fillna(empty)

                    # Reference stamp columns — always last
                    dataframe["Reference Month"] = current_date.strftime("%m")
                    dataframe["Reference Year"] = current_date.strftime("%Y")
                    dataframe["Reference Date"] = current_date.strftime("%Y-%m-%d")

                    dataframe.to_csv(os.path.join(dir, f"{project}_{host_os}.csv"), index=False, encoding="utf-8")

            # Saving data
            save_per_os(matched_hosts, dir_to_save_csv, PROJECT)
            save_per_os(unmatched_hosts, dir_to_save_csv_unwatched,PROJECT_CHILD_01)

           
        except Exception as err: print(err)
        
    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")