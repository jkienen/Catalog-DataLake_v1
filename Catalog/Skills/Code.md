---
name: code-project-standard
description: Build a data-extraction project from zero in the CYBER__ standard, in Catalog/Skills/Temp/CYBER__<Project>/ - from what the user wants to report on when Catalog/Skills/Temp/ holds no project, and also from zero when it holds one (any name - it does not need the CYBER__ prefix), using that project as the example whose information must not be left out; or, only on explicit request, reorganize an existing project in place without changing what it produces - numbered source folders, the Part-by-Part script anatomy, vault authentication, Datas/ outputs, Ok/Attention item checks, README, CLAUDE.md, LICENCE.md, .gitignore and requirements. Use when the user asks to review, generate, create, standardize, organize, refactor or "put in the pattern" a project in Catalog/Skills/Temp/.
---

```text
Use the file 'Catalog/Skills/Code.md' to generate/review the code of the project in 'Catalog/Skills/Temp/'.
```

# Build or standardize a CYBER__ project

**Scope: one project folder, from the first read to the handover** -
`Catalog/Skills/Temp/CYBER__<Project>/` in Create mode, the existing project
folder in Standardize mode. The skill runs in one of two modes, and the mode is
settled before anything is written:

| Mode | When | What changes | What never changes |
|---|---|---|---|
| Create | **the default.** No project in `Temp/`: built from what the user wants to report on. A project in `Temp/`: built from zero too, with that project as the example | everything - it is written from zero | the standard itself, and no information of the example is left out by accident |
| Standardize | only when the user explicitly asks to keep an existing project and reorganize it in place | how the code is organized | what the code produces and what it does on the platforms |

The work is a trail of five stages, run in this order:

| Stage | Create | Standardize |
|---|---|---|
| Read | map the sources the user wants to report on, and the example when there is one | map what the code does today |
| Plan | the folder tree, the datasets and their columns, crossed with the example | the deviation table against the standard |
| Build | write script by script, output validated by the user | refactor script by script, output unchanged |
| Project files | README, CLAUDE.md, LICENCE.md, .gitignore, requirements, .env | the same |
| Close | whole-project audit, the example's coverage included, and handover | whole-project audit and handover |

**Where the project goes next.** Every project built here is later taken into
the documentation flow of the catalog skill, `Catalog/Skills/Catalog.md`,
which documents its Raw and Silver layers and builds the GOLD indicators on
top of them. So the order of the work is: collect the data from the platform
endpoints first, then split it into scripts by function - one dataset per
object type - so that each CSV is a Silver dataset the catalog can document
and the indicators can be built from. This skill never changes `Catalog.md`
and does not build the GOLD indicators itself.

The standard is **not scattered through the steps**. It lives in its own
section, "The standard", near the end of this file, with the full skeleton of a
script. Read it before the first file of the Build stage and follow it line by
line.

## Step 0 - Set the verbosity, announce the trail, keep the user located

### Model check

Before the first message of the trail, silently check which model this
session is running - it is stated in the environment context you are given.
This skill expects at least a mid-tier current-generation model (Sonnet-class
or above): the judgment calls it demands - telling organization apart from
behavior, proving that a refactor left every output identical, reading a
business rule out of code written by someone else - are not reliable on a
fast/cheap tier (Haiku-class or below).

- **Meets the bar** - say nothing. This check has no output of its own; it is
  not part of the opening message.
- **Below the bar** - say so plainly, before anything else, and ask the user
  to switch to a stronger model (in Claude Code, `/model`) before continuing.
  A refactor that silently changes a column is a defect in production, not a
  warning label the user can fix on review.

### Verbosity

**The default is quiet.** Offer the switch in the opening message, in one
line - that you will return only the questions, what was written and what was
validated, and that they can ask for verbose to follow the reasoning. Do not
wait for an answer: quiet is what happens if the user says nothing, and they
can flip it at any point in the trail.

**Quiet** - an answer carries the status line, the question or the result, and
nothing else - a few lines, not a page. Do not think out loud and do not
restate this file to the user: the trail, the rules and the standard are yours
to follow, not text to repeat. Specifically, do not write:

- which files you opened and in what order
- why you chose a structure and what you discarded
- what a Part of the skeleton is for, or how the standard came about
- a summary of the work at the end of a stage beyond the lines that say what
  was written and what was validated

**Verbose** - the reasoning is part of the answer: the read presented as a
table, the options weighed, the checks reported one by one.

**Quiet is never silence about a problem.** Whatever the setting, always say:

- every question the step requires, with its format example
- the confirmations the trail demands - the inventory of Step 3
  (Standardize), the deviation table of Step 5, the design and coverage table
  of Step 6, and the crossing between stages
- anything you had to assume to keep going, and the assumption itself
- any difference between the output before and after a change, however small
- anything sensitive that reached your screen or left the machine when it
  should not have - a printed name, a credential sent to the wrong endpoint -
  said at once, with what to do about it
- a file written with something pending inside it, naming what is pending

Quiet reduces narration, never honesty. A difference withheld is not brevity,
it is a defect delivered.

### Language

**This file is written in English. That is the language of the instructions,
and also the language of the code.**

- **Code** - identifiers, comments, constants, file names, column names and
  printed messages are English, following the standard skeleton.
- **README.md** - English, following the template in "The standard". The
  reference projects in `Projects/` are all written that way.
- **Conversation** - the language the user writes in, in every message: the
  opening, the status lines, the tables, the questions and the one-line
  updates between tool calls. The English of this file and of the code stays
  in the files; it never becomes the language of the answer when the user
  writes another one. Terms of the trail (Read, Plan, Build, bucket) and code
  names stay as they are, inside a sentence in the user's language.

### Where the code is

**The code this skill works on is always inside `Catalog/Skills/Temp/`.** The
target - the folder that is written - is the new project in Create mode and the
existing project in Standardize mode. Nothing is written anywhere else:

    Catalog/Skills/Temp/CYBER__<Project>/    the new project (Create)
    Catalog/Skills/Temp/<Project folder>/    the example (Create) or the target (Standardize)

- **Any name.** A project dropped in often arrives with the name it had before
  (`Cyber_<Name>`, `<name>-flow`). It does not need the `CYBER__` prefix - do
  not stop or ask because of the name. In Create mode it is the example, read
  only; in Standardize mode its name is a bucket 2 row of the deviation table,
  kept by default.
- **Not the repository you are in.** The catalog repository is itself named
  `CYBER__Catalog-DataLake`, but it is never the target: its scripts,
  templates and `Layers/` are not reviewed, not standardized and not changed
  by this skill.
- **One project folder in `Temp/`** - that is the example (or the target, in
  Standardize mode). Name it in the opening message, so a wrong folder is
  caught before anything is read.
- **More than one** - ask which one is the example. The others are the
  siblings of Step 2, reference only. The `CYBER__<Project>/` folder this
  session created is the target, never part of the question.
- **A `CYBER__<Project>/` from an earlier session** - a project this skill
  already started is the target, not an example: ask whether to continue it,
  and read what is on disk before writing anything.
- **None** - in Create mode, the new folder is created there,
  `Catalog/Skills/Temp/CYBER__<Project>/`, once the token is confirmed in
  Step 1. In Standardize mode, say so and stop: ask the user to drop the
  project into `Catalog/Skills/Temp/`.
- `Temp/` is also where the catalog skill writes its YAML files before they
  move into `Catalog/Layers/`. Those files are not code for this skill: do not
  read or change them. A folder is a project when it holds code (scripts); a
  folder that holds only YAML files belongs to the catalog skill.

### What may be written

**Everything this skill writes goes inside the target folder, plus scratch
files in the session scratchpad. Nothing else is created, edited, moved,
renamed or deleted.**

- The other project folders in `Catalog/Skills/Temp/` - the example included -
  are REFERENCE ONLY -
  open them, read them, copy the shared VCenter extraction from them, compare
  the fixed files with them, never change them.
- The rest of the catalog repository - `Catalog/Layers/`,
  `Catalog/Skills/Templates/`, the other skill files, `Catalog/Scripts/` - is
  untouched.
- **This file is the one exception.** When the user gives a direction that
  holds beyond the project at hand - a naming rule, a question that should not
  be asked again, a step that was missing - write it into this file, in the
  section where it belongs, as a rule in this file's style: English,
  imperative, with its reason when the reason is not obvious. Say what changed
  in one line in total, in the same answer. A decision that holds only for the
  project at hand stays in the project - its deviation table, its README -
  never here. This file stays generic: it serves projects of every source, so
  the facts found in one project or one source - field names, counts,
  endpoint quirks, a region, a retention - never enter it; only the method
  does. Everything a session needs is in this file: no rule lives only in the
  memory of a past session, so a rule learned is written here, where the
  next session will read it.
- Probes, validation wrappers and dumps (such as an API schema) go to the
  scratchpad, never inside the project.
- **Data files stay closed.** `*.csv`, `*.json`, `*.db` and `*.env` are never
  opened, read or printed, in the target and in the siblings - the reference
  projects' `CLAUDE.md` says so, and the target gets the same file. The one
  thing allowed on a `.env` is checking WHICH variable names are set, printing
  only set / missing, never a value. A `.env.example` or any other `.env.*`
  gets the same treatment: variable names only.
- Deleting is allowed only for files this session created. Anything that
  arrived with the project is deleted only when the user asks for that file by
  name.

When something outside the target folder genuinely needs to change, **say so
and stop**. The user decides and does it.

### Running the project's code

Standardizing is proven by running, and creating is validated by running - so
this skill does run scripts, unlike documentation skills. The rules are strict
because the scripts authenticate against production platforms:

- **Never without the user's go-ahead** for that script in this session. A
  go-ahead covers the script it was given for, not the whole project.
- **Only read-only scripts.** A script with an active call that writes to a
  platform - assigning a tag, deleting an asset, creating or deleting a policy
  rule, a GraphQL mutation, revoking an exception - is never run. Write calls
  that arrive commented out stay commented out. Classify a call by what it
  does, not by its HTTP verb: a POST that fetches entities by id is a read,
  and says so when the user asks whether a scope needs write.
- **Validate through the in-memory summary** (appendix), never by opening the
  output file. The summary prints shape, column names and value counts of
  non-identifying columns only.
- **Ad-hoc probes** (schema introspection, counts) live in the scratchpad, call
  read-only endpoints only, and print aggregates only. They authenticate
  exactly as the scripts do: through the vault flow. The `.env` of a CYBER__
  project holds VAULT credentials - passing its values straight to a platform
  SDK sends an internal credential to an outside service. Direct platform
  credentials are used only when the user explicitly says the `.env` contains
  them, and the code that uses them is marked TEMP and removed before closing.
- **Check which credential the `.env` holds before every run**, not only the
  first, by its variable names: a `BASE_URL` next to `CLIENT_ID` and
  `SECRET_ID` is the vault. When the names change in the middle of a session,
  ask which kind they are before running anything, and delete the probes
  written for the other kind - a probe made for a direct credential sends a
  vault credential to the platform.
- **Credentials never travel in the conversation.** When the user offers to
  send a client and secret, ask them to write them into the project's
  `Scripts/.env` instead, and say which variable names to use. A secret pasted
  in the chat is exposed: say so at once and recommend rotating it.
- If a run printed something it should not have - an e-mail, a name, a host -
  say so in the same answer and fix the summary before the next run.

### The trail

Say it before reading anything, in one or two lines: which mode, and the five
stages by name - reading, planning against the standard, building script by
script with validation, the project files, and a closing audit of the whole
folder.

From there on, every answer opens with the stage and the position inside it,
followed by the file at hand and what is still missing from it:

    [Build 2/4] 2.2. Generate_Users - refactored, output compared, 1 difference pending

- Count **files finished**, not questions asked. Progress is what exists on
  disk and has been validated.
- Announce the end of a stage out loud, listing what was written and what was
  validated.
- **Ask before crossing into the next stage.** Never start Build with the plan
  unconfirmed, and never move on by yourself.

# Stage 1 - Read

## Step 1 - Locate the target and settle the mode

The project folders in `Catalog/Skills/Temp/`, whatever their names (see
"Where the code is"), and the request settle the mode:

- **Create is the default**, whether `Temp/` holds a project or not - a
  request to review code lands here as much as a request to generate it.
  - No project in `Temp/`: the new project is built from what the user wants
    to report on.
  - A project in `Temp/`, working or partial: the new project is also built
    from zero, in its own folder `Catalog/Skills/Temp/CYBER__<Project>/`, and
    the existing project is the **example** - read only, like a sibling. The
    new project follows the standard, not the example; the example is read so
    that no information it has is left out (Step 6).
- **Standardize** only when the user explicitly asks to keep the existing
  project and reorganize it in place, with its output unchanged.
- Never create a project the user did not ask for - a request to review or to
  generate one is that ask.

Confirm the project token: `CYBER__<Project>`, `<Project>` in English
CamelCase, no spaces and no accents - `HealthIDP`, `GVulnerabilities`,
`DeviceControl`. A business name in another language is translated into the
token, not transliterated. In Create mode, also ask for the goal in one
sentence - an example of the format: "monthly health report of the domain
controllers and accounts in Identity Protection". In Standardize mode, a folder that arrives with
another name keeps it unless the user asks for the rename: do not block on the
token - it is asked only when the user wants the rename row applied.

## Step 2 - Read the standard and the references

Read "The standard" at the end of this file in full.

Then look for the other `CYBER__*` folders: in `Catalog/Skills/Temp/`, next to
the target, and in `Projects/` at the root of the catalog repository, where
the reference projects live. Both are reference only. When they exist,
they are the living examples of the standard. Read, whole, the most recent one
that follows it end to end - at the time of writing that is
`CYBER__RVulnerabilities`, then `CYBER__HealthIDP`. Older projects carry known
deviations. Never copy them into a new project; in Standardize mode they are
exactly what the deviation table is for:

| Project | Known deviation from the standard |
|---|---|
| CYBER__DeviceControl | `.env` inside the source folder (`./.env`); a rolling `Datas/Entry/` outside any month folder; month folder written `YYYY-MM` |
| CYBER__GVulnerabilities | `Unwatched/` under `Entry/`; the date repeated in every file name; CSV and JSON written for every output, not only for the ones another script reads; the window of the fixed records opens at the run's time of day instead of 00:00, and its upper bound is compared in local time against UTC dates |
| CYBER__HealthEDR | scripts saved without BOM |

When no reference project is in reach, in `Temp/` or in `Projects/`,
this file alone is the reference - say so in one line; the user may drop one
in.

When a reference and this file disagree, this file wins - say so, so the
reference can be fixed later as its own task.

The Raw specs the catalog already holds are references too:
`Catalog/Layers/<Client>/<Env>/1-Raw/RAW_*.yaml`. When one documents a
source of the same kind (another scanner's vulnerabilities, another
platform's inventory), read it before designing the queries - endpoint,
filters, states, windows, frequency and storage path - and follow its shape
unless the user decides otherwise. Read only; never change them. A spec can
leave out a filter its script applies in code (a window closed after the
query): when the reference script is at hand, read it before drawing any
conclusion from the spec alone.

## Step 3 - Read the example (Create) or the target (Standardize)

Start with the `README.md` and `CLAUDE.md` of
`Catalog/Skills/Temp/<Project folder>/`, and respect the restrictions of the
`CLAUDE.md` from the first command. A project without its own `CLAUDE.md`
follows the one of the catalog repository, which carries the same
restrictions.

Read every script **whole**. Scripts come from different authors and do not
share a layout: locate the phases by what the code does - read configuration,
authenticate, call the API, transform, write the output.

Build the inventory, one block per script, and present it:

- **Inputs** - files read, and which script produced them
- **Calls** - platform, endpoint or SDK method, filters, and whether it READS
  or WRITES; mark every write call, active or commented out
- **Rules** - what is dropped, what is derived, what is set apart
- **Outputs** - path, file name, format, and the columns in the order written
- **Credentials** - where the `.env` is read from, which vault identity
- **Messages** - what the script prints on success and on failure

In Standardize mode, the inventory is the contract of the refactor: everything
under Calls, Rules and Outputs must still hold, word for word, at the end of
Build. Confirm it with the user before planning.

In Create mode, the inventory of the example is the checklist of Step 6:
present it, but it needs no confirmation - it states what the example does,
not what the new project will do.

In Create mode, the inventory also carries a **Beyond the API** block:
everything the example's code adds that a sweep of the endpoints would never
show. Read the code for it, not the API responses:

- outside sources - a public feed, a file, another script's output
- hardcoded lists, mappings, thresholds and time windows
- derived values and business rules - what is computed, flagged, filtered
  or set apart
- destinations and side effects - an upload, a share, a local file deleted
- run rules - a cache, a skip when the month already exists, a schedule
- auxiliary or manual scripts next to the main flow
- dead code that points to an intended feature - a field computed and never
  written, a function never called

# Stage 2 - Plan

## Step 4 - Separate organization from behavior

Every difference between the target and the standard falls into one of three
buckets. The bucket decides what happens to it:

| Bucket | Examples | What the skill does |
|---|---|---|
| **1. Organization** | Part banners, section order, fixed comments, the shape of the auth block, where constants live, helper functions, dead code, guards the data proves unnecessary, saving the scripts as UTF-8 with BOM, README, CLAUDE.md, LICENCE.md, .gitignore | applies it |
| **2. Operation** | renaming or moving a script or a folder, moving the `.env`, changing a pinned dependency version | lists it and asks, item by item - the data does not change, but whatever calls the scripts (a scheduler, the README, a colleague) breaks |
| **3. Behavior** | output paths, file names, formats, columns (name, order, value), records kept or dropped, filters, time windows, retention, calls made and the fields each query requests (the Raw layer), read versus write, vault identity | never changed in Standardize - if the user wants it, it is a separate, explicit request |

When unsure of the bucket, it is the higher one.

## Step 5 - Present the deviation table (Standardize)

One row per deviation, numbered, with the bucket:

    | # | Where | Today | Standard | Bucket |
    |---|---|---|---|---|
    | 1 | 2.1. Extract_Assets.py | auth block inline, no Part 2 | Part 1 token + Part 2 secrets | 1 |
    | 2 | Scripts/Falcon/ | folder without a number | 1. Falcon/ | 2 |

Bucket 1 is applied once the table is confirmed. Bucket 2 needs a yes per row -
the default is to keep. Bucket 3 is listed for the record and kept.

One bucket 3 item is always on the table when it applies: **CSV outputs
written without BOM**. The standard is UTF-8 with BOM, so propose the change
as its own row, recommended - but whatever reads those files today (a BI
import, another script reading with `utf-8`) sees one extra character at the
start, so it is applied only on the user's yes.

## Step 6 - Design the project (Create)

- **Sources** - discover them read-only, in the scratchpad: schema
  introspection, field names, counts. Never guess an endpoint or a field; a
  field that does not exist is a crash in production. With an example, start
  from what the example calls and extracts today, then sweep the rest of the
  platform's read endpoints on the same subject - the example is the first
  candidate list, not the spec.
- **How to sweep the sources** - the steps that worked, in this order:
  - find the candidate endpoints in the SDK's own endpoint catalog or the
    API's own schema (an OpenAPI spec, a GraphQL introspection) - with their
    methods, filter fields and limits - never from memory
  - probe access with the smallest page per endpoint; a permission error is a
    scope the API client lacks - list those for the user, they are not
    missing data
  - map the fields by flattening a sample into dotted paths, printing type,
    fill count and distinct count, and values only for an allowlist of
    non-identifying fields
  - count exactly, not from the sample: one smallest-page query per filter
    value, reading the total the API returns
  - for what the API does not show plainly, ask the user early for the
    console screen as the answer key - a list copied from the settings page
    of one or two tenants - and compare it with what the API returns for
    those same tenants: it settles in one step what probing alone cannot
  - close the sweep with the **extra sources** worth getting access to, taken
    from two places only: the endpoints of the same platform that answered
    with a permission error or were not tried, and the sources the example
    itself uses outside the platform (a public feed, another system). Never
    suggest a source neither of them has - not even the inventory crossing of
    the standard - unless the user brings it. List a source only when it adds
    something the readable sources do not carry - check that first - with
    what it adds and what it takes (a scope, a license, a vault identity); a
    source with no gain is left out, not listed as "not recommended". The
    user decides what to request; the design goes on with what is readable
    today, and every source the user releases is swept like the first ones
- **Themes, then datasets** - present the themes the sources can answer, once,
  as a short table with your recommendation. Then take them **one at a time**:
  settle one theme with the user - its datasets, columns and checks - before
  opening the next; never ask for the whole selection at once. Stay inside
  the project's goal: what another project of the team already reports - a
  health check of the same platform - is out of scope even when the source
  carries it; when a theme could belong to another project, ask. Then the
  datasets: **one script per object type**
  (domain controllers, users, connectors), not one per theme and not one per
  call. The number of scripts follows the data, not the reference projects.
- **A new idea in the middle of the trail** - when the user proposes a theme
  the plan did not have, say whether it belongs in this project or in a
  separate one before designing it, with your recommendation weighed on four
  points: the nature of the data (a snapshot of what exists, or events
  inside a time window), its sensitivity (counts, or personal data such as
  users and logins), the scopes it adds to the API client (least
  privilege), and its audience and cadence. A theme that differs on any of
  them usually makes a project of its own; the user decides.
- **Columns** - propose them per dataset. When a project of the same subject
  already exists (another source's vulnerabilities, another platform's
  inventory), start from its column names and order, map each one to the new
  source, add the columns only the new source has, and name the ones with no
  equivalent that leave. Where its names break this file (a unit outside
  parentheses), point it out and let the user choose: keeping the existing
  name, for the same name across projects, is a valid answer. The user
  decides what stays in the CSV: a column nobody asked for still has to be
  maintained. A column the user rejects leaves the CSV, not the query - the
  field it came from stays in the Raw layer while it is still interesting
  data (see "Raw and Silver inside a script").
- **Checks** - a check becomes an `Item:` column with `Ok` / `Attention`, and
  the rule for `Ok` is stated to the user. Numbers - CPU, memory, disk, counts -
  stay numbers unless the user asks for a classification. A flag that is not a
  weakness (a watchlist, a manual marking) is a plain True/False column, never
  an Item.
- **A fact the API does not expose** - a subscription, a license, an enabled
  module - may be inferred from an indirect signal (the roles available in a
  tenant, an endpoint that answers) only after the signal is checked against
  the console of real tenants in both directions: one that has the feature
  and one that does not. The inference is a fixed mapping in Part 0, next to
  the list of the signals known to indicate nothing, and the script prints
  anything new outside both, so the mapping can be maintained. The known
  false positives go into the README; a feature with no signal that holds is
  left out, and the README says why.
- **Order** - when the reports are crossed with the inventory, the inventory
  extraction is script `1.1` and everything else comes after it.
- **Raw** - for each source, which fields the queries request beyond what
  the CSV shows, and whether the Raw layer is persisted at all (see "Raw and
  Silver inside a script"). Ask it once, for the whole project - an example
  of the format: "CSV only" or "raw JSON per endpoint in
  Datas/{MM-YYYY}/Raw/". When the catalog already holds a Raw spec of the
  same kind (Step 2), its storage notes answer it - say so as the assumption
  instead of asking.
- **Coverage of the example** - with an example, cross its Step 3 inventory
  with the design, one row per item: each field it reads, each enrichment (an
  outside feed, a lookup), each filter and rule, each output column, and each
  line of the Beyond the API block - the endpoint sweep covers the API, this
  table covers the code. Every row is covered by the design or marked as
  dropped by the user - never left out by accident. A behavior that does not
  fit the standard (an upload, a write to a platform, another file layout) is
  a row too, and the user decides whether the new project keeps it.

Present the tree, the dataset list and, with an example, the coverage table,
and confirm before writing.

# Stage 3 - Build

## Step 7 - Write or refactor one script at a time

Follow the skeleton in "The standard" top to bottom. In dependency order: a
script whose output another script reads is finished and validated first.

Size the largest dataset before writing its script: the size and time of one
page, times the total the API reports. When the raw pages would not sit
comfortably in memory, the script turns each page into records as it
arrives, with a generator defined in the Obtaining Part and consumed in
Extracting Fields, and never keeps the raw responses; the last Part still
does all the saving.

In Standardize mode, move code into the skeleton without rewriting what it
does. Keep every rule, every filter, every column expression; change where it
sits and how it is written. When a line can only be made to fit by changing
its behavior, leave it as it is and add it to the deviation table as bucket 3.

## Step 8 - Validate the script

- **Standardize** - with the go-ahead and only for a read-only script, run the
  original through the in-memory summary, then the refactored one, and compare:
  the same files, the same columns in the same order, the same row counts, the
  same distributions. Live data drifts between two runs - a counter that grew,
  a user created in between. Name every drift and explain it; anything you
  cannot explain is a difference, not drift.
- **Create** - run it through the in-memory summary and let the user validate
  columns and values. The validated output becomes the spec of the script's
  Silver layer; the Raw layer is what its queries fetch.

If the script cannot be run - it writes to a platform, the user said no, the
credentials are not there yet - say that it was not validated, and keep it on
the pending list until the end.

## Step 9 - Clean the script

- **Clean the transformation, not the extraction.** Once an output is
  validated, it is the spec of the Silver layer: remove every derivation,
  rename and computed value that does not end up in a column or an Item of
  that output. The queries are the Raw layer and are not trimmed to the CSV: a
  field or a sub-table that is interesting data stays requested even when the
  CSV drops it - the column is removed where the record is built. A field
  leaves a query only when it is noise (it carries nothing anyone would want
  to read later) or when the user says the data itself is not wanted. Never
  remove a validated column on your own initiative.
- **No unnecessary guards.** A check for a value that the API schema declares
  non-null, a fallback the data never takes, a unit test for a unit that never
  varies - prove it with the schema or the data, then remove it. Keep a guard
  only when removing it would produce a silently wrong result, and say which
  one and why.
- **Nothing temporary survives.** No `TEMP` comment, no test credential, no
  hardcoded region or base URL, no path to a test file.
- **Re-run and compare after cleaning.** A cleanup is a refactor too.

Before calling a script finished, check:

- [ ] It follows the skeleton: Part 0 to the last Part, banners and fixed
      comments as written in the standard.
- [ ] It authenticates through the vault flow and builds SDK clients without a
      base URL.
- [ ] Every computed value reaches the output. Every requested field either
      reaches it or is kept on purpose as Raw data - never by accident.
- [ ] Every guard left in place is justified.
- [ ] No active write call was added; commented ones are still commented.
- [ ] It was validated (Step 8), or it is on the pending list with the reason.
- [ ] Saved as UTF-8 with BOM, CRLF line endings; every CSV it writes uses
      `encoding="utf-8-sig"`, every JSON it writes has no BOM.

# Stage 4 - Project files

## Step 10 - The fixed files

- **`CLAUDE.md`** and **`LICENCE.md`** - generated from the texts in "Fixed
  files" under "The standard", with the writer given there, and confirmed by
  their MD5. Never typed from memory and never paraphrased: `LICENCE.md` is a
  legal text, and every project carries the same bytes. When a sibling project
  is in reach, compare its checksum too - a sibling that differs from the
  checksum in this file carries a newer version: use the sibling's file, and
  tell the user this skill's copy is outdated. First rule out line endings: a
  clone checked out with `core.autocrlf` has working-tree bytes that differ
  from the committed ones. Read `git ls-files --eol` (paths only): when only the
  working tree differs, the committed file is the same version.
- **A project kept inside this catalog repository**, under `Projects/`, carries no
  `LICENCE.md` of its own: the root licence of the repository (MIT) covers it.
  The `LICENCE.md` of the standard is for a project kept in its own repository.
- **`Scripts/requirements.txt`** - pinned versions, the same pins the siblings
  use for the same libraries; without a sibling, the pins listed in
  "requirements.txt" under "The standard". A different pin is bucket 2.
- **`.gitignore`** - at the project root, with two lines, `.env` and `Datas/`
  (CRLF, no BOM). Neither the vault credentials in `Scripts/.env` nor the data
  the scripts write under `Datas/` may reach the repository. Each pattern
  matches in any folder. Create it in every project, in Create and in
  Standardize mode alike; when the project already has a `.gitignore`, add the
  missing lines instead of replacing the file. A `.gitignore` does not untrack a
  file git already tracks. Check with `git ls-files` (paths only): when a
  `.env` or a file under `Datas/` is tracked, say so at once. The user must:
  - remove it from the index (`git rm --cached <path>`) and commit;
  - rotate the credentials a tracked `.env` held, which stay in the repository
    history.

  This skill does not run git commands.
- **`Scripts/.env`** - never created, read or written by this skill. Tell the
  user the keys it must carry (`BASE_URL`, `CLIENT_ID`, `SECRET_ID`, the vault
  credentials) and let them write it.
- **`Scripts/1. VCenter/1.1. Extract_Assets.py`** - when the project crosses its
  reports with the server inventory, copied verbatim from the reference
  project of the same team. The copy is not refactored: it is shared code, and
  a fix to it is a task for every project that carries it.

## Step 11 - The README

Follow the README template in "The standard". Two rules on top of it:

- **No invented number.** The "Before" column and the Situation / Result
  paragraphs usually carry the manual effort the project replaces ("~8 hours
  per client"). That number comes from the user. Ask for it; if the user does
  not have it, write the sentences without a number.
- **Describe what the code does, as the code does it.** A script description
  that promises a column the output does not have is wrong documentation.

# Stage 5 - Close

## Step 12 - Audit the whole project

Open every file of the target together and check:

- [ ] The tree matches "The standard" - or every difference is a bucket 2 / 3
      item the user chose to keep.
- [ ] Every script finished Step 9.
- [ ] The README lists every script, in run order, and nothing that does not
      exist.
- [ ] `CLAUDE.md` and `LICENCE.md` (the latter only in a project with its own
      repository) are present and match their MD5;
      `requirements.txt` is present with the reference pins.
- [ ] `.gitignore` is present at the root and lists `.env` and `Datas/`, and
      `git ls-files` shows no `.env` and nothing under `Datas/` tracked - or
      the user was told how to untrack it.
- [ ] No `TEMP`, no hardcoded base URL, no test credential anywhere.
- [ ] No data file was opened, and nothing in the scratchpad was left inside
      the project.
- [ ] Every script is UTF-8 with BOM and CRLF, and every CSV it writes is
      UTF-8 with BOM. Markdown files are UTF-8 without BOM, and the fixed
      files keep their own bytes (`LICENCE.md` in LF).
- [ ] (Standardize) Every item of the Step 3 inventory still holds.
- [ ] (Create with an example) Every row of the coverage table is in the new
      project, or was dropped by the user.
- [ ] The outputs the validation runs left in `Datas/` are listed, and the
      ones written before a later change to their script are marked stale.

Report what the audit finds however quiet the verbosity is.

## Step 13 - Hand it over

Close with a SHORT message:

1. The files created or changed, one per line.
2. What was validated by running, and what was not - with the reason.
3. What the user must do: fill in the `.env`, run the scripts that could not
   be run here, decide on the stale test outputs in `Datas/`, and so on.
   Always ask them to rotate the credentials the session used - the vault
   client in `Scripts/.env` and the platform API client behind the vault
   identity - whether or not anything leaked: they went through the tools
   and logs of the session, and rotating them closes that window.
4. That committing is the user's step - this skill does not run git commands.

No recap of the stages and no explanation of the standard: the user has just
been through it.

# The standard

## Folder layout

    CYBER__<Project>/
      .gitignore
      README.md
      CLAUDE.md
      LICENCE.md
      Scripts/
        .env
        requirements.txt
        1. <Inventory>/
          1.1. Extract_Assets.py
        2. <Platform>/
          2.1. Generate_<Object>.py
          2.2. Generate_<Object>.py
      Datas/
        <MM-YYYY>/
          <Project>-<Object>.csv
          Entry/
            <inventory>-assets_<MM-YYYY>.csv
            <inventory>-assets_<MM-YYYY>.json
          Unwatched/
            (Unwatched)_<Project>-<Object>.csv

- `Datas/` is created by the scripts at run time; nothing is written there by
  hand.
- `1. <Inventory>/`, `Entry/` and `Unwatched/` exist only when the project
  crosses its reports with the inventory. Without an inventory, the platform
  folder is `1.` and nothing is set apart.
- Source folders are numbered in run order: `N. <Source>/`, where `<Source>` is
  the platform (`VCenter`, `EDR`, `IDP`, `Tenable`).
- Scripts inside them are numbered `N.M.`, with the folder number first.

## Naming

- Script: `N.M. <Verb>_<Object>.py`. `Extract_` for a plain extraction that
  feeds other scripts (the inventory); `Generate_` for a script that produces a
  report dataset. When a project of the same kind already uses one verb for
  the same job, follow it.
- The shared inventory extraction (`1. VCenter/1.1. Extract_Assets.py`) is
  copied verbatim and still writes its CSV without BOM. It is shared code: a
  change to it is a task for every project that carries it, never a local
  edit.
- The object of the script and the object of its output match: `2.1.
  Generate_Controllers.py` writes `HealthIDP-Controllers.csv`. Renaming one
  renames the other.
- Constants at the top of the script: `PROJECT = "<Project>-<Object>"`,
  `PROJECT_CHILD_01 = "(Unwatched)_<Project>-<Object>"` for the set-apart file,
  `PROJECT_PARENT` for a dataset the script reads from a previous one.
- Variants of one dataset - per OS, per type, per state - are
  `<Project>-<Object>_<Variant>.csv`, one file each, when their columns
  differ.
- When the project token already names the object - a vulnerabilities
  project whose script generates vulnerabilities - the object leaves the file
  name and the variant takes its place: `<Project>-<Variant>.csv`
  (`<Project>-Active.csv`, `<Project>-Fixed.csv`), with
  `PROJECT = "<Project>"`.

## Script anatomy

Every script follows this skeleton, and is saved as **UTF-8 with BOM, CRLF**.
The Parts are numbered from 0, separated by three blank lines, and each starts
with the banner exactly as written. The
fixed comments are copied as they are - including "If valid itens", which is
how every reference project spells it.

```python
#################################### Part 0: Environment Evaluation ->

# Imports necessary modules
import os
import sys
import json
import requests
import datetime
import pandas as pd
from falconpy import <ServiceClass>

# ----------------------------------------->

# Results
PROJECT = "<Project>-<Object>"
PROJECT_CHILD_01 = "(Unwatched)_<Project>-<Object>"

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

# <Platform> query: <what it returns>
QUERY = """
...
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
    IDENTITY = "<identity>"

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
            falcon = <ServiceClass>(client_id=CLIENT_ID, client_secret=SECRET_ID)



            #################################### Part 3: Obtaining <Object> ->

            response = falcon.<read_method>(...)

            if response["status_code"] != 200:
                print(f"API returned status code {response['status_code']}. Please validate your token (CLIENT_ID / SECRET_ID).")
                raise SystemExit(1)



            #################################### Part 4: Extracting Fields ->

            empty = "-"
            records = []

            # <one short comment per helper, saying what it returns>
            def format_date(value): ...

            for item in ...:
                records.append({
                    "Department": empty,
                    "Server VM": empty,
                    "<Column>": item.get("<field>", empty),
                    "Item: <Check>": "Ok" if <rule> else "Attention",
                })



            #################################### Part 5: Departments Population & Unwatched Separation ->

            # Build a lookup: mac_address -> vcenter record
            ...



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
            save_csv(matched_records, dir_to_save_csv, PROJECT)
            save_csv(unmatched_records, dir_to_save_csv_unwatched, PROJECT_CHILD_01)


        except Exception as err: print(err)

    else: print(".env file exists but is missing some variables!")
else: print(".env file does not exist!")
```

What the skeleton implies:

- **Part 0** holds everything that does not need credentials: imports, output
  constants, dates, paths, the input check, the embedded queries, the time
  windows, the fixed mappings (`UPPER_CASE` dicts).
- **Parts 1 and 2** are the vault flow, always the same two Parts, always
  right after Part 0. The platform work starts at Part 3.
- **The work Parts** are named by what they do - "Obtaining <Object>",
  "Extracting Fields", "Departments Population & Unwatched Separation",
  "Executing <Platform> Query". A Part that only exists for one step of
  another is a sub-part: `# --------------------------------- Part 5.1: <Title> ->`.
- **The inventory pieces are conditional.** The input check for the inventory
  file in Part 0, the `Department` and `Server VM` columns, the
  "Departments Population & Unwatched Separation" Part and the
  `PROJECT_CHILD_01` save exist only when the project crosses its reports with
  the inventory. A project - or a client - without one has none of them: the
  records start at the identity columns and the save Part comes right after
  "Extracting Fields".
- **The last Part saves.** Nothing is written to disk before it.
- **Helpers** are small functions defined inside the `try`, right before the
  Part that uses them, each with one comment line saying what it returns.
- Only the imports the script uses. `sys` only when it exits on a pending
  input; `time` only when it polls.
- **Several services of one platform share one token.** Build one auth object
  with the vault credentials (FalconPy `OAuth2`) and pass it to each service
  class, instead of one login per service.

## Authentication

- The `.env` sits in `Scripts/.env` and carries the vault credentials:
  `BASE_URL`, `CLIENT_ID`, `SECRET_ID`. Scripts read it as `../.env`.
- The platform credentials come from the vault, by identity, in Part 2. The
  reference projects use placeholder identities - `crowdstrike_sample`,
  `crowdstrike_audits_sample`, `crowdstrike_parent_sample`, `vcenter_sample`,
  `tenable_sample` - and lists such as the departments come from
  `default-depts-sample`; replace them with the identities your vault holds.
  Which identity a project uses is the user's answer, never copied from the
  last project.
- SDK clients are built with the vault credentials and **no base URL** - the
  SDK discovers the region. A hardcoded region is a test leftover.

## Outputs

- **Path** - `Datas/<MM-YYYY>/` for the report files, `Datas/<MM-YYYY>/Entry/`
  for datasets other scripts read, `Datas/<MM-YYYY>/Unwatched/` for records set
  apart. The date is in the folder, not repeated in the file name.
- **Format** - CSV, **UTF-8 with BOM** (`encoding="utf-8-sig"`, so Excel opens
  the accents correctly), no index. JSON (`orient="records"`) only for a
  dataset another script reads back, written next to its CSV, and **without**
  BOM - `json.load` with `utf-8` fails on one. A script that reads a CSV
  written by another script reads it with `encoding="utf-8-sig"`, or the first
  column name carries the BOM.
- **Unwatched** - records that could not be matched against the inventory are
  never dropped: they go to `Unwatched/` with the same columns as the main
  file, prefixed `(Unwatched)_`.
- **Reference stamp** - `Reference Month`, `Reference Year`, `Reference Date`,
  always the last three columns, taken from the run date. They are what lets
  the monthly files stack into a history.

## Columns and values

- Column names are English, Title Case, with spaces: `Host Name`, `Last Seen`,
  `Risk Score`. Units go in parentheses: `CPU Max Usage (%)`, `Storage Total (GB)`,
  `Inspected Requests (7d)`.
- Order: `Department` and `Server VM` first when the dataset is crossed with
  the inventory; then identity, state and numbers; then any score; then the
  `Item:` columns; then the reference stamp.
- The empty value is the string `-`, defined once per script as `empty` and
  applied to the whole frame with `fillna` before saving.
- **Checks** are `Item: <Check>` with `Ok` or `Attention`, and `-` when the
  check does not apply to that row. A check computed from every value of a
  list (one column per risk factor, per sensor signal) is generated from the
  data, not hardcoded.
- **Labels** - API enums become readable text (`LDAP_SIGNING_DISABLED` becomes
  `LDAP Signing Disabled`), keeping acronyms in capitals.
- **Dates** - `%Y-%m-%d`, converted from UTC to local time (UTC-3) when the
  API returns UTC.
- **One spelling per value.** A value that arrives in two spellings - a
  domain in capitals from one API and in lowercase from another, a product
  version written `25H2` and `25h2` by the same API - is normalized to one, so
  the reports cross. Pick the spelling by a rule that does not depend on the
  data of one file - the one with the most capitals - never the most frequent
  one: the most frequent changes from file to file, and the same value ends
  up spelled two ways across the project. The summary (appendix) flags every
  column that still carries two spellings.

## Raw and Silver inside a script

The layers of the Data Lake catalog map onto the parts of every script:

| Layer | Where it lives in the script | What decides its content |
|---|---|---|
| **Raw** | the API calls and the query constants - what the platform returns | what is interesting about the source, not what the report shows |
| **Silver** | the record built in "Extracting Fields" and saved in the last Part - the CSV | the columns the user validated |
| **Gold** | not in the scripts - the indicators built on top of the CSV | the business, documented by the catalog skill |

- **REST endpoints** return the whole object whatever the code reads, so their
  Raw layer is complete by default. **GraphQL and NGSIEM/LogScale** return only
  what the query asks for: there the query IS the Raw layer, and trimming it to
  the CSV throws data away for good.
- **A column leaves the report where the record is built.** The field it came
  from stays in the query - a KB the user did not want as a column is still
  requested, so the Raw layer keeps it.
- **A field leaves a query** only when it is noise, or when the user says the
  data itself is not wanted - not because the CSV does not show it.
- **Keeping a field is not a reason to derive from it.** A derivation that
  reaches no output is dead code (Step 9), whatever the Raw layer carries.
- **Persisting Raw is a per-project decision.** The scripts write the Silver
  CSV. Whether the Raw layer is also saved as the platform returned it - and
  where, such as the catalog's Raw path - is the user's answer, asked in Plan;
  never add a Raw writer by default.

## Queries embedded in code

- A query longer than one line (GraphQL, NGSIEM/LogScale) is a constant in
  Part 0: `NAME_QUERY = """ ... """.strip()`, with one comment line saying what
  it returns.
- A query taken from a vendor dashboard keeps its logic and its fields - they
  are the Raw layer - and the filters of every branch stay as the vendor wrote
  them. A sub-table leaves the query only when the user says its data is not
  wanted at all. Dashboard parameters (`?Param`) are removed, never left
  unresolved.
- Time windows are constants too (`start_ms` / `end_ms`), and every sub-table
  of a query states its own window explicitly.
- **State and events are separate queries.** When a source keeps both what
  is active and what has finished (open and fixed vulnerabilities, open and
  resolved alerts):
  - the active records are fetched whole, as a snapshot at run time, and the
    finished ones only inside a closed window - the previous calendar month;
  - a record can finish in more than one way - fixed, or expired because its
    host is gone - and each way is its own query and its own event file:
    leaving one out makes a drop in the active count look like remediation;
  - each query is its own Raw, each file its own Silver variant
    (`<Project>-<Object>_<Variant>.csv`, or `<Project>-<Variant>.csv` when
    the token already names the object - see "Naming");
  - run monthly, the files stack into a history with no gap and no
    duplicate: what finishes between the first day of the month and the run
    date falls into the next month's window;
  - the window has both bounds - with only a start date, a run more frequent
    than monthly puts the same event in several files, and stacking them
    counts it more than once; when the API accepts only a start date, close
    the window in code, right after the query;
  - both bounds fall at 00:00:00 local time of the first day of each month -
    never at the run's time of day - and are compared in the timezone of the
    field: a UTC field gets its bounds converted to UTC;
  - the reference stamp of an event file is still the run date; the event's
    own date column (`Last Fixed`) carries the month it happened;
  - check how long the source keeps each finished state before trusting the
    window - it only works when the records outlive the gap between runs.
    When the documentation does not say, infer it from the data (the oldest
    finished record, the longest inactivity among the current ones) and
    confirm it by watching one record cross the limit.
- Pagination is a `while True` loop that stops on the platform's own signal
  (`hasNextPage`, the total count), never on a fixed number of pages.

## Crossing with the inventory

- The key is the MAC address: lowercase, `-` replaced by `:`, from every
  interface the host reports.
- The department comes from the inventory's `Department`; the VM name from
  `Asset VM`.
- Workstations follow the fixed rule of the reference project
  (`TI-SERVICEDESK`, with the host name as the VM) instead of the inventory.
- A host that matches nothing goes to `Unwatched/`.

## Messages and error handling

- `print`, never `logging`. The messages are the ones in the skeleton, word for
  word: "Pending files!", ".env file does not exist!", ".env file exists but is
  missing some variables!", "API returned status code ... Please validate your
  token (CLIENT_ID / SECRET_ID).".
- The whole platform work sits inside one `try` that ends in
  `except Exception as err: print(err)`.
- A secondary call that fails does not stop the report: the script prints what
  failed, with its status code, and fills its columns with `-`. The first call
  of the script, which proves the credentials, does stop it. Any other line
  the script prints - a count per dataset - says what happened in one line.
- A partial answer that is still an answer - a lookup that returns 404 for the
  ids that no longer exist and data for the rest - is used, with a comment
  saying so.

## README template

The README is English, in this exact structure - the spacer images in the
table headers are what give the columns their width on GitHub. The title is
the business name of the report with the client the project serves in
parentheses (`Vulnerability Management (CLIENT_A)`); the platform goes in the
sentence below it, not in the title. The concept image is optional: a capture
of the project's chain in the catalog graph, saved under `Catalog/Files/` -
leave the block out when there is none:

    # <Report name> (<Client>)

    > <One sentence: what the project turns into what.>

    <p align="center">
      <img src="../../Catalog/Files/concept-<project>.png" alt="<what the graph shows, layer by layer>">
    </p>

    <table width="100%">
    <thead>
    <tr><th>Before<div><img width="300" height="1" alt=""></div></th><th>Now<div><img width="300" height="1" alt=""></div></th><th>What it buys<div><img width="400" height="1" alt=""></div></th></tr>
    </thead>
    <tbody>
    <tr><td><how it was, with the manual effort the user reported></td><td><how it is now></td><td><the gain></td></tr>
    </tbody>
    </table>

    ---

    ## Why This Project Exists

    **Situation:** <the problem, with the manual effort the user reported>

    **Task:** <what had to be solved>

    **Action:** <what the pipeline does, in business language>

    **Result:** <what changed>

    ---

    <details>
    <summary><strong>Scripts</strong> (click to expand)</summary>

    <table width="100%">
    <thead>
    <tr><th>Script<div><img width="400" height="1" alt=""></div></th><th>What it does<div><img width="800" height="1" alt=""></div></th></tr>
    </thead>
    <tbody>
    <tr><td><code>Scripts/1. <Source>/1.1. <Script>.py</code></td><td><what it does></td></tr>
    </tbody>
    </table>

    </details>

    <details>
    <summary><strong>Setup and Usage</strong> (click to expand)</summary>

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

    ```
    cd Scripts
    pip install -r requirements.txt
    ```

    <One sentence on the run order and the dependency between the scripts.>

    ```
    python './1. <Source>/1.1. <Script>.py'
    ```

    ```
    deactivate
    ```

    </details>

    ---

    ## License

    <One line on the licence of the organization>. Full terms in [LICENCE.md](LICENCE.md).

## Fixed files

`CLAUDE.md` and `LICENCE.md` are the same bytes in every project. They are
generated, never typed: the bytes carry details a copy by eye loses, and the
checksum is the only proof the file came out right.

| File | Blank lines | Line endings | Last line | Encoding | MD5 |
|---|---|---|---|---|---|
| `CLAUDE.md` | empty | CRLF | no line break after it | UTF-8, no BOM | `95841fd84bb859fbfb47be50cd2c1a28` |
| `LICENCE.md` | **one space**, not empty | **LF** - the one file that is not CRLF | no line break after it | UTF-8, no BOM | `ee405466b8072c07df8f6824994bf6cc` (the template below, before your organization's details) |

The writer reads the two texts straight from this file - the `CLAUDE_TEXT`
and `LICENCE_TEXT` blocks below - so they are never typed, and applies the
byte rules itself. Run it in the scratchpad, pointing at this file and at the
target folder:

```python
# Writes a fixed project file byte-exact (UTF-8 without BOM, no line break after the last line) and prints its MD5
import hashlib, re

# The texts come from Code.md itself: the ```text block that follows each label
source = open("<path>/Catalog/Skills/Code.md", encoding="utf-8").read().replace("\r\n", "\n")
def block(name):
    return re.search(rf"^`{name}`.*?\n\n```text\n(.*?)\n```", source, re.S | re.M).group(1)
CLAUDE_TEXT, LICENCE_TEXT = block("CLAUDE_TEXT"), block("LICENCE_TEXT")

def write_fixed(path, text, blank_line="", newline="\r\n"):
    lines = text.strip("\n").split("\n")
    data = newline.join(blank_line if line == "" else line for line in lines).encode("utf-8")
    with open(path, "wb") as file: file.write(data)
    print(path, hashlib.md5(data).hexdigest())

write_fixed("<target>/CLAUDE.md", CLAUDE_TEXT)
write_fixed("<target>/LICENCE.md", LICENCE_TEXT, blank_line=" ", newline="\n")
```

A checksum that does not match is a file that is not written yet: find the
byte that differs, fix it, write again. Never hand over a fixed file with a
checksum that differs from this table.

`CLAUDE_TEXT`:

```text
# Claude Code Instructions

## File Access Restrictions

Do NOT read, open, or inspect the following file types:
- `*.json` (may contain sensitive data)
- `*.csv` (may contain sensitive data)
- `*.db` (may contain sensitive data)
- `*.env` (contains secrets/credentials)

If a task requires understanding data structure, ask the user to describe it instead.
```

`LICENCE_TEXT` - the legal text of the organization. In this public repository
it is a template: replace `<Organization>`, `<Address>`,
`<security-team@example.com>` and `<Year>` with your organization's details
once, here, and update the checksum in the table in the same edit. After that,
the year in the last line changes only when the user asks, and the checksum is
updated in the same edit again. The projects under `Projects/` in this
repository carry no `LICENCE.md`: the root licence of the repository (MIT)
covers them:

```text
# Corporate Use Licence

## Limited Use Licence

This software is provided exclusively for internal use by <Organization>. By using, copying, modifying or distributing this software, you agree to the following terms and conditions:

### Rights and Restrictions of Use

1. **Internal Use Only**: This software may be used only by employees, contractors or affiliates of the Corporation for internal purposes. Use of this software by unauthorized third parties is not permitted.

2. **Internal Distribution**: Distribution of this software is permitted only within the Corporation. Redistribution to any external entity or individual outside the Corporation is not permitted.

3. **Modifications and Derivatives**: Modifications, improvements and derivative versions of the software are permitted, provided they are used and distributed exclusively within the Corporation. Modifications must keep this licence notice.

4. **Intellectual Property**: The Corporation retains all intellectual property rights over this software. No ownership right is transferred to the user.

5. **Confidentiality**: This software may contain confidential information of the Corporation. The user agrees to keep it confidential and not to disclose any part of the software to unauthorized third parties.

6. **Warranty and Support**: This software is provided "as is", without warranties of any kind, express or implied. The Corporation is not liable for any damage resulting from the use of this software. Technical support is provided solely at the Corporation's discretion.

### General Terms

- **Termination**: The licence terminates automatically if the user breaches any of the terms and conditions set out above. Upon termination, the user must immediately stop using the software and destroy all copies in their possession.

- **Governing Law**: This licence is governed by and construed in accordance with the laws of the country or state where the Corporation is headquartered.

- **Changes to the Licence**: The Corporation reserves the right to modify the terms of this licence at any time. Any modification will be notified to internal users and takes effect immediately upon notification.

## Contact

For more information about this licence, contact:
- Corporation name: <Organization>
- Address: <Address>
- Email: <security-team@example.com>

---
<Organization> © <Year>. All rights reserved.
```

## requirements.txt

One pinned line per library the scripts import, with the pins the reference
projects use - at the time of writing:

    crowdstrike-falconpy==1.6.2
    pyTenable==26.5.1
    pandas==2.3.3
    python-dotenv==1.0.1

Only the libraries the project uses. `requests` comes with the SDKs and is not
listed.

# Rules that apply to every stage

## Behavior is the contract

In Standardize mode the output is sacred: the same files, in the same place,
with the same columns in the same order and the same values. A refactor that
"improves" a column is a behavior change hidden inside an organization change.
If it is worth doing, it is a bucket 3 item and the user's decision.

## Read-only by default

The skill never adds a call that writes to a platform. A write call the user
asks for is written, reviewed with them line by line, and never run by the
skill - the first run of an action on production is the user's.

## Raw and Silver are separate

The Silver layer is measured against the validated output and the Raw layer
is not - the full rule is in "Raw and Silver inside a script" and Step 9.

## Short answers cover the whole question

When the user answers a question about several items with "yes", "go ahead
and remove them", "ok", the answer applies to every item in the question - not only to
the one you recommended. If the answer really could mean less, ask once, then
act on the reply.

## Sensitive data

- Data files stay closed (see "What may be written").
- Summaries never print identifying columns - names, e-mails, UPNs, accounts,
  hosts, IPs, MACs, OUs, people who changed a configuration. Print how many
  are filled instead.
- Raw API errors can carry identifiers; show only what the diagnosis needs.
- Examples in comments, docstrings and the README use placeholders
  (`CLIENT_A`), never a real client - in a real deployment the folders under
  `Catalog/Layers/` are real clients and the repository is shared. A real name
  appears only as an actual value: the project's own client in its README, a
  vault identity.

## How to ask

- **One question per message.** Never a list of questions, not even of
  independent decisions: ask the next one after the answer. Put it plainly, in
  one or two lines, with your recommendation first when there is one.
- **Show an example of the expected format** in every free-text question - an
  example of the format, never a guess at this project's value presented as
  though it were the answer.
- **Say what the answer will change**: "if yes, 2 columns leave the CSV".
- If the user does not know, do not block: keep the current behavior (in
  Standardize) or leave the item out (in Create), and put it on the pending
  list.

## Reporting

- Every result comes with how it was obtained: ran and compared, ran and
  shown, or not run.
- Every mistake is reported in the answer where it is found, with its
  consequence and the fix - a column dropped by accident, a guess that turned
  out wrong, a value that reached the screen.
- Numbers are counted, not estimated. When a count depends on how you measure
  (line counts, rows), say how you measured.

# Appendix - In-memory output summary

Save this in the scratchpad - never inside the project - and run a script
through it: `python run_with_summary.py "<path to script>"`. The script runs
unchanged; every DataFrame it saves is summarized before being written. Extend
`HIDE` with every identifying column of the project before the first run.

```python
# Runs a project script unchanged, printing an in-memory summary of each DataFrame before it is saved.
import sys, runpy, pandas as pd

HIDE = {"Email", "UPN", "Account", "Display Name", "Host Name", "Host Id", "Host Ip", "OU", "Title", "Local Ip",
        "Last Ip", "IP", "Mac Address", "Sensor Id", "Server VM", "Last Modified By"}
_to_csv = pd.DataFrame.to_csv

def to_csv_with_summary(self, path, *args, **kwargs):
    print(f"\n===== {str(path).replace(chr(92), '/').split('/Datas/')[-1]} -> {self.shape[0]} rows x {self.shape[1]} cols")
    print("  columns: " + " | ".join(self.columns))
    for column in self.columns:
        values = self[column].astype(str)
        if column in HIDE:
            print(f"  {column:<45} filled x{int((values != '-').sum())} (hidden)")
            continue
        counts = values.value_counts()
        extra = f" | ... ({len(counts)} distinct)" if len(counts) > 12 else ""
        print(f"  {column:<45} " + " | ".join(f"{str(k)[:60]} x{v}" for k, v in counts.head(12).items()) + extra)
        spellings = values.groupby(values.str.lower()).nunique()
        if (spellings > 1).any():
            print(f"  {'':<45} !! {int((spellings > 1).sum())} values with more than one spelling, e.g. {list(spellings[spellings > 1].index[:3])}")
    return _to_csv(self, path, *args, **kwargs)

pd.DataFrame.to_csv = to_csv_with_summary
runpy.run_path(sys.argv[1], run_name="__main__")
```

To compare two runs, save both summaries to the scratchpad and compare them
line by line: the header lines (files, shapes, columns) must be identical, and
every differing count must be explained as live-data drift.

# Appendix - Platform notes

Things that cost time once and should not cost it again:

- **GraphQL fields that belong to one entity type** (for example `agentId` on
  an endpoint) need an inline fragment (`... on EndpointEntity { agentId }`);
  without it the query fails with a 400 that looks like a permission problem.
- **Schema introspection** must ask for `includeDeprecated: true` and for the
  field descriptions, or whole root queries go missing from the dump.
- **Non-null in the schema is proof.** A field declared non-null needs no
  guard in the code; check the schema before keeping one.
- **FalconPy NGSIEM** `start_search` returns `resources` at the top level, not
  inside `body`; poll `get_search_status` every few seconds until `done`.
- **Hosts device details** answers 404 when some of the ids no longer exist,
  and still returns the rest - it is a partial answer, not a failure.
- **Long-lived notifications** in a timeline (a connector failure open for
  months) keep their original timestamp and move `lastUpdateTime`; count
  "recent" by the right one.
- **Vendor dashboard queries** hide `?Param` placeholders and per-widget time
  windows; list both before running a copy through the API.
