# Data Lake Documentation Catalog


> An automated, visual Data Lake, auto-filled by an AI skill + live projects documented from scratch.

---

<details style="border:1px solid #57606a;border-radius:6px;padding:12px 16px;margin-bottom:16px;">
<summary><strong>From Spreadsheet to Catalog</strong> (click to expand)</summary>

The previous version of this documentation lived in a single Excel workbook, and it did the job, until the Data Lake outgrew it:

- ⏱️ **Documenting one automation was a day of work.** An analyst had to read the code, then transcribe every endpoint, filter, transformation and KPI into the right row of the right sheet by hand. A single project could eat a full day before one automation was fully documented.
- 📈 **The workbook itself became the bottleneck.** As more endpoints, and more Silver, Gold and Automation rules were added, the sheets grew into the thousands of rows. Finding one entry, tracing a source back to its Raw endpoint, or spotting a duplicate meant scrolling and filtering across sheets that were never built to hold that much.
- 🎲 **Consistency depended on discipline, not structure.** Nothing stopped two rows from describing the same rule differently, or a field from being skipped, because a spreadsheet cell does not enforce a shape.

This version keeps every idea the workbook got right (one entry per source, rule, or automation; the same medallion architecture; an Audit layer that survives the action that erases its evidence) and changes how those entries get produced: read straight from the code by a Claude Code skill, written as structured files, and rendered as a graph instead of scrolled through as rows.

> ℹ️ The previous version of this project is available [here](https://github.com/jkienen/Catalog-DataLake_v0).

</details>

---

## Why This Matters

Automations save time, but every one of them is a decision made on someone's behalf, silently, on a schedule, using logic only the person who wrote it can see. As they multiply across teams and platforms, that convenience turns into risk:

- **No one owns the full picture.** Automations get built script by script, each with its own credentials, schedule, and hard-coded rule. Ask "what automatically deletes, tags, or closes something in production right now?" and the honest answer is usually "let me check with a few people."
- **Evidence disappears with the action.** An automation that deletes or closes a record also removes the only proof it existed. When an audit, an incident, or a customer complaint asks "why is this record gone," there is nothing to point to.
- **Duplicated effort.** Without a shared catalog, two teams solve the same problem twice, slightly differently, against the same source system, doubling the maintenance burden and the number of places a bug can hide.
- **Institutional risk.** The rule that decides what gets changed or deleted lives in one person's script, in one person's head. When that person is unavailable, nobody can safely extend, or even fully trust, what the automation does.

Every automation exists to solve one problem, and in this catalog that problem has a name: it traces back to a **project**, a folder under [`Projects/`](Projects/) holding the code the automation was built for. `CYBER__HealthEDR` exists to keep EDR sensor health above a threshold; `CYBER__DeviceControl` exists to keep USB exceptions from going stale; `CYBER__GVulnerabilities` exists to track vulnerabilities against the asset inventory. Documenting an automation without naming the problem it solves is documenting an action with no reason attached; the catalog ties the two together by construction, not by convention.

That is the case worth making to a manager: not "we documented our data," but **"we can show, at any moment, everything that acts on our systems automatically, why it does it, and what it did, before an incident forces us to find out the hard way."**

---

## Overview

As a Data Lake grows, the hardest thing to keep is not the data; it is the *knowledge* about the data: where each source comes from, how it is transformed, what each indicator means, and which automations act on it. That knowledge usually lives scattered across people, scripts, and chat history.

This catalog centralizes that knowledge as one YAML file per source, rule, audit, indicator or automation, organized around the **medallion architecture** (Raw → Silver → Gold) plus an **Audit** layer and an **Automation** layer. Every file follows the fixed template of its layer, so anyone, or the skill itself, can read or extend the documentation without guessing.

Unlike the spreadsheet, these files are not filled in by hand: a Claude Code skill reads a project dropped into the catalog and writes them for you, straight from the code.

---

## How It Works

![Data Lake architecture: sources (EDR, SIEM, PAM) flow into the Raw, Silver, and Gold layers, feeding business answers, automations, and fixes.](Catalog/Files/architecture-concept.png)

The documentation mirrors the lifecycle of the data across five layers:

<table width="100%">
<thead>
<tr><th>Layer<div><img width="200" height="1" alt=""></div></th><th>What it holds<div><img width="700" height="1" alt=""></div></th><th>Documented in<div><img width="300" height="1" alt=""></div></th></tr>
</thead>
<tbody>
<tr><td><strong>Raw</strong></td><td>Data ingested exactly as the source delivers it, with no transformation.</td><td><code>1-Raw/RAW_*.yaml</code></td></tr>
<tr><td><strong>Silver</strong></td><td>Cleaned, cross-referenced, and structured data, ready for analysis.</td><td><code>2-Silver/SILVER_*.yaml</code></td></tr>
<tr><td><strong>Audit</strong></td><td>Records the pipeline sets apart, kept inside the Silver layer's history so the evidence survives an automation acting on them.</td><td><code>3-Audits/AUDIT_*.yaml</code></td></tr>
<tr><td><strong>Gold</strong></td><td>Business indicators / KPIs derived from the Silver layer.</td><td><code>4-Gold/GOLD_*.yaml</code></td></tr>
<tr><td><strong>Automation</strong></td><td>Automated actions that read the curated data and act back on the platform it came from.</td><td><code>5-Automations/AUTOMATA_*.yaml</code></td></tr>
</tbody>
</table>

Each layer feeds the next: Raw is the input to the Silver rules, the records those rules set apart become Audits, the Silver output is consolidated into Gold indicators, and Automations consume the curated data — and the audits — to act.

---

<details style="border:1px solid #57606a;border-radius:6px;padding:12px 16px;margin-bottom:16px;">
<summary><strong>Repository Structure</strong> (click to expand)</summary>

```
Catalog-DataLake/
├── Projects/                       # The source repositories being documented, one problem per project
│   ├── CYBER__HealthEDR/
│   ├── CYBER__DeviceControl/
│   └── CYBER__GVulnerabilities/
└── Catalog/
    ├── Layers/                     # The live catalog: one YAML per dataset, rule, audit, indicator or automation
    │   └── <Client>/
    │       ├── HML/{1-Raw,2-Silver,3-Audits,4-Gold,5-Automations}/
    │       └── PRD/{1-Raw,2-Silver,3-Audits,4-Gold,5-Automations}/
    ├── Skills/
    │   ├── Catalog.md              # The Claude Code skill that documents a dropped project
    │   ├── Templates/              # The five YAML templates, one per layer
    │   └── Temp/                   # Where a dropped project is documented and reviewed before moving to Layers/
    ├── Scripts/
    │   └── Generate-Graph_Pyvis.py # Reads Layers/ and renders the HTML graph
    ├── Files/                      # Images referenced by the documentation
    └── DataLake-Graph_Pyvis.html   # The generated visualization
```

</details>

---

<details style="border:1px solid #57606a;border-radius:6px;padding:12px 16px;margin-bottom:16px;">
<summary><strong>Documenting a New Project</strong> (click to expand)</summary>

Where the spreadsheet asked an analyst to read the code and transcribe it by hand, this catalog asks a Claude Code skill to do the reading:

1. Drop the project's repository into `Catalog/Skills/Temp/<RepositoryName>/`.
2. Ask the skill to document it. It sweeps every API call, business rule, set-aside record, indicator and platform action in the code, and turns each one into a YAML file (`RAW_*`, `SILVER_*`, `AUDIT_*`, `GOLD_*`, `AUTOMATA_*`) following the field-by-field template of its layer.
3. Review the files it wrote in `Catalog/Skills/Temp/`. Nothing reaches the live catalog until you approve them.
4. Once approved, the files move into `Catalog/Layers/<Client>/<HML or PRD>/`, one numbered folder per layer.

The skill only ever reads the dropped project; it never runs its scripts, since those authenticate against production platforms and, in the Automation layer, act on them.

**Benefits:**

- **Fewer nodes**: one node per rule instead of one per manually transcribed entry, cutting redundancy out of the graph.
- **Derived from the code**: every document reflects the rules actually applied in the scripts, not what an analyst remembered while transcribing them.
- **Consistent structure**: every file the skill writes follows the same field-by-field template, no matter who ran it or which project it came from.

</details>

---

<details style="border:1px solid #57606a;border-radius:6px;padding:12px 16px;margin-bottom:16px;">
<summary><strong>Visualizing the Catalog</strong> (click to expand)</summary>

Every YAML file under `Catalog/Layers/` is a node; every `sources_raw`, `sources_silver`, `sources_audit` and `generates_audits` reference is an edge between them. Running

```
python Catalog/Scripts/Generate-Graph_Pyvis.py
```

reads the whole `Layers/` tree and renders `Catalog/DataLake-Graph_Pyvis.html`: an interactive graph, one column per layer and colored by layer, where opening a node shows its description, sample, owner and schedule. Re-run it after every batch of files moves into `Layers/`, so the graph never drifts from the catalog it was built from.

</details>

---

## License

Provided as-is for reference and reuse. Adapt it freely to your environment.