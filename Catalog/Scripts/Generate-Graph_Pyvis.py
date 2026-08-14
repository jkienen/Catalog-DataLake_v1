#################################### Part 0: Import modules ->

import os
import re
import html
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

# Browser tab icon - data URI, fully local (no external file/network fetch).
# <link rel="icon"> needs an image, not raw text, so the emoji is wrapped in
# the minimal SVG needed to render it as one - nothing else is added to it.
FAVICON = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text x='50' y='75' font-size='80' text-anchor='middle'>🔻</text></svg>"

# Layout: each layer gets a fixed column
COLORS = {"raw": "#ff7f50", "silver": "#4fc3f7", "audit": "#ab47bc", "gold": "#ffd54f", "automation": "#66bb6a"}
COLUMN = {"raw": 0, "silver": 0.7, "audit": 1.1, "gold": 1.8, "automation": 2.3}
COL_WIDTH = 650

# States checkbox: (value stored on the node, label shown in the sidebar).
STATE_LABELS = [("PRD", "In production"), ("HML", "In staging")]

# Fields shown in the detail panel, per layer.
DETAIL_FIELDS_BY_LAYER = {
  "raw": ["description", "sample_output", "owner", "execution_schedule"],
  "silver": ["sample_output", "owner", "execution_schedule"],
  "audit": ["description"],
  "gold": ["description", "kpis"],
  "automation": ["target", "description", "frequency", "execution_schedule"],
}

JSON_TOKEN_RE = re.compile(r'("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\btrue\b|\bfalse\b|\bnull\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)')




#################################### Part 2: Catalog Loading ->

def as_list(value):
  """sources_*/generates_audits should be a list or absent, but the
  catalog uses "NA" as an empty placeholder - treat both as []."""
  return value if isinstance(value, list) else []

def load_all():
  """Reads Layers/<Client>/{PRD,HML}/**/*.yaml - Client is any direct
  subfolder of Layers/, discovered at runtime (not hardcoded)."""
  nodes = {}
  for client in sorted(os.listdir(LAYERS_DIR)):
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
            nodes[rec.get("id", fname[:-5])] = rec
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

def format_kpis(kpis):
  """Only title/calculation/reason (filters/view are left out), colored,
  to fit in a <pre>."""
  blocks = []
  for i, kpi in enumerate(kpis, 1):
    title = html.escape(str(kpi.get("title", "")))
    lines = [f'<span class="kt">{i}. {title}</span>']
    for field in ("calculation", "reason"):
      value = kpi.get(field)
      value_text = "null" if value is None else html.escape(str(value))
      lines.append(f'   <span class="kk">{field}</span>: <span class="kv">{value_text}</span>')
    blocks.append("\n".join(lines))
  return "\n\n".join(blocks)

def node_details(nid, rec):
  """HTML for the detail panel when a node is clicked - full text, no truncation."""
  parts = [f"<b>{html.escape(nid)}</b>"]
  for field in DETAIL_FIELDS_BY_LAYER.get(rec.get("layer"), []):
    value = rec.get(field)
    if not value: continue
    if field == "sample_output": body = f"<pre>{highlight_json(str(value))}</pre>"
    elif field == "kpis": body = f"<pre>{format_kpis(value)}</pre>"
    else: body = html.escape(str(value)).replace("\n", "<br>")
    parts.append(f"<u>{field}</u>:<br>{body}")
  return "<br><br>".join(parts)



#################################### Part 4: Graph Construction ->

def group_of(rec):
  """Raw has no 'project' (platform is shared across projects) - falls
  back to 'platform' in that case."""
  return rec.get("project") or rec.get("platform") or "outros"

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
      nid, label=nid, detail=node_details(nid, rec), color=COLORS.get(rec.get("layer"), "#aaaaaa"),
      shape="dot", size=16, x=col * COL_WIDTH, y=row * 90, physics=False, row=row,
      layer=rec.get("layer"), plat=rec.get("platform"), proj=rec.get("project"),
      env=rec.get("_env"), client=rec.get("_client"))
  for nid, rec in nodes.items():
    sources = as_list(rec.get("sources_raw")) + as_list(rec.get("sources_silver")) + as_list(rec.get("sources_audit"))
    for ref in sources:
      if ref in nodes: graph.add_edge(ref, nid)
    for ref in as_list(rec.get("generates_audits")):
      if ref in nodes: graph.add_edge(nid, ref)
  return graph



#################################### Part 5: Sidebar (Filters) ->

def checkbox_group(label, cls, items):
  """items: list of (value, text) - multi-select, OR within the category."""
  boxes = "".join(
    f'<label style="display:block;color:#ccc;font-size:13px;margin:2px 0;">'
    f'<input type="checkbox" class="{cls}" value="{html.escape(value)}"> {html.escape(text)}</label>'
    for value, text in items)
  return f'<div><div style="color:#fff;font-weight:600;margin-bottom:4px;">{html.escape(label)}</div>{boxes}</div>'

# Pyvis has no "connected to X" filter nor a detail panel built in - injects
# into the generated HTML a sidebar that toggles between the filters
# (States/Platforms/Projects, multi-select - OR within a category, AND
# across categories, cascading) and the clicked node's details, always in
# the same place (a gray title says which). Client is single-select, stays
# outside the toggle, and is the outermost filter in the cascade.
SIDE_PANEL = """
<style>
  body {{ margin: 0; display: flex; height: 100vh; overflow: hidden; }}
  .card {{ flex: 1 1 0; min-width: 0; }}
  #side-panel {{
    width: 25%; flex-shrink: 0; background: #111; box-sizing: border-box;
    height: 100vh; overflow-y: auto; font-family: sans-serif;
    display: flex; flex-direction: column;
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
  #client-bar {{ padding: 16px; }}
  #client-bar label {{
    display: block; color: #888; text-transform: uppercase;
    letter-spacing: 0.05em; font-size: 12px; font-weight: 700;
  }}
  #client-bar select {{
    width: 100%; margin-top: 6px; padding: 7px 8px; background: #1b1b1b;
    color: #ddd; border: 1px solid #333; border-radius: 4px;
    font-family: sans-serif; font-size: 13px;
  }}
  #client-bar select:focus {{ outline: none; border-color: #4fc3f7; }}
  #mode-title {{
    color: #888; text-transform: uppercase; letter-spacing: 0.05em;
    font-size: 12px; font-weight: 700; padding: 16px 16px 0 16px;
  }}
  #filter-sidebar {{ padding: 16px; }}
  #filter-sidebar > div {{ margin-bottom: 24px; }}
  #detail-panel {{ display: none; padding: 16px; color: #ddd; font-size: 13px; }}
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
  #detail-panel u {{ font-weight: bold; }}
  /* <pre> preserves JSON indentation - plain text would collapse whitespace */
  #detail-panel pre {{
    background: #0a0a0a; padding: 10px; border-radius: 4px; margin: 6px 0 0;
    font-family: Consolas, monospace; font-size: 12px;
    white-space: pre-wrap; word-break: break-word;
  }}
  #detail-panel .jk {{ color: #4fc3f7; font-weight: bold; }}
  #detail-panel .js {{ color: #a5d6a7; }}
  #detail-panel .jn {{ color: #ffd54f; }}
  #detail-panel .jb {{ color: #ff8a65; }}
  #detail-panel .kt {{ color: #ffd54f; font-weight: bold; }}
  #detail-panel .kk {{ color: #4fc3f7; font-weight: bold; }}
  #detail-panel .kv {{ color: #a5d6a7; }}
</style>
<div id="counts-box"></div>
<div id="updated-at">Updated at {updated_at}</div>
{repo_link}
<div id="graph-title">{title}</div>
<div id="empty-state">Nenhum resultado para este filtro</div>
<div id="side-panel">
  <div id="client-bar">
    <label for="client-select">Client</label>
    <select id="client-select">{client_options}</select>
  </div>
  <div id="mode-title">Filters</div>
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
  var modeTitle = document.getElementById('mode-title');
  var clientSelect = document.getElementById('client-select');
  var countsBox = document.getElementById('counts-box');
  var emptyState = document.getElementById('empty-state');
  var LAYER_LABELS = [["raw", "Raw"], ["silver", "Silver"], ["audit", "Audit"], ["gold", "Gold"], ["automation", "Automation"]];
  var LAYER_COLORS = {"raw": "#ff7f50", "silver": "#4fc3f7", "audit": "#ab47bc", "gold": "#ffd54f", "automation": "#66bb6a"};

  function showFilters() {
    detailPanel.style.display = 'none';
    filterSidebar.style.display = 'block';
    modeTitle.textContent = 'Filters';
    edges.update(edges.getIds().map(function (id) { return {id: id, color: '#555555'}; }));
  }

  function showDetail(nodeId) {
    detailPanel.innerHTML = nodes.get(nodeId).detail;
    filterSidebar.style.display = 'none';
    detailPanel.style.display = 'block';
    modeTitle.textContent = 'Details';
  }

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

  // disable options with no node in "candidates" (filter cascade)
  function restrictOptions(cls, field, candidates) {
    var available = new Set();
    candidates.forEach(function (id) {
      var v = nodes.get(id)[field];
      if (v) available.add(v);
    });
    document.querySelectorAll('.' + cls).forEach(function (el) {
      var ok = available.has(el.value);
      el.disabled = !ok;
      el.closest('label').style.opacity = ok ? '1' : '0.35';
      if (!ok) el.checked = false;
    });
  }

  function updateCounts(visible) {
    var counts = {};
    visible.forEach(function (id) {
      var layer = nodes.get(id).layer;
      counts[layer] = (counts[layer] || 0) + 1;
    });
    countsBox.innerHTML = LAYER_LABELS.map(function (pair) {
      var n = String(counts[pair[0]] || 0).padStart(2, '0');
      var dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;' +
        'background:' + LAYER_COLORS[pair[0]] + ';margin-right:6px;"></span>';
      return '<div>' + dot + '<b>' + n + '</b> ' + pair[1] + '</div>';
    }).join('');
  }

  // reflow Y for visible nodes only (removes gaps left by hidden nodes) -
  // groups by column and sorts by the original "row", not the current y
  // (which a previous pass may have already compacted).
  function compactLayout(visible) {
    var byCol = {};
    visible.forEach(function (id) {
      var n = nodes.get(id);
      (byCol[n.x] = byCol[n.x] || []).push(id);
    });
    var updates = [];
    Object.keys(byCol).forEach(function (x) {
      var ids = byCol[x];
      ids.sort(function (a, b) { return nodes.get(a).row - nodes.get(b).row; });
      ids.forEach(function (id, i) { updates.push({id: id, y: i * 90}); });
    });
    nodes.update(updates);
  }

  function applyFilter() {
    var client = clientSelect.value;
    var envs = checked('f-env');
    restrictOptions('f-plat', 'plat', computeVisible(client, envs, [], []));
    var plats = checked('f-plat');
    restrictOptions('f-proj', 'proj', computeVisible(client, envs, plats, []));
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
    if (visible.size > 0) {
      // fit() frames node POSITIONS and ignores label width, so the longest
      // ids in the last column get clipped - zoom out to leave the margin
      network.fit({nodes: Array.from(visible)});
      network.moveTo({scale: network.getScale() * 0.9,
                      animation: {duration: 300, easingFunction: 'easeInOutQuad'}});
    }
  }
  document.querySelectorAll('.f-plat, .f-proj, .f-env').forEach(function (el) {
    el.addEventListener('change', applyFilter);
  });
  clientSelect.addEventListener('change', applyFilter);
  applyFilter();

  // click on a node: highlight its connected edges and show the details;
  // click on empty space goes back to filters (showFilters() resets the edges)
  network.on('click', function (params) {
    if (params.nodes.length > 0) {
      var connected = network.getConnectedEdges(params.nodes[0]);
      edges.update(edges.getIds().map(function (id) {
        return {id: id, color: connected.indexOf(id) !== -1 ? '#ffffff' : '#555555'};
      }));
      showDetail(params.nodes[0]);
    } else {
      showFilters();
    }
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
  net.set_options("""
  {
    "physics": { "enabled": false },
    "edges": { "color": "#555555", "smooth": { "type": "cubicBezier", "roundness": 0.5 },
    "arrows": { "to": { "scaleFactor": 0.5 } } }
  }""")

  out_path = os.path.join(ROOT, "DataLake-Graph_Pyvis.html")
  net.write_html(out_path, open_browser=False)

  clients = sorted({rec.get("_client") for rec in nodes.values() if rec.get("_client")})
  platforms = sorted({rec.get("platform") for rec in nodes.values() if rec.get("platform")})
  projects = sorted({rec.get("project") for rec in nodes.values() if rec.get("project")})
  client_options = "".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in clients)

  # empty REPO -> no box at all; otherwise a clickable link, same style as #updated-at
  repo_link = (
    f'<div id="repo-link"><a href="{html.escape(REPO)}" target="_blank" rel="noopener">{html.escape(REPO)}</a></div>'
    if REPO else "")

  side_panel = SIDE_PANEL.format(
    title=html.escape(TITLE),
    client_options=client_options,
    updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    repo_link=repo_link,
    status_group=checkbox_group("States", "f-env", STATE_LABELS),
    platform_group=checkbox_group("Platforms", "f-plat", [(p, p) for p in platforms]),
    project_group=checkbox_group("Projects", "f-proj", [(p, p) for p in projects]))

  with open(out_path, encoding="utf-8") as f:
    page = f.read()
  # side-panel comes after .card in the DOM so it lands on the right (body is a flex row)
  page = page.replace("</body>", side_panel + FILTER_SCRIPT + "</body>", 1)
  # pyvis writes no <title> or favicon - the tab would otherwise show the file path and a blank icon
  head_tags = f'<title>{html.escape(TAB_TITLE)}</title>\n<link rel="icon" href="{FAVICON}">'
  page = page.replace("<head>", f"<head>\n{head_tags}", 1)
  with open(out_path, "w", encoding="utf-8") as f: f.write(page)

  # print(f"{len(nodes)} nodes -> {out_path}")