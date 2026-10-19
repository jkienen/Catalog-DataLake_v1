#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import sys
import json
import time
import requests
import datetime
import pandas as pd
from falconpy import IdentityProtection, Hosts, NGSIEM

# ----------------------------------------->

# Results
PROJECT = "HealthIDP-Controllers"
PROJECT_CHILD_01 = "(Unwatched)_HealthIDP-Controllers"

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

# GraphQL query: Domain Controllers known by Identity Protection, with their risk factors
DC_QUERY = """
query ($after: Cursor) {
  entities(types: [ENDPOINT], roles: [DomainControllerRole], archived: false, first: 200, after: $after) {
    nodes {
      entityId primaryDisplayName riskScore riskScoreSeverity watched riskFactors { type score }
      accounts { ... on ActiveDirectoryAccountDescriptor { domain } }
      ... on EndpointEntity { agentId hostName lastIpAddress mostRecentActivity operatingSystemInfo { displayName } }
    }
    pageInfo { hasNextPage endCursor }
  }
}
""".strip()

# Define time filter to events from last 7 days (NGSIEM)
end_ms = int((end_time := datetime.datetime.now(datetime.timezone.utc)).timestamp() * 1000)
start_ms = int((end_time - datetime.timedelta(days=7)).timestamp() * 1000)

# NGSIEM query: "Domain controllers" widget of the Identity Protection - Service health dashboard (7d window; watchdog alerts keep 30d)
NGSIEM_QUERY = """
// Table to get dc connectivity
defineTable(query={
#repo=base_sensor #event_simpleName=/^IdpCloudHealthStatus|IdpCloudHealthCheck$/i
| case {
  #event_simpleName=IdpCloudHealthStatus;
  #event_simpleName=IdpCloudHealthCheck | "Cloud Connectivity.Last Checked":= @timestamp;
}
| groupBy([cid, aid],function=selectLast(IdpCloudConnectivityState,"Cloud Connectivity.Last Checked"), limit=5000)
| case{
  test(getField("Cloud Connectivity.Last Checked") < now() - 10 * 60000) |  "Cloud Connectivity.IdP Service Status":="Disconnected";  // Not checked for more than 10min is considered Disconnected
  IdpCloudConnectivityState=0 | "Cloud Connectivity.IdP Service Status":="Healthy";
  IdpCloudConnectivityState=1 | "Cloud Connectivity.IdP Service Status":="Laggy";
  IdpCloudConnectivityState=2 | "Cloud Connectivity.IdP Service Status":="Disconnected";
  * | "Cloud Connectivity.IdP Service Status":="Healthy"
}
}, include=[cid, aid, "Cloud Connectivity.IdP Service Status", "Cloud Connectivity.Last Checked"], name="cloud_connectivity", start=7d)

// Table to get watchdog alerts: alert count and the traffic inspection state forced by remediations (branch filters kept as in the dashboard)
| defineTable(query={
  #repo=base_sensor #event_simpleName=/^IdpWatchdog|HostInfo/i
  | match(file="aid_master_main.csv", field=[cid, aid])
  | ProductType=2
  | case{
      #event_simpleName=IdpWatchdogRemediationActionTaken* AND RemediationAction=0;
      #event_simpleName=IdpWatchdogRemediationActionTaken* AND RemediationAction=1 | "Traffic Inspection.Enforcement":= "Forced Disabled";
      #event_simpleName=IdpWatchdogRemediationActionTaken* AND RemediationAction=2 | "Traffic Inspection.Status":= "Forced Disabled";
      #event_simpleName=IdpWatchdogRemediationActionTaken* AND RemediationAction=3 | "Traffic Inspection.Status":= "Limited";
      #event_simpleName=IdpWatchdogReEnabled AND RemediationActionReverted=0 | "Traffic Inspection.Enforcement":= "Enabled";
      #event_simpleName=IdpWatchdogReEnabled AND RemediationActionReverted=1 | "Traffic Inspection.Status":= "Enabled";
      #event_simpleName=IdpWatchdogReEnabled AND RemediationActionReverted=2 | "Traffic Inspection.Status":= "Enabled";
      #event_simpleName=HostInfo | "Traffic Inspection.Status":= "Enabled" | "Traffic Inspection.Enforcement":= "Enabled"; // HostInfo indicates a reboot or sensor upgrade which restarts idp services
  }
  | groupBy([aid, cid], function=[
      selectLast(["Traffic Inspection.Enforcement", "Traffic Inspection.Status"]),
      {#event_simpleName=IdpWatchdogRemediationActionTaken* | count(as="Service Health Alert.Total")}], limit=5000)
  | "Service Health Alert.Total" > 0
}, include=["cid", "aid", "Traffic Inspection.Enforcement", "Traffic Inspection.Status", "Service Health Alert.Total"], name="watchdog_status", start=30d)

// Table to list all KBs installed on DCs (Raw layer only: latest and pending KB are fetched, not written to the report)
| defineTable(query={#repo=base_sensor #event_simpleName=InstalledUpdates
| match(file="aid_master_main.csv", field=[cid, aid])
| ProductType=2
| splitString(by=";", InstalledUpdateIds, as=InstalledUpdateIds)
| splitString(by=";", PendingUpdateIds, as=PendingUpdateIds)
| rename(field="InstalledUpdateIds[0]", as="MostRecentlyInstalledKB")
| rename(field="PendingUpdateIds[0]", as="MostRecentlyInstalledPendingKB")
| default(value="None", field=[MostRecentlyInstalledKB,MostRecentlyInstalledPendingKB], replaceEmpty=true)
| groupBy([cid, aid], function=selectLast([MostRecentlyInstalledKB, MostRecentlyInstalledPendingKB, InstalledUpdateIds, PendingUpdateIds]), limit=5000)}, include=[cid, aid, MostRecentlyInstalledKB, MostRecentlyInstalledPendingKB], name="installed_kbs", start=7d)

// Table to list DC inspected traffic in the last 7d
| defineTable(query={#repo=base_sensor #event_simpleName=/^ActiveDirectory(?:(?!Audit|Account).)*$/i | groupBy([cid, aid], function=sum("AggregationActivityCount", as="Traffic Inspection.Insp. Reqs (7d)"), limit=5000)
}, include=[cid, aid, "Traffic Inspection.Insp. Reqs (7d)"], name="inspected_traffic", start=7d)

// Table to list DC with traffic inspection ON by policy
| defineTable(query={#repo=base_sensor #event_simpleName=CurrentSystemTags | match(file="aid_master_main.csv", field=[cid, aid]) | ProductType=2
| groupBy([cid, aid], function=selectLast([Tags]), limit=5000)
| case {
  Tags=/26388279067565/ | "Traffic Inspection.Configuration":="Forced Disabled"; // Has tag IdpKillSwitch
  Tags=/26456998544302/ | "Traffic Inspection.Configuration":="Enabled"; // Has tag IdpEnabledDomainController
  * | "Traffic Inspection.Configuration":="Disabled by policy";
}}, include=[cid, aid, "Traffic Inspection.Configuration"], name="ati_enabled", start=7d)

// Table to list DC Resource usage
| defineTable(query={
#repo=base_sensor #event_simpleName=/^SystemCapacity|ResourceUtilization$/i
| match(file="aid_master_main.csv", field=[cid, aid])
| ProductType=2
| groupBy([cid, aid], function=[max(MaxUsedRam, as=MaxUsedRam), max(MaxCpuUsage, as=MaxCpuUsage), avg(AverageUsedRam, as=AverageUsedRam), avg(AverageCpuUsage, as=AverageCpuUsage), selectLast([UsedDiskSpace, AvailableDiskSpace, LogicalCoreCount, MemoryTotal])], limit=5000)
| MemoryTotal := unit:convert(field=MemoryTotal, to=Gi)
| MaxUsedRam := unit:convert(field=MaxUsedRam, from=Mi, to=Gi)
| MaxPercentUsedRam := (MaxUsedRam/MemoryTotal)*100
| AverageUsedRam := unit:convert(field=AverageUsedRam, from=Mi, to=Gi)
| AveragePercentUsedRam := (AverageUsedRam/MemoryTotal)*100
| TotalDiskSpace:= (UsedDiskSpace + AvailableDiskSpace)
| default(value="-", field=[MemoryTotal, MaxPercentUsedRam, AveragePercentUsedRam, MaxCpuUsage, AverageCpuUsage, TotalDiskSpace, UsedDiskSpace, AvailableDiskSpace, LogicalCoreCount])
}, include=[cid, aid, MemoryTotal, MaxPercentUsedRam, AveragePercentUsedRam, MaxCpuUsage, AverageCpuUsage, TotalDiskSpace, UsedDiskSpace, AvailableDiskSpace, LogicalCoreCount], name="resources")

// Get the list of active DCs
| #repo=base_sensor #event_simpleName=SensorHeartbeat
| groupBy([cid, aid], function=[], limit=max)
| match(file="aid_master_main.csv", field=[cid, aid])
| ProductType=2
| match(file="cloud_connectivity", field=[cid, aid], strict=false)
| default(value="Disconnected", field=["Cloud Connectivity.IdP Service Status"]) // DCs that have not reported a cloud connectivity status or checked are considered disconnected
| match(file="ati_enabled", field=[cid, aid], strict=false)
| default(value="Disabled (unknown)", field=["Traffic Inspection.Configuration"])
| "Traffic Inspection.Status":=getField("Traffic Inspection.Configuration")
| "Traffic Inspection.Enforcement":=getField("Traffic Inspection.Configuration")
| match(file="inspected_traffic", field=[cid, aid], strict=false)
| default(value="0", field=["Traffic Inspection.Insp. Reqs (7d)"])
| match(file="installed_kbs", field=[cid, aid], strict=false)
| match(file="watchdog_status", field=[cid, aid], strict=false)
| default(value="0", field=["Service Health Alert.Total"])
| match(file="resources", field=[cid, aid], strict=false)
| rename([LogicalCoreCount, "CPU.Cores (Logical)"], [AverageCpuUsage, "CPU.Avg Usage (%)"], [MaxCpuUsage, "CPU.Max Usage (%)"], [MemoryTotal, "Memory.Total (GB)"], [MaxPercentUsedRam, "Memory.Max Usage (%)"], [AveragePercentUsedRam, "Memory.Avg Usage (%)"], [aid, "Domain Controller.Sensor Id"], [MostRecentlyInstalledKB, "Domain Controller.Latest KB"], [MostRecentlyInstalledPendingKB, "Domain Controller.Pending KB"],[UsedDiskSpace, "Storage.Used (GB)"], [TotalDiskSpace, "Storage.Total (GB)"], [AvailableDiskSpace, "Storage.Available (GB)"])
| table(["Domain Controller.Sensor Id", "Domain Controller.Latest KB", "Domain Controller.Pending KB", "Cloud Connectivity.IdP Service Status", "Cloud Connectivity.Last Checked", "Traffic Inspection.Status", "Traffic Inspection.Configuration", "Traffic Inspection.Enforcement", "Traffic Inspection.Insp. Reqs (7d)", "CPU.Cores (Logical)", "CPU.Avg Usage (%)", "CPU.Max Usage (%)", "Memory.Total (GB)", "Memory.Avg Usage (%)", "Memory.Max Usage (%)", "Storage.Total (GB)", "Storage.Used (GB)", "Storage.Available (GB)", "Service Health Alert.Total"], limit=5000)
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



            #################################### Part 3: Obtaining Sensors ->

            # Query every sensor id (paginated), then pull their details
            sensor_ids, offset = [], 0
            while True:
                response = falcon.query_sensors(limit=200, offset=offset)

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                page = response["body"]["resources"] or []
                sensor_ids += page
                offset = len(sensor_ids)
                if not page or offset >= response["body"]["meta"]["pagination"]["total"]: break

            sensors = falcon.get_sensor_details(ids=sensor_ids)["body"]["resources"] or [] if sensor_ids else []



            #################################### Part 4: Obtaining Domain Controllers Risk Factors ->

            # Every DC seen by Identity Protection (with or without sensor), paginated
            dc_entities, after = [], None
            while True:
                response = falcon.graphql(query=DC_QUERY, variables={"after": after})
                data = (response["body"].get("data") or {}).get("entities") or {}
                if response["body"].get("errors"): print(f"GraphQL errors: {response['body']['errors']}"); break
                dc_entities += data.get("nodes") or []
                if not (data.get("pageInfo") or {}).get("hasNextPage"): break
                after = data["pageInfo"]["endCursor"]

            # Every risk factor found on any DC becomes an "Item:" column (WATCHED is a watchlist flag, not a weakness -> "Watched" column)
            risk_factor_types = sorted({rf["type"] for e in dc_entities for rf in (e.get("riskFactors") or []) if rf["type"] != "WATCHED"})



            #################################### Part 5: Obtaining Mac Addresses ->

            # Sensor device_id is the Falcon AID -> Hosts API carries the MAC used to match VCenter
            empty = "-"
            aids = sorted({s["device_id"] for s in sensors if s.get("device_id")} | {e["agentId"] for e in dc_entities if e.get("agentId")})

            macs_by_aid = {}
            if aids:
                response = Hosts(client_id=CLIENT_ID, client_secret=SECRET_ID).get_device_details(ids=aids)
                # 404 is a partial result: some AIDs no longer exist in Hosts, the others are still returned
                if response["status_code"] not in (200, 404): print(f"Hosts API returned status code {response['status_code']}. Mac Address left empty.")
                for item in (response["body"].get("resources") or []):
                    macs_by_aid[item["device_id"]] = sorted({mac.replace("-", ":") for mac in (item.get("mac_address", ""), item.get("connection_mac_address", "")) if mac})



            #################################### Part 6: Executing NGSIEM Query (DC Service Health) ->

            # Start the search job
            falcon_siem = NGSIEM(client_id=CLIENT_ID, client_secret=SECRET_ID)
            response_start = falcon_siem.start_search(repository="search-all", query_string=NGSIEM_QUERY, start=start_ms, end=end_ms)

            health_by_aid = {}
            if response_start["status_code"] != 200: print(f"NGSIEM returned status code {response_start['status_code']}. Service health left empty.")
            else:

                # Poll until the job is complete
                while True:
                    response_status = falcon_siem.get_search_status(repository="search-all", id=response_start["resources"]["id"])
                    body = response_status["body"]
                    if body.get("cancelled"): raise RuntimeError(f"NGSIEM search cancelled: {body}")
                    if body.get("done"): raw_events = body.get("events", []); break
                    time.sleep(3)

                # Index service health by aid (matches the sensor device_id)
                health_by_aid = {event["Domain Controller.Sensor Id"]: event for event in raw_events if event.get("Domain Controller.Sensor Id")}



            #################################### Part 7: Extracting Fields ->

            hosts = []

            # Map a raw config value to Ok / Attention
            def item(value, ok_value):
                if value in (None, "", empty): return empty
                return "Ok" if str(value).lower() == ok_value else "Attention"

            # Risk factor label: LDAP_SIGNING_DISABLED -> LDAP Signing Disabled (acronyms kept)
            acronyms = {"MFA", "AD", "RPC", "KRBTGT", "LDAP", "LDAPS", "NTLM", "SMB", "SPN", "OS", "IP", "DC", "VPN", "RDP", "UPN", "SID", "SPNS"}
            def risk_label(risk_factor):
                return " ".join(("SPNs" if w == "SPNS" else w) if w in acronyms else w.capitalize() for w in risk_factor.split("_"))

            # Risk factor columns for a DC entity: Attention when the factor is present
            def risk_items(entity):
                present = {rf["type"] for rf in (entity.get("riskFactors") or [])} if entity else None
                return {f"Item: {risk_label(rf)}": (empty if present is None else "Attention" if rf in present else "Ok") for rf in risk_factor_types}

            # Risk score follows the highest-scoring factor -> that factor explains the score (watchlist flag ignored)
            def top_risk_factor(entity):
                factors = [rf for rf in ((entity or {}).get("riskFactors") or []) if rf["type"] != "WATCHED"]
                return risk_label(max(factors, key=lambda rf: rf.get("score") or 0)["type"]) if factors else empty

            # Convert heartbeat epoch ms to local date (UTC-3)
            def format_heartbeat(ts):
                if not ts: return empty
                return (datetime.datetime.fromtimestamp(ts / 1000, tz=datetime.timezone.utc) - datetime.timedelta(hours=3)).strftime("%Y-%m-%d")

            # Convert NGSIEM epoch ms to local datetime (UTC-3)
            def format_ms(ts):
                try: return (datetime.datetime.fromtimestamp(float(ts) / 1000, tz=datetime.timezone.utc) - datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                except (TypeError, ValueError): return empty

            # NGSIEM numbers arrive as strings: round them (digits=0 -> integer)
            def number(value, digits=1):
                try: return round(float(value), digits) if digits else int(float(value))
                except (TypeError, ValueError): return empty

            # Service health columns (NGSIEM): resource usage is reported as numbers only, no Ok / Attention
            def health_fields(health):
                health = health or {}
                return {
                    "IdP Service Status": health.get("Cloud Connectivity.IdP Service Status", empty),
                    "IdP Last Checked": format_ms(health.get("Cloud Connectivity.Last Checked")),
                    "Traffic Inspection Status": health.get("Traffic Inspection.Status", empty),
                    "Traffic Inspection Configuration": health.get("Traffic Inspection.Configuration", empty),
                    "Traffic Inspection Enforcement": health.get("Traffic Inspection.Enforcement", empty),
                    "Inspected Requests (7d)": number(health.get("Traffic Inspection.Insp. Reqs (7d)"), 0),
                    "CPU Cores": number(health.get("CPU.Cores (Logical)"), 0),
                    "CPU Avg Usage (%)": number(health.get("CPU.Avg Usage (%)")),
                    "CPU Max Usage (%)": number(health.get("CPU.Max Usage (%)")),
                    "Memory Total (GB)": number(health.get("Memory.Total (GB)")),
                    "Memory Avg Usage (%)": number(health.get("Memory.Avg Usage (%)")),
                    "Memory Max Usage (%)": number(health.get("Memory.Max Usage (%)")),
                    "Storage Total (GB)": number(health.get("Storage.Total (GB)")),
                    "Storage Used (GB)": number(health.get("Storage.Used (GB)")),
                    "Storage Available (GB)": number(health.get("Storage.Available (GB)")),
                }

            # Service health items (NGSIEM)
            def health_items(health):
                health = health or {}
                return {
                    "Item: IdP Service": item(health.get("Cloud Connectivity.IdP Service Status"), "healthy"),
                    "Item: Traffic Inspection Status": item(health.get("Traffic Inspection.Status"), "enabled"),
                    "Item: Traffic Inspection Enforcement": item(health.get("Traffic Inspection.Enforcement"), "enabled"),
                    "Item: Service Health Alerts": item(health.get("Service Health Alert.Total"), "0"),
                }

            # Sensor device_id is the entity agentId
            entity_by_aid = {e["agentId"]: e for e in dc_entities if e.get("agentId")}
            matched_entities = set()

            # Sensors: one row per DC with a sensor
            for sensor in sensors:

                entity = entity_by_aid.get(sensor.get("device_id"))
                if entity: matched_entities.add(entity["entityId"])
                health = health_by_aid.get(sensor.get("device_id"))

                hosts.append({
                    "Department": empty,
                    "Server VM": empty,
                    "Last Seen": format_heartbeat(sensor.get("heartbeat_time")),
                    "Sensor Id": sensor.get("device_id", empty),
                    "Host Name": sensor.get("hostname", empty),
                    "Mac Address": macs_by_aid.get(sensor.get("device_id"), [empty]),
                    "Domain": (sensor.get("machine_domain") or empty).lower(),
                    "Local Ip": sensor.get("local_ip", empty),
                    "OS Version": sensor.get("os_version", empty),
                    "Agent Version": sensor.get("agent_version", empty),
                    "IDP Policy": sensor.get("idp_policy_name", empty),
                    "Status": sensor.get("status", empty).replace("status.", "").capitalize(),
                    "Status Causes": ", ".join(sensor.get("status_causes") or []) or empty,
                    "New Enforcement Mode": sensor.get("new_enforcement_mode", empty).capitalize(),
                    "Group Policy Object": sensor.get("group_policy_object", empty).capitalize(),
                    **health_fields(health),
                    "Watched": entity.get("watched", empty) if entity else empty,
                    "Risk Score": entity.get("riskScore", empty) if entity else empty,
                    "Risk Severity": entity.get("riskScoreSeverity", empty).capitalize() if entity else empty,
                    "Top Risk Factor": top_risk_factor(entity),
                    "Item: Sensor Installed": "Ok",
                    "Item: Sensor Status": item(sensor.get("status"), "status.active"),
                    "Item: Kerberos": item(sensor.get("kerberos_config"), "enforcement"),
                    "Item: NTLM": item(sensor.get("ntlm_config"), "enforcement"),
                    "Item: LDAP": item(sensor.get("ldap_config"), "enforcement"),
                    "Item: LDAPS": item(sensor.get("ldaps_config"), "on"),
                    "Item: SMB to DC": item(sensor.get("smb_to_dc_config"), "enforcement"),
                    "Item: RDP to DC": item(sensor.get("rdp_to_dc_config"), "on"),
                    "Item: Directory Auditing": item(sensor.get("directory_auditing"), "true"),
                    "Item: Traffic Inspection": item(sensor.get("ti_enabled"), "true"),
                    **health_items(health),
                    **risk_items(entity),
                })

            # DCs seen by Identity Protection without a sensor: coverage gap (same columns as sensor rows, sensor fields empty)
            sensor_columns = list(hosts[0].keys()) if hosts else []

            for entity in dc_entities:
                if entity["entityId"] in matched_entities: continue

                # Domain in lowercase, same as the sensor rows (AD sends it uppercase)
                domains = sorted({a["domain"].lower() for a in (entity.get("accounts") or []) if a.get("domain")})
                last_activity = entity.get("mostRecentActivity")

                hosts.append({
                    **{column: empty for column in sensor_columns},
                    "Last Seen": last_activity[:10] if last_activity else empty,
                    "Sensor Id": entity.get("agentId") or empty,
                    "Host Name": entity.get("hostName") or entity.get("primaryDisplayName", empty),
                    "Mac Address": macs_by_aid.get(entity.get("agentId"), [empty]),
                    "Domain": ", ".join(domains) or empty,
                    "Local Ip": entity.get("lastIpAddress") or empty,
                    "OS Version": (entity.get("operatingSystemInfo") or {}).get("displayName", empty),
                    **health_fields(health_by_aid.get(entity.get("agentId"))),
                    "Watched": entity.get("watched", empty),
                    "Risk Score": entity.get("riskScore", empty),
                    "Risk Severity": entity.get("riskScoreSeverity", empty).capitalize(),
                    "Top Risk Factor": top_risk_factor(entity),
                    "Item: Sensor Installed": "Attention",
                    **health_items(health_by_aid.get(entity.get("agentId"))),
                    **risk_items(entity),
                })



            #################################### Part 8: Departments Population & Unwatched Separation ->

            # Match each DC to a vcenter record by MAC; matched DCs get their department, unmatched are set aside
            matched_hosts = []
            unmatched_hosts = []

            # Build a lookup: mac_address -> vcenter record
            vcenter_by_mac = {}
            for v in data_vcenter:
                for mac in v.get("Mac Address", []):
                    if mac != empty:
                        vcenter_by_mac[mac.lower()] = v

            for item_host in hosts:
                macs = [m for m in item_host.get("Mac Address", []) if m != empty]
                vcenter = next((vcenter_by_mac[m.lower()] for m in macs if m.lower() in vcenter_by_mac), None)

                if vcenter:
                    item_host["Department"] = vcenter.get("Department", empty)
                    item_host["Server VM"] = vcenter.get("Asset VM", empty)
                    matched_hosts.append(item_host)
                else:
                    unmatched_hosts.append(item_host)



            #################################### Part 9: Saving the information ->

            # Save a set of DC records to a CSV (adds the reference stamp columns last)
            def save_csv(records, dir, project):
                if not records: return
                dataframe = pd.DataFrame(records).fillna(empty)

                # Reference stamp columns — always last
                dataframe["Reference Month"] = current_date.strftime("%m")
                dataframe["Reference Year"] = current_date.strftime("%Y")
                dataframe["Reference Date"] = current_date.strftime("%Y-%m-%d")

                dataframe.to_csv(os.path.join(dir, f"{project}.csv"), index=False, encoding="utf-8-sig")

            # Saving data
            save_csv(matched_hosts, dir_to_save_csv, PROJECT)
            save_csv(unmatched_hosts, dir_to_save_csv_unwatched, PROJECT_CHILD_01)


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
