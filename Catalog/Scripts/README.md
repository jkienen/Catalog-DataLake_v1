# Graph Generator

Renders `Catalog/DataLake-Graph_Pyvis.html` from the YAML files under `Catalog/Layers/`: an interactive, color-coded graph of the whole catalog — one column per layer, with the nodes grouped into named boxes (one per platform in Raw), filterable by client, platform and project, with a detail panel per node.

---

## Environment Setup and Usage

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

<details>
<summary><strong>Configuration (script constants)</strong> (click to expand)</summary>

A set of constants at the top of the script (`Part 1: Setup`) controls how the graph looks and reads, without touching the logic that builds it. Change them directly in `Generate-Graph_Pyvis.py` and re-run the script to apply them.

<table width="100%">
<thead>
<tr><th>Variable<div><img width="320" height="1" alt=""></div></th><th>Controls<div><img width="880" height="1" alt=""></div></th></tr>
</thead>
<tbody>
<tr><td><code>TITLE</code></td><td>Text shown at the top of the canvas, over the graph.</td></tr>
<tr><td><code>TAB_TITLE</code></td><td>Browser tab title, independent of <code>TITLE</code>.</td></tr>
<tr><td><code>REPO</code></td><td>Source repository link, shown as a clickable box in the bottom-left corner. Set to <code>""</code> to hide the box entirely.</td></tr>
<tr><td><code>PARENT_CLIENT</code></td><td>Main client, with the same name as its folder under <code>Catalog/Layers/</code>. It is loaded first, listed first in the "Client" selector (so it is the one selected when the page opens) and shown with <code>PARENT_LABEL</code>. The other clients follow in alphabetical order.</td></tr>
<tr><td><code>PARENT_LABEL</code></td><td>Text appended to the main client's name in the "Client" selector, for example <code>CLIENT-A (Parent)</code>.</td></tr>
<tr><td><code>CLIENT_LABELS</code></td><td>Name shown in the "Client" selector for each folder under <code>Catalog/Layers/</code>, for example <code>{"CLIENT-A": "Client A Corp"}</code>. A folder not listed in the dictionary is shown with its own name. Only the shown text changes: the filters, <code>PARENT_CLIENT</code> and the lake paths keep using the folder name, and the selector order follows the shown name.</td></tr>
<tr><td><code>BOX_NAMES</code></td><td>Name of the box each layer is drawn in, shown in uppercase at the top of the box, for example <code>{"gold": "DASHBOARDS"}</code>. Layers with the same name share a single box, side by side. A layer not listed in the dictionary gets one box per platform, named after the platform, and a platform's nodes are never split across sub-columns (unless it alone exceeds <code>MAX_ROWS_PER_COLUMN</code> — then its box spans its own sub-columns). The boxes of smaller platforms sit side by side under a wider one, stretched to its width, instead of leaving the space next to it empty. Each box takes the color of the first layer it contains.</td></tr>
<tr><td><code>FAVICON</code></td><td>Browser tab icon, as a fully local inline SVG (no external file or network fetch).</td></tr>
<tr><td><code>COLORS</code></td><td>Hex color per layer, used for that layer's node dots.</td></tr>
<tr><td><code>COLUMN</code></td><td>Horizontal position of each layer's column, as a multiplier of <code>COL_WIDTH</code>.</td></tr>
<tr><td><code>COL_WIDTH</code></td><td>Pixel width of each layer's column.</td></tr>
<tr><td><code>ROW_HEIGHT</code></td><td>Vertical distance in pixels between two nodes of the same column.</td></tr>
<tr><td><code>NODE_SIZE</code></td><td>Radius in pixels of each node's dot. It also enters the calculation of the space the boxes reserve around the nodes.</td></tr>
<tr><td><code>MAX_ROWS_PER_COLUMN</code></td><td>Maximum number of visible nodes in a column. When a layer exceeds that number after the filters, it is split into balanced side-by-side sub-columns, and the layers to its right shift to make room. Applies to any layer.</td></tr>
<tr><td><code>SUBCOLUMN_WIDTH</code></td><td>Horizontal distance in pixels between the sub-columns of the same layer.</td></tr>
<tr><td><code>BOX_PADDING</code></td><td>Space in pixels between the nodes and the box edge.</td></tr>
<tr><td><code>BOX_LABEL_HEIGHT</code></td><td>Extra space in pixels at the top of the box, reserved for its name.</td></tr>
<tr><td><code>BOX_GAP</code></td><td>Minimum distance in pixels between two boxes. If a box would run into the box on its left (for example, because of long labels), its layer, and every layer after it, shifts right until that distance is kept.</td></tr>
<tr><td><code>STATE_LABELS</code></td><td>The <code>(value, label)</code> pairs behind the "States" filter checkboxes. <code>value</code> must match the <code>PRD</code>/<code>HML</code> folder name under <code>Catalog/Layers/&lt;Client&gt;/</code>; <code>label</code> is the text shown in the sidebar.</td></tr>
<tr><td><code>NON_PRD_OPACITY</code></td><td>Opacity (from 0 to 1) of the nodes not in production, that is, of any state other than <code>PRD</code>: the dot and the label are drawn faded, so what already runs in production stands out. While it is below <code>1</code>, the "States" filter shows, next to each state, a dot drawn the way its nodes are. Use <code>1</code> to draw them like the others (the dot goes away too).</td></tr>
<tr><td><code>HIGHLIGHT_COLOR</code></td><td>Hex color of the highlight when a node is clicked. The clicked node and the nodes connected to it light up: they are drawn at full opacity, even when not in production, with a border and a glow in this color, and the edges between them take this color too. Clicking empty space turns the highlight off.</td></tr>
<tr><td><code>HIGHLIGHT_CHAIN</code></td><td>Which nodes light up together with the clicked node. <code>True</code> lights the whole chain: every source upstream and every consumer downstream, walked the same way the "Projects" filter does. <code>False</code> lights only the nodes one edge away.</td></tr>
<tr><td><code>DETAIL_FIELDS_BY_LAYER</code></td><td>Which fields of a node's YAML show up in the detail panel when it is clicked, per layer.</td></tr>
</tbody>
</table>

</details>

<details>
<summary><strong>Dependencies</strong> (click to expand)</summary>

- [`pyyaml`](https://pyyaml.org/): reads the `.yaml` files under `Catalog/Layers/`, one per dataset, rule, audit, indicator or automation.
- [`networkx`](https://networkx.org/): builds the node/edge structure from the links declared in each YAML (`sources_raw`, `sources_silver`, `sources_audit`, `generates_audits`) — no rendering of its own. Each node is keyed by client + `id`, so the same `id` can exist in several clients, and a link only resolves inside its own client.
- [`pyvis`](https://pyvis.readthedocs.io/): turns that graph into the interactive HTML page (`Catalog/DataLake-Graph_Pyvis.html`), using [vis.js](https://visjs.org/) to draw and let the user drag, zoom and click nodes. The client/platform/project filters and the detail panel are layered on top of pyvis's own output.

</details>

<details>
<summary><strong>A Note on Internet Access and Data Exposure</strong> (click to expand)</summary>

**The script itself makes no network calls.** It only reads the local `.yaml` files under `Catalog/Layers/` and writes a local HTML file — nothing leaves the machine at this step.

**The internet dependency happens later, in the browser.** The generated HTML loads `vis-network.js` from an external CDN (`cdn_resources="remote"`) instead of bundling it locally, so opening the file requires a connection; without one, the page loads but the graph doesn't render.

**What that dependency means for security.** The catalog data itself — labels, descriptions, samples, KPIs — is embedded as escaped text, not executed as code, so the catalog's own content cannot inject a script. The one piece of code the page runs from the outside is `vis-network.js`, fetched fresh from the CDN on every open: a standard third-party-CDN trust relationship, worth naming plainly for an internal security catalog even though it is not a flaw specific to this script. If that CDN were compromised, or the connection intercepted, the injected script would run in the same page as the catalog data — a low-probability but non-zero supply-chain exposure for an internal catalog.

**If that trade-off matters for your environment**, `pyvis` also supports `cdn_resources="local"`, which copies the library next to the generated HTML instead of fetching it — the page then renders fully offline. That is a one-line change in `Generate-Graph_Pyvis.py` if the team decides the extra local file is worth it.

</details>
