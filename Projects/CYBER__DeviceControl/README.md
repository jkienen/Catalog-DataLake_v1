# Device Control (USB)

>Keeps CrowdStrike's USB Device Control exceptions honest: it builds the usage history Falcon does not keep on its own, so an exception nobody uses anymore can be found and revoked instead of sitting open indefinitely.

---

## Why This Project Exists

**Situation:** CrowdStrike Falcon lets specific USB hardware bypass the default block policy, but only keeps usage history for **7 days**; past that, there's no way to tell if a months-old exception is still in use.

**Task:** Build a usage history that outlives Falcon's 7-day window, so exceptions can be checked against real usage instead of staying open indefinitely.

**Action:** Every 7 days, one script pulls USB/removable-storage events from NGSIEM into a rolling 3 or 6-month history. A second pulls the current exceptions from Falcon's Device Control policies. A third cross-references both, flagging each exception active or dormant with the machines and dates that prove it, feeding the automation that revokes what nobody uses.

**Result:** The check goes from impossible — the data needed simply doesn't survive past 7 days on the platform — to automatic, replacing roughly **8 hours per review** of manual work per analyst.

---

## Scripts

<table width="100%">
<thead>
<tr><th>Script<div><img width="400" height="1" alt=""></div></th><th>What it does<div><img width="800" height="1" alt=""></div></th></tr>
</thead>
<tbody>
<tr><td><code>Scripts/Falcon/1. Extract_Weekly_Usage.py</code></td><td>Authenticates to Falcon and runs an NGSIEM query for the last 7 days of USB/removable-storage events (connected, blocked, policy violation). Appends the new events to the rolling usage history, deduplicates, and drops anything older than 6 months.</td></tr>
<tr><td><code>Scripts/Falcon/2. Extract_USB_Devices.py</code></td><td>Authenticates to Falcon and pulls every Device Control policy, flattening each USB exception (by vendor/product/serial) into one row: the current allow-list.</td></tr>
<tr><td><code>Scripts/3. Generate_USB-Audit-Usage.py</code></td><td>Cross-references the exceptions against the accumulated usage history, matching each one by its combined ID, or by vendor+product+serial, or by vendor+product alone, depending on what the exception itself declares. Outputs one audit row per exception: active or dormant, last seen, and on which machines.</td></tr>
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

Run on a weekly schedule, so no usage window is lost to Falcon's 7-day retention:

```
python './Falcon/1. Extract_Weekly_Usage.py'
python './Falcon/2. Extract_USB_Devices.py'
python './3. Generate_USB-Audit-Usage.py'
```

```
deactivate
```
