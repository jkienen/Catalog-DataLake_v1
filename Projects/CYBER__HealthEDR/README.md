# EDR Health Check

> Turns a day of manual CrowdStrike auditing into an automated report: sensor health, policy coverage, and exclusions, cross-referenced against the real server inventory.

---

## Why This Project Exists

**Situation:** Building a CrowdStrike EDR health-check report (sensor health, security best practices, configured exceptions) took an analyst roughly **8 hours**, a full day, on a monthly or weekly cadence, and it had to be rebuilt per client. At a day each, doing it by hand for every client stops being feasible.

**Task:** Automate that report so it protects the endpoint perimeter the way the manual version did (sensor status, policy exceptions, security best practices), without costing a day of analyst time per client.

**Action:** One script pulls the real server inventory from VCenter, the source of truth for which VM belongs to which department. A second pulls every host from CrowdStrike Falcon, its assigned policies and its sensor-health signals, cross-referencing it against that inventory to attribute it correctly; whatever cannot be matched is set aside instead of silently dropped. A third pulls every exclusion configured in Falcon, the exceptions that could otherwise quietly weaken protection without anyone noticing.

**Result:** The manual report is gone, and what replaced it didn't just save the analyst's **day per client**: the automated reports come out to a noticeably more consistent standard than the manual ones ever did.

---

## Scripts

<table width="100%">
<thead>
<tr><th>Script<div><img width="400" height="1" alt=""></div></th><th>What it does<div><img width="800" height="1" alt=""></div></th></tr>
</thead>
<tbody>
<tr><td><code>Scripts/1. VCenter/1.1. Extract_Assets.py</code></td><td>Pulls the VM inventory from VCenter (hostname, MAC address, department), skipping templates. This is the source of truth used to attribute every monitored endpoint to the right department.</td></tr>
<tr><td><code>Scripts/2. EDR/2.1. Generate_Assets.py</code></td><td>Pulls every host from CrowdStrike Falcon: its assigned policies (Prevention, Device Control, Firewall, Sensor Update, Content Update) and its Zero Trust Assessment sensor-health signals, including Reduced Functionality Mode. Cross-references each host against the VCenter inventory by MAC address to assign it a department; hosts it cannot match are set aside in a separate "Unwatched" file per OS instead of silently dropped.</td></tr>
<tr><td><code>Scripts/2. EDR/2.2. Generate_Exclusions.py</code></td><td>Pulls every exclusion configured in Falcon (IOA, Sensor Visibility, and ML): the specific processes, paths or files exempted from detection or prevention, one report per exclusion type.</td></tr>
</tbody>
</table>

---

## Setup

**Windows**

```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux**

```
python3 -m venv .venv
source .venv/bin/activate
```

(Skip this step if `.venv` already exists.)

---

## Usage

```
cd Scripts
pip install -r requirements.txt
```

Run the VCenter extraction first: the EDR script depends on it to attribute hosts to a department.

```
python './1. VCenter/1.1. Extract_Assets.py'
python './2. EDR/2.1. Generate_Assets.py'
python './2. EDR/2.2. Generate_Exclusions.py'
```

```
deactivate
```
