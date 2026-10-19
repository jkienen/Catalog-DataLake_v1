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
PROJECT = "HealthIDP-Users"

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

# GraphQL query: every non-archived user with its AD / Entra ID accounts and risk factors
USERS_QUERY = """
query ($after: Cursor) {
  entities(types: [USER], archived: false, first: 1000, after: $after) {
    nodes {
      entityId primaryDisplayName riskScore riskScoreSeverity watched riskFactors { type score }
      roles { type }
      privileged: hasRole(type: AdminAccountRole)
      ... on UserEntity { emailAddresses mostRecentActivity }
      associations { bindingType ... on OriginAssociation { entity { primaryDisplayName ... on EndpointEntity { hostName } } } }
      accounts {
        __typename
        ... on ActiveDirectoryAccountDescriptor { domain ou department title enabled lockoutTime expirationTime samAccountName upn passwordAttributes { lastChange mayExpire } containingGroupIds flattenedContainingGroupIds }
        ... on AzureSsoUserAccountDescriptor { department title enabled dataSourceLoginIdentifier }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
""".strip()

# GraphQL query: endpoints with local administrators (domain users or domain groups), collected by the Falcon sensor
LOCAL_ADMINS_QUERY = """
query ($after: Cursor) {
  entities(types: [ENDPOINT], archived: false, associationBindingTypes: [LOCAL_ADMINISTRATOR], first: 500, after: $after) {
    nodes {
      primaryDisplayName ... on EndpointEntity { hostName }
      associations { bindingType ... on LocalAdminDomainEntityAssociation { entity { entityId type primaryDisplayName } } }
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



            #################################### Part 3: Obtaining Users ->

            # Every user entity, paginated by cursor
            users, after = [], None
            while True:
                response = falcon.graphql(query=USERS_QUERY, variables={"after": after})

                if response["status_code"] != 200:
                    print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                    raise SystemExit(1)

                if response["body"].get("errors"): print(f"GraphQL errors: {response['body']['errors']}"); break
                data = response["body"]["data"]["entities"]
                users += data.get("nodes") or []
                if not data["pageInfo"]["hasNextPage"]: break
                after = data["pageInfo"]["endCursor"]

            # Every risk factor found on any user becomes an "Item:" column (WATCHED is a watchlist flag, not a weakness -> "Watched" column)
            risk_factor_types = sorted({rf["type"] for u in users for rf in (u.get("riskFactors") or []) if rf["type"] != "WATCHED"})



            #################################### Part 4: Obtaining Local Administrators ->

            # Endpoints with local administrators, paginated by cursor
            admin_endpoints, after = [], None
            while True:
                response = falcon.graphql(query=LOCAL_ADMINS_QUERY, variables={"after": after})
                if response["body"].get("errors"): print(f"GraphQL errors: {response['body']['errors']}"); break
                data = response["body"]["data"]["entities"]
                admin_endpoints += data.get("nodes") or []
                if not data["pageInfo"]["hasNextPage"]: break
                after = data["pageInfo"]["endCursor"]

            # Local admin is granted to a user directly or to a domain group the user belongs to
            admin_machines_by_user = {}   # user entityId  -> machine names
            admin_machines_by_group = {}  # group entityId -> machine names
            group_names = {}
            for endpoint in admin_endpoints:
                machine = endpoint.get("hostName") or endpoint.get("primaryDisplayName")
                for association in endpoint.get("associations") or []:
                    admin = association.get("entity") if association.get("bindingType") == "LOCAL_ADMINISTRATOR" else None
                    if not admin: continue
                    if admin["type"] == "USER": admin_machines_by_user.setdefault(admin["entityId"], set()).add(machine)
                    else:
                        admin_machines_by_group.setdefault(admin["entityId"], set()).add(machine)
                        group_names[admin["entityId"]] = admin["primaryDisplayName"]



            #################################### Part 5: Extracting Fields ->

            empty = "-"
            records = []

            # Readable label: DomainAdminsRole -> Domain Admins Role, ACCOUNT_WITHOUT_MFA_CONFIGURED -> Account Without MFA Configured
            acronyms = {"MFA", "AD", "RPC", "KRBTGT", "LDAP", "LDAPS", "NTLM", "SMB", "SPN", "OS", "IP", "DC", "VPN", "RDP", "UPN", "SID", "SPNS"}
            def label(value):
                words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(value)).replace("_", " ").split()
                return " ".join(("SPNs" if w.upper() == "SPNS" else w.upper()) if w.upper() in acronyms else w.capitalize() for w in words)

            # Convert GraphQL ISO datetime to local date (UTC-3)
            def format_date(value):
                if not value: return empty
                date = datetime.datetime.fromisoformat(value.replace("Z", "+00:00")) - datetime.timedelta(hours=3)
                return date.strftime("%Y-%m-%d")

            # Risk factor columns: Attention when the factor is present
            def risk_items(user):
                present = {rf["type"] for rf in (user.get("riskFactors") or [])}
                return {f"Item: {label(rf)}": "Attention" if rf in present else "Ok" for rf in risk_factor_types}

            # Risk score follows the highest-scoring factor -> that factor explains the score (watchlist flag ignored)
            def top_risk_factor(user):
                factors = [rf for rf in (user.get("riskFactors") or []) if rf["type"] != "WATCHED"]
                return label(max(factors, key=lambda rf: rf.get("score") or 0)["type"]) if factors else empty

            # Domain in lowercase (AD sends it uppercase, sensors lowercase); Entra ID only users take their login suffix
            def user_domain(ad, entra):
                if ad: domain = ad.get("domain") or ""
                else: domain = (entra.get("dataSourceLoginIdentifier") or "").rpartition("@")[2]
                return domain.lower() or empty

            # Classification roles are shown as Account Type; every other role is a privilege
            classification_roles = {"HumanUserAccountRole": "Human", "ProgrammaticUserAccountRole": "Programmatic"}

            # Owned machines and local admin rights of a user (group-granted machines are only counted, never listed)
            def machine_fields(user, ad):
                owned = sorted({a["entity"].get("hostName") or a["entity"].get("primaryDisplayName")
                                for a in (user.get("associations") or []) if a.get("bindingType") == "OWNERSHIP"})
                direct = admin_machines_by_user.get(user["entityId"], set())
                groups = [g for g in set(ad.get("containingGroupIds") or []) | set(ad.get("flattenedContainingGroupIds") or []) if g in admin_machines_by_group]
                via_groups = set().union(*(admin_machines_by_group[g] for g in groups))
                admin_owned = sorted(m for m in owned if m in direct or m in via_groups)
                return {
                    "Owned Machines": ", ".join(owned) or empty,
                    "Local Admin": bool(direct or via_groups),
                    "Local Admin Machines": ", ".join(sorted(direct)) or empty,
                    "Local Admin Groups": ", ".join(sorted(f"{group_names[g]} ({len(admin_machines_by_group[g])})" for g in groups)) or empty,
                    "Local Admin Machines (Total)": len(direct | via_groups),
                    "Local Admin On Owned Machines": ", ".join(admin_owned) or empty,
                }

            for user in users:

                accounts = user.get("accounts") or []
                ad = next((a for a in accounts if a.get("__typename") == "ActiveDirectoryAccountDescriptor"), {})
                entra = next((a for a in accounts if a.get("__typename") == "AzureSsoUserAccountDescriptor"), {})
                password = ad.get("passwordAttributes") or {}
                roles = [r["type"] for r in (user.get("roles") or [])]

                records.append({
                    "Department": ad.get("department") or entra.get("department") or empty,
                    "Title": ad.get("title") or entra.get("title") or empty,
                    "Display Name": user.get("primaryDisplayName", empty),
                    "Account": ad.get("samAccountName") or empty,
                    "UPN": ad.get("upn") or entra.get("dataSourceLoginIdentifier") or empty,
                    "Email": (user.get("emailAddresses") or [empty])[0],
                    "Domain": user_domain(ad, entra),
                    "OU": ad.get("ou") or empty,
                    "Account Source": " + ".join(s for s, a in (("AD", ad), ("Entra ID", entra)) if a) or empty,
                    "Account Type": ", ".join(classification_roles[r] for r in roles if r in classification_roles) or empty,
                    "Privileged": bool(user.get("privileged")),
                    "Privileged Roles": ", ".join(label(r).removesuffix(" Role") for r in roles if r not in classification_roles) or empty,
                    "AD Enabled": ad.get("enabled", empty) if ad else empty,
                    "Entra ID Enabled": entra.get("enabled", empty) if entra else empty,
                    "Locked": bool(ad.get("lockoutTime")) if ad else empty,
                    "Account Expires": format_date(ad.get("expirationTime")),
                    "Password Last Change": format_date(password.get("lastChange")),
                    "Password Never Expires": (not password["mayExpire"]) if "mayExpire" in password else empty,
                    "Last Activity": format_date(user.get("mostRecentActivity")),
                    **machine_fields(user, ad),
                    "Watched": user.get("watched", empty),
                    "Risk Score": user.get("riskScore", empty),
                    "Risk Severity": (user.get("riskScoreSeverity") or empty).capitalize(),
                    "Top Risk Factor": top_risk_factor(user),
                    **risk_items(user),
                })



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
