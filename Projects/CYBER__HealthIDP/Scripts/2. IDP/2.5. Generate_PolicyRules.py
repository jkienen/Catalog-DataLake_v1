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
PROJECT = "HealthIDP-PolicyRules"

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

# GraphQL query: name of the users, groups and endpoints a policy rule condition points to
ENTITIES_QUERY = """
query ($ids: [UUID!], $after: Cursor) {
  entities(entityIds: $ids, first: 1000, after: $after) {
    nodes { entityId primaryDisplayName ... on EndpointEntity { hostName } }
    pageInfo { hasNextPage endCursor }
  }
}
""".strip()

# Policy rule matches are only exposed as timeline events -> read the whole history
HISTORY_START = "2020-01-01T00:00:00Z"

# GraphQL query: every policy rule match (which rule, when, in which mode and with which result)
MATCHES_QUERY = """
query ($start: DateTimeInput, $after: Cursor) {
  timeline(types: [POLICY_RULE_MATCH], startTime: $start, first: 1000, after: $after, sortOrder: ASCENDING) {
    nodes { timestamp ... on TimelinePolicyRuleMatchEvent { ruleId ruleName simulationMode successful } }
    pageInfo { hasNextPage endCursor }
  }
}
""".strip()

# Policy rule condition (block.field) -> column, in the order the columns are written;
# a condition not listed here gets a column of its own, named from its path
CONDITION_COLUMNS = {
    "activity.accessType": "Access Type",
    "activity.protocolType": "Protocol",
    "activity.baseline": "Baseline",
    "sourceUser.accountType": "Source User Type",
    "sourceUser.attributes": "Source User Attributes",
    "sourceUser.privileges": "Source User Privileges",
    "sourceUser.entityId": "Source Users",
    "sourceUser.groupMembership": "Source User Groups",
    "sourceEndpoint.attributes": "Source Endpoint Attributes",
    "sourceEndpoint.entityId": "Source Endpoints",
    "sourceEndpoint.groupMembership": "Source Endpoint Groups",
    "destination.endpointRole": "Destination Roles",
    "destination.entityId": "Destinations",
    "destination.groupMembership": "Destination Groups",
}

# Condition fields whose options are entity ids (users, groups, endpoints), shown by name
ENTITY_FIELDS = {"entityId", "groupMembership"}

# Words kept in capitals when an API enum becomes readable text
ACRONYMS = {"MFA", "OTP", "SMB", "RDP", "NTLM", "LDAP", "LDAPS", "SSO", "AD", "DC"}



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



            #################################### Part 3: Obtaining Policy Rules ->

            # Every rule id (the query takes no paging - it returns them all), then their details, 100 ids per call
            response = falcon.query_policy_rules()

            if response["status_code"] != 200:
                print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                raise SystemExit(1)

            rule_ids = response["body"]["resources"] or []

            rules = []
            for start in range(0, len(rule_ids), 100):
                response = falcon.get_policy_rules(ids=rule_ids[start:start + 100])
                if response["status_code"] != 200: print(f"Policy rule details returned status code {response['status_code']}. Those rules are left out."); continue
                rules += response["body"]["resources"] or []



            #################################### Part 4: Obtaining Policy Rule Matches ->

            # Every match event, oldest first, paginated by cursor (a failed query leaves the match columns as "-")
            matches, after = [], None
            while True:
                response = falcon.graphql(query=MATCHES_QUERY, variables={"start": HISTORY_START, "after": after})
                if response["body"].get("errors"): print(f"GraphQL errors: {response['body']['errors']}. Match columns left as '-'."); matches = None; break
                data = response["body"]["data"]["timeline"]
                matches += data.get("nodes") or []
                if not data["pageInfo"]["hasNextPage"]: break
                after = data["pageInfo"]["endCursor"]



            #################################### Part 5: Resolving Entity Names ->

            # Conditions keep users, groups and endpoints as entity ids (the keys of their options)
            entity_ids = sorted({key for rule in rules for condition in (rule.get("ruleConditions") or [])
                                 for block in condition.values() if isinstance(block, dict)
                                 for field, setting in block.items() if field in ENTITY_FIELDS and isinstance(setting, dict)
                                 for key in (setting.get("options") or {})})

            # Entity id -> name, paginated by cursor (an endpoint by its host name, anything else by its display name)
            entity_names, after = {}, None
            while entity_ids:
                response = falcon.graphql(query=ENTITIES_QUERY, variables={"ids": entity_ids, "after": after})
                if response["body"].get("errors"): print(f"GraphQL errors: {response['body']['errors']}. Entity ids left unresolved."); break
                data = response["body"]["data"]["entities"]
                for node in data.get("nodes") or []:
                    entity_names[node["entityId"]] = node.get("hostName") or node.get("primaryDisplayName")
                if not data["pageInfo"]["hasNextPage"]: break
                after = data["pageInfo"]["endCursor"]



            #################################### Part 6: Extracting Fields ->

            empty = "-"
            records = []

            # Convert GraphQL ISO datetime to local date (UTC-3)
            def format_date(value):
                if not value: return empty
                date = datetime.datetime.fromisoformat(value.replace("Z", "+00:00")) - datetime.timedelta(hours=3)
                return date.strftime("%Y-%m-%d")

            # Match timestamps per rule id; "recent" means inside the last 30 days, counted from the run
            matches_by_rule = {}
            for match in matches or []:
                if match.get("timestamp"): matches_by_rule.setdefault(match.get("ruleId"), []).append(match["timestamp"])
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
            def recent(timestamp): return datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00")) >= cutoff

            # Readable label: REMOTE_DESKTOP -> Remote Desktop, AdminAccountRole -> Admin Account, ServerRole -> Server (acronyms kept)
            def label(value):
                words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(value)).replace("_", " ").split()
                return " ".join(w.upper() if w.upper() in ACRONYMS else w.capitalize() for w in words).removesuffix(" Role")

            # Column of a condition: CONDITION_COLUMNS, or its path as readable text (sourceUser.newField -> Source User New Field)
            def condition_column(path):
                return CONDITION_COLUMNS.get(path) or label(path.replace(".", "_"))

            # Conditions of a rule, by column: included options first, excluded ones prefixed "Not ", entities by name
            # (an entity the GraphQL lookup did not return keeps its id)
            def rule_conditions(rule):
                options = {}
                for condition in rule.get("ruleConditions") or []:
                    for block_name, block in condition.items():
                        if not isinstance(block, dict): continue
                        for field, setting in block.items():
                            if not isinstance(setting, dict) or "options" not in setting: continue
                            column = options.setdefault(condition_column(f"{block_name}.{field}"), {"INCLUDED": set(), "EXCLUDED": set()})
                            for key, state in (setting.get("options") or {}).items():
                                text = entity_names.get(key, key) if field in ENTITY_FIELDS else label(key)
                                column.setdefault(state, set()).add(text)
                return {column: ", ".join(sorted(values["INCLUDED"]) + [f"Not {v}" for v in sorted(values["EXCLUDED"])]) or empty
                        for column, values in options.items()}

            conditions_by_rule = {rule.get("_id"): rule_conditions(rule) for rule in rules}

            # Known conditions always get their column, in CONDITION_COLUMNS order; any other one found comes after them
            condition_columns = list(CONDITION_COLUMNS.values())
            condition_columns += sorted({c for conditions in conditions_by_rule.values() for c in conditions} - set(condition_columns))

            for rule in rules:

                action = (rule.get("ruleAction") or {}).get("action")
                mfa = ((rule.get("ruleAction") or {}).get("globalProperties") or {}).get("MFA") or {}
                indicator = rule.get("indicatorNotification") or {}
                email = rule.get("emailNotification") or {}
                conditions = conditions_by_rule.get(rule.get("_id"), {})
                rule_matches = matches_by_rule.get(rule.get("_id"), [])

                records.append({
                    "Rule Id": rule.get("_id", empty),
                    "Rule Name": rule.get("name", empty),
                    "Enabled": rule.get("enabled", empty),
                    "Simulation Mode": rule.get("simulationMode", empty),
                    "Action": label(action) if action else empty,
                    **{column: conditions.get(column, empty) for column in condition_columns},
                    "MFA Connector": ", ".join(label(d["connectorType"]) for d in mfa.get("mfaConnectorDescriptors") or []) or empty if action == "MFA" else empty,
                    "MFA Factors": ", ".join(label(f) for f in mfa.get("mfaFactorTypes") or []) or empty if action == "MFA" else empty,
                    "Indicator Notification": indicator.get("enabled", empty),
                    "Indicator Severity": label((indicator.get("properties") or {}).get("severity") or empty) if indicator.get("enabled") else empty,
                    "Email Notification": email.get("enabled", empty),
                    "Matches": len(rule_matches) if matches is not None else empty,
                    "Matches (30d)": sum(recent(t) for t in rule_matches) if matches is not None else empty,
                    "Last Match": format_date(max(rule_matches)) if rule_matches else empty,
                    "Item: Enforced": "Ok" if rule.get("enabled") and not rule.get("simulationMode") else "Attention",
                })



            #################################### Part 7: Saving the information ->

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
