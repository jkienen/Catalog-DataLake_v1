---
name: catalog-datalake-layers
description: Read the extraction scripts the user dropped in Skills/Temp and document them in the Data Lake catalog - first the Raw layer, the API endpoints the code queries, then the Silver layer, the business rules the code applies, then the Audit layer, the records the pipeline sets apart for history, then the Gold layer, the indicators built on top of them, and finally the Automation layer, the routines that act back on the platform. Use when the user asks to document, catalog, or create the YAMLs for a project placed in Skills/Temp.
---

```text
Use the file 'Catalog/Skills/Catalog.md' to document the project inside 'Catalog/Skills/Temp/' in the Data Lake catalog.
```

# Document a project in the Data Lake catalog

**Scope: the whole catalog - Raw, Silver, Audit, Gold and Automation.** The
files are generated and reviewed in `Catalog/Skills/Temp/`; they only move into
`Catalog/Layers/` at the very end, in Step 22, once the user gives the go-ahead.

The work is a trail of five stages, run in this order:

| Stage | What it documents | Files | Template |
|---|---|---|---|
| Raw | the API endpoints the code queries | `RAW_*.yaml` | `Catalog/Skills/Templates/1 - RAW_[Platform]-[Endpoint].yaml` |
| Silver | the business rules the code applies | `SILVER_*.yaml` | `Catalog/Skills/Templates/2 - SILVER_[Project]-[Function].yaml` |
| Audit | the records the pipeline sets apart | `AUDIT_*.yaml` | `Catalog/Skills/Templates/3 - AUDIT_[Project]-[Audit].yaml` |
| Gold | the indicators built on the structured data | `GOLD_*.yaml` | `Catalog/Skills/Templates/4 - GOLD_[Project]-[Function].yaml` |
| Automation | the routines that act back on the platform | `AUTOMATA_*.yaml` | `Catalog/Skills/Templates/5 - AUTOMATA_[Context]-in-[Target].yaml` |

The per-field rules are **not in this file**. They live in the comments of the
five templates. Read the template of the stage you are in before writing the
first file of that stage, and follow it field by field.

## Step 0 - Set the verbosity, announce the trail, keep the user located

### Model check

Before the first message of the trail, silently check which model this
session is running - it is stated in the environment context you are given.
This skill expects at least a mid-tier current-generation model (Sonnet-class
or above): the judgment calls it demands - reading a business rule out of
code, deciding whether a per-OS partition needs its own Silver file,
anonymizing a free-text field without being told which names hide in it - are
not reliable on a fast/cheap tier (Haiku-class or below).

- **Meets the bar** - say nothing. This check has no output of its own; it is
  not part of the opening message.
- **Below the bar** - say so plainly, before anything else, and ask the user
  to switch to a stronger model (in Claude Code, `/model`) before continuing.
  Do not run the trail on a weaker model and hope for the best - a business
  rule written wrong by an underpowered model is a defect sitting in the
  catalog, not a warning label the user can fix on review.

### Verbosity

**The default is quiet.** Offer the switch in the opening message, in one
line - that you will return only the questions and what was written, and that
they can ask for verbose to follow the reasoning. Do not wait for an answer:
quiet is what happens if the user says nothing, and they can flip it at any
point in the trail.

**Quiet** - an answer carries the status line, the question, and nothing else.
Do not think out loud. Specifically, do not write:

- what you read, which files you opened, how you swept the calls
- why you chose a token, a filter or a column, and what you discarded
- what a field means, what the template says, how the layers relate
- a summary of the work at the end of a stage beyond the one line that says
  what was written
- the validation you ran, unless it failed

**Verbose** - the reasoning is part of the answer: the sweep presented as a
table, the readings offered as suggestions, the alternatives weighed, the
checks reported one by one.

**Quiet is never silence about a problem.** Whatever the setting, always say:

- every question the step requires, with its format example
- the confirmations the trail demands - the dataset lists of Step 2 and Step 5
  with their names, the KPI choice of Step 13, the load types and schedules
  of Step 19, the replication plan of Step 23, and the crossing between
  stages
- anything you had to assume to keep going, and the assumption itself
- anything you found that the user has not seen: a rule that deletes data, a
  sample that diverges from the code, a source that does not resolve, a
  threshold nobody defined
- a file written with something pending inside it, naming what is pending

Quiet reduces narration, never honesty. A doubt withheld is not brevity, it
is a defect delivered.

### Language

**This file is written in English and so is every template comment. That is
the language of the instructions, not of the work.**

What you SPEAK to the user, and what you WRITE inside the generated `.yaml`,
follows **the language of the templates** - the fixed texts of
`extraction_notes`, `storage_notes` and `pipeline`, and the example values of
`description` and `structure_notes`. Those texts are copied verbatim into
every file, so a catalog written in another language would contradict itself
file by file.

Read the template of the stage before the first message of that stage and
match it. When the templates change language, the catalog and the
conversation change with them - no rule in this file needs editing.

**Tokens are English regardless of the template language.** Every token that
becomes part of an `id` or a file name - `<Platform>`, `<Endpoint>`,
`<Project>`, `<Function>`, `<Audit>`, `<Context>`, `<Target>` - is written in
English, single word or CamelCase, no spaces and no accents, even when the
templates and the rest of the conversation are in another language. A business
name given in that other language is translated into the token, not
transliterated: "Controle de Dispositivos USB" becomes `USBControl`, not
`ControleUSB`. Confirm the token with the user same as any other - this rule
only fixes the language, not the word choice.

### What may be written

**Everything this skill writes goes inside `Catalog/Skills/Temp/`. Nothing outside it
is created, edited, moved, renamed or deleted, except in the moments listed
below.**

Outside that folder the repository is REFERENCE ONLY - open it, read it, quote
it, never change it outside the exceptions below:

- `Catalog/Layers/` is the live catalog. The generated files land in `Catalog/Skills/Temp/` and
  are reviewed there first. There are three exceptions. In Step 22, once the
  user gives the explicit go-ahead after reviewing, move (never re-generate)
  the files reviewed into `Catalog/Layers/`. In Step 23, once the user confirms a
  replication plan, write the replicas into the other clients' folders. And
  when a decision settled with the user requires changing a file that is
  already there - a Raw widened to serve this project too, an id renamed so
  the name fits both uses, a schedule shifted in Step 19 - edit it only after
  the user's explicit go-ahead, changing nothing beyond what was settled. For
  a rename, list every file that declares or names that id, in EVERY client
  folder and not only the one at hand: rename the file, change `id` and the
  path line of `storage_notes`, and update every `sources_*` that names it. A
  rename that skips one client leaves that client's graph with broken edges.
  Outside those moments, never write there, and never read it to
  overwrite a decision the user already made.
- `Catalog/Scripts/Generate-Graph_Pyvis.py` is the catalog's own tool, not the dropped
  project's - see Step 24. It is read-only over `Catalog/Layers/` and writes
  `Catalog/DataLake-Graph_Pyvis.html`; running it carries none of the risk the
  rule below exists for.
- `Catalog/Skills/Templates/` is read at every stage and followed field by field.
  Editing a template changes the standard for every future project, so it
  happens only when the user asks for it as its own task - never in the middle
  of cataloging, and never to make a file you are writing fit.
- This file, `Catalog/Skills/Catalog.md`, changes only when the user asks for
  it as its own task - the lessons learned reviewed at the end of a trail are
  the usual one. Write them generic: no client, source or tenant facts.
- Everything else - scripts, documentation, and the generated HTML outside
  the run of Step 24 - is untouched.

Inside `Catalog/Skills/Temp/` the dropped repository may be edited, but only for the
sample and volume capture, and it is put back exactly as it arrived (see
"Getting the output sample and the volume"). Never delete anything in `Temp/`
that you did not create there.

**Never run the project's scripts. Not once, for any reason** - not to test a
change, not to see the output, not to check the syntax, and not because they
sit inside `Temp/`. They authenticate against production platforms with real
credentials, pull real data, and in the Automation layer they act on it:
deleting, tagging, revoking. A syntax check is the same command as a run.

The only execution is the user's. You add the capture, say what changed and
where, and wait for them to run it and say it is done. If they cannot run
it, the sample stays `"?"` - it never becomes a reason to run it yourself.

The data files of the dropped project stay closed whenever its `CLAUDE.md` or
`README` restricts reading them - the sample comes from running the script,
never from opening the file.

When something outside `Temp/` genuinely needs to change, **say so and stop**.
The user decides - and either does it, or gives the go-ahead that one of the
exceptions above requires.

### The trail

The user asks for "the YAMLs" and gets five stages. Say so before reading
anything, in one short paragraph naming what happens in each and where you
are starting: the endpoints the code queries in Raw, the business rules it
applies in Silver, the records it sets apart in Audit, the indicators built on
top in Gold, and the routines that act back on the platform in Automation. Close the
paragraph saying the trail ends with a pass over the whole set, where the
catalog is reviewed together, the load type of each Raw and the schedule of
the chain are confirmed and the set is signed - and, once it is in the
catalog, it can be replicated to other clients.

From there on, every answer opens with the stage and the position inside it,
followed by the file at hand and what is still missing from it:

    [Raw 2/4] RAW_Tenable-Assets - <what was read, what is pending>

- Count **files written**, not questions asked. Progress is what exists on disk.
- Announce the end of a stage out loud, listing what was written.
- **Ask before crossing into the next stage.** Never start Silver with a Raw
  file still pending, and never move on by yourself.

# Stage 1 - Raw

## Step 1 - Read the project

The user drops the repository in `Catalog/Skills/Temp/<RepositoryName>/`, and
the prompt does not name it - find it yourself. A folder in `Temp/` is a
project when it holds code (scripts); the YAML files this skill writes sit in
`Temp/` itself and are not a project.

- **One project folder** - that is the one. Name it in the opening message,
  so a wrong folder is caught before anything is read.
- **More than one** - ask which one to document.
- **None** - say so and stop: ask the user to drop the repository there.

Start with the project's `README.md` and `CLAUDE.md`. When the `CLAUDE.md`
restricts reading data files (`*.json`, `*.csv`, `*.db`, `*.env`), **respect
it** - the output sample is obtained by running the script, never by opening
the file (see "Getting the output sample and the volume").

Scripts come from different authors and do not share a layout. Do not rely on
a fixed comment or folder structure: locate the phases by what the code does -
read configuration, authenticate, call the API, transform, write the output.

## Step 2 - Identify the endpoints being queried

Sweep **every** API call in the project and build the dataset list. One
extracted dataset = one Raw file. It is not one per script, nor one per call:

- **Discard** calls that only obtain credentials - token/authentication
  endpoints and secret-vault endpoints. They carry no business data.
- **One call becomes two Raw files** when it is invoked more than once with
  different filters and produces distinct datasets.
- **Two calls collapse into one Raw** when the second only exists to complete
  the first (trigger the export, then fetch the result in chunks).
- **Auxiliary lookups** may be a Raw file of their own or just internal
  plumbing. When unsure, ask - do not decide silently.
- **A dataset is the call, not its consumer.** When the endpoint is already
  cataloged and this project reads a different part of the same record -
  another score, another block of signals - it is the same Raw. Widen the
  existing file (its `description`, and its id when the old name no longer
  fits both uses) instead of writing a second one, and document what each
  consumer keeps in the `filters` and `pipeline` of its own Silver.

Run the check of "Checking for an existing file before generating" during
this sweep, against the whole `Catalog/Layers/` tree, and flag every overlap
it finds in the list itself. The decision on each overlap comes after the
client is answered (Step 3), because a reuse is only valid inside the client
that owns the data - see that section for when the decision is taken here
and when it waits for the end.

Present the list to the user and **confirm the count before writing any
file**: it defines every `id`. Present it with the suggested file name of each
dataset beside it (see Step 3), so the list and the names are confirmed in the
same answer.

Once the list is confirmed, add the sample and volume capture to the scripts -
Raw and Silver together, in one edit - and ask for the single run of the
trail (see "Getting the output sample and the volume").

## Step 3 - Ask for whatever cannot be identified

The code gives you the platform, what each dataset contains, and the literal
filters of the call. Everything else is a business decision, and business is
never inferred. Two answers are always required - the client is asked, the
file name is suggested and confirmed:

- **Client** - the organization that owns the data. Never assume the client of
  the last project you looked at. It appears in the `storage_notes` path and
  defines the folder under `Catalog/Layers/`, which may be spelled differently from
  the path segment. Before asking it blind, check whether `Catalog/Layers/` already
  has client folders: if it does, present them as options and ask the user to
  confirm one of them instead of opening the question cold - a new spelling
  for a client that already has a folder fragments the catalog in two.
  Once identified, the client is written Capitalized everywhere outside the
  `Catalog/Layers/` folder name itself - conversation, `storage_notes` path, any other
  field - regardless of the case the folder uses. `Catalog/Layers/CLIENT` is spoken
  and written as `Client`; the uppercase form is reserved for that one
  folder name.
- **File name** - the `<Endpoint>` that closes the `storage_notes` path
  (`CYBER/<Client>/Raw/<PLATFORM>/YYYY-MM-DD/<Endpoint>.json`). **Suggest one
  per dataset without waiting to be asked** - the user confirms or replaces
  it. Name what the data IS, not the SDK class or method, in English
  CamelCase, and keep it distinct from the files the same platform folder
  already holds under `Catalog/Layers/`: when another project already put an
  `Assets` in that folder and the two are genuinely different datasets (see
  "Checking for an existing file before generating" - a superset is reused,
  not renamed), a prefix naming this project's product line keeps the two
  apart. The path has no segment folder between the date and the
  file.
- **One client, more than one tenant** - when a client keeps one tenant of
  the same platform per host class (one for workstations, one for servers),
  the same call made in each tenant is one Raw per tenant. The tenant goes at
  the end of the token as a short hyphenated suffix - `-WS` for workstations,
  `-SRV` for servers - in the id and in the file name alike
  (`RAW_Crowdstrike-RTRSessions-SRV`, `.../RTRSessions-SRV.json`), so the ids
  stay short and readable. Each Raw says in `description` which tenant it
  reads and, in a `Note:` of `extraction_notes`, which Raw holds the same call
  for the other tenant. The Silver stays one file reading every tenant's Raw,
  with a `Tenant` column telling the rows apart, while the tenants share the
  same columns and rules; it splits per tenant only when the rules or the
  indicators differ between them.

Raw carries no `project` field - the graph falls back to `platform` - so do not
ask for the business project name here. It is asked in Stage 2, where the field
exists.

The `<Endpoint>` token of the `id` defaults to the file name just answered - do
not ask it as a separate question. Confirm it only when the file name does not
read well as an id token (spaces, punctuation, a name that still echoes the SDK
class) or when the user volunteers a different value unprompted.

## Step 4 - Generate the files

One file per dataset, named `RAW_<Platform>-<Endpoint>.yaml`, written to
`Catalog/Skills/Temp/`. They move into `Catalog/Layers/` only in Step 22.

Follow `Catalog/Skills/Templates/1 - RAW_[Platform]-[Endpoint].yaml`: it defines the
field order, what to fill in from the code, what to leave as `"?"`, when to use
`NA`, the fixed text of `extraction_notes` and `storage_notes`, and the sample
anonymization rules.

Before closing the stage, check:

- [ ] The YAML parses and carries the template's 16 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `"?"` is quoted - without the quotes the parser breaks.
- [ ] `NA` used only where the value does not exist, and `"?"` only where it
      exists and is pending.
- [ ] No endpoint path was guessed: it came from the vendor documentation or
      the SDK source, from the user, or stayed as `/path/example`.
- [ ] The output sample was anonymized before the file was written.
- [ ] `volume_per_frequency` carries the size measured in the sample run, or
      `"?"` when the run could not measure it.
- [ ] The user confirmed the dataset list from Step 2.

Then announce that Raw is finished, list the files, and ask whether to start
Silver.

# Stage 2 - Silver

Raw documented WHERE the data comes from. Silver documents WHAT THE CODE DOES
TO IT. Everything the Raw template pushed away - records dropped after the
call, dates trimmed in code, values matched against another source - is
described here.

## Step 5 - Enumerate the structured outputs

Sweep every output the code writes, the same way Step 2 swept every call. One
structured output with its own set of columns = one Silver file. The template's
STEP 0 lists the cases that fool the count (plumbing files, second passes,
records set apart as audits).

Read the write phase of each script, not the filenames alone: a script that
saves three data frames may be one Silver plus two audits.

**Watch for a partition that breaks the schema.** A write invoked once per OS,
environment, region, tenant or version is a single Silver file only while every
variant keeps the same columns. The moment the code drops or adds a column per
variant - a `dropna` after a `groupby`, a field only one platform's payload
carries - each variant is its own dataset with its own `structure_notes`, and
the default becomes one Silver file per variant, not one merged file. Say this
default out loud when the sweep finds such a partition, instead of waiting for
the user to catch a schema mismatch in the sample. Confirm the per-variant
schemas from the code (or from the samples once collected) before finalizing
the count - a hunch that they differ is not the same as having checked.

Present the list and **confirm the count before writing any file**.

## Step 6 - Read the business rules from the code

For each dataset, walk the transformation phase line by line and separate:

- **What it drops** - conditions that remove records after the extraction.
  This is `filters`.
- **What it derives** - every column whose value is computed rather than
  copied: precedence chains, fallback values, cross-source matching, state
  carried over from a previous run. This is `pipeline`, one block per column.
  Columns filled by a LATER script that reopens this dataset are derived here
  too, naming the routine that fills them: that script is an enrichment, not
  a source, and never enters `sources_silver`.
- **What it sets apart** - records written to a separate file because they did
  not match. This is `generates_audits`, and the audit ids are settled with
  the user in Stage 3.
- **What comes out** - the output columns, in the order the code writes them.
  This is `structure_notes`, and it must match the sample keys one to one.

Describe rules, never syntax: no variable names, no function names, no line
numbers. A rule the code does not apply is not a rule, however clearly a
comment states it.

Present your reading of each rule as a **suggestion** and let the user correct
it - the code shows the mechanics, the user owns the intent.

## Step 7 - Ask for whatever cannot be identified

Two answers are always required, on top of the ones Stage 1 already settled:

- **Project** - a repository is not a project. Suggest a business name and its
  token - the README title is the usual source, shaped like the projects
  already cataloged - and offer the possibility that the script belongs to an
  already cataloged project despite the repository name. It fills `project`,
  the `<Project>` token of the `id` and the project folder of the path.
- **File name** - the `<Function>` that closes the `storage_notes` path
  (`CYBER/<Client>/Silver/<Project>/YYYY-MM-DD/<Function>.json`). Suggest one
  per dataset, same rule as Raw, beside the Step 5 list. When the dataset
  covers a single variant of a dimension - one OS, one platform, one
  environment - the name carries the variant (`AssetsWindows`, not
  `Assets`), even when the code produces no other variant: the name is read
  beside other projects' files, where the unqualified name promises the whole
  population. The same holds for the Raw `<Endpoint>`.

The `<Function>` token of the `id` defaults to the file name just answered -
do not ask it as a separate question, following the same rule as Raw. Do NOT
ask for audit ids here: leave `generates_audits` as
`"?"` wherever the code sets records apart, and `NA` only where it separates
nothing - the ids are settled in Stage 3. The client was already answered in
Stage 1 - reuse it, do not ask twice.

## Step 8 - Generate the files

One file per dataset, named `SILVER_<Project>-<Function>.yaml`, written to
`Catalog/Skills/Temp/`.

Follow `Catalog/Skills/Templates/2 - SILVER_[Project]-[Function].yaml`: it defines the
field order - what to fill in from the code, and what to leave as `"?"`.

The samples and the volume measures come from the run already made in Stage
1 - do not ask for another one unless Step 5 changed what the sweep found.
Report the measured size of each Silver output with the files, since the
template has no field for it.

Before closing the stage, check:

- [ ] The YAML parses and carries the template's 15 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `"?"` is quoted, and `NA` used only where the value does not exist.
- [ ] Every id in `sources_raw` and `sources_silver` exists as a file written
      in this session, or as a file already in the same client's folder under
      `Catalog/Layers/` that the user chose to reuse, spelled identically - a
      typo breaks the graph edge.
- [ ] The `structure_notes` column list matches the `sample_output` keys, one
      to one and in the same order.
- [ ] Every derived column has a block in `pipeline`, and no block names a
      variable or a function.
- [ ] The output sample was anonymized before the file was written.
- [ ] The user confirmed the dataset list from Step 5.
- [ ] `generates_audits` is `"?"` where the code separates records and `NA`
      where it does not - never left blank.

Then announce that Silver is finished, list the files, and ask whether to
start Audit.

# Stage 3 - Audit

An audit holds the records the pipeline SET APART, stored in the same layer as
the structured data: `layer` says audit, the path says Silver, and that is
correct. It transforms nothing - it carries the columns of the Silver dataset
it came from.

## Step 9 - Explain what an audit is for, then present the ones you found

Do not open this stage with a question. Explain first, because the answer
depends on understanding the purpose. Two paragraphs:

1. An audit keeps, inside the Silver layer itself, the records the pipeline
   set apart. It exists for the history: once an automation acts on those
   records - deleting, closing, notifying - they disappear from the source,
   and the audit is what remains showing they existed.
2. An example the user can recognize, drawn from their own project. The
   canonical one: the hosts that do not match the inventory server are set
   apart into an audit; later an automation deletes them automatically; even
   deleted, the Silver history keeps the record that they were separated and
   why.

Then list what the code already separates - every set of records Stage 2 sent
to a file of its own - and confirm each one as an audit, with a suggested
`<Audit>` name beside it: what was set apart, not the condition that set it
apart (`Unwatched<Function>`, following the Silver it came from).

## Step 10 - Ask what else the user wants to register

**Ask when the code already produces audits, and ask when it produces none.**
An audit does not have to exist in code: the user may want to register a
separation the pipeline does not perform yet, and that file is written all the
same - the Silver that will feed it declares it in `generates_audits`.

Ask it as an open question, one at a time, and do not suggest thresholds. When
the user describes an audit, the numbers in the rule come from the answer, not
from what a similar project used.

If the answer is none and the code separates nothing, `generates_audits` stays
`NA` in every Silver file and this stage produces no file - say so and close
the stage.

## Step 11 - Generate the files

One file per audit, named `AUDIT_<Project>-<Audit>.yaml`, written to
`Catalog/Skills/Temp/`.

Follow `Catalog/Skills/Templates/3 - AUDIT_[Project]-[Audit].yaml`. It has 9 fields and
no `filters`, `pipeline` or `sample_output`: the only substance is which
records were separated, and it goes in `description`.

Then go back to the Silver files and replace the `"?"` in `generates_audits`
with the ids just settled. The stage is not finished while the two ends of the
edge disagree. Whether each audit gets a Gold of its own is decided in Stage 4
(Step 12).

Before closing the stage, check:

- [ ] The YAML parses and carries the template's 9 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `"?"` is quoted, and `NA` used only where the value does not exist.
- [ ] Every id in `sources_silver` exists as a Silver file, and that Silver
      declares this audit back in `generates_audits`.
- [ ] `storage_notes` still says Silver, both in the sentence and in the path.
- [ ] `description` carries the title line, the selection rule and the "Note:"
      paragraph.
- [ ] No threshold was invented: every number in the rule came from the code
      or from the user.
- [ ] The user confirmed the audit list from Steps 9 and 10.

Then announce that Audit is finished and ask whether to start Gold.

# Stage 4 - Gold

The three stages before this one describe DATA. Gold describes the QUESTIONS
answered with it. Nothing here is read from the code - the scripts stop at
Silver. What fills this stage is the `structure_notes` and the `sample_output`
of the Silver files already written.

## Step 12 - Decide the Gold files

One Gold per Silver is the default. Deviate only when the user says so.

**Every Audit is evaluated for a Gold of its own, too.** It is built on the
records the audit set apart, and its columns are those of the Silver the audit
came from: an audit carries that Silver's columns. Such a Gold lists the audit
in `sources_audit` and leaves `sources_silver` as `[]`. An audit of records
that did not match the inventory (unwatched) gets at least two KPIs:

- the total of records set apart (distinct ids);
- the ones inactive for more than 10 days, where Reference Date minus Last
  Seen is greater than 10 days, leaving out the records whose Last Seen is
  `-`. These are the records a removal automation deletes, so the KPI measures
  that automation's queue. A different cutoff comes from the user.

When the Gold of the Silver already carries the indicator the audit stands for
- the queue of the records it sets apart - that KPI moves to the audit's Gold:
the Silver's Gold drops it instead of repeating it, and the rule against
repeating a KPI across two files below still holds. When the audit's own
selection rule already is a cutoff (records inactive for N days or more), its
total and its inactive count are the same number: write it once.

A Silver whose columns answer nothing on their own may deserve no Gold at all.
Say that instead of inventing indicators to fill the slot - a KPI nobody asked
for still has to be maintained.

The KPIs are not decided by you. They are chosen by the user, one Gold at a
time, from a list of candidates you propose (Step 13). Work through the Gold
files in the order of their Silver files, and do not propose the next Gold
before the current one is written.

## Step 13 - Propose the candidates, then let the user choose

Open the source Silver and read its `sample_output` column by column, asking
what each one lets somebody decide. Then present **up to ten candidate KPIs** -
the most important and most critical the columns support, ranked, most
critical first - in one table: number, title, calculation with the exact
column names, and why it matters in one line. Below the table, list apart the
indicators that would need a cutoff, naming the column each one reads, and
say the number has to come from the user.

When the Silver is narrow and fewer than ten genuine candidates exist, stop at
the real ones and say why - ten is a ceiling, not a quota.

Then ask which to keep, by number, and whether any of the cutoff indicators
should be added with a number of theirs. Before writing a cutoff indicator,
settle what the number alone leaves open, one question at a time and with the
reading you recommend: which column it applies to (a peak or an average), which
population it counts (all accounts or only the enabled ones), and what happens
to records whose value is `-`.

The `-` question is not only for cutoff indicators. Every KPI that counts,
averages or takes a proportion over a column that can hold `-` - a host never
assessed, a field the source did not return - says in `filters` whether those
records enter. Left in, a `-` can count as compliant or drag an average, and
the number is wrong without anything looking wrong. State the reading you
chose when you list the KPIs written, so the user can reverse it.

Every candidate, and every indicator the user adds, must survive two tests:

- **Computable** from the columns of the source Silver, with the values the
  sample actually shows. A KPI over a column nobody produces is a promise.
- **No invented threshold.** When the indicator needs a cutoff - days without
  being seen, a minimum score, an age band - the number comes from the user,
  never from what a similar project used. When the user has no number, drop
  the cutoff and keep the indicator whole.

The field that carries the weight is `reason`. It answers WHY THE NUMBER
MATTERS - what decision it feeds, what it means when it grows - not what it
counts. A reason that restates the title is a KPI nobody will act on.

Do not repeat one indicator across two Gold files. When two datasets answer
the same question, the KPI belongs to the one whose columns answer it best,
and the other file says something else.

## Step 14 - Generate the files

One file per Gold, named `GOLD_<Project>-<Function>.yaml`, written to
`Catalog/Skills/Temp/` only after the user picked its KPIs - with exactly the
ones chosen, in the order of the candidate list, followed by the ones the user
added.

Follow `Catalog/Skills/Templates/4 - GOLD_[Project]-[Function].yaml`. It has 8 fields
and no `storage_notes` - Gold produces no file in the lake.

Then list the KPIs written, one title per line - the calculation and the
reason were already in the candidate table - spell out how each cutoff
indicator was settled, and move on to the next Gold with Step 13.

Before closing the stage, check:

- [ ] The YAML parses and carries the template's 8 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `filters` is `null`, lowercase and unquoted, wherever the KPI filters
      nothing. This layer uses null where the others use NA.
- [ ] No `": "` inside a KPI field - they are plain scalars and it breaks the
      parser.
- [ ] Every column named in `calculation`, `filters` and `view` exists in the
      `structure_notes` of the source Silver - for a Gold built on an audit,
      the Silver that audit came from - spelled identically. A column
      whose own name carries `": "` - the `Item: <name>` columns - cannot be
      written literally in a plain scalar: name it as the item column
      `<name>`, in the language of the templates, and that counts as
      spelled identically.
- [ ] Every threshold in a KPI came from the user.
- [ ] Every `reason` says why the number matters, not what it counts.
- [ ] Every id in `sources_silver` exists as a Silver file, and every id in
      `sources_audit` as an Audit file. A Gold built on an audit has
      `sources_silver: []`.
- [ ] Every Audit of the project has a Gold of its own, or the user was told
      why it has none.

Then announce that Gold is finished and ask whether to start Automation.

# Stage 5 - Automation

Every stage before this one DESCRIBES. This one CHANGES THE WORLD: the routine
acts back on the platform the data came from - it revokes, deletes, tags,
closes, notifies. Nothing here is inferred from code or from the other layers.
The action is the user's decision, and it is written down from their words.

## Step 15 - Ask what should be automated

Open with the question, then help the user answer it with candidates drawn
from THIS project - never from a generic list:

- **The audits already written.** Records set apart because they did not match
  are the natural input of an automation, and the audit is what keeps their
  history after the routine erases them from the source.
- **Code that already acts on the platform.** A call that assigns a tag,
  deletes an asset or closes a finding is an automation already written -
  frequently commented out, waiting for approval. Point at it.
- **A Silver column that exists only to drive a decision** - a changed flag, a
  state that nobody reads downstream.

Then ask for a short summary of the routine in the user's own words, and write
`description` from that summary. A candidate you presented is a suggestion
until the user describes it back.

If there is no automation, this stage produces no file - say so and go on to
the closing.

## Step 16 - Ask what cannot be inferred

- **target** - the platform where the action LANDS. It is not necessarily the
  platform the data came from, so ask instead of copying the source. It is
  written three times and they must agree: the `target` field, the end of the
  `id` after `-in-`, and the title line of `description`.
- **sources** - which Silver and which Audit files the routine reads. Raw is
  untreated and Gold is an indicator: neither is ever a source here.
- **safeguards** - anything the routine must guarantee before acting, such as
  a minimum history or an approval step. They go in `pipeline`, and they are
  the part that keeps the routine from acting on incomplete data.
- **id** - suggest the `<Context>` token from the user's own summary, verb
  first, and let them confirm it together with the target.

Every threshold in the condition comes from the user. An automation with an
invented number is an automation that deletes the wrong thing.

## Step 17 - Generate the files

One file per action, named `AUTOMATA_<Context>-in-<Target>.yaml`, written to
`Catalog/Skills/Temp/`. The same source read twice, once to notify and once to delete,
is two files - they run on different schedules and are approved separately.

Follow `Catalog/Skills/Templates/5 - AUTOMATA_[Context]-in-[Target].yaml`: 13 fields, no
`storage_notes` and no `owner`.

Before closing the stage, check:

- [ ] The YAML parses and carries the template's 13 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `"?"` is quoted, `NA` used only where the value does not exist, and `[]`
      for a source list that carries nothing.
- [ ] `source_repo` is `"?"`, never `NA` - the routine always came from
      somewhere, even when the code is not there yet.
- [ ] Every id in `sources_silver` and `sources_audit` exists as a file, and
      no Raw or Gold id appears in either list.
- [ ] The action in `description` is the one the user described, not the one
      you proposed, and every threshold in it came from them.
- [ ] `id` names the action verb first, without the project token, and closes
      with `-in-<Target>`.

# Closing - read the set as one, then sign it

The five stages run file by file. This pass is the only moment the catalog is
read as ONE THING, and it is where the decisions that are not per dataset get
answered at once: the load type of every Raw, the schedule of the chain, the
signature, and whether the project is replicated to other clients.

## Step 18 - Read the set as a whole

Open every file written in the session together and check what only shows up
side by side:

- **Every declared source resolves.** Each id in `sources_raw`,
  `sources_silver` and `sources_audit` exists, with that exact name, among the
  files of this session or in the same client's folder under
  `Catalog/Layers/` - the graph resolves a source only inside the client that
  declares it.
- **The audit edge agrees on both ends.** Every id in a `generates_audits` has
  a file that declares that Silver back in its `sources_silver`.
- **No `RAW_` or `GOLD_` inside a source list** of any automation.
- **No orphan in the chain.** A Silver nobody consumes and that produces no
  Gold is either the end of a real chain or a file that lost its purpose - say
  which one it is. An Audit with no Gold of its own needs the reason said too.
- **What is still pending**, counted per field, so the user knows what the
  review will cost before opening the files.
- **What changed in `Catalog/Layers/` holds too.** Every file this session
  edited there through an exception is part of the pass: a renamed id no
  longer appears in any client, and every `sources_*` that named it now
  resolves in every client it was changed in.

Report what this pass finds however quiet the verbosity is. A broken edge is
not narration.

## Step 19 - Review the load type and the schedule

### The load type

Every Raw was written with the template's `load_type` - usually `Full` - and
no question was asked per file. Now, with every layer documented, review it
once for the whole set: for each Raw, say what one run returns and recommend
keeping `Full` or moving to `Incremental`, all in one table, and ask the user
to confirm or name the ones that change. Change nothing they did not confirm.

What decides the recommendation is what one run returns, not the time filter
of the call:

- **A snapshot of the current state** - an inventory, a configuration, the
  accounts that exist today - is `Full`. The history comes from the dated
  partitions of the lake, not from the load type.
- **A summary over a window** - one row per entity aggregated over the last
  days - is `Full` too, even with a time filter: consecutive runs overlap and
  cannot be added up.
- **An event log** is where `Incremental` is a real option, and only when an
  event never changes after it is created. Say what it costs: a
  deduplication key (does the payload carry a unique id?), a watermark of the
  last event extracted, and a Silver that reads every accumulated partition
  instead of the last one. Recommend `Full` when an event's state is updated
  later - resolved, dismissed, a last-update time - because a cut by event
  date never fetches the update, and when the Silver replays the whole
  history.
- **Retention tips the balance.** When the platform keeps the history for a
  limited time, a `Full` re-read loses the old events without warning, and an
  `Incremental` load is what keeps them. Ask when the retention is not known.
- **The window must match the frequency.** A call that reads the last seven
  days only covers the period when it runs weekly; say so when `frequency`
  says otherwise.

### The schedule

Every Raw, Silver and Automation was written with the template's
`execution_schedule`, so every file of a layer starts at the same time. The
template value is the BASE SLOT of the layer, not the final answer. Once the
load types are settled - a change of `frequency` changes the slots - review
the schedule of the whole set the same way: one table, one confirmation.

First confirm the client the files go to - the folder under
`Catalog/Layers/` settled in Stage 1. The check runs against that folder only
(HML and PRD together) plus the files of this session. Then apply, in order:

- **Dependency comes first.** A file starts at least 30 minutes after every
  file it depends on, even when both runs are quick - it needs the source
  finished, not just started. The dependencies are the ids in `sources_raw`,
  `sources_silver` and `sources_audit`, plus the one the source lists do not
  show: a Raw that sends another Raw's output in its own call (the ids of an
  inventory, one call per host) depends on that Raw. Read it from its
  `filters` and the `Note:` of `extraction_notes`.
- **No overlap on the same platform.** Two files overlap when they belong to
  the same client and the same platform and start at the same time - they
  share the API credential and its rate limit. The platform is `platform` in
  a Raw and `target` in an Automation. A Silver reads the lake, not the API,
  so it is placed by dependency alone. Different clients or different
  platforms never overlap.
- **30 minutes apart, unless both are quick.** Overlapping files are spaced
  30 minutes apart. Two quick runs may share a slot. Quick is decided by the
  shape of the call, never by a guess at its duration: a single call or a
  plain paginated query is quick; a loop per host or per entity (one call per
  host, ids sent in batches) or a two-step export that waits for the result
  is not. Read it from the code and from the `Note:` of the Raw.
- **The slots follow the frequency.** A weekly `frequency` takes a weekly
  slot (one weekday, every seven days) plus the monthly one on the first day
  of the month; a monthly `frequency` takes only the monthly slot, on the
  first day of the month or another fixed day. A schedule that carries a
  slot its frequency does not have, or lacks one it has, is a mismatch -
  report it and propose the fix with the rest of the table. A Silver takes
  the frequency of the sources it depends on. An Automation carries its own
  `frequency` and may run less often than its sources (monthly over a weekly
  Silver); its slot only has to fall after the latest run of every source.
- **Each slot on its own.** A schedule with a weekly and a monthly slot is
  checked slot by slot: a monthly-only file collides with the monthly slot of
  a weekly-and-monthly one.
- **Existing files move only with a go-ahead.** When the only free slot needs
  a file already in `Catalog/Layers/` to shift, say which one and why; moving
  it follows the exception in "What may be written".

Present one table - file, current slot, proposed slot, and the reason
(dependency, overlap, quick) - and write the confirmed slots in the wording of
the template, changing only the hours. Change nothing the user did not
confirm. Report the conflicts found among files already in the catalog even
when this project does not touch them: an overlap nobody moved is still an
overlap.

## Step 20 - Sign the catalog

Two fields close the work, and neither belongs to a single dataset:

- **`owner`** - who documented the catalog. **Do not ask when you already have
  it**: the template may carry it as a default, an earlier stage may have
  settled it, or the user may have signed files of their own in the same
  session. Reuse it and say where you took it from, so a wrong name is
  corrected instead of inherited. Ask only when nothing in reach answers it,
  and ask for the form they want written, not just the name. The field exists
  in Raw, Silver and Audit only.
- **`last_reviewed`** - the current date, single-quoted, in every file of
  every layer written in this session. This is the date the catalog was
  written, not a date read from the project README. A file already in
  `Catalog/Layers/` that this session changed through an exception - a
  rename, a widened description, a schedule shift - keeps its original
  `last_reviewed` unless the user asks otherwise.

Write both into every file that carries the field and report the counts. Then
list what is still `"?"`: the documentation is complete, and everything left
is review.

## Step 21 - Hand it over

Close with a SHORT message. The user has just been through the whole trail:
no recap of the stages, no summary of the decisions, no explanation of what a
layer is. Five things and nothing else:

1. The files that were written, one per line, nothing after the name.
2. Ask them to review the texts and the documented rules, and say that the
   move into `Catalog/Layers/<Client>/HML` happens as soon as they give the go-ahead.
3. That the KPIs of the Gold files need validating in particular - the user
   chose them from candidates proposed from the columns that existed, so they
   are still examples until the business confirms them.
4. That the move is followed by a commit, to sync with Git - the user's own
   step, this skill does not run git commands.
5. That `PRD` comes later, only when the rules are in production.

Keep the pending fields out of it - they were listed in Step 20 and repeating
them buries the instruction. A handover that has to be read twice is a
handover that gets skipped.

## Step 22 - Move on confirmation, then offer to clear Temp

Wait for the user's go-ahead on the review asked for in Step 21. Do not move
anything before it arrives, and do not chase it - the user may take the files
away to review offline.

When it arrives:

1. **Move, do not recreate.** For each file written this session, move it
   (rename/relocate the file itself) from `Catalog/Skills/Temp/` into
   `Catalog/Layers/<Client>/HML/<numbered layer folder>/` -
   `1-Raw`, `2-Silver`, `3-Audits`, `4-Gold`, `5-Automations`. `<Client>` is
   the folder under `Catalog/Layers/`, uppercase, settled back in Stage 1 - it may
   differ from the spelling used inside the YAML paths. Do not touch the
   content while moving it, and do not move anything the user has not
   reviewed and approved.
2. Report what moved, one line per file, in the same order as Step 21.
3. **Then, and only then, ask** whether to remove the dropped repository from
   `Catalog/Skills/Temp/` so the folder is ready for the next project - after
   the move it is the only thing left there. The repository is the user's:
   wait for an explicit yes to this question, never delete it as part of the
   same step, and never delete anything else in `Temp/` that you did not
   create.

## Step 23 - Offer to replicate the project to other clients

Once the files are in `Catalog/Layers/`, ask whether this project's catalog
should be replicated to other clients - the same routines often run for more
than one client, and each client keeps its own catalog. If the answer is no,
go to Step 24.

If yes, settle the plan before writing anything, one question at a time:

- **Which clients.** Present the folders already under `Catalog/Layers/` as
  options. A new client gets a new folder, uppercase like the existing ones.
  The name the graph shows for it comes from `CLIENT_LABELS` in
  `Catalog/Scripts/Generate-Graph_Pyvis.py`, and falls back to the folder name
  when it is not listed there - say so, since the script is the user's to
  edit.
- **Which layers.** A replica often leaves out the audits and the
  automations, and with the audits the Golds built on them: they depend on a
  cross-check or an approval that may exist only for the main client.
- **Which sources stay, go or are added.** When a source goes - an inventory
  the other client does not have - follow everything that depended on it: the
  filters that matched against it, the audit it fed (`generates_audits`
  becomes `NA`), the `pipeline` blocks and the columns it filled, the
  `structure_notes`, the sample keys, and the Gold `calculation`, `filters`
  and `view` that name those columns.
- **Which columns stop existing.** Ask about each column the removed source
  filled, and point out columns with the same name that come from somewhere
  else - a column dropped in one dataset may have a different origin, and a
  reason to stay, in another.
- **`source_repo`** - the main client's repository, unless the user says the
  replica runs from another one.

Then present the plan - the files per client and what changes in each - and
write only after it is confirmed, directly into `Catalog/Layers/<Client>/HML/`.

- **The ids stay the same** as the main client's. The graph keys each node by
  client + id and resolves every source inside the same client, so every
  source a replica declares must be replicated into that client as well -
  including a Raw that belongs to another project but feeds this one. A Raw
  already replicated into that client by another project is not copied twice.
- **In every file**, change the client in the `storage_notes` path, set
  `last_reviewed` to the current date, and keep `owner`. The samples stay,
  trimmed of the columns that no longer exist.
- **Re-check the schedule in the target client.** The slots that were free in
  the main client may be taken in the other one: run the schedule check of
  Step 19 against the target client's folder and present its table with the
  plan.

Before closing, check:

- [ ] Every source a replica declares resolves inside the same client.
- [ ] No replica still names a removed source, a removed column, or an audit
      that was not replicated.
- [ ] The `structure_notes` of every changed Silver matches its sample keys.
- [ ] Verbatim template text that no longer fits a replica - a line about
      departments when the department column was dropped - is pointed out to
      the user, not rewritten.

## Step 24 - Render the graph

Run `Catalog/Scripts/Generate-Graph_Pyvis.py` from the repository root. This is the
catalog's own tool, not the dropped project's - it only reads the YAML files
already sitting under `Catalog/Layers/` and writes `Catalog/DataLake-Graph_Pyvis.html`.
It carries none of the risk the "never run the project's scripts" rule in
Stage 1 exists for, and running it here is expected.

Tell the user the path of the generated file - `Catalog/DataLake-Graph_Pyvis.html`
- and ask them to open it and validate that what just moved, and every
replica, renders correctly: selecting each client in turn, the new nodes
appear in the right layer and column, with edges reaching their declared
sources.

If something looks inconsistent - a node with no edge that should have one, a
source that does not resolve, a node in the wrong layer column, a project
whose chain comes out incomplete when it is picked in the Projects filter - do
not fix it yourself. Say what looks wrong and ask the user how
they want it corrected: the fix would touch files already moved into
`Catalog/Layers/`, which this skill does not edit unprompted.

Once the user closes this last check, end the trail with a single bold line
and nothing after it: **Skill completed**.

# Rules that apply to every stage

## Writing the files

- **No blank line between keys.** The generated file is dense, key after key.
  The blank lines you see in the templates are there to separate their comment
  blocks and are not part of the output. A blank line INSIDE a literal block is
  content - it separates the paragraphs of `storage_notes`, `pipeline` and
  `description` - and stays.
  One exception: in Gold, the entries of `kpis` are separated by a blank line,
  because each KPI is a block of five fields and they run together without it.
- **CRLF line endings**, in every file of every stage.
- **Edit with a tool that keeps CRLF.** `sed -i` in Git Bash on Windows
  rewrites the whole file with LF endings, and a pattern anchored on `\r`
  silently stops matching. Edit through the Edit tool or a script that reads
  and writes bytes, and check the endings with `file` after every edit - in
  `Temp/` and in `Catalog/Layers/` alike.
- **`last_reviewed` is the last field**, in every layer. The rest of the
  order comes from the template of the stage.
- **The template carries the defaults.** A field whose template comment ends
  in "Example of what the user answers" is copied into the file exactly as the
  template leaves it. `"?"` means unanswered - carry it over and let the user
  fill it on review. Any other value is a standing answer for the whole
  project: write it in and **do not ask the question**. A default that still
  carries a placeholder segment is a pattern, not an answer: in `source_repo`,
  `project_folder_name` is replaced by the folder name of the dropped
  repository. Read those lines before the first file of a stage, so you do
  not ask what the user already answered by editing the template. Two exceptions: a `"?"` in the Raw
  `volume_per_frequency` is replaced by the size measured in the sample run -
  that number is measured, not decided - and the Raw `load_type` and
  `frequency` and every `execution_schedule`, written with the template
  value, are reviewed once for the whole set in Step 19.
- Everything else about format lives in the template of the stage - field order,
  when to use `"?"`, when to use `NA`, which text is verbatim. Read it before
  writing the first file, not after the user points at the difference.

## Checking for an existing file before generating

Before writing a new file, check whether `Catalog/Layers/` already documents the same
thing under a different project - the same API endpoint, the same business
rule, the same action on the same target. Cross-project reuse is common, and
a duplicate does not show up until the graph is rendered.

When a match exists:

- **Decide in the sweep when only the call differs.** When the two files
  return the same record and differ only in the parameters of the call - a
  narrower filter, another id list or batch size, another pair of endpoints
  serving the same entity - present the comparison in Step 2, field by field,
  and let the user decide before anything is written. Waiting for the end
  only produces a draft that is thrown away.
- **Recommend the wider file.** When the existing Raw is a superset of the
  new call - the same record over a wider population, every platform where
  this code asks for one - recommend reusing it and moving the narrowing into
  the `filters` of this project's Silver, which then lists the existing id in
  `sources_raw`.
- **Otherwise, finish documenting the current file anyway**, read from this
  project's own code - when the record itself may differ (a field the code
  adds or drops, another facet), that difference is what the comparison at
  the end must show. Do not skip it, and do not copy the old file blind - the
  two may have diverged.
- **Skip re-collecting the output sample only when the match is exact** - same
  platform, same endpoint, same filters (Raw) or the same source columns
  (Silver). Reuse the `sample_output` already sitting in the old file instead
  of asking the user to run the script again for a picture you already have.
  When anything about the call differs - a filter, a field the code adds or
  drops - get a fresh sample as usual; that difference is exactly what the
  comparison at the end needs to show.
- **At the end, present the differences** between the two files to the user,
  field by field, and ask whether to keep both or drop the old one in favor of
  the one just written - for every overlap that was not already decided in
  the sweep.
- **If the user keeps the new one, give it the same `id` as the old file** -
  it replaces it rather than sitting beside it under a different name, so
  every edge already pointing at the old id keeps resolving. When neither
  name fits both uses, the way out is a new id for the one file that serves
  both, applied through the rename exception of "What may be written": every
  client that holds the old file and every `sources_*` that names it change
  together.
- **If the user keeps the old one instead, discard the draft written this
  session** - it never moves to `Catalog/Layers/`. From here on, reference the old
  file's id directly as the source in this project's own Silver/Audit files,
  exactly as if this project's own Raw stage had produced it.

This runs per file, against the whole `Catalog/Layers/` tree, including other
projects' folders. Only a match in the same client's folder can be reused as a
source: the graph resolves a source inside the client that declares it, so a
match in another client's folder is that client's own copy, not a source for
this one. It is not the same check as Step 18's "every declared source
resolves," which runs once at the end, over the sources the files of this
session declare.

## Validating an audit or automation description

When the user describes an Audit (Step 10) or an Automation (Step 15) in their
own words, do not transcribe it straight into the file. Before writing:

- **Restate the condition using the exact column names** of the source Silver
  (or Audit) `structure_notes` - not a paraphrase. If a field the user named
  does not exist under that spelling, say so and ask which column they meant
  instead of guessing the closest match.
- **Say whether it makes sense** given what the pipeline already does - does
  the condition identify something the business would plausibly act on, does
  it overlap with a rule already documented elsewhere, is a threshold missing.
  A quiet "faz sentido" is enough when it does; when something is off, say
  what and let the user confirm before the file is written.
- This is a check, not a gate: the user's description still wins. State the
  concern once, then proceed with what they confirm.

## How to ask

- **One question at a time**, waiting for the answer before the next one. No
  numbered block of ten questions, and no several questions in a single call:
  the user answers part of it and the rest slips through as if it had been
  confirmed. A list of options answered in one go - the Gold candidates, a
  table of suggested names - is one question, not ten.
- **Names come with a suggestion, always.** Every file name and id token -
  `<Endpoint>`, `<Function>`, `<Project>`, `<Audit>`, `<Context>` - is proposed,
  not asked cold, and the user confirms or replaces it. A suggestion is never
  applied on its own: nothing is written into a file with a name the user has
  not answered, even when every earlier suggestion was accepted. When a stage names
  several datasets, put all the suggestions in one table and confirm them in
  one answer instead of one question per name. Gold needs no name question:
  its `<Function>` repeats the Silver it reads.
- **Show an example of the expected format** in every other free-text
  question: an example of the format, never a guess at this project's value
  presented as though it were the answer. Names are the exception above;
  business values - the client, a threshold, a schedule - are never guessed.
  A schedule slot proposed in Step 19 is not a guess: it is derived from the
  template's base slot by the rules of that step, and confirmed by the user.
- If the user picks an "other / I'll describe it" option and no text comes with
  it, **ask again**. A chosen option with no content is not an answer.
- If the user does not know, **do not block**: use the template's placeholders
  (`/path/example` for an endpoint path, `"?"` for a business field) and move
  on. The user fills them in on review.

## Getting the output sample and the volume (Raw and Silver only)

- **One edit, one run.** The user runs each script once for the whole trail,
  never once per stage. Right after the Step 2 list is confirmed, sweep the
  write phase of every script the way Step 5 will - the Silver outputs are
  captured before their list is confirmed - and add every capture point in a
  single pass: Raw and Silver, in every script. Then ask for the run. The
  Silver stage reads its samples from the same file later. A second run is
  needed only when Step 5 changes what the sweep found - an output treated as
  plumbing turns out to be a Silver - and then only for that output; say why.
- **Do not rely on console output, and do not ask the user to write the print
  themselves.** A sample can be too large to paste without truncation. Edit
  the script and, instead of printing, append the record to one shared text
  file for the whole session: `<dropped repository root>/catalog_samples.txt`
  (append mode, `"a"`, `encoding="utf-8"`), preceded by a one-line English
  comment saying it is a temporary catalog capture. Where the write goes
  depends on the layer: Raw appends the record right after the API call and
  before any transformation; Silver appends it after the record is assembled
  and before it is written to disk.
- One entry per dataset, one record each, preceded by a header line naming the
  layer and the dataset (`=== RAW <Endpoint> ===`, `=== SILVER <Function> ===`,
  or the call or output name the code uses while the names are not settled)
  so entries stay tell-apart when several scripts write to the same file. The
  record is the one with the most fields filled in - across the whole list or
  iteration, not merely the first item - so the sample shows every key the
  dataset can carry. In Raw it is the record as the API returned it, without
  the envelope the SDK or the HTTP response puts around the list (status,
  meta, pagination): the catalog documents the record, not the transport.
- **One record per shape.** When one dataset carries more than one record
  shape - configuration events and failure events in the same timeline - write
  one record of each shape, and say so when presenting the sample.
- **Accumulate, never hold.** Choosing the richest record must not keep the
  dataset in memory: a paginated call can return gigabytes. Keep, per
  dataset, only the best record so far, the record count and the byte total,
  updated page by page, and write them once the last page is read.
- **Measure the volume in the same write.** Beside the sample, write the size
  of the WHOLE dataset that run produced: the record count and the total size
  in bytes of every record serialized as JSON - all the pages of a paginated
  call, every row of a Silver output - and no content beyond the one sample
  record. In Raw it fills `volume_per_frequency` (one run is one frequency
  period), in the unit notation of the template example, rounded to a
  readable number and presented to the user as an estimate from a single run.
  Silver has no volume field: report its numbers to the user with the Silver
  files, without writing them into any file.
- Then **tell the user the path of the file** and that every script can be run
  in one pass, in any order - append mode means nothing overwrites - but one
  after the other, never in parallel: the scripts share the capture file,
  where two processes appending large records at once can interleave them,
  and usually the same API credential, where parallel runs raise the
  rate-limit errors that abort a run or blank its columns. Wait for
  them to say the run is done, then **read the file yourself** with the Read
  tool. Do not write the catalog file with an invented sample.
- Anonymize the collected record before writing it into the YAML, following
  the template's rules.
- **Trim what repeats before writing.** An array whose entries repeat the same
  shape - a dozen network interfaces, forty packages - teaches nothing after the
  first entry and buries the record it was meant to illustrate. Keep one, choose
  the entry with the most fields filled in, and leave distinct values alone.
- **The code is the authority on the shape of the record.** When the collected
  sample diverges from what the code writes - a column named differently, a key
  the code drops before saving, a field that no longer exists - correct the
  sample to match the code and say so. A sample collected from an older run is
  far more common than code that lies about its own output.
- **Put the script back exactly as it arrived** as soon as the file is read -
  every sample and every measure is in the text file by then, so the scripts
  do not stay touched through the rest of the trail. Restore by copy, not by
  hand: before adding the capture, copy every file you will touch to the
  scratchpad directory; to put it back, confirm with a diff that the only
  differences are the lines you added, copy the original over it, and
  confirm with `cmp` that it is byte-identical - encoding, BOM and line
  endings included. Only when no copy exists, remove by hand every line
  added - the write call, the comment, the blank line, an added import. Either
  way, say that the script is back as it arrived. The script belongs to the
  project, not to the cataloging, and a leftover write floods a shared file
  on every future run, inside a try/except that hides the real cause. The
  same applies to anything else touched to get the sample. Once the last
  Silver file is written, **delete `catalog_samples.txt` itself** - it is
  scratch for this cataloging session, not a project artifact, and a
  leftover copy is stale the moment the next project reuses the same file
  name.
- If the user cannot run the script, leave `"?"` and move on.