---
name: catalog-datalake-layers
description: Read the extraction scripts the user dropped in Skills/Temp and document them in the Data Lake catalog - first the Raw layer, the API endpoints the code queries, then the Silver layer, the business rules the code applies, then the Audit layer, the records the pipeline sets apart for history, then the Gold layer, the indicators built on top of them, and finally the Automation layer, the routines that act back on the platform. Use when the user asks to document, catalog, or create the YAMLs for a project placed in Skills/Temp.
---

# Document a project in the Data Lake catalog

**Scope: the whole catalog - Raw, Silver, Audit, Gold and Automation.** The
files are generated and reviewed in `Catalog/Skills/Temp/`; they only move into
`Catalog/Layers/` at the very end, in Step 21, once the user gives the go-ahead.

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
- the confirmations the trail demands - the dataset list of Step 2 and Step 5,
  and the crossing between stages
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
is created, edited, moved, renamed or deleted.**

Outside that folder the repository is REFERENCE ONLY - open it, read it, quote
it, never change it:

- `Catalog/Layers/` is the live catalog. The generated files land in `Catalog/Skills/Temp/` and
  are reviewed there first. The one exception is Step 21: once the user gives
  the explicit go-ahead after reviewing, move (never re-generate) the files
  reviewed into `Catalog/Layers/`. Outside that one moment, never write there, and
  never read it to overwrite a decision the user already made.
- `Catalog/Scripts/Generate-Graph_Pyvis.py` is the catalog's own tool, not the dropped
  project's - see Step 22. It is read-only over `Catalog/Layers/` and writes
  `Catalog/DataLake-Graph_Pyvis.html`; running it carries none of the risk the
  rule below exists for.
- `Catalog/Skills/Templates/` is read at every stage and followed field by field.
  Editing a template changes the standard for every future project, so it
  happens only when the user asks for it as its own task - never in the middle
  of cataloging, and never to make a file you are writing fit.
- Everything else - scripts, generated HTML, documentation - is untouched.

Inside `Catalog/Skills/Temp/` the dropped repository may be edited, but only for the
sample print, and it is put back exactly as it arrived (see "Getting the output
sample"). Never delete anything in `Temp/` that you did not create there.

**Never run the project's scripts. Not once, for any reason** - not to test a
change, not to see the output, not to check the syntax, and not because they
sit inside `Temp/`. They authenticate against production platforms with real
credentials, pull real data, and in the Automation layer they act on it:
deleting, tagging, revoking. A syntax check is the same command as a run.

The only execution is the user's. You add the print, say what changed and
where, and wait for them to run it and paste the output. If they cannot run
it, the sample stays `"?"` - it never becomes a reason to run it yourself.

The data files of the dropped project stay closed whenever its `CLAUDE.md` or
`README` restricts reading them - the sample comes from running the script,
never from opening the file.

When something outside `Temp/` genuinely needs to change, **say so and stop**.
The user decides and does it.

### The trail

The user asks for "the YAMLs" and gets five stages. Say so before reading
anything, in one short paragraph naming what happens in each and where you
are starting: the endpoints the code queries in Raw, the business rules it
applies in Silver, the records it sets apart in Audit, the indicators built on
top in Gold, and the routines that act back on the platform in Automation. Close the
paragraph saying the trail ends with a pass over the whole set, where the
catalog is reviewed together and signed.

From there on, every answer opens with the stage and the position inside it,
followed by the file at hand and what is still missing from it:

    [Raw 2/4] RAW_Tenable-Assets - <what was read, what is pending>

- Count **files written**, not questions asked. Progress is what exists on disk.
- Announce the end of a stage out loud, listing what was written.
- **Ask before crossing into the next stage.** Never start Silver with a Raw
  file still pending, and never move on by yourself.

# Stage 1 - Raw

## Step 1 - Read the project

The user drops the repository in `Catalog/Skills/Temp/<RepositoryName>/`.

Start with the project's `README.md` and `CLAUDE.md`. When the `CLAUDE.md`
restricts reading data files (`*.json`, `*.csv`, `*.db`, `*.env`), **respect
it** - the output sample is obtained by running the script, never by opening
the file (see "Getting the output sample").

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

Present the list to the user and **confirm the count before writing any
file**: it defines every `id`.

## Step 3 - Ask for whatever cannot be identified

The code gives you the platform, what each dataset contains, and the literal
filters of the call. Everything else is a business decision, and business is
never inferred. Two answers are always required:

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
  (`CYBER/<Client>/Raw/<PLATFORM>/AAAA-MM-DD/<Endpoint>.json`). It does not
  necessarily match the `id` token, so ask it per dataset instead of
  transcribing the id. The path has no segment folder between the date and
  the file.

Raw carries no `project` field - the graph falls back to `platform` - so do not
ask for the business project name here. It is asked in Stage 2, where the field
exists.

The `<Endpoint>` token of the `id` defaults to the file name just answered - do
not ask it as a separate question. Confirm it only when the file name does not
read well as an id token (spaces, punctuation, a name that still echoes the SDK
class) or when the user volunteers a different value unprompted.

## Step 4 - Generate the files

One file per dataset, named `RAW_<Platform>-<Endpoint>.yaml`, written to
`Catalog/Skills/Temp/`. The user moves them into `Catalog/Layers/` manually afterwards.

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
- [ ] No endpoint path was guessed: it either came from the user or stayed as
      `/path/example`.
- [ ] The output sample was anonymized before the file was written.
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
  not match. This is `generates_audits`, and the audit ids come from the user.
- **What comes out** - the output columns, in the order the code writes them.
  This is `structure_notes`, and it must match the sample keys one to one.

Describe rules, never syntax: no variable names, no function names, no line
numbers. A rule the code does not apply is not a rule, however clearly a
comment states it.

Present your reading of each rule as a **suggestion** and let the user correct
it - the code shows the mechanics, the user owns the intent.

## Step 7 - Ask for whatever cannot be identified

Two answers are always required, on top of the ones Stage 1 already settled:

- **Project** - a repository is not a project. Ask what business name the user
  wants for it, and offer the possibility that the script belongs to an already
  cataloged project despite the repository name. It fills `project`, the
  `<Project>` token of the `id` and the project folder of the path.
- **File name** - the `<Function>` that closes the `storage_notes` path
  (`CYBER/<Client>/Silver/<Project>/AAAA-MM-DD/<Function>.json`).

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

Before closing the stage, check:

- [ ] The YAML parses and carries the template's 15 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `"?"` is quoted, and `NA` used only where the value does not exist.
- [ ] Every id in `sources_raw` and `sources_silver` exists as a file written
      in this session, spelled identically - a typo breaks the graph edge.
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
to a file of its own - and confirm each one as an audit.

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
the trail.

## Step 11 - Generate the files

One file per audit, named `AUDIT_<Project>-<Audit>.yaml`, written to
`Catalog/Skills/Temp/`.

Follow `Catalog/Skills/Templates/3 - AUDIT_[Project]-[Audit].yaml`. It has 9 fields and
no `filters`, `pipeline` or `sample_output`: the only substance is which
records were separated, and it goes in `description`.

Then go back to the Silver files and replace the `"?"` in `generates_audits`
with the ids just settled. The trail is not finished while the two ends of the
edge disagree.

Before closing the trail, check:

- [ ] The YAML parses and carries the template's 9 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `"?"` is quoted, and `NA` used only where the value does not exist.
- [ ] Every id in `sources_silver` exists as a Silver file, and that Silver
      declares this audit back in `generates_audits`.
- [ ] `storage_notes` still says Silver, both in the sentence and in the path.
- [ ] `description` carries the title line, the selection rule and the "Obs:"
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

One Gold per Silver is the default, and three KPIs per file is the starting
point. Deviate only when the user says so.

A Silver whose columns answer nothing on their own may deserve no Gold at all.
Say that instead of inventing indicators to fill the slot - a KPI nobody asked
for still has to be maintained.

## Step 13 - Design the KPIs from the sample

Open the source Silver and read its `sample_output` column by column, asking
what each one lets somebody decide. Every KPI must survive two tests:

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
`Catalog/Skills/Temp/`.

Follow `Catalog/Skills/Templates/4 - GOLD_[Project]-[Function].yaml`. It has 7 fields
and no `storage_notes` - Gold produces no file in the lake.

Then **present every KPI in the answer** - title, calculation and why it
matters - so the user can reject one without opening the file.

Before closing the trail, check:

- [ ] The YAML parses and carries the template's 7 fields, in the same order.
- [ ] Files written with CRLF line endings.
- [ ] `filters` is `null`, lowercase and unquoted, wherever the KPI filters
      nothing. This layer uses null where the others use NA.
- [ ] No `": "` inside a KPI field - they are plain scalars and it breaks the
      parser.
- [ ] Every column named in `calculation`, `filters` and `view` exists in the
      `structure_notes` of the source Silver, spelled identically.
- [ ] Every threshold in a KPI came from the user.
- [ ] Every `reason` says why the number matters, not what it counts.
- [ ] Every id in `sources_silver` exists as a Silver file.

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

If there is no automation, the trail ends here with no file. Say so.

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

Every threshold in the condition comes from the user. An automation with an
invented number is an automation that deletes the wrong thing.

## Step 17 - Generate the files

One file per action, named `AUTOMATA_<Context>-in-<Target>.yaml`, written to
`Catalog/Skills/Temp/`. The same source read twice, once to notify and once to delete,
is two files - they run on different schedules and are approved separately.

Follow `Catalog/Skills/Templates/5 - AUTOMATA_[Context]-in-[Target].yaml`: 13 fields, no
`storage_notes` and no `owner`.

Before closing the trail, check:

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
read as ONE THING, and it is where the two fields that are not a per-dataset
decision get answered at once.

## Step 18 - Read the set as a whole

Open every file written in the session together and check what only shows up
side by side:

- **Every declared source resolves.** Each id in `sources_raw`,
  `sources_silver` and `sources_audit` exists as a file with that exact name.
- **The audit edge agrees on both ends.** Every id in a `generates_audits` has
  a file that declares that Silver back in its `sources_silver`.
- **No `RAW_` or `GOLD_` inside a source list** of any automation.
- **No orphan in the chain.** A Silver nobody consumes and that produces no
  Gold is either the end of a real chain or a file that lost its purpose - say
  which one it is.
- **What is still pending**, counted per field, so the user knows what the
  review will cost before opening the files.

Report what this pass finds however quiet the verbosity is. A broken edge is
not narration.

## Step 19 - Sign the catalog

Two fields close the work, and neither belongs to a single dataset:

- **`owner`** - who documented the catalog. **Do not ask when you already have
  it**: the template may carry it as a default, an earlier stage may have
  settled it, or the user may have signed files of their own in the same
  session. Reuse it and say where you took it from, so a wrong name is
  corrected instead of inherited. Ask only when nothing in reach answers it,
  and ask for the form they want written, not just the name. The field exists
  in Raw, Silver and Audit only.
- **`last_reviewed`** - the current date, single-quoted, in every file of
  every layer. This is the date the catalog was written, not a date read from
  the project README.

Write both into every file that carries the field and report the counts. Then
list what is still `"?"`: the trail is over, and everything left is review.

## Step 20 - Hand it over

Close with a SHORT message. The user has just been through the whole trail:
no recap of the stages, no summary of the decisions, no explanation of what a
layer is. Five things and nothing else:

1. The files that were written, one per line, nothing after the name.
2. Ask them to review the texts and the documented rules, and say that the
   move into `Catalog/Layers/<Client>/HML` happens as soon as they give the go-ahead.
3. That the KPIs of the Gold files need validating in particular - nobody
   asked for those indicators, they were proposed from the columns that
   existed, so they are examples until the business confirms them.
4. That the move is followed by a commit, to sync with Git - the user's own
   step, this skill does not run git commands.
5. That `PRD` comes later, only when the rules are in production.

Keep the pending fields out of it - they were listed in Step 19 and repeating
them buries the instruction. A handover that has to be read twice is a
handover that gets skipped.

## Step 21 - Move on confirmation, then offer to clear Temp

Wait for the user's go-ahead on the review asked for in Step 20. Do not move
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
2. Report what moved, one line per file, in the same order as Step 20.
3. **Then, and only then, ask** whether to clear `Catalog/Skills/Temp/` so it is ready
   for the next project. Wait for a yes - do not clear it as part of the same
   step, and do not clear anything the move in step 1 did not already relocate
   (the dropped repository itself is the user's, never delete it without being
   asked separately).

## Step 22 - Render the graph

Run `Catalog/Scripts/Generate-Graph_Pyvis.py` from the repository root. This is the
catalog's own tool, not the dropped project's - it only reads the YAML files
already sitting under `Catalog/Layers/` and writes `Catalog/DataLake-Graph_Pyvis.html`.
It carries none of the risk the "never run the project's scripts" rule in
Stage 1 exists for, and running it here is expected.

Tell the user the path of the generated file - `Catalog/DataLake-Graph_Pyvis.html`
- and ask them to open it and validate that what just moved renders correctly:
the new nodes appear in the right layer and column, with edges reaching their
declared sources.

If something looks inconsistent - a node with no edge that should have one, a
source that does not resolve, a project split across nodes that do not share
its color - do not fix it yourself. Say what looks wrong and ask the user how
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
- **`last_reviewed` is the last field**, in every layer. The rest of the
  order comes from the template of the stage.
- **The template carries the defaults.** A field whose template comment ends
  in "Example of what the user answers" is copied into the file exactly as the
  template leaves it. `"?"` means unanswered - carry it over and let the user
  fill it on review. Any other value is a standing answer for the whole
  project: write it in and **do not ask the question**. Read those lines before
  the first file of a stage, so you do not ask what the user already answered
  by editing the template.
- Everything else about format lives in the template of the stage - field order,
  when to use `"?"`, when to use `NA`, which text is verbatim. Read it before
  writing the first file, not after the user points at the difference.

## Checking for an existing file before generating

Before writing a new file, check whether `Catalog/Layers/` already documents the same
thing under a different project - the same API endpoint, the same business
rule, the same action on the same target. Cross-project reuse is common, and
a duplicate does not show up until the graph is rendered.

When a match exists:

- **Finish documenting the current file anyway**, read from this project's own
  code. Do not skip it, and do not copy the old file blind - the two may have
  diverged.
- **Skip re-collecting the output sample only when the match is exact** - same
  platform, same endpoint, same filters (Raw) or the same source columns
  (Silver). Reuse the `sample_output` already sitting in the old file instead
  of asking the user to run the script again for a picture you already have.
  When anything about the call differs - a filter, a field the code adds or
  drops - get a fresh sample as usual; that difference is exactly what the
  comparison at the end needs to show.
- **At the end, present the differences** between the two files to the user,
  field by field, and ask whether to keep both or drop the old one in favor of
  the one just written.
- **If the user keeps the new one, give it the same `id` as the old file** -
  it replaces it rather than sitting beside it under a different name, so
  every edge already pointing at the old id keeps resolving.
- **If the user keeps the old one instead, discard the draft written this
  session** - it never moves to `Catalog/Layers/`. From here on, reference the old
  file's id directly as the source in this project's own Silver/Audit files,
  exactly as if this project's own Raw stage had produced it.

This runs per file, against the whole `Catalog/Layers/` tree, including other
projects' folders. It is not the same check as Step 18's "every declared
source resolves," which runs once at the end, over the files of the current
session only.

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
  numbered block of ten items, and no several questions in a single call: the
  user answers part of it and the rest slips through as if it had been
  confirmed.
- **Show an example of the expected format** in every free-text question - an
  example of the format, never a guess at this project's value presented as
  though it were the answer.
- If the user picks an "other / I'll describe it" option and no text comes with
  it, **ask again**. A chosen option with no content is not an answer.
- If the user does not know, **do not block**: use the template's placeholders
  (`/path/example` for an endpoint path, `"?"` for a business field) and move
  on. The user fills them in on review.

## Getting the output sample (Raw and Silver only)

- **Do not rely on console output, and do not ask the user to write the print
  themselves.** A sample can be too large to paste without truncation. Edit
  the script and, instead of printing, append the record to one shared text
  file for the whole session: `<dropped repository root>/catalog_samples.txt`
  (append mode, `"a"`, `encoding="utf-8"`), preceded by a one-line English
  comment saying it is for the catalog sample. Where the write goes depends on
  the stage: Raw appends the record right after the API call and before any
  transformation; Silver appends it after the record is assembled and before
  it is written to disk.
- One entry per dataset, one record each, preceded by a header line naming the
  dataset (`=== <Endpoint or Function> ===`) so entries stay tell-apart when
  several scripts write to the same file. In Raw it must carry the wrapper the
  response puts around it; when the extraction is an SDK iterator, write the
  first item of the iteration.
- Then **tell the user the path of the file** and that every script that needs
  a sample can be run in one pass, in any order - append mode means nothing
  overwrites. Wait for them to say the run is done, then **read the file
  yourself** with the Read tool. Do not write the catalog file with an
  invented sample.
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
- **Put the script back exactly as it arrived.** Once every sample is read and
  the catalog files are written, remove every line added to reach it - the
  write call, the comment, the blank line - and say that you removed them.
  The script belongs to the project, not to the cataloging, and a leftover
  write floods a shared file on every future run, inside a try/except that
  hides the real cause. The same applies to anything else touched to get the
  sample. Then **delete `catalog_samples.txt` itself** - it is scratch for
  this cataloging session, not a project artifact, and a leftover copy is
  stale the moment the next project reuses the same file name.
- If the user cannot run the script, leave `"?"` and move on.