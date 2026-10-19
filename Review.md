---
name: catalog-review
description: Load the full context of the Data Lake catalog without changing anything - the two skill files, every YAML under Catalog/Layers and the reference projects in Projects/ - report what is inconsistent, and then make only the pointed fixes the user asks for, one request at a time. Never opens a .env file. Use when the user asks to review the catalog, load its context, or fix a specific point in a YAML, a skill file or a reference project.
---

```text
Use the file 'Review.md' to load the context of the catalog and make the fixes I ask for.
```

# Review the catalog and make pointed fixes

**Scope: the catalog repository and the reference projects, read whole, changed only where the user points.**
The work has two phases, and the first one never writes:

| Phase | What happens | What is written |
|---|---|---|
| Context | read the skill files, every layer and every reference project, then report | nothing |
| Fixes | one change per request - the one the user asked for | only the files that change needs |

This file does not document projects (that is `Catalog/Skills/Catalog.md`) and does not build or
standardize code (that is `Catalog/Skills/Code.md`). It reads what those two produced and corrects
it point by point.

## Step 0 - Set the verbosity, keep the user located

### Model check

Before the first message, silently check which model this session is running - it is stated in the
environment context. This file expects at least a mid-tier current-generation model (Sonnet-class or
above): telling a real inconsistency from a deliberate choice, and following one change through
every file that depends on it, is not reliable on a fast/cheap tier. If the model is below that bar,
say so before anything else and ask the user to switch (in Claude Code, `/model`). Otherwise say
nothing about it.

### Verbosity

**The default is quiet.** Offer the switch in the opening message, in one line. Quiet means a status
line, the result or the question, and nothing else - no list of files opened, no narration of how the
reading was done. Verbose shows the reasoning: the comparisons as tables, the checks one by one.

**Quiet is never silence about a problem.** Whatever the setting, always say: anything urgent found
(see Step 4), every inconsistency found, anything assumed to keep going, and every file touched.

### Language

This file is written in English. The conversation follows the language the user writes in. Each file
keeps its own language when edited: YAML values follow the language of the templates, code and code
comments are English, project READMEs are English.

### The status line

Every answer opens with the phase and the position inside it:

    [Context 2/3] Layers - main client read, replicas compared
    [Fix 3] SILVER_<Project>-<Function>.yaml - sample corrected, YAML parses

### What may be read

- **Everything in the catalog repository**, except what its `CLAUDE.md` restricts.
- **In each reference project**: `README.md`, `CLAUDE.md`, `LICENCE.md`, `Scripts/requirements.txt`
  and every script.
- **Never a `.env` file - nor `.env.*`.** Do not open, read, print, search, diff, hash it or list
  its variable names, in any folder. A search over a folder must exclude it explicitly (a `glob`
  filter, or a file list built by extension): a recursive search without that filter reads the
  `.env` along with everything else. Git commands that print only paths (`git ls-files`,
  `git status`) are fine. `git diff`, `git show` or `git log -p` on a `.env` are not. The one
  exception is a run or a probe that follows Code.md (see "What may be written"). It loads the
  `.env` the way the project scripts do, and prints at most set / missing for the variables the
  scripts use - never a value.
- **Never the data files** - `*.json`, `*.csv`, `*.db`, anything under `Datas/`. The YAMLs under
  `Catalog/Layers/` are catalog files, not data, and are read normally.
- When a fix depends on what a data file or a `.env` contains, ask the user to describe it.

### What may be written

- **Context phase: nothing.** Not a line, not a line ending, not a renamed file. Scratch files go to
  the session scratchpad.
- **Fixes phase: only the files the requested fix needs, and the ones that depend on it** (Step 6).
  Each one is named to the user before the edit, or in the same answer as the edit.
- **The skill files** - `Catalog/Skills/Catalog.md`, `Catalog/Skills/Code.md`, the templates under
  `Catalog/Skills/Templates/` and this file - change only when the user's request is about them.
  They set the standard for every future project. A fix to a YAML never edits a template to make the
  YAML fit.
- **No git command that writes** - `add`, `commit`, `rm`, `mv`, `checkout`, `reset`, `stash`,
  `push`. Committing is the user's step.
- **Nothing is deleted** unless the user names the file to delete.
- **Never run a project's script on your own initiative.** The scripts authenticate against
  production platforms. Three cases are allowed, each with its own rule:
  - a validation run, or a read-only probe against a platform, follows "Running the project's code"
    in Code.md: the user's go-ahead for that script, read-only scripts only, the output seen through
    the in-memory summary;
  - a capture for a catalog sample follows Catalog.md: you add the capture, and the user runs it;
  - the catalog's own `Catalog/Scripts/Generate-Graph_Pyvis.py` may run after the user accepts it
    (Step 8).

  Your own checks run from the scratchpad and never import or execute a project script.

# Phase 1 - Context

## Step 1 - Read the skill files

Read `Catalog/Skills/Catalog.md` and `Catalog/Skills/Code.md` whole, then the five templates under
`Catalog/Skills/Templates/`. Together they are the rule set every file in the catalog and every
project was made under. They are also the measure of every fix: a correction that breaks a rule
written there is not a correction.

## Step 2 - Read the layers

List every file under `Catalog/Layers/` by client, environment (`HML`, `PRD`) and layer folder.

- **Find the main client.** It is the folder the others were replicated from: its chains are complete
  (inventory crossing, audits, automations) and its files are the reference for the replicas. When it
  is not obvious from the files, ask.
- **Read the main client whole**, every environment.
- **Compare each replica file with the main client's file of the same name**, ignoring the path line
  of `storage_notes`. Read whole only the files that differ and the files that exist only in that
  client.
- **The same name is not the same content.** Two clients can hold the same id for different projects
  (another source, another repository). Compare `source_repo` and the content, never the id alone.

While reading, build:

- the map: which project, from which repository, has which files in which client and environment;
- the chains: Raw -> Silver -> Audit / Gold -> Automation, with every `sources_*` and
  `generates_audits` edge;
- the schedule: the slot of every Raw, Silver and Automation, per client and platform.

And note, without fixing:

- a source that does not resolve inside its own client, or an audit edge that disagrees at its two
  ends;
- a sample that contradicts the filters or the `structure_notes` of its own file;
- a column named in a Gold `calculation`, `filters` or `view` that the source Silver does not have -
  for a Gold built on an audit, the Silver that audit came from;
- an Audit with no Gold of its own, and no reason recorded for it (Step 12 of Catalog.md);
- a `"?"` still pending, counted per field;
- a free-text sample value that looks like a real name or e-mail that was not anonymized - as a doubt,
  since it may be fictitious;
- a file written in an older style than its template.

## Step 3 - Read the reference projects

The projects live in the folder `Projects/` at the root of the catalog repository, one folder per
project. If the folder is not there, ask where the projects are.

For each project, read the files allowed above. Never open `Scripts/.env` or anything under `Datas/`.
Then check, read-only:

- **The standard.** Measure the project against "The standard" in Code.md, using its buckets and its
  table of known deviations. A deviation Code.md already lists is reported as known, and a new one as
  new.
- **The fixed files.** Compare `CLAUDE.md` and `LICENCE.md` with the checksums in Code.md. The
  projects under `Projects/` carry no `LICENCE.md` - the root licence of the repository covers them -
  so a missing one there is not a finding. A clone checked out with `core.autocrlf` has working-tree
  bytes that differ from the committed ones, so a different checksum is not yet a different version.
  Read `git ls-files --eol` before calling it one.
- **Encoding.** Check BOM and line endings of every script by its bytes.
- **Shared copies.** A file that several projects copy verbatim, such as the inventory extraction, is
  compared across the projects. A difference is reported, not normalized.
- **Tracked sensitive files.** Run `git ls-files` and look only at the paths, for a `.env`, anything
  under `Datas/`, or a `.csv`/`.json`. A tracked `.env` is urgent (Step 4). Report it from its path
  and its commit dates, never from its content. Check too that the project has the `.gitignore`
  Code.md requires (`.env` and `Datas/`). A missing one is reported, since a `git add -A` would
  publish both.
- **Age.** Check the last commit of each project (`git log -1 -- Projects/<project>/`), to know which
  one is the newest example of the standard.

Then cross each project with the catalog. Map every script output to its Raw, Silver and Audit ids,
and list both directions:

- what the code does that the catalog does not document - an output set apart with no audit, a lookup
  call with no Raw, a column the YAML does not list;
- what the catalog documents that the code does not do - an audit or an automation with no code, a
  filter, a batch size or a name that differs.

A difference is not automatically an error. An automation registered before its code exists is
allowed by Catalog.md. Report it as a difference and let the user judge.

## Step 4 - Report the context, then wait

One message, in this order:

1. **Anything urgent, first** - a tracked `.env`, a credential that reached a file or the screen, a
   data file committed. Say what to do about it: rotate the credential, remove the file from tracking,
   add a `.gitignore`. It is the user's action, not this file's.
2. **The map** - one table, project x client, with environment and file counts.
3. **The projects** - one row each: last commit and how far it is from the standard.
4. **The pending list** - every inconsistency found in the layers and between code and catalog,
   numbered, one line each, with a link to the file. The user refers to items by these numbers for the
   rest of the session.
5. One line saying that nothing was changed.

Then stop. Do not propose an order of fixes and do not start fixing. The next move is the user's.

# Phase 2 - Pointed fixes

## Step 5 - Take the request as asked

- **A fix is what the user asked, nothing more.** Make the smallest change that resolves the point -
  no reformatting around it, no improvement nobody asked for.
- A request may name a pending item by its number, or describe a new point.
- When the request leaves a real choice open, ask one question with the reading you recommend. Do not
  ask what the request already answers.
- **Found while fixing, not asked: report it, never fix it in passing.** Add it to the pending list
  with a new number. Updating what depends on the change is part of the fix (Step 6), not a fix in
  passing.

## Step 6 - Find everything that depends on the change

**No change is made alone.** Before any fix, even a one-line request in one file, find everything that
depends on what changes. Nothing may be left pointing at the old value. A fix that leaves a README
describing a folder that no longer exists, or a Gold reading a column that was renamed, has not fixed
anything: it has moved the inconsistency somewhere else.

- **Search for the old value** across the project and the whole catalog: the name, path, id, column or
  value the fix replaces. Search with a filter that excludes `.env` and data files (see "What may be
  read"). A path is searched in every form it can appear in: with `/` and `\`, quoted, inside a
  command.
- **Read each hit** and decide whether it depends on the change. Typical dependents:
  - in a project: the README (the scripts table, the run commands, the sentence on run order), the
    other scripts (an input path or file name a later script looks for, a relative path whose depth
    changes when a folder moves), `requirements.txt`, the project's `CLAUDE.md`;
  - in the catalog: every YAML that names it - `id`, `sources_*`, `generates_audits`,
    `structure_notes`, sample keys, the Gold `calculation`, `filters` and `view`, the `storage_notes`
    path, `source_repo`, and any text in `extraction_notes` or `pipeline` that names a script or a
    file;
  - the replicas of that YAML in the other clients;
  - the skill files, when they name what changes - such as the table of known deviations in Code.md
    naming a project's folder. A skill file is not changed inside the fix: report it as stale, and it
    changes on its own request.
- **What cannot be seen from here** - a scheduler, a pipeline or a person that calls a script by its
  path - breaks silently on a rename. Name it in the plan, so the user updates it.

An example. Renaming a project's source folder to give it its number touches four places:

- the README's scripts table and run commands, which name the old path;
- the scripts, which may build paths relative to their own folder;
- the table of known deviations in Code.md, which names the old folder;
- whatever schedules the scripts, which calls the old path.

Then:

- **When the search finds nothing beyond the file the request names**, apply the fix (Step 7) and
  report it together with the result of the search.
- **Otherwise, present the plan first and wait for the yes**: each file, its lines before and after,
  and every dependent left out, with the reason. A short yes applies to the whole plan.

The plan always covers:

- **Every copy.** A fix in one client's YAML may belong in the replicas too. List them and ask: all
  clients, only this one, or which. A renamed id follows the rename rule of Catalog.md: rename the
  file, `id` and the `storage_notes` path, and every `sources_*` and `generates_audits` that names it,
  in every client.
- **Every consumer.** A Silver column renamed or removed also touches its `structure_notes`, its sample
  keys, and every Gold `calculation`, `filters` and `view` that names it - including the Golds built
  on an audit of that Silver. An audit added or removed touches the `generates_audits` of its
  Silver, its own Gold, and the `sources_audit` of every Gold and automation that reads it.
- **Code and catalog together.** A fix in a script that changes what the catalog documents - a column,
  a filter, an output, a file set apart - leaves a YAML stale. Name it and ask whether to update it in
  the same fix. The same goes the other way.
- **Renames happen in the file system.** A file or folder is moved, never renamed with `git mv` - git
  sees the move on its own, and committing stays the user's step.

## Step 7 - Apply

In a YAML under `Catalog/Layers/`:

- Follow the template of that layer and "Writing the files" in Catalog.md: field order, CRLF, `"?"`
  quoted, `NA` or `null` as the layer uses, no blank line between keys, Gold KPIs separated by a blank
  line, no `": "` inside a KPI plain scalar.
- A sample that is touched follows the anonymization rules of the template.
- `last_reviewed` keeps its original date unless the user asks otherwise. That is the rule Catalog.md
  sets for an edit made outside a cataloging run. Say so in the report, so the user can ask for the
  current date.

In a reference project:

- Follow the standard in Code.md. A fix that changes behavior - an output, a column, a filter, a
  window (bucket 3) - is made only because the user asked for it. Say exactly what the output will
  look like after the fix.
- Keep the file's bytes: BOM when it has one, CRLF.
- The script is not run. When a fix needs a run to be validated, say so. The run is the user's, or
  follows "Running the project's code" in Code.md: the user's go-ahead for that script, and only for a
  read-only script.

In a skill file:

- Keep its style and keep it generic: no client, source or tenant fact. The method goes in, the facts
  of one project never do.

In every file: edit with the Edit tool, or with a script that reads and writes bytes - never
`sed -i`, which rewrites the file with LF endings. Check the line endings after each edit.

## Step 8 - Verify and report

- **YAML**: it parses (load it from a scratchpad script), the line endings are CRLF, and every
  `sources_*` it declares resolves inside its own client.
- **Python**: it parses (`ast.parse` on the text, from a scratchpad script). It is never imported or
  run. Encoding and line endings are unchanged.
- **Nothing left behind**: run the Step 6 search again for the old value. Every hit that remains is
  either intended, such as a skill file reported as stale, or listed in the report. Say how the search
  was made.
- **Report**: the status line, then the files changed, one per line, then what was verified. Mark the
  pending item as closed.
- **The graph**: after a change under `Catalog/Layers/`, offer once to regenerate it with
  `Catalog/Scripts/Generate-Graph_Pyvis.py`. The script only reads the layers and writes
  `Catalog/DataLake-Graph_Pyvis.html`. Run it only on a yes, and ask the user to check the nodes and
  edges the fix touched.

## Step 9 - Close

When the user says the review is done, close with a short message:

1. The files changed in the session, one per line.
2. The pending items still open, by number, one line each.
3. Anything urgent still open from Step 4, repeated.
4. Committing is the user's step - this file does not run git commands that write.

# Rules that apply to every step

## How to ask

- **One question per message**, in one or two lines, with the recommended answer first when there is
  one.
- **Show an example of the expected format** in every free-text question - an example of the format,
  never a guess at the answer.
- **Say what the answer changes**: "if yes, 3 files in 2 clients change".
- When the user does not know, do not block. Leave the point on the pending list and move on.

## Reporting

- Every result says how it was obtained: read, compared, parsed, or not checked.
- Every mistake is reported in the answer where it is found, with its consequence and the fix - a file
  touched by accident, a replica forgotten, a wrong reading.
- Numbers are counted, not estimated.
