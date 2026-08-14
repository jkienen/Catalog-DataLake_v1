# Graph Generator

Renders `Catalog/DataLake-Graph_Pyvis.html` from the YAML files under `Catalog/Layers/`: an interactive, color-coded graph of the whole catalog.

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
cd Catalog/Scripts
pip install -r requirements.txt
```

```
python ./Generate-Graph_Pyvis.py
```

```
deactivate
```

---

## Configuration

A handful of constants near the top of the script (`Part 1: Setup`) control how the graph looks and reads, without touching the logic that builds it. Change them directly in `Generate-Graph_Pyvis.py` and re-run the script to apply them.

<table width="100%">
<thead>
<tr><th>Variable<div><img width="320" height="1" alt=""></div></th><th>Controls<div><img width="880" height="1" alt=""></div></th></tr>
</thead>
<tbody>
<tr><td><code>TITLE</code></td><td>Text shown at the top of the canvas, over the graph.</td></tr>
<tr><td><code>TAB_TITLE</code></td><td>Browser tab title, independent of <code>TITLE</code>.</td></tr>
<tr><td><code>REPO</code></td><td>Source repository link, shown as a clickable box in the bottom-left corner. Set to <code>""</code> to hide the box entirely.</td></tr>
<tr><td><code>FAVICON</code></td><td>Browser tab icon, as a fully local inline SVG (no external file or network fetch).</td></tr>
<tr><td><code>COLORS</code></td><td>Hex color per layer, used for that layer's node dots.</td></tr>
<tr><td><code>COLUMN</code></td><td>Horizontal position of each layer's column, as a multiplier of <code>COL_WIDTH</code>.</td></tr>
<tr><td><code>COL_WIDTH</code></td><td>Pixel width of each layer's column.</td></tr>
<tr><td><code>STATE_LABELS</code></td><td>The <code>(value, label)</code> pairs behind the "States" filter checkboxes. <code>value</code> must match the <code>PRD</code>/<code>HML</code> folder name under <code>Catalog/Layers/&lt;Client&gt;/</code>; <code>label</code> is the text shown in the sidebar.</td></tr>
<tr><td><code>DETAIL_FIELDS_BY_LAYER</code></td><td>Which fields of a node's YAML show up in the detail panel when it is clicked, per layer.</td></tr>
</tbody>
</table>

---

## Dependencies

- [`pyyaml`](https://pyyaml.org/): a library for reading and writing YAML files in Python. Here it reads the `.yaml` files under `Catalog/Layers/`, one per dataset, rule, audit, indicator or automation.
- [`networkx`](https://networkx.org/): a library for creating and analyzing graphs (nodes and the edges between them) as plain Python objects, with no rendering of its own. Here it builds that node/edge structure from the links declared in each YAML (`sources_raw`, `sources_silver`, `sources_audit`, `generates_audits`).
- [`pyvis`](https://pyvis.readthedocs.io/): a library that takes a graph (a `networkx` graph, in this case) and turns it into an interactive HTML page, using the JavaScript library [vis.js](https://visjs.org/) to draw and let the user drag, zoom and click nodes in the browser. Here it renders the graph as `Catalog/DataLake-Graph_Pyvis.html`, and the script layers the client/platform/project filters and the detail panel on top of that page after `pyvis` generates it.

---

## A Note on Internet Access and Data Exposure

**The script itself makes no network calls.** It only reads the local `.yaml` files under `Catalog/Layers/` and writes a local HTML file: the catalog data never leaves the machine at this step, and nothing is uploaded anywhere.

**The internet dependency happens later, in the browser.** The generated HTML loads the `vis-network.js` library from an external CDN (`cdn_resources="remote"` in the script) instead of bundling it locally, so opening `Catalog/DataLake-Graph_Pyvis.html` requires an internet connection; without it, the page loads but the graph does not render.

**What that dependency means for security.** The catalog data itself (node labels, descriptions, samples, KPIs) is embedded directly in the local HTML file, escaped as text, not executed as code, so the catalog's own content cannot inject a script into the page. The one piece of code the page does execute from the outside is `vis-network.js`, fetched fresh from the CDN every time the file is opened. That is a standard third-party-CDN trust relationship, not a flaw specific to this script, but it is worth naming plainly: if that CDN were ever compromised or the connection intercepted, the injected script would run on the same page as the catalog's data. For an internal security catalog, that is a low-probability but non-zero supply-chain exposure.

**If that trade-off matters for your environment**, `pyvis` also supports `cdn_resources="local"`, which copies the JavaScript library next to the generated HTML instead of fetching it from the CDN; the page then renders fully offline and makes no external request at all. That is a one-line change in `Generate-Graph_Pyvis.py` if the team decides the extra local file is worth trading for removing the CDN dependency.
