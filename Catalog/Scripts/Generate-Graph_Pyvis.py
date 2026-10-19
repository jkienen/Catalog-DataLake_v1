#################################### Part 0: Import modules ->

import os
import re
import html
import json
import yaml
import networkx as nx
from datetime import datetime
from pyvis.network import Network



#################################### Part 1: Setup ->

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS_DIR = os.path.join(ROOT, "Layers")

# Shown at the top of the side panel, over the canvas
TITLE = "DATA LAKE"

# Shown in the browser tab (title bar) - independent of TITLE
TAB_TITLE = "Catalog - Data Lake"

# Source repo documentation
REPO = "https://github.com/jkienen/Catalog-DataLake_v1"

# Main client: always loaded first, listed first in the Client selector (so
# it is the one selected when the page opens) and shown with PARENT_LABEL.
# Must match the folder name under Layers/.
PARENT_CLIENT = "CLIENT-A"
PARENT_LABEL = "(Parent)"

# Text shown in the Client selector, per folder under Layers/ - e.g.
# {"CLIENT": "Client Corp Ltd"}. A folder not listed here is shown with its own
# name. Only the shown text changes: filters, PARENT_CLIENT and the lake
# paths keep using the folder name.
CLIENT_LABELS = {
  "CLIENT-A": "Client A",
  "CLIENT-B": "Client B",
  "CLIENT-C": "Client C",
}

# Every node is drawn inside a box, with the box name on top (shown in
# uppercase). Name of the box of each layer - layers with the same name
# share one box, side by side. A layer left out gets one box per platform
# instead, named after the platform, and a platform is never split across
# sub-columns (unless it alone has more than MAX_ROWS_PER_COLUMN nodes -
# then its box spans its own sub-columns). The smaller platform boxes sit
# side by side under a wider one, all stretched to its width.
BOX_NAMES = {
  "silver": "PIPELINES",
  "audit": "PIPELINES",
  "gold": "DASHBOARDS",
  "automation": "SOAR",
}

# Browser tab icon - data URI, fully local (no external file/network fetch).
# <link rel="icon"> needs an image, not raw text, so the emoji is wrapped in
# the minimal SVG needed to render it as one - nothing else is added to it.
FAVICON = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text x='50' y='75' font-size='80' text-anchor='middle'>🔻</text></svg>"

# Layout: each layer gets a fixed column
COLORS = {"raw": "#ff7f50", "silver": "#4fc3f7", "audit": "#ab47bc", "gold": "#ffd54f", "automation": "#66bb6a"}
COLUMN = {"raw": 0, "silver": 0.7, "audit": 1.2, "gold": 1.9, "automation": 2.4}
COL_WIDTH = 650
ROW_HEIGHT = 90
NODE_SIZE = 16

# A layer with more visible nodes than MAX_ROWS_PER_COLUMN (after the
# filters) is split into balanced side-by-side sub-columns, SUBCOLUMN_WIDTH
# apart, and every layer to its right shifts by the extra width. Applies to
# any layer.
MAX_ROWS_PER_COLUMN = 15
SUBCOLUMN_WIDTH = 300

# Space around the boxes of BOX_NAMES: BOX_PADDING between the nodes and the
# box edge, BOX_LABEL_HEIGHT on top for the name, BOX_GAP between two boxes.
# A box never runs into the one on its left - its layer (and every layer
# after it) moves right until they are BOX_GAP apart.
BOX_PADDING = 20
BOX_LABEL_HEIGHT = 28
BOX_GAP = 40

# States checkbox: (value stored on the node, label shown in the sidebar).
STATE_LABELS = [("PRD", "In production"), ("HML", "In staging")]

# Nodes not in production (any state but PRD) are drawn faded, dot and
# label, at this opacity - 1 draws them as the others. While below 1, the
# States filter shows each state's look as a dot after its label.
NON_PRD_OPACITY = 0.40

# Clicking a node lights it up together with the nodes connected to it: they
# are drawn at full opacity (even when not in production), with a border and a
# glow in HIGHLIGHT_COLOR, and the edges between them take the same color.
# HIGHLIGHT_CHAIN True lights the whole chain - every source upstream and every
# consumer downstream, walked as the Projects filter does. False lights only the
# nodes one edge away. Clicking empty space turns the highlight off.
HIGHLIGHT_COLOR = "#ff1744"
HIGHLIGHT_CHAIN = True

# Fields shown in the detail panel, per layer. "state" is not a YAML field: it
# is the folder the file is in (PRD/HML), shown as its STATE_LABELS text alone,
# with no label.
DETAIL_FIELDS_BY_LAYER = {
  "raw": ["state", "description", "sample_output", "owner", "execution_schedule"],
  "silver": ["state", "sample_output", "owner", "execution_schedule"],
  "audit": ["state", "description"],
  "gold": ["state", "description", "kpis"],
  "automation": ["state", "description", "target", "frequency", "execution_schedule"],
}

# Short fields, shown as a compact label/value list instead of a full section
# - still in DETAIL_FIELDS_BY_LAYER order, consecutive ones grouped together.
DETAIL_INLINE_FIELDS = {"state", "owner", "execution_schedule", "frequency", "target"}

# Detail panel: the title of each field's section - a field left out is shown
# with its own name, "_" as a space.
DETAIL_LABELS = {"sample_output": "Sample output", "execution_schedule": "Execution schedule", "kpis": "KPIs"}

JSON_TOKEN_RE = re.compile(r'("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\btrue\b|\bfalse\b|\bnull\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)')




#################################### Part 2: Catalog Loading ->

def as_list(value):
  """sources_*/generates_audits should be a list or absent, but the
  catalog uses "NA" as an empty placeholder - treat both as []."""
  return value if isinstance(value, list) else []

def client_label(client):
  """CLIENT_LABELS when the folder is listed there, the folder name
  otherwise - PARENT_LABEL is appended to the main client either way."""
  label = CLIENT_LABELS.get(client, client)
  return f"{label} {PARENT_LABEL}" if client == PARENT_CLIENT else label

def client_order(clients):
  """PARENT_CLIENT first, the others alphabetically by the label shown."""
  return sorted(clients, key=lambda c: (c != PARENT_CLIENT, CLIENT_LABELS.get(c, c)))

def node_key(client, rid):
  """The same id is reused across clients (each one documents its own copy
  of a dataset), so a node is keyed by client + id, never by id alone."""
  return f"{client}/{rid}"

def load_all():
  """Reads Layers/<Client>/{PRD,HML}/**/*.yaml - Client is any direct
  subfolder of Layers/, discovered at runtime (not hardcoded)."""
  nodes = {}
  for client in client_order(os.listdir(LAYERS_DIR)):
    client_dir = os.path.join(LAYERS_DIR, client)
    if not os.path.isdir(client_dir):
      continue
    for env in ("PRD", "HML"):
      base = os.path.join(client_dir, env)
      if not os.path.isdir(base):
          continue
      for dirpath, _dirs, filenames in os.walk(base):
          for fname in filenames:
            if not fname.endswith(".yaml"):
              continue
            with open(os.path.join(dirpath, fname), encoding="utf-8") as f:
              rec = yaml.safe_load(f)
            rec["_env"] = env
            rec["_client"] = client
            rec["_id"] = rec.get("id", fname[:-5])
            nodes[node_key(client, rec["_id"])] = rec
  return nodes



#################################### Part 3: Detail Panel ->

def highlight_json(text):
  """Syntax highlight for sample_output - html.escape runs with
  quote=False to keep literal ", which the regex uses to find strings."""
  escaped = html.escape(text, quote=False)
  def repl(m):
    token = m.group(0)
    if token.startswith('"'): cls = "jk" if token.rstrip().endswith(":") else "js"
    elif token in ("true", "false", "null"): cls = "jb"
    else: cls = "jn"
    return f'<span class="{cls}">{token}</span>'
  return JSON_TOKEN_RE.sub(repl, escaped)

def format_text(text):
  """A blank line starts a new paragraph, a single line break stays a line
  break - paragraphs get a small gap instead of a whole empty line."""
  paragraphs = re.split(r"\n\s*\n", str(text).strip())
  return "".join("<p>" + html.escape(p).replace("\n", "<br>") + "</p>" for p in paragraphs)

def format_kpis(kpis):
  """One block per KPI: its number and title, then calculation and reason,
  each led by its name (filters/view are left out)."""
  blocks = []
  for i, kpi in enumerate(kpis, 1):
    title = html.escape(str(kpi.get("title", "")))
    rows = ""
    for field in ("calculation", "reason"):
      value = kpi.get(field)
      value_text = "—" if value is None else html.escape(str(value))
      rows += f'<p><span class="d-kpi-key">{field.capitalize()}</span>{value_text}</p>'
    blocks.append(f'<div class="d-kpi"><div class="d-kpi-title"><span class="d-kpi-n">{i}</span>{title}</div>{rows}</div>')
  return "".join(blocks)

def node_details(nid, rec):
  """HTML for the detail panel when a node is clicked - full text, no
  truncation. A header (layer color, id, project or platform), then the
  DETAIL_FIELDS_BY_LAYER fields in order: one section each, or a label/value
  list for a run of DETAIL_INLINE_FIELDS - the layer is told by the dot's
  color, so it is not written out again."""
  layer = rec.get("layer")
  sections = meta = ""
  for field in DETAIL_FIELDS_BY_LAYER.get(layer, []):
    value = rec.get("_env") if field == "state" else rec.get(field)
    if not value: continue
    label = html.escape(DETAIL_LABELS.get(field, field.replace("_", " ").capitalize()))
    if field in DETAIL_INLINE_FIELDS:
      if field == "state":
        meta += (f'<dd class="d-state {"d-prd" if value == "PRD" else "d-hml"}">'
                 f'{html.escape(dict(STATE_LABELS).get(value, value))}</dd>')
      else: meta += f"<dt>{label}</dt><dd>{html.escape(str(value))}</dd>"
      continue
    if meta:
      sections += f'<dl class="d-meta">{meta}</dl>'
      meta = ""
    if field == "sample_output": body = f"<pre>{highlight_json(str(value))}</pre>"
    elif field == "kpis": body = format_kpis(value)
    else: body = format_text(value)
    sections += f'<div class="d-row"><div class="d-label">{label}</div><div class="d-value">{body}</div></div>'
  if meta:
    sections += f'<dl class="d-meta">{meta}</dl>'
  return (f'<div class="d-head"><span class="d-dot" style="background:{COLORS.get(layer, "#aaaaaa")}"></span>'
          f'<span class="d-name">{html.escape(nid)}</span></div>'
          f'<div class="d-sub">{html.escape(str(group_of(rec)))}</div>{sections}')



#################################### Part 4: Graph Construction ->

def group_of(rec):
  """Raw has no 'project' (platform is shared across projects) - falls
  back to 'platform' in that case."""
  return rec.get("project") or rec.get("platform") or "others"

def platform_of(rec):
  """Automation has no 'platform' - its 'target' is the platform it acts
  on, so the Platforms filter treats both as the same field."""
  return rec.get("platform") or rec.get("target")

def state_opacity(env):
  """Production nodes are drawn as they are, any other state faded to
  NON_PRD_OPACITY - the States filter dots use the same value."""
  return 1 if env == "PRD" else NON_PRD_OPACITY

def build_graph(nodes):
  graph = nx.DiGraph()
  # stack nodes from the same project/platform together within a column (layer)
  ordered = sorted(nodes.items(), key=lambda kv: (COLUMN.get(kv[1].get("layer"), 0), group_of(kv[1]), kv[0]))
  row_in_col = {}
  for nid, rec in ordered:
    col = COLUMN.get(rec.get("layer"), 0)
    row = row_in_col.get(col, 0)
    row_in_col[col] = row + 1
    graph.add_node(
      nid, label=rec["_id"], detail=node_details(rec["_id"], rec), color=COLORS.get(rec.get("layer"), "#aaaaaa"),
      shape="dot", size=NODE_SIZE, x=col * COL_WIDTH, y=row * ROW_HEIGHT, physics=False, row=row,
      opacity=state_opacity(rec.get("_env")),
      layer=rec.get("layer"), plat=platform_of(rec), proj=rec.get("project"),
      env=rec.get("_env"), client=rec.get("_client"))
  # a declared source resolves inside the same client only - an edge never
  # crosses from one client's catalog into another's
  for nid, rec in nodes.items():
    sources = as_list(rec.get("sources_raw")) + as_list(rec.get("sources_silver")) + as_list(rec.get("sources_audit"))
    for ref in sources:
      key = node_key(rec["_client"], ref)
      if key in nodes: graph.add_edge(key, nid)
    for ref in as_list(rec.get("generates_audits")):
      key = node_key(rec["_client"], ref)
      if key in nodes: graph.add_edge(nid, key)
  return graph



#################################### Part 5: Sidebar (Filters) ->

def checkbox_group(label, cls, items, swatch=None):
  """items: list of (value, text) - multi-select, OR within the category.
  swatch (optional): value -> opacity, shown as a dot after the text (how
  the nodes with that value are drawn)."""
  def option(value, text):
    dot = f'<span class="f-swatch" style="opacity:{swatch(value)}"></span>' if swatch else ""
    return (f'<label class="f-option"><input type="checkbox" class="{cls}" value="{html.escape(value)}">'
            f'{html.escape(text)}{dot}</label>')
  boxes = "".join(option(value, text) for value, text in items)
  return f'<div class="f-group"><div class="f-group-title">{html.escape(label)}</div>{boxes}</div>'

# Pyvis has no "connected to X" filter nor a detail panel built in - injects
# into the generated HTML a sidebar that toggles between the filters
# (States/Platforms/Projects, multi-select - OR within a category, AND
# across categories, cascading) and the clicked node's details, always in
# the same place (a gray title says which). Client is single-select, stays
# outside the toggle, and is the outermost filter in the cascade: Platforms and
# Projects the client does not have are hidden, a State it has no file in is
# grayed out.
SIDE_PANEL = """
<style>
  body {{ margin: 0; display: flex; height: 100vh; overflow: hidden; }}
  .card {{ flex: 1 1 0; min-width: 0; }}
  #side-panel {{
    width: 25%; flex-shrink: 0; background: #111; box-sizing: border-box;
    height: 100vh; overflow-y: auto; font-family: sans-serif;
    display: flex; flex-direction: column; border-left: 1px solid #222;
    scrollbar-width: thin; scrollbar-color: #333 transparent;
  }}
  /* centered over the canvas: the side panel takes the right 25%, so the
     middle of the remaining 75% is at 37.5% of the viewport */
  #graph-title {{
    position: fixed; top: 14px; left: 37.5%; transform: translateX(-50%);
    z-index: 5; color: #fff; font-family: sans-serif; font-size: 18px;
    font-weight: 700; letter-spacing: 0.18em; pointer-events: none;
  }}
  /* same centering as #graph-title, vertically centered on the canvas */
  #empty-state {{
    position: fixed; top: 50%; left: 37.5%; transform: translate(-50%, -50%);
    z-index: 5; color: #888; font-family: sans-serif; font-size: 14px;
    pointer-events: none; display: none;
  }}
  #client-bar {{ padding: 20px; border-bottom: 1px solid #222; }}
  #client-bar label, #mode-title {{
    display: block; color: #888; text-transform: uppercase;
    letter-spacing: 0.08em; font-size: 11px; font-weight: 700;
  }}
  /* native arrow swapped for an inline chevron, so it matches the dark theme */
  #client-bar select {{
    width: 100%; margin-top: 8px; padding: 9px 34px 9px 12px;
    background: #1b1b1b url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 4.5l3 3 3-3' fill='none' stroke='%23888' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") no-repeat right 12px center;
    color: #eee; border: 1px solid #333; border-radius: 6px; cursor: pointer;
    font-family: sans-serif; font-size: 13px; appearance: none; -webkit-appearance: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }}
  #client-bar select:hover {{ border-color: #4a4a4a; }}
  #client-bar select:focus {{ outline: none; border-color: #4fc3f7; box-shadow: 0 0 0 3px rgba(79,195,247,0.15); }}
  #client-bar option {{ background: #1b1b1b; color: #eee; }}
  /* the gray title says Filters or Details; Details also gets a way back */
  #mode-title {{ display: flex; align-items: center; justify-content: space-between; padding: 20px 20px 0; }}
  #back-btn {{
    background: none; border: 0; padding: 0; cursor: pointer; color: #777;
    font-family: sans-serif; font-size: 11px; transition: color 0.12s;
  }}
  #back-btn:hover {{ color: #eee; }}
  #filter-sidebar {{ padding: 8px 20px 20px; }}
  .f-group {{ padding: 14px 0; }}
  .f-group + .f-group {{ border-top: 1px solid #1f1f1f; }}
  .f-group-title {{ color: #eee; font-size: 13px; font-weight: 600; margin-bottom: 6px; }}
  /* how the option's nodes are drawn: a dot at their opacity */
  .f-swatch {{
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background: #ddd; margin-left: 8px; vertical-align: 1px;
  }}
  /* each option is a full-width row; display stays block, as restrictOptions sets it */
  .f-option {{
    display: block; color: #aaa; font-size: 13px; padding: 6px 8px; margin: 0 -8px;
    border-radius: 6px; cursor: pointer; user-select: none;
    transition: background 0.12s, color 0.12s;
  }}
  .f-option:hover {{ background: #1a1a1a; color: #fff; }}
  .f-option:has(input:checked) {{ color: #fff; }}
  .f-option:has(input:disabled) {{ cursor: not-allowed; background: none; color: #aaa; }}
  .f-option input {{
    appearance: none; -webkit-appearance: none; width: 16px; height: 16px;
    margin: 0 10px 0 0; vertical-align: -3px; border: 1.5px solid #555;
    border-radius: 4px; background: #0d0d0d; cursor: inherit;
    transition: background-color 0.12s, border-color 0.12s;
  }}
  .f-option:hover input:not(:disabled) {{ border-color: #888; }}
  .f-option input:checked {{
    border-color: #4fc3f7;
    background: #4fc3f7 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 6.2l2.3 2.3 4.7-4.9' fill='none' stroke='%23111' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center / 12px no-repeat;
  }}
  .f-option input:focus-visible {{ outline: 2px solid rgba(79,195,247,0.5); outline-offset: 2px; }}
  /* detail card: header (layer dot, id, project), then each field in
     order - a section, or a label/value list for the short ones; spacing and
     muted grays set them apart, no lines or boxes */
  #detail-panel {{ display: none; padding: 16px 20px 32px; color: #bbb; font-size: 13px; }}
  .d-head {{ display: flex; align-items: center; gap: 10px; }}
  .d-dot {{ width: 8px; height: 8px; border-radius: 50%; flex: none; }}
  .d-name {{ color: #f2f2f2; font-size: 11px; font-weight: 600; line-height: 1.4; word-break: break-word; }}
  .d-sub {{ color: #777; font-size: 11px; margin: 2px 0 0 18px; }}
  .d-meta {{ display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; margin: 26px 0 0; font-size: 12px; line-height: 1.5; }}
  .d-meta dt {{ color: #777; }}
  .d-meta dd {{ margin: 0; color: #bbb; word-break: break-word; }}
  /* the state has no label, so it spans both columns of the .d-meta list */
  .d-meta .d-state {{ grid-column: 1 / -1; display: flex; align-items: center; gap: 6px; }}
  .d-state::before {{ content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }}
  .d-meta .d-prd {{ color: #66bb6a; }}
  .d-meta .d-hml {{ color: #777; }}
  .d-row {{ margin-top: 26px; }}
  .d-label {{
    color: #777; text-transform: uppercase; letter-spacing: 0.08em;
    font-size: 10px; font-weight: 600; margin-bottom: 8px;
  }}
  .d-value {{ color: #bbb; line-height: 1.6; word-break: break-word; }}
  .d-value p {{ margin: 0; }}
  .d-value p + p {{ margin-top: 8px; }}
  .d-kpi + .d-kpi {{ margin-top: 16px; }}
  .d-kpi-title {{ display: flex; gap: 10px; color: #dcc57a; font-weight: 500; margin-bottom: 4px; }}
  .d-kpi-n {{ flex: none; width: 12px; color: #666; font-variant-numeric: tabular-nums; }}
  .d-kpi p {{ margin-left: 22px; color: #999; font-size: 12px; line-height: 1.55; }}
  .d-kpi p + p {{ margin-top: 4px; }}
  .d-kpi-key {{ color: #666; margin-right: 6px; }}
  #counts-box, #updated-at, #repo-link {{
    position: fixed; top: 12px; z-index: 5; background: rgba(17,17,17,0.85);
    color: #ddd; font-family: sans-serif; font-size: 12px; padding: 10px 14px;
    border-radius: 6px; line-height: 1.6; font-variant-numeric: tabular-nums;
  }}
  #counts-box {{ left: 12px; }}
  /* the side panel takes the right 25%, so this sits inside the canvas edge */
  #updated-at {{ right: calc(25% + 12px); }}
  /* bottom-left, same box style as #updated-at - only rendered when REPO is set */
  #repo-link {{ left: 12px; top: auto; bottom: 12px; }}
  #repo-link a {{ color: #4fc3f7; text-decoration: none; }}
  #repo-link a:hover {{ text-decoration: underline; }}
  #counts-box b {{ color: #fff; }}
  /* <pre> preserves JSON indentation - plain text would collapse whitespace */
  #detail-panel pre {{
    background: #0c0c0c; padding: 12px 14px; border-radius: 6px; margin: 0;
    font-family: Consolas, monospace; font-size: 11.5px; line-height: 1.55; color: #888;
    white-space: pre-wrap; word-break: break-word;
  }}
  /* the JSON colors, desaturated so a long sample does not take over the panel */
  #detail-panel .jk {{ color: #7fa7bd; }}
  #detail-panel .js {{ color: #93b48f; }}
  #detail-panel .jn {{ color: #c9b479; }}
  #detail-panel .jb {{ color: #c58f7b; }}
</style>
<div id="counts-box"></div>
<div id="updated-at">Updated at {updated_at}</div>
{repo_link}
<div id="graph-title">{title}</div>
<div id="empty-state">No results for this filter</div>
<div id="side-panel">
  <div id="client-bar">
    <label for="client-select">Client</label>
    <select id="client-select">{client_options}</select>
  </div>
  <div id="mode-title"><span id="mode-text">Filters</span><button type="button" id="back-btn" hidden>&#8592; Back to filters</button></div>
  <div id="filter-sidebar">
    {status_group}
    {platform_group}
    {project_group}
  </div>
  <div id="detail-panel"></div>
</div>
"""

FILTER_SCRIPT = """
<script>
(function () {
  var filterSidebar = document.getElementById('filter-sidebar');
  var detailPanel = document.getElementById('detail-panel');
  var modeText = document.getElementById('mode-text');
  var backBtn = document.getElementById('back-btn');
  var clientSelect = document.getElementById('client-select');
  var countsBox = document.getElementById('counts-box');
  var emptyState = document.getElementById('empty-state');
  var LAYER_LABELS = [["raw", "Raw"], ["silver", "Silver"], ["audit", "Audit"], ["gold", "Gold"], ["automation", "Automation"]];
  var OPTIONAL_LAYERS = ["audit", "automation"];
  var LAYER_COLORS = {"raw": "#ff7f50", "silver": "#4fc3f7", "audit": "#ab47bc", "gold": "#ffd54f", "automation": "#66bb6a"};

  // each node's own look, restored when the highlight is turned off
  var BASE_LOOK = {};
  nodes.get().forEach(function (n) { BASE_LOOK[n.id] = {color: n.color, opacity: n.opacity, font: n.font}; });
  // the nodes lit up by the last click (see highlight)
  var lit = [];

  function showFilters() {
    detailPanel.style.display = 'none';
    filterSidebar.style.display = 'block';
    modeText.textContent = 'Filters';
    backBtn.hidden = true;
    clearHighlight();
  }

  function showDetail(nodeId) {
    detailPanel.innerHTML = nodes.get(nodeId).detail;
    filterSidebar.style.display = 'none';
    detailPanel.style.display = 'block';
    modeText.textContent = 'Details';
    backBtn.hidden = false;
  }
  backBtn.addEventListener('click', showFilters);

  function checked(cls) {
    return Array.from(document.querySelectorAll('.' + cls + ':checked')).map(function (el) { return el.value; });
  }

  // "forward" follows e.from->e.to (descendants); "backward" follows
  // e.to->e.from (ancestors) - never flips direction mid-walk.
  function walk(startIds, poolSet, direction) {
    var seen = new Set(startIds);
    var queue = startIds.slice();
    while (queue.length > 0) {
      var current = queue.pop();
      edges.get().forEach(function (e) {
        if (direction === 'forward' && e.from === current && poolSet.has(e.to) && !seen.has(e.to)) {
          seen.add(e.to); queue.push(e.to);
        }
        if (direction === 'backward' && e.to === current && poolSet.has(e.from) && !seen.has(e.from)) {
          seen.add(e.from); queue.push(e.from);
        }
      });
    }
    return seen;
  }

  // the nodes a click lights up, among the visible ones: the clicked node and
  // its whole chain (HIGHLIGHT.chain - upstream and downstream walked apart, as
  // in computeVisible) or only the nodes one edge away
  function connectedNodes(nodeId) {
    var pool = new Set(nodes.getIds({filter: function (n) { return !n.hidden; }}));
    if (!HIGHLIGHT.chain) {
      return new Set([nodeId].concat(network.getConnectedNodes(nodeId)).filter(function (id) { return pool.has(id); }));
    }
    var chain = walk([nodeId], pool, 'forward');
    walk([nodeId], pool, 'backward').forEach(function (id) { chain.add(id); });
    return chain;
  }

  // lights up the clicked node and its connected nodes - full opacity, a
  // HIGHLIGHT.color border and glow - and the edges between them
  function highlight(nodeId) {
    clearHighlight();
    var on = connectedNodes(nodeId);
    lit = Array.from(on);
    nodes.update(lit.map(function (id) {
      var fill = BASE_LOOK[id].color;
      return {id: id, opacity: 1, font: {color: '#ffffff'}, borderWidth: 3, borderWidthSelected: 4,
              color: {background: fill, border: HIGHLIGHT.color,
                      highlight: {background: fill, border: HIGHLIGHT.color},
                      hover: {background: fill, border: HIGHLIGHT.color}},
              shadow: {enabled: true, color: HIGHLIGHT.color, size: 18, x: 0, y: 0}};
    }));
    edges.update(edges.get().map(function (e) {
      var inChain = on.has(e.from) && on.has(e.to);
      return {id: e.id, color: inChain ? HIGHLIGHT.color : '#555555', width: inChain ? 2 : 1};
    }));
  }

  // turns the highlight off: every lit node back to its own look (BASE_LOOK)
  // and every edge back to gray
  function clearHighlight() {
    if (lit.length === 0) return;
    nodes.update(lit.map(function (id) {
      var base = BASE_LOOK[id];
      return {id: id, color: base.color, opacity: base.opacity, font: base.font,
              borderWidth: 1, borderWidthSelected: 2, shadow: false};
    }));
    edges.update(edges.getIds().map(function (id) { return {id: id, color: '#555555', width: 1}; }));
    lit = [];
  }

  // client+status restrict the universe (pool); platform/project mark the
  // "base" and expand to the full connected chain (forward+backward kept
  // separate - see walk() - to avoid crossing through a shared node, e.g.
  // RAW_VCenter-Assets, into another project's chain).
  function computeVisible(client, envs, plats, projs) {
    var pool = nodes.getIds().filter(function (id) {
      var n = nodes.get(id);
      return n.client === client && (envs.length === 0 || envs.indexOf(n.env) !== -1);
    });
    if (plats.length === 0 && projs.length === 0) return new Set(pool);
    var poolSet = new Set(pool);
    var base = [];
    pool.forEach(function (id) {
      var n = nodes.get(id);
      if ((n.plat && plats.indexOf(n.plat) !== -1) || (n.proj && projs.indexOf(n.proj) !== -1)) base.push(id);
    });
    var visible = new Set(base);
    walk(base, poolSet, 'forward').forEach(function (id) { visible.add(id); });
    walk(base, poolSet, 'backward').forEach(function (id) { visible.add(id); });
    return visible;
  }

  function valuesOf(ids, field) {
    var values = new Set();
    ids.forEach(function (id) {
      var v = nodes.get(id)[field];
      if (v) values.add(v);
    });
    return values;
  }

  // an option with no node in the selected client does not exist there: it is
  // hidden when hideAbsent is set (Platforms/Projects), and only grayed out
  // and disabled otherwise (States keep both boxes on screen). An option that
  // exists in the client but has no node in "candidates" (filter cascade) is
  // grayed out and disabled.
  function restrictOptions(cls, field, candidates, clientIds, hideAbsent) {
    var inClient = valuesOf(clientIds, field);
    var available = valuesOf(candidates, field);
    document.querySelectorAll('.' + cls).forEach(function (el) {
      var label = el.closest('label');
      var exists = inClient.has(el.value);
      var ok = exists && available.has(el.value);
      label.style.display = exists || !hideAbsent ? 'block' : 'none';
      label.style.opacity = ok ? '1' : '0.35';
      el.disabled = !ok;
      if (!ok) el.checked = false;
    });
  }

  function updateCounts(visible) {
    var counts = {};
    visible.forEach(function (id) {
      var layer = nodes.get(id).layer;
      counts[layer] = (counts[layer] || 0) + 1;
    });
    // Audit and Automation only show when the selection has at least one of them; Raw, Silver and Gold always show
    countsBox.innerHTML = LAYER_LABELS.filter(function (pair) {
      return counts[pair[0]] || OPTIONAL_LAYERS.indexOf(pair[0]) < 0;
    }).map(function (pair) {
      var n = String(counts[pair[0]] || 0).padStart(2, '0');
      var dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;' +
        'background:' + LAYER_COLORS[pair[0]] + ';margin-right:6px;"></span>';
      return '<div>' + dot + '<b>' + n + '</b> ' + pair[1] + '</div>';
    }).join('');
  }

  // space a box takes around its nodes: from the first node's center up to
  // the box top, and from the last node's center down to the box bottom (the
  // node label hangs NODE_LABEL below the dot, in vis-network's default
  // NODE_FONT). BOX_STEP goes from the last node of a box to the first node
  // of the box below it.
  var NODE_FONT = '14px arial';
  var BOX_FONT = 'bold 16px arial';
  var NODE_LABEL = 20;
  var BOX_TOP = LAYOUT.nodeSize + LAYOUT.boxPadding + LAYOUT.boxLabelHeight;
  var BOX_BOTTOM = LAYOUT.nodeSize + NODE_LABEL + LAYOUT.boxPadding;
  var BOX_STEP = BOX_BOTTOM + LAYOUT.boxGap + BOX_TOP;

  var measure = document.createElement('canvas').getContext('2d');
  function textWidth(text, font) {
    measure.font = font;
    return measure.measureText(text).width;
  }

  // how far a node reaches to each side: half its label (measured once per
  // node) or its dot, whichever is wider
  var halfWidths = {};
  function halfWidth(id) {
    if (!(id in halfWidths)) {
      halfWidths[id] = Math.max(LAYOUT.nodeSize, textWidth(nodes.get(id).label, NODE_FONT) / 2);
    }
    return halfWidths[id];
  }

  // a named box takes the color of its first layer (PIPELINES: silver's)
  var BOX_COLORS = {};
  LAYOUT.order.forEach(function (layer) {
    var name = LAYOUT.boxNames[layer];
    if (name && !BOX_COLORS[name]) BOX_COLORS[name] = LAYER_COLORS[layer];
  });

  // the box a node is drawn in: its layer's LAYOUT.boxNames entry (shared by
  // every layer with that name), or, for a layer left out, its platform's.
  // The name is shown in uppercase.
  function boxOf(n) {
    var name = LAYOUT.boxNames[n.layer];
    if (name) return {key: name, name: name.toUpperCase(), color: BOX_COLORS[name]};
    return {key: n.layer + '/' + (n.plat || ''), name: (n.plat || 'others').toUpperCase(), color: LAYER_COLORS[n.layer]};
  }

  // left/right edges of a box around the nodes ids (xOf: a node's x), wide
  // enough for the node labels and the box name
  function boxEdges(ids, xOf, name) {
    var left = Infinity, right = -Infinity;
    ids.forEach(function (id) {
      left = Math.min(left, xOf(id) - halfWidth(id));
      right = Math.max(right, xOf(id) + halfWidth(id));
    });
    left -= LAYOUT.boxPadding;
    return {left: left,
            right: Math.max(right + LAYOUT.boxPadding, left + textWidth(name, BOX_FONT) + 2 * LAYOUT.boxPadding)};
  }

  // left/right edges a box is stretched to, per box key, set by the last
  // compactLayout (see layoutByPlatform) - a box is never narrower than its
  // nodes, only wider
  var boxSpans = {};

  // the rectangle of each box around its visible nodes (boxOf), from the
  // live positions (getPositions), so a dragged node stretches its box
  // along.
  function boxRects() {
    var boxes = {};
    nodes.get({filter: function (n) { return !n.hidden; }}).forEach(function (n) {
      var box = boxOf(n);
      (boxes[box.key] = boxes[box.key] || {name: box.name, color: box.color, ids: []}).ids.push(n.id);
    });
    return Object.keys(boxes).map(function (key) {
      var box = boxes[key];
      var positions = network.getPositions(box.ids);
      var edges = boxEdges(box.ids, function (id) { return positions[id].x; }, box.name);
      var span = boxSpans[key] || edges;
      var top = Infinity, bottom = -Infinity;
      box.ids.forEach(function (id) {
        top = Math.min(top, positions[id].y);
        bottom = Math.max(bottom, positions[id].y);
      });
      return {name: box.name, color: box.color,
              left: Math.min(edges.left, span.left), right: Math.max(edges.right, span.right),
              top: top - BOX_TOP, bottom: bottom + BOX_BOTTOM};
    });
  }

  // frames every box - fit() frames node positions only, so box edges,
  // names and long labels got clipped - inside the part of the canvas left
  // free, FIT_MARGIN px from its edges: below the lowest of counts-box/
  // graph-title/updated-at, above repo-link and the page bottom (the canvas
  // runs past it, under the card padding). Never zooms in past 1, as fit()
  // does not either.
  var FIT_MARGIN = 24;
  function fitBoxes() {
    var rects = boxRects();
    if (rects.length === 0) return;
    var left = Math.min.apply(null, rects.map(function (r) { return r.left; }));
    var right = Math.max.apply(null, rects.map(function (r) { return r.right; }));
    var top = Math.min.apply(null, rects.map(function (r) { return r.top; }));
    var bottom = Math.max.apply(null, rects.map(function (r) { return r.bottom; }));
    var canvas = document.querySelector('#mynetwork canvas').getBoundingClientRect();
    var freeTop = Math.max.apply(null, [canvas.top].concat(['counts-box', 'graph-title', 'updated-at'].map(function (id) {
      return document.getElementById(id).getBoundingClientRect().bottom;
    })));
    var repoLink = document.getElementById('repo-link');
    var freeBottom = Math.min(canvas.bottom, window.innerHeight, repoLink ? repoLink.getBoundingClientRect().top : Infinity);
    var marginTop = freeTop - canvas.top + FIT_MARGIN;
    var marginBottom = canvas.bottom - freeBottom + FIT_MARGIN;
    var scale = Math.min(1, (canvas.width - 2 * FIT_MARGIN) / (right - left),
                         (canvas.height - marginTop - marginBottom) / (bottom - top));
    // moveTo centers "position" on the canvas - shifted so the boxes center
    // on the free part instead
    network.moveTo({position: {x: (left + right) / 2, y: (top + bottom) / 2 - (marginTop - marginBottom) / 2 / scale},
                    scale: scale, animation: {duration: 300, easingFunction: 'easeInOutQuad'}});
  }

  // the blocks of one stack into shelves, top to bottom: the stack is as
  // wide as its widest block, and each block goes on the first shelf with
  // room left for it, or on a new shelf below - small platforms sit side by
  // side under a wide one instead of leaving the space next to them empty.
  // A shelf is as tall as its tallest block.
  function shelve(blocks) {
    var width = Math.max.apply(null, blocks.map(function (b) { return b.subcolumns; }));
    var shelves = [];
    blocks.forEach(function (block) {
      var shelf = shelves.find(function (s) { return s.used + block.subcolumns <= width; });
      if (!shelf) shelves.push(shelf = {items: [], used: 0, height: 0});
      shelf.items.push({block: block, column: shelf.used});
      shelf.used += block.subcolumns;
      shelf.height = Math.max(shelf.height, block.height);
    });
    var height = shelves.reduce(function (sum, s) { return sum + s.height; }, 0) + (shelves.length - 1) * BOX_STEP;
    return {width: width, height: height, shelves: shelves};
  }

  // blocks (in order) into stacks: first the fewest stacks that fit the
  // LAYOUT.maxRows rows of a plain column, then the lowest height limit that
  // still keeps that many stacks, so they come out even (binary search - the
  // limit it lands on always keeps that many stacks or fewer)
  function stackBlocks(blocks) {
    function split(limit) {
      var stacks = [];
      blocks.forEach(function (block) {
        var last = stacks[stacks.length - 1];
        if (last && shelve(last.concat([block])).height <= limit) last.push(block);
        else stacks.push([block]);
      });
      return stacks;
    }
    var high = (LAYOUT.maxRows - 1) * LAYOUT.rowHeight;
    var count = split(high).length;
    var low = 0;
    while (low < high) {
      var mid = Math.floor((low + high) / 2);
      if (split(mid).length <= count) high = mid; else low = mid + 1;
    }
    return split(high);
  }

  // layer with a box name: one column, split into balanced sub-columns past
  // LAYOUT.maxRows nodes, filled top to bottom one after the other (so
  // project grouping reads in order). Returns the extra width taken past the
  // layer's own column.
  function layoutPlain(ids, x0, placed) {
    var subcolumns = Math.max(1, Math.ceil(ids.length / LAYOUT.maxRows));
    var perColumn = Math.ceil(ids.length / subcolumns);
    ids.forEach(function (id, i) {
      placed.push({id: id,
                   x: x0 + Math.floor(i / perColumn) * LAYOUT.subcolumnWidth,
                   y: (i % perColumn) * LAYOUT.rowHeight});
    });
    return (subcolumns - 1) * LAYOUT.subcolumnWidth;
  }

  // layer without a box name: one block per platform, in "row" order, a
  // block with more than LAYOUT.maxRows nodes split into its own balanced
  // sub-columns. Blocks go in stacks (see stackBlocks), each stack to the
  // right of the previous one, and on shelves inside a stack (see shelve).
  // Every box of a stack is stretched to the stack's outer edges - those of
  // its widest box - and the boxes of a shelf split that width
  // LAYOUT.boxGap apart (pushed to spans). Returns the extra width taken
  // past the layer's own column, as layoutPlain does.
  function layoutByPlatform(ids, x0, placed, spans) {
    var blocks = [];
    var byPlat = {};
    ids.forEach(function (id) {
      var plat = nodes.get(id).plat || '';
      if (!byPlat[plat]) blocks.push(byPlat[plat] = []);
      byPlat[plat].push(id);
    });
    blocks = blocks.map(function (members) {
      var subcolumns = Math.ceil(members.length / LAYOUT.maxRows);
      var perColumn = Math.ceil(members.length / subcolumns);
      var box = boxOf(nodes.get(members[0]));
      return {ids: members, key: box.key, name: box.name, subcolumns: subcolumns,
              perColumn: perColumn, height: (perColumn - 1) * LAYOUT.rowHeight};
    });
    var x = x0;
    stackBlocks(blocks).forEach(function (stack) {
      var shelved = shelve(stack);
      var xs = {};
      // first node at y 0, as in layoutPlain, so every box top lines up
      var y = 0;
      shelved.shelves.forEach(function (shelf) {
        shelf.items.forEach(function (item) {
          item.block.ids.forEach(function (id, i) {
            xs[id] = x + (item.column + Math.floor(i / item.block.perColumn)) * LAYOUT.subcolumnWidth;
            placed.push({id: id, x: xs[id], y: y + (i % item.block.perColumn) * LAYOUT.rowHeight});
          });
        });
        y += shelf.height + BOX_STEP;
      });
      var edges = stack.map(function (block) {
        return boxEdges(block.ids, function (id) { return xs[id]; }, block.name);
      });
      var stackLeft = Math.min.apply(null, edges.map(function (e) { return e.left; }));
      var stackRight = Math.max.apply(null, edges.map(function (e) { return e.right; }));
      // two boxes side by side part halfway between their facing sub-columns
      function between(column) { return x + (column - 0.5) * LAYOUT.subcolumnWidth; }
      shelved.shelves.forEach(function (shelf) {
        shelf.items.forEach(function (item, i) {
          var next = shelf.items[i + 1];
          spans.push({key: item.block.key,
                      left: i === 0 ? stackLeft : between(item.column) + LAYOUT.boxGap / 2,
                      right: next ? between(next.column) - LAYOUT.boxGap / 2 : stackRight});
        });
      });
      x += shelved.width * LAYOUT.subcolumnWidth + LAYOUT.boxGap;
    });
    return x - x0 - LAYOUT.subcolumnWidth - LAYOUT.boxGap;
  }

  // reflow X/Y for visible nodes only (removes gaps left by hidden nodes) -
  // groups by layer and sorts by the original "row", not the current y
  // (which a previous pass may have already compacted). Each layer is laid
  // out by layoutPlain or layoutByPlatform, and every layer to its right
  // shifts by the extra width it takes. A box never runs into the box on its
  // left: when it would start less than LAYOUT.boxGap away, its layer (and
  // every layer after it, and its box spans) moves right.
  function compactLayout(visible) {
    var byLayer = {};
    visible.forEach(function (id) {
      var n = nodes.get(id);
      (byLayer[n.layer] = byLayer[n.layer] || []).push(id);
    });
    var updates = [];
    var shift = 0;
    var prev = null;  // the box on the left: {key, right edge of its nodes}
    boxSpans = {};
    LAYOUT.order.forEach(function (layer) {
      var ids = byLayer[layer] || [];
      if (ids.length === 0) return;
      ids.sort(function (a, b) { return nodes.get(a).row - nodes.get(b).row; });
      var x0 = LAYOUT.column[layer] * LAYOUT.colWidth + shift;
      var placed = [];
      var spans = [];
      shift += LAYOUT.boxNames[layer] ? layoutPlain(ids, x0, placed) : layoutByPlatform(ids, x0, placed, spans);
      var key = LAYOUT.boxNames[layer] || layer;
      var left = Infinity, right = -Infinity;
      placed.forEach(function (p) {
        left = Math.min(left, p.x - halfWidth(p.id));
        right = Math.max(right, p.x + halfWidth(p.id));
      });
      if (prev && prev.key !== key) {
        var push = Math.max(0, prev.right + 2 * LAYOUT.boxPadding + LAYOUT.boxGap - left);
        placed.forEach(function (p) { p.x += push; });
        spans.forEach(function (s) { s.left += push; s.right += push; });
        shift += push;
        right += push;
      }
      prev = {key: key, right: prev && prev.key === key ? Math.max(prev.right, right) : right};
      spans.forEach(function (s) { boxSpans[s.key] = s; });
      updates = updates.concat(placed);
    });
    nodes.update(updates);
  }

  function applyFilter() {
    // a lit chain would stay lit on nodes the new filter hides
    clearHighlight();
    var client = clientSelect.value;
    var clientIds = computeVisible(client, [], [], []);
    restrictOptions('f-env', 'env', clientIds, clientIds, false);
    var envs = checked('f-env');
    restrictOptions('f-plat', 'plat', computeVisible(client, envs, [], []), clientIds, true);
    var plats = checked('f-plat');
    restrictOptions('f-proj', 'proj', computeVisible(client, envs, plats, []), clientIds, true);
    var projs = checked('f-proj');

    var visible = computeVisible(client, envs, plats, projs);
    var ids = nodes.getIds();
    nodes.update(ids.map(function (id) { return {id: id, hidden: !visible.has(id)}; }));
    edges.update(edges.get().map(function (e) {
      return {id: e.id, hidden: !(visible.has(e.from) && visible.has(e.to))};
    }));
    compactLayout(visible);
    updateCounts(visible);
    emptyState.style.display = visible.size === 0 ? 'block' : 'none';
    fitBoxes();
  }
  document.querySelectorAll('.f-plat, .f-proj, .f-env').forEach(function (el) {
    el.addEventListener('change', applyFilter);
  });
  clientSelect.addEventListener('change', applyFilter);
  // the network was created before the side panel existed, at the full page
  // width - its canvas only catches up on its own later, rescaling the view
  // fitBoxes set, so it is resized to the current layout first
  network.setSize('100%', '100%');
  applyFilter();
  // on a later resize (window resized, devtools opened) vis-network rescales
  // the view on its own, which can push boxes past the edge - framed again
  // instead, deferred since vis restores its own view right after the event
  network.on('resize', function () { setTimeout(fitBoxes, 0); });

  // click on a node: light it up with its connected nodes and show the details;
  // click on empty space goes back to filters (showFilters() turns the highlight off)
  network.on('click', function (params) {
    if (params.nodes.length > 0) {
      highlight(params.nodes[0]);
      showDetail(params.nodes[0]);
    } else {
      showFilters();
    }
  });

  // the boxes (boxRects), drawn under nodes and edges
  network.on('beforeDrawing', function (ctx) {
    ctx.save();
    ctx.font = BOX_FONT;
    ctx.textBaseline = 'middle';
    ctx.lineWidth = 1.5;
    boxRects().forEach(function (box) {
      ctx.beginPath();
      ctx.roundRect(box.left, box.top, box.right - box.left, box.bottom - box.top, 8);
      ctx.fillStyle = box.color;
      ctx.strokeStyle = box.color;
      ctx.globalAlpha = 0.06;
      ctx.fill();
      ctx.globalAlpha = 0.6;
      ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillText(box.name, box.left + LAYOUT.boxPadding, box.top + (LAYOUT.boxPadding + LAYOUT.boxLabelHeight) / 2);
    });
    ctx.restore();
  });
})();
</script>
"""



#################################### Part 6: HTML Generation ->

if __name__ == "__main__":
  nodes = load_all()

  # cdn_resources="remote" keeps Pyvis from copying the lib/ folder to
  # disk - it inlines utils.js into the HTML and loads vis-network from the CDN.
  net = Network(
    height="100vh", width="100%", directed=True, bgcolor="#000000", font_color="#ffffff",
    cdn_resources="remote")
  net.from_nx(build_graph(nodes))
  # vis-network's node opacity leaves the label as it is, and pyvis replaces
  # any node font with font_color - so a faded node gets its label faded here
  # (the white of font_color, at the node's opacity)
  for n in net.nodes:
    if n.get("opacity", 1) < 1:
      n["font"] = {"color": f"rgba(255, 255, 255, {n['opacity']})"}
  net.set_options("""
  {
    "physics": { "enabled": false },
    "edges": { "color": "#555555", "smooth": { "type": "cubicBezier", "roundness": 0.5 },
    "arrows": { "to": { "scaleFactor": 0.5 } } }
  }""")

  out_path = os.path.join(ROOT, "DataLake-Graph_Pyvis.html")
  net.write_html(out_path, open_browser=False)

  clients = client_order({rec.get("_client") for rec in nodes.values() if rec.get("_client")})
  # platform_of() folds automation 'target' in, so a platform that only ever
  # appears as an automation target still gets a checkbox
  platforms = sorted({platform_of(rec) for rec in nodes.values() if platform_of(rec)})
  projects = sorted({rec.get("project") for rec in nodes.values() if rec.get("project")})
  # value stays the folder name (the filter compares it to node.client); only the shown text uses client_label()
  client_options = "".join(
    f'<option value="{html.escape(c)}">{html.escape(client_label(c))}</option>'
    for c in clients)

  # empty REPO -> no box at all; otherwise a clickable link, same style as #updated-at
  repo_link = (
    f'<div id="repo-link"><a href="{html.escape(REPO)}" target="_blank" rel="noopener">{html.escape(REPO)}</a></div>'
    if REPO else "")

  side_panel = SIDE_PANEL.format(
    title=html.escape(TITLE),
    client_options=client_options,
    updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    repo_link=repo_link,
    status_group=checkbox_group("States", "f-env", STATE_LABELS,
                                swatch=state_opacity if NON_PRD_OPACITY < 1 else None),
    platform_group=checkbox_group("Platforms", "f-plat", [(p, p) for p in platforms]),
    project_group=checkbox_group("Projects", "f-proj", [(p, p) for p in projects]))

  with open(out_path, encoding="utf-8") as f:
    page = f.read()
  # FILTER_SCRIPT is plain JS (not a format string), so the layout constants
  # its reflow needs, and the click highlight settings, go in as JSON globals
  # defined right before it
  layout = {
    "order": sorted(COLUMN, key=COLUMN.get), "column": COLUMN, "colWidth": COL_WIDTH,
    "rowHeight": ROW_HEIGHT, "maxRows": MAX_ROWS_PER_COLUMN, "subcolumnWidth": SUBCOLUMN_WIDTH,
    "nodeSize": NODE_SIZE, "boxNames": BOX_NAMES, "boxPadding": BOX_PADDING,
    "boxLabelHeight": BOX_LABEL_HEIGHT, "boxGap": BOX_GAP}
  highlight = {"color": HIGHLIGHT_COLOR, "chain": HIGHLIGHT_CHAIN}
  layout_script = f"<script>var LAYOUT = {json.dumps(layout)}; var HIGHLIGHT = {json.dumps(highlight)};</script>\n"
  # side-panel comes after .card in the DOM so it lands on the right (body is a flex row)
  page = page.replace("</body>", side_panel + layout_script + FILTER_SCRIPT + "</body>", 1)
  # pyvis writes no <title> or favicon - the tab would otherwise show the file path and a blank icon
  head_tags = f'<title>{html.escape(TAB_TITLE)}</title>\n<link rel="icon" href="{FAVICON}">'
  page = page.replace("<head>", f"<head>\n{head_tags}", 1)
  with open(out_path, "w", encoding="utf-8") as f: f.write(page)

  # print(f"{len(nodes)} nodes -> {out_path}")