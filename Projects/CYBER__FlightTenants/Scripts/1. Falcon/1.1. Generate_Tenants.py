#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import re
import requests
import datetime
import pandas as pd
from collections import Counter
from falconpy import OAuth2, FlightControl, Hosts, UserManagement

# ----------------------------------------->

# Results
PROJECT = "FlightTenants"

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

# Flight Control page size (children per query and per lookup)
PAGE_SIZE = 100

# Falcon module -> roles only available in a CID where the module is enabled (a role ending in "_" is a prefix)
# Next-Gen SIEM shares its roles with Falcon Log Management, Discover with Falcon for IT, and Falcon Prevent is the platform base
MODULE_ROLES = {
    "Module: Falcon Cloud Security": ("horizon_", "cspg_", "cspm_", "kubernetes_", "image_"),
    "Module: Falcon Data Protection": ("data_protection_",),
    "Module: Falcon Device Control": ("device_control_manager",),
    "Module: Falcon Discover": ("discover_",),
    "Module: Falcon Firewall Management": ("firewall_manager",),
    "Module: Falcon for IT": ("falcon_for_it_",),
    "Module: Falcon for Mobile": ("mobile_admin",),
    "Module: Falcon Forensics": ("forensic_",),
    "Module: Falcon Identity Threat Protection": ("identity_protection_", "idp_"),
    "Module: Falcon Insight XDR": ("falconhost_investigator", "event_viewer"),
    "Module: Falcon Next-Gen SIEM": ("xdr_",),
    "Module: Falcon Prevent": ("prevention_policy_manager",),
    "Module: Falcon Spotlight": ("vulnerability_manager",),
}

# Roles that are not an indicator of a monitored module: the platform base, modules left out, or roles available without the module
OTHER_ROLES = {
    "action_requests_manager", "action_requests_rejector", "adversary_intelligence_admin", "adversary_intelligence_analyst",
    "app_developer", "app_user", "aspm_admin", "aspm_analyst", "aspm_read_only", "aspm_tam", "attackpath_analyst",
    "billing_dashboard_admin", "binarly_admin", "binarly_user", "charlotte_ai_agent_author", "charlotte_ai_analyst",
    "charlotte_ai_auditor", "charlotte_ai_promptbook_manager", "charlotte_ai_usage_monitor", "cloud_inventory_read",
    "cloud_registration_admin", "cloud_registration_analyst", "configvantage_analyst", "configvantage_manager",
    "connector_manager", "connector_viewer", "content_control_manager", "crowdstrike_mcp_user", "crowdstrike_mcp_user_read_only",
    "custom_ioas_manager", "dashboard_admin", "desktop_support", "endpoint_manager", "exploit_validation_manager",
    "exposure_management_manager", "falcon_console_guest", "falcon_query_manager", "falcon_query_user", "falconhost_admin",
    "falconhost_analyst", "falconhost_analyst_no_dp", "falconhost_read_only", "fc_contact_manager", "fctl_managed_analyst",
    "help_desk", "intel_admin", "intel_basic_analyst", "kestrel_scheduled_reports_admin", "kestrel_user",
    "ngsiem_federated_connection_manager", "ngsiem_federated_connection_querier", "ngsiem_federated_connection_viewer",
    "overwatch_cloud_admin", "overwatch_cloud_analyst", "overwatch_endpoint_admin", "overwatch_endpoint_analyst",
    "overwatch_malware_submitter", "premium_support_documents_viewer", "prevention_hashes_manager", "quarantine_manager",
    "recon_admin", "recon_analyst", "remediation_manager", "remote_responder", "remote_responder_one", "remote_responder_three",
    "response_workflow_author", "risk_manager", "saas_security_admin", "saas_security_owner", "saas_security_scoped_admin",
    "saas_security_scoped_user", "saas_security_viewer", "scheduled_report_admin", "scheduled_report_analyst", "security_lead",
    "surface_admin", "surface_read_only", "vault_nva_reader", "vault_nva_writer", "workflow_executor",
}



#################################### Part 1: Obtaining Authorization Token ->

# Data obtained from project file
from dotenv import load_dotenv
if os.path.exists(env_path):

    load_dotenv(env_path)

    # Get .env variables
    BASE_URL = os.getenv("BASE_URL")
    CLIENT_ID = os.getenv("CLIENT_ID")
    SECRET_ID = os.getenv("SECRET_ID")
    IDENTITY = "crowdstrike_parent_sample"

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

            # Define falcon request (the global parent CID, shared by every service)
            auth = OAuth2(client_id=CLIENT_ID, client_secret=SECRET_ID)
            flight = FlightControl(auth_object=auth)



            #################################### Part 3: Obtaining Tenants ->

            empty = "-"

            # Returns the child CIDs linked to the CID of a Flight Control session, and the status code of the query
            def query_children(flight):
                ids, offset = [], 0
                while True:
                    response = flight.query_children(limit=PAGE_SIZE, offset=offset)
                    if response["status_code"] != 200: return ids, response["status_code"]
                    page = response["body"].get("resources") or []
                    ids += page
                    offset += len(page)
                    if not page or offset >= response["body"]["meta"]["pagination"]["total"]: return ids, 200

            # Returns the Flight Control records (name, status, domains) of a list of child CIDs
            def get_children(flight, ids):
                children = []
                for start in range(0, len(ids), PAGE_SIZE):
                    response = flight.get_children(ids=ids[start:start + PAGE_SIZE])
                    children += response["body"].get("resources") or []
                return children

            # Returns a session logged into a child CID (member_cid), or None when the login fails
            def open_session(cid, tenant):
                session = OAuth2(client_id=CLIENT_ID, client_secret=SECRET_ID, member_cid=cid)
                session.login()
                if session.token_status != 201:
                    print(f"Login returned status code {session.token_status} for {tenant}.")
                    return None
                return session

            # First call proves the credentials
            parent_ids, status = query_children(flight)
            if status != 200:
                print(f"API returned status code {status}. Please validate your token (CLIENT_ID / SECRET_ID).")
                raise SystemExit(1)

            parents = get_children(flight, parent_ids)
            global_cid = parents[0]["child_of"]

            # Children of every parent, read inside the parent: one link per parent x child
            links = []
            for parent in parents:
                session = open_session(parent["child_cid"], parent["name"])
                if not session: continue
                parent_flight = FlightControl(auth_object=session)
                child_ids, status = query_children(parent_flight)
                if status != 200: print(f"Flight Control returned status code {status} for the children of {parent['name']}.")
                links += [(parent, child) for child in get_children(parent_flight, child_ids)]
                session.logout()

            links_per_child = Counter(child["child_cid"] for _, child in links)



            #################################### Part 4: Obtaining Hosts, Users and Roles ->

            # Returns the total a query reports for its smallest page, or "-" when the call fails
            def query_total(method, service, tenant):
                response = method(limit=1)
                if response["status_code"] != 200:
                    print(f"{service} returned status code {response['status_code']} for {tenant}.")
                    return empty
                return response["body"]["meta"]["pagination"]["total"]

            # Returns the hosts total, the users total and the available roles of the CID a session is logged into
            def measure(session, tenant):
                users = UserManagement(auth_object=session)
                response = users.query_roles()
                if response["status_code"] != 200: print(f"User Management returned status code {response['status_code']} for the roles of {tenant}.")
                return {
                    "Hosts Total": query_total(Hosts(auth_object=session).query_devices_by_filter_scroll, "Hosts", tenant),
                    "Users Total": query_total(users.query_users, "User Management", tenant),
                    "Roles": response["body"].get("resources") or [] if response["status_code"] == 200 else None,
                }

            # Every CID is measured once, the global with its own session and the others through member_cid
            tenants = {parent["child_cid"]: parent["name"] for parent in parents}
            tenants.update({child["child_cid"]: child["name"] for _, child in links})

            measures = {global_cid: measure(auth, "the global parent")}
            for cid, name in tenants.items():
                session = open_session(cid, name)
                measures[cid] = measure(session, name) if session else {"Hosts Total": empty, "Users Total": empty, "Roles": None}
                if session: session.logout()



            #################################### Part 5: Extracting Fields ->

            # Returns an API enum as readable text
            def label(value):
                return value.replace("_", " ").title() if value else empty

            # Returns the distinct values of a list joined by "; ", or "-" when there is none
            def join(values):
                values = list(dict.fromkeys(value for value in values if value))
                return "; ".join(values) if values else empty

            # Returns one True/False column per module, or "-" when the roles of the CID could not be read
            def modules(roles):
                if roles is None: return {column: empty for column in MODULE_ROLES}
                return {column: any(role.startswith(prefixes) for role in roles) for column, prefixes in MODULE_ROLES.items()}

            # Returns the record of one tenant under its parent
            def build_record(tenant_type, parent_name, parent_cid, tenant):
                measured = measures[tenant["child_cid"]]
                record = {
                    "Tenant Type": tenant_type,
                    "Parent Name": parent_name,
                    "Parent CID": parent_cid,
                    "Tenant Name": tenant.get("name") or empty,
                    "Tenant CID": tenant["child_cid"],
                    "Status": label(tenant.get("status")),
                    "Domains": join(tenant.get("domains") or []),
                    "Shared Tenant": links_per_child[tenant["child_cid"]] > 1,
                    "Hosts Total": measured["Hosts Total"],
                    "Users Total": measured["Users Total"],
                }
                record.update(modules(measured["Roles"]))
                return record

            # The global has no Flight Control record of its own: only its CID is known (the parent of every parent)
            records = [build_record("Global", empty, empty, {"child_cid": global_cid})]
            records += [build_record("Parent", empty, global_cid, parent) for parent in parents]
            records += [build_record("Child", parent["name"], parent["child_cid"], child) for parent, child in links]
            print(f"Tenants: 1 Global, {len(parents)} Parents, {len(links)} Children ({len(links_per_child)} distinct)")

            # Roles outside both tables (custom roles aside) may be a new module to map
            module_prefixes = tuple(prefix for prefixes in MODULE_ROLES.values() for prefix in prefixes)
            unmapped = sorted({role for measured in measures.values() for role in measured["Roles"] or []
                               if not role.startswith(module_prefixes) and role not in OTHER_ROLES and not re.fullmatch(r"[0-9a-f]{32}", role)})
            if unmapped: print(f"Roles outside the module table: {', '.join(unmapped)}")



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
