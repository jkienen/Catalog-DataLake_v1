# Graph Generator

Renders `Catalog/DataLake-Graph_Pyvis.html` from the YAML files under `Catalog/Layers/`: an interactive, color-coded graph of the whole catalog — one column per layer, filterable by client, platform and project, with a detail panel per node.

---

## Usage

```
cd Catalog/Scripts
pip install -r requirements.txt
```

```
python ./Generate-Graph_Pyvis.py
```

---

<details>
<summary><strong>Configuration</strong> (click to expand)</summary>

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

</details>

<details>
<summary><strong>Dependencies</strong> (click to expand)</summary>

- [`pyyaml`](https://pyyaml.org/): reads the `.yaml` files under `Catalog/Layers/`, one per dataset, rule, audit, indicator or automation.
- [`networkx`](https://networkx.org/): builds the node/edge structure from the links declared in each YAML (`sources_raw`, `sources_silver`, `sources_audit`, `generates_audits`) — no rendering of its own.
- [`pyvis`](https://pyvis.readthedocs.io/): turns that graph into the interactive HTML page (`Catalog/DataLake-Graph_Pyvis.html`), using [vis.js](https://visjs.org/) to draw and let the user drag, zoom and click nodes. The client/platform/project filters and the detail panel are layered on top of pyvis's own output afterward.

</details>

<details>
<summary><strong>A Note on Internet Access and Data Exposure</strong> (click to expand)</summary>

**The script itself makes no network calls.** It only reads the local `.yaml` files under `Catalog/Layers/` and writes a local HTML file — nothing leaves the machine at this step.

**The internet dependency happens later, in the browser.** The generated HTML loads `vis-network.js` from an external CDN (`cdn_resources="remote"`) instead of bundling it locally, so opening the file requires a connection; without one, the page loads but the graph doesn't render.

**What that dependency means for security.** The catalog data itself — labels, descriptions, samples, KPIs — is embedded as escaped text, not executed as code, so the catalog's own content cannot inject a script. The one piece of code the page runs from the outside is `vis-network.js`, fetched fresh from the CDN on every open: a standard third-party-CDN trust relationship, worth naming plainly for an internal security catalog even though it is not a flaw specific to this script.

**If that trade-off matters for your environment**, `pyvis` also supports `cdn_resources="local"`, which copies the library next to the generated HTML instead of fetching it — the page then renders fully offline. That is a one-line change in `Generate-Graph_Pyvis.py` if the team decides the extra local file is worth it.

</details>
