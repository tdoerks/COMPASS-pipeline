#!/usr/bin/env python3
"""
build_phage_therapy_viewer.py

Phage-therapy-focused interactive HTML viewer from COMPASS summary output.
Scores each bacterial isolate as a phage therapy candidate based on AMR burden
and prophage landscape, then visualizes candidates, resistance profiles,
prophage ecology, and strain diversity.

USAGE:
    python3 bin/build_phage_therapy_viewer.py \
        --compass compass_summary.tsv \
        [--phinder phinder_summary.tsv] \
        [--out phage_therapy_viewer.html]

Inputs:
    compass_summary.tsv   COMPASS pipeline summary (required)
    phinder_summary.tsv   PHINDER pipeline summary (optional — enables Phage Matching tab)

Output:
    phage_therapy_viewer.html   Self-contained interactive HTML
"""

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

# ── Drug class keywords that indicate last-resort resistance ─────────────────
LAST_RESORT_CLASSES = {
    'carbapenem', 'colistin', 'polymyxin', 'cefiderocol',
    'tigecycline', 'fosfomycin',
}
LAST_RESORT_GENES = re.compile(
    r'\b(blaKPC|blaNDM|blaOXA-48|blaVIM|blaIMP|mcr-[0-9]|tet[A-Z]M|vanA|vanB)\b',
    re.IGNORECASE,
)

# ── AMR drug class → short label ─────────────────────────────────────────────
CLASS_LABELS = {
    'aminoglycoside': 'Aminoglycoside',
    'beta-lactam': 'β-lactam',
    'carbapenem': 'Carbapenem',
    'cephalosporin': 'Cephalosporin',
    'colistin': 'Colistin',
    'fluoroquinolone': 'Fluoroquinolone',
    'fosfomycin': 'Fosfomycin',
    'macrolide': 'Macrolide',
    'phenicol': 'Phenicol',
    'polymyxin': 'Polymyxin',
    'sulfonamide': 'Sulfonamide',
    'tetracycline': 'Tetracycline',
    'tigecycline': 'Tigecycline',
    'trimethoprim': 'Trimethoprim',
}

# ── helpers ───────────────────────────────────────────────────────────────────

def num(v, default=0):
    try:
        return float(v) if v not in ('', '-', 'N/A', None) else default
    except (ValueError, TypeError):
        return default

def parse_list(v, sep=','):
    if not v or v in ('-', 'N/A', 'None', 'none'):
        return []
    return [x.strip() for x in str(v).split(sep) if x.strip()]

def median(lst):
    if not lst:
        return 0
    s = sorted(lst)
    n = len(s)
    return (s[n // 2 - 1] + s[n // 2]) / 2 if n % 2 == 0 else s[n // 2]

# ── scoring ───────────────────────────────────────────────────────────────────

def amr_burden_score(classes_str, genes_str=''):
    """0–5: how hard antibiotics will be (more classes / last-resort = higher)."""
    classes = [c.lower() for c in parse_list(classes_str)]
    genes   = genes_str or ''
    last_resort = any(c in LAST_RESORT_CLASSES for c in classes) or bool(LAST_RESORT_GENES.search(genes))
    n = len(classes)
    if last_resort:
        return 5
    if n >= 8:
        return 4
    if n >= 5:
        return 3
    if n >= 3:
        return 2
    if n >= 1:
        return 1
    return 0

def prophage_susceptibility_score(n_prophages):
    """0–5: how receptive to new phage infection (fewer prophages = higher score)."""
    n = int(n_prophages or 0)
    if n <= 1:
        return 5
    if n <= 3:
        return 4
    if n <= 6:
        return 3
    if n <= 10:
        return 2
    if n <= 15:
        return 1
    return 0

def priority_tier(pt_score, last_resort):
    """1 (best candidate) → 4 (low priority)."""
    if pt_score >= 8 and last_resort:
        return 1
    if pt_score >= 7 or (pt_score >= 5 and last_resort):
        return 2
    if pt_score >= 3:
        return 3
    return 4

PRIORITY_LABEL  = {1: 'Priority 1 ★★★', 2: 'Priority 2 ★★', 3: 'Priority 3 ★', 4: 'Low priority'}
PRIORITY_COLOR  = {1: '#c0392b', 2: '#e67e22', 3: '#f1c40f', 4: '#27ae60'}
PRIORITY_BG     = {1: '#fdecea', 2: '#fef3e7', 3: '#fefde7', 4: '#eafaf1'}

# ── data loading ──────────────────────────────────────────────────────────────

def load_compass(path):
    rows = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            classes_str = r.get('amr_classes', '') or ''
            genes_str   = r.get('top_amr_genes', '') or ''
            classes     = [c.lower() for c in parse_list(classes_str)]
            last_resort = (any(c in LAST_RESORT_CLASSES for c in classes)
                           or bool(LAST_RESORT_GENES.search(genes_str)))
            n_prophages = int(num(r.get('num_prophages'), 0))
            amr_s  = amr_burden_score(classes_str, genes_str)
            phg_s  = prophage_susceptibility_score(n_prophages)
            pt     = amr_s + phg_s
            tier   = priority_tier(pt, last_resort)

            rows.append({
                'id':             r.get('sample_id', ''),
                'organism':       r.get('organism', '') or '',
                'st':             r.get('mlst_st', '') or '',
                'scheme':         r.get('mlst_scheme', '') or '',
                'serovar':        r.get('serovar', '') or '',
                'state':          r.get('state', '') or '',
                'year':           r.get('year', '') or '',
                'source':         r.get('source', '') or '',
                'mdr_status':     r.get('mdr_status', '') or '',
                'amr_classes':    classes_str,
                'num_amr_classes':len(classes),
                'amr_classes_list': classes,
                'top_amr_genes':  genes_str,
                'last_resort':    last_resort,
                'num_amr_genes':  int(num(r.get('num_amr_genes'), 0)),
                'num_prophages':  n_prophages,
                'num_lytic':      int(num(r.get('num_lytic'), 0)),
                'num_lysogenic':  int(num(r.get('num_lysogenic'), 0)),
                'top_prophage_matches': r.get('top_prophage_matches', '') or '',
                'num_plasmids':   int(num(r.get('num_plasmids'), 0)),
                'inc_groups':     r.get('inc_groups', '') or '',
                'top_vf_genes':   r.get('top_virulence_genes', '') or r.get('top_vf_genes', '') or '',
                'stx_type':       r.get('stx_type', '') or '',
                'assembly_quality': r.get('assembly_quality', '') or '',
                'n50':            int(num(r.get('n50'), 0)),
                'amr_score':      amr_s,
                'phage_score':    phg_s,
                'pt_score':       pt,
                'priority':       tier,
            })
    print(f'COMPASS: {len(rows)} isolates loaded')
    return rows

def load_phinder(path):
    if not path or not os.path.exists(path):
        return []
    rows = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            rows.append({
                'id':       r.get('sample_id', ''),
                'host':     r.get('host', '') or r.get('organism', '') or '',
                'lifestyle':r.get('lifestyle', '') or '',
                'taxonomy': r.get('taxonomy', '') or r.get('ictv_family', '') or '',
                'checkv':   r.get('checkv_quality', '') or '',
                'length':   int(num(r.get('genome_length'), 0)),
            })
    print(f'PHINDER: {len(rows)} phages loaded')
    return rows

# ── aggregate stats ───────────────────────────────────────────────────────────

def summarize(records):
    n = len(records)
    if n == 0:
        return {}
    mdr_counts   = Counter(r['mdr_status'] or 'Unknown' for r in records)
    tier_counts  = Counter(r['priority'] for r in records)
    last_resort_n = sum(1 for r in records if r['last_resort'])
    prophage_vals = [r['num_prophages'] for r in records]
    amr_class_vals = [r['num_amr_classes'] for r in records]
    sts = [r['st'] for r in records if r['st'] and r['st'] not in ('', '-', 'Novel', 'ND')]
    unique_sts = len(set(sts))

    # AMR class frequency across all isolates
    all_classes = []
    for r in records:
        all_classes.extend(r['amr_classes_list'])
    class_freq = Counter(all_classes)

    # Prophage family frequency
    phage_families = []
    for r in records:
        for hit in parse_list(r['top_prophage_matches']):
            # strip accession/score parts — keep first token
            fam = hit.split('|')[0].split('_')[0].strip()
            if fam:
                phage_families.append(fam)
    family_freq = Counter(phage_families)

    # ST frequency
    st_freq = Counter(sts)

    return {
        'n': n,
        'mdr_counts': dict(mdr_counts),
        'tier_counts': {str(k): v for k, v in tier_counts.items()},
        'last_resort_n': last_resort_n,
        'last_resort_pct': round(100 * last_resort_n / n, 1),
        'median_prophages': median(prophage_vals),
        'median_amr_classes': median(amr_class_vals),
        'unique_sts': unique_sts,
        'class_freq': dict(class_freq.most_common(20)),
        'family_freq': dict(family_freq.most_common(20)),
        'st_freq': dict(st_freq.most_common(25)),
        'prophage_hist': build_histogram(prophage_vals, bins=list(range(0, 25))),
    }

def build_histogram(values, bins):
    counts = Counter()
    for v in values:
        b = min(int(v), max(bins))
        counts[b] += 1
    return {str(b): counts.get(b, 0) for b in bins}

# ── HTML builder ──────────────────────────────────────────────────────────────

def json_s(obj):
    return json.dumps(obj, ensure_ascii=False)

def build_html(records, phinder_records, stats, out_path):
    records_js   = json_s(records)
    phinder_js   = json_s(phinder_records)
    stats_js     = json_s(stats)
    priority_colors_js = json_s(PRIORITY_COLOR)
    priority_bg_js     = json_s(PRIORITY_BG)
    priority_labels_js = json_s({str(k): v for k, v in PRIORITY_LABEL.items()})
    has_phinder  = 'true' if phinder_records else 'false'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>COMPASS — Phage Therapy Viewer</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #f8f9fa; --card: #fff; --border: #dee2e6;
  --text: #212529; --muted: #6c757d;
  --p1: #c0392b; --p2: #e67e22; --p3: #f1c40f; --p4: #27ae60;
  --accent: #2980b9;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: var(--bg); color: var(--text); font-size: 14px; }}
header {{ background: #1a252f; color: #fff; padding: 14px 24px; display: flex;
          align-items: center; gap: 12px; }}
header h1 {{ font-size: 20px; font-weight: 600; }}
header .sub {{ font-size: 13px; color: #adb5bd; margin-left: auto; }}
.disclaimer {{ background: #fff3cd; border-bottom: 2px solid #ffc107;
               padding: 8px 24px; font-size: 12px; color: #856404; }}
.statsbar {{ display: flex; gap: 0; border-bottom: 1px solid var(--border);
             background: var(--card); }}
.stat {{ flex: 1; text-align: center; padding: 10px 6px;
         border-right: 1px solid var(--border); }}
.stat:last-child {{ border-right: none; }}
.stat .val {{ font-size: 22px; font-weight: 700; color: var(--accent); }}
.stat .lbl {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}
nav {{ background: var(--card); border-bottom: 2px solid var(--border);
       display: flex; gap: 0; overflow-x: auto; }}
nav button {{ padding: 10px 18px; border: none; background: none; cursor: pointer;
              font-size: 13px; color: var(--muted); border-bottom: 3px solid transparent;
              white-space: nowrap; transition: all .15s; }}
nav button.active {{ color: var(--accent); border-bottom-color: var(--accent);
                     font-weight: 600; }}
nav button:hover {{ background: #f0f4f8; color: var(--text); }}
.tab {{ display: none; padding: 20px 24px; }}
.tab.active {{ display: block; }}
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
.grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
@media(max-width: 900px) {{ .grid-2,.grid-3 {{ grid-template-columns: 1fr; }} }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 6px;
         padding: 16px; }}
.card h3 {{ font-size: 13px; font-weight: 600; color: var(--muted);
            text-transform: uppercase; letter-spacing: .5px; margin-bottom: 12px; }}
.chart-wrap {{ position: relative; height: 240px; }}
.chart-wrap-lg {{ position: relative; height: 320px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
thead th {{ background: #f0f4f8; padding: 7px 9px; text-align: left;
            border-bottom: 2px solid var(--border); cursor: pointer;
            user-select: none; white-space: nowrap; }}
thead th:hover {{ background: #e2e8f0; }}
tbody tr {{ border-bottom: 1px solid #f1f3f5; }}
tbody tr:hover {{ background: #f8f9fa; }}
td {{ padding: 6px 9px; vertical-align: top; }}
.badge {{ display: inline-block; padding: 2px 7px; border-radius: 10px;
          font-size: 11px; font-weight: 600; white-space: nowrap; }}
.tag {{ display: inline-block; padding: 1px 5px; border-radius: 3px;
        font-size: 10px; background: #e9ecef; color: #495057; margin: 1px; }}
.tag.lr {{ background: #fde8e8; color: #c0392b; }}
.filter-bar {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;
               align-items: center; }}
.filter-bar label {{ font-size: 12px; color: var(--muted); }}
.filter-bar select, .filter-bar input {{ padding: 5px 8px; border: 1px solid var(--border);
  border-radius: 4px; font-size: 12px; background: var(--card); }}
.filter-bar input[type=checkbox] {{ width: auto; margin-right: 4px; }}
.score-bar {{ display: flex; align-items: center; gap: 6px; }}
.score-bar .fill {{ height: 8px; border-radius: 4px; min-width: 4px; }}
.section-title {{ font-size: 16px; font-weight: 600; margin-bottom: 14px;
                  padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
.info-box {{ background: #e8f4fd; border-left: 4px solid var(--accent);
             padding: 10px 14px; border-radius: 0 4px 4px 0; font-size: 12.5px;
             margin-bottom: 14px; line-height: 1.5; }}
.score-legend {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; font-size: 12px; }}
.score-legend span {{ display: flex; align-items: center; gap: 5px; }}
.dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
#phinder-tab-btn {{ display: none; }}
</style>
</head>
<body>

<header>
  <div>
    <h1>COMPASS — Phage Therapy Viewer</h1>
  </div>
  <div class="sub" id="hdr-sub"></div>
</header>

<div class="disclaimer">
  For research use only. Phage therapy candidacy scores are computational estimates
  based on AMR burden and prophage landscape — not a clinical recommendation.
  Phage susceptibility requires empirical testing.
</div>

<div class="statsbar" id="statsbar"></div>

<nav>
  <button class="active" onclick="showTab('overview')">Overview</button>
  <button onclick="showTab('candidates')">Candidate Ranking</button>
  <button onclick="showTab('amr')">AMR Profile</button>
  <button onclick="showTab('prophage')">Prophage Landscape</button>
  <button onclick="showTab('strains')">Strain Diversity</button>
  <button id="phinder-tab-btn" onclick="showTab('matching')">Phage Matching</button>
</nav>

<!-- ── OVERVIEW TAB ────────────────────────────────────────────────────── -->
<div id="tab-overview" class="tab active">
  <div class="info-box">
    <strong>Phage Therapy Score</strong> = AMR Burden (0–5) + Prophage Susceptibility (0–5).
    Higher AMR burden = antibiotics are failing.
    Lower prophage count = bacteria more receptive to new phage infection.
    <strong>Priority 1 ★★★</strong> isolates have last-resort resistance <em>and</em> low prophage burden — the strongest candidates.
  </div>
  <div class="score-legend">
    <span><span class="dot" style="background:#c0392b"></span>Priority 1 — Last-resort resistance + low prophage burden</span>
    <span><span class="dot" style="background:#e67e22"></span>Priority 2 — High AMR, tractable phage target</span>
    <span><span class="dot" style="background:#f1c40f"></span>Priority 3 — Moderate candidate</span>
    <span><span class="dot" style="background:#27ae60"></span>Priority 4 — Low priority (antibiotics still viable)</span>
  </div>
  <div class="grid-2">
    <div class="card">
      <h3>Candidate Priority Distribution</h3>
      <div class="chart-wrap"><canvas id="chart-priority"></canvas></div>
    </div>
    <div class="card">
      <h3>MDR Classification</h3>
      <div class="chart-wrap"><canvas id="chart-mdr"></canvas></div>
    </div>
  </div>
  <div class="card">
    <h3>AMR Burden vs. Prophage Count (each dot = one isolate)</h3>
    <div class="chart-wrap-lg"><canvas id="chart-scatter"></canvas></div>
  </div>
</div>

<!-- ── CANDIDATE RANKING TAB ──────────────────────────────────────────── -->
<div id="tab-candidates" class="tab">
  <div class="filter-bar">
    <label>Priority:</label>
    <select id="f-priority" onchange="renderCandidates()">
      <option value="">All</option>
      <option value="1">Priority 1 ★★★</option>
      <option value="2">Priority 2 ★★</option>
      <option value="3">Priority 3 ★</option>
      <option value="4">Low priority</option>
    </select>
    <label>Organism:</label>
    <select id="f-organism" onchange="renderCandidates()"></select>
    <label><input type="checkbox" id="f-lr" onchange="renderCandidates()"> Last-resort only</label>
    <label style="margin-left:auto">Search: <input type="text" id="f-search" oninput="renderCandidates()" placeholder="ID / ST / gene…" style="width:160px"></label>
  </div>
  <div style="overflow-x:auto">
    <table id="tbl-candidates">
      <thead>
        <tr>
          <th onclick="sortBy('priority')">Priority ↕</th>
          <th onclick="sortBy('pt_score')">PT Score ↕</th>
          <th onclick="sortBy('id')">Sample ID ↕</th>
          <th onclick="sortBy('organism')">Organism ↕</th>
          <th onclick="sortBy('st')">ST ↕</th>
          <th onclick="sortBy('mdr_status')">MDR Status ↕</th>
          <th onclick="sortBy('num_amr_classes')">AMR Classes ↕</th>
          <th onclick="sortBy('num_prophages')">Prophages ↕</th>
          <th>Last Resort</th>
          <th>Top AMR Genes</th>
        </tr>
      </thead>
      <tbody id="cand-tbody"></tbody>
    </table>
  </div>
  <div id="cand-count" style="margin-top:8px;font-size:12px;color:var(--muted)"></div>
</div>

<!-- ── AMR PROFILE TAB ────────────────────────────────────────────────── -->
<div id="tab-amr" class="tab">
  <div class="grid-2">
    <div class="card">
      <h3>Resistance Class Frequency</h3>
      <div class="chart-wrap-lg"><canvas id="chart-amr-classes"></canvas></div>
    </div>
    <div class="card">
      <h3>MDR Status Breakdown</h3>
      <div class="chart-wrap"><canvas id="chart-amr-mdr"></canvas></div>
    </div>
  </div>
  <div class="card">
    <h3>Last-Resort Resistance Genes Detected</h3>
    <div id="lr-genes-table" style="overflow-x:auto;margin-top:8px"></div>
  </div>
</div>

<!-- ── PROPHAGE LANDSCAPE TAB ─────────────────────────────────────────── -->
<div id="tab-prophage" class="tab">
  <div class="grid-2">
    <div class="card">
      <h3>Prophage Count Distribution</h3>
      <div class="chart-wrap"><canvas id="chart-phg-hist"></canvas></div>
    </div>
    <div class="card">
      <h3>Lytic vs Lysogenic Prophages</h3>
      <div class="chart-wrap"><canvas id="chart-phg-lifestyle"></canvas></div>
    </div>
  </div>
  <div class="grid-2">
    <div class="card">
      <h3>Top Prophage Families / Matches</h3>
      <div class="chart-wrap"><canvas id="chart-phg-families"></canvas></div>
    </div>
    <div class="card">
      <h3>Superinfection Immunity Risk</h3>
      <div id="si-risk-content"></div>
    </div>
  </div>
</div>

<!-- ── STRAIN DIVERSITY TAB ───────────────────────────────────────────── -->
<div id="tab-strains" class="tab">
  <div class="grid-2">
    <div class="card">
      <h3>Top Sequence Types (ST)</h3>
      <div class="chart-wrap-lg"><canvas id="chart-st"></canvas></div>
    </div>
    <div class="card">
      <h3>Phage Coverage Estimate</h3>
      <div id="coverage-content" style="margin-top:8px"></div>
    </div>
  </div>
</div>

<!-- ── PHAGE MATCHING TAB ─────────────────────────────────────────────── -->
<div id="tab-matching" class="tab">
  <div class="info-box">
    PHINDER phages are matched to bacterial isolates by host organism. Exact host range
    requires empirical plaque assays — this tab shows which PHINDER phage types are
    available for each bacterial species group in the dataset.
  </div>
  <div id="matching-content"></div>
</div>

<script>
// ── data ──────────────────────────────────────────────────────────────────
const RECORDS         = {records_js};
const PHINDER         = {phinder_js};
const STATS           = {stats_js};
const PRIORITY_COLORS = {priority_colors_js};
const PRIORITY_BG     = {priority_bg_js};
const PRIORITY_LABELS = {priority_labels_js};
const HAS_PHINDER     = {has_phinder};

// ── tab switching ─────────────────────────────────────────────────────────
function showTab(name) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}}

// ── stats bar ─────────────────────────────────────────────────────────────
function renderStatsBar() {{
  const n = RECORDS.length;
  const lr = RECORDS.filter(r => r.last_resort).length;
  const p1 = RECORDS.filter(r => r.priority === 1).length;
  const mdn_phg = median(RECORDS.map(r => r.num_prophages));
  const pct_mdr = RECORDS.filter(r => ['MDR','XDR','PDR'].includes(r.mdr_status)).length;
  document.getElementById('hdr-sub').textContent = `${{n}} isolates`;
  document.getElementById('statsbar').innerHTML = [
    ['Isolates', n],
    ['Priority 1 ★★★', p1],
    ['Last-Resort Resistance', lr + ' (' + pct(lr,n) + '%)'],
    ['MDR / XDR / PDR', pct_mdr + ' (' + pct(pct_mdr,n) + '%)'],
    ['Median Prophages', mdn_phg.toFixed(1)],
    ['Unique STs', STATS.unique_sts],
  ].map(([l,v]) => `<div class="stat"><div class="val">${{v}}</div><div class="lbl">${{l}}</div></div>`).join('');
}}

function pct(a,b) {{ return b ? (100*a/b).toFixed(1) : 0; }}
function median(arr) {{
  if (!arr.length) return 0;
  const s = [...arr].sort((a,b)=>a-b);
  const m = Math.floor(s.length/2);
  return s.length%2 ? s[m] : (s[m-1]+s[m])/2;
}}

// ── overview charts ───────────────────────────────────────────────────────
function renderOverview() {{
  // Priority donut
  const tierC = STATS.tier_counts;
  new Chart(document.getElementById('chart-priority'), {{
    type: 'doughnut',
    data: {{
      labels: ['Priority 1 ★★★','Priority 2 ★★','Priority 3 ★','Low priority'],
      datasets: [{{ data: [tierC['1']||0,tierC['2']||0,tierC['3']||0,tierC['4']||0],
        backgroundColor: ['#c0392b','#e67e22','#f1c40f','#27ae60'], borderWidth: 2 }}]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      plugins: {{ legend: {{ position:'right' }} }} }}
  }});

  // MDR donut
  const mdr = STATS.mdr_counts;
  const mdrKeys = Object.keys(mdr).sort();
  const mdrColors = mdrKeys.map(k => ({{
    'PDR':'#c0392b','XDR':'#e74c3c','MDR':'#e67e22',
    'Susceptible':'#27ae60','Non-MDR':'#2ecc71','Unknown':'#95a5a6'
  }})[k] || '#bdc3c7');
  new Chart(document.getElementById('chart-mdr'), {{
    type: 'doughnut',
    data: {{
      labels: mdrKeys,
      datasets: [{{ data: mdrKeys.map(k=>mdr[k]), backgroundColor: mdrColors, borderWidth: 2 }}]
    }},
    options: {{ responsive:true, maintainAspectRatio:false,
      plugins: {{ legend: {{ position:'right' }} }} }}
  }});

  // Scatter: AMR classes vs prophage count, colored by priority
  const scatterData = RECORDS.map(r => ({{
    x: r.num_amr_classes, y: r.num_prophages,
    label: r.id + ' (' + (r.st||'?') + ')',
    priority: r.priority,
  }}));
  const byPriority = [1,2,3,4].map(p => ({{
    label: PRIORITY_LABELS[p],
    data: scatterData.filter(d=>d.priority===p).map(d=>({{x:d.x,y:d.y,label:d.label}})),
    backgroundColor: PRIORITY_COLORS[p] + '99',
    borderColor: PRIORITY_COLORS[p],
    pointRadius: 5, pointHoverRadius: 7,
  }}));
  new Chart(document.getElementById('chart-scatter'), {{
    type: 'scatter',
    data: {{ datasets: byPriority }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins: {{
        legend: {{ position:'top' }},
        tooltip: {{ callbacks: {{ label: ctx => ctx.raw.label + ' | AMR:' + ctx.raw.x + ' Phg:' + ctx.raw.y }} }}
      }},
      scales: {{
        x: {{ title: {{ display:true, text:'AMR Drug Classes Detected' }} }},
        y: {{ title: {{ display:true, text:'Prophage Count' }} }},
      }}
    }}
  }});
}}

// ── candidate ranking ─────────────────────────────────────────────────────
let sortCol = 'priority', sortAsc = true;
function sortBy(col) {{
  if (sortCol === col) sortAsc = !sortAsc;
  else {{ sortCol = col; sortAsc = true; }}
  renderCandidates();
}}

function renderCandidates() {{
  const fp = document.getElementById('f-priority').value;
  const fo = document.getElementById('f-organism').value;
  const lr = document.getElementById('f-lr').checked;
  const fs = document.getElementById('f-search').value.toLowerCase();

  let rows = RECORDS.filter(r => {{
    if (fp && r.priority !== +fp) return false;
    if (fo && !r.organism.toLowerCase().includes(fo.toLowerCase())) return false;
    if (lr && !r.last_resort) return false;
    if (fs && !(r.id+r.st+r.top_amr_genes+r.organism).toLowerCase().includes(fs)) return false;
    return true;
  }});

  rows.sort((a,b) => {{
    let av = a[sortCol], bv = b[sortCol];
    if (typeof av === 'string') {{ av=av.toLowerCase(); bv=bv.toLowerCase(); }}
    if (av < bv) return sortAsc ? -1 : 1;
    if (av > bv) return sortAsc ? 1 : -1;
    return 0;
  }});

  const tbody = document.getElementById('cand-tbody');
  tbody.innerHTML = rows.map(r => {{
    const col  = PRIORITY_COLORS[r.priority];
    const bg   = PRIORITY_BG[r.priority];
    const lbl  = PRIORITY_LABELS[r.priority];
    const lrBadge = r.last_resort
      ? `<span class="badge" style="background:#fde8e8;color:#c0392b">⚠ Last-resort</span>` : '—';
    const topGenes = r.top_amr_genes ? r.top_amr_genes.split(',').slice(0,4)
      .map(g=>`<span class="tag${{r.last_resort && g.match(/KPC|NDM|OXA-48|VIM|IMP|mcr/i) ? ' lr' : ''}}">${{g.trim()}}</span>`).join('') : '—';
    const scoreBar = `<div class="score-bar">
      <span style="width:24px;text-align:right;font-weight:700">${{r.pt_score}}</span>
      <div class="fill" style="width:${{r.pt_score*18}}px;background:${{col}}"></div>
    </div>`;
    return `<tr style="background:${{bg}}">
      <td><span class="badge" style="background:${{col}};color:#fff">${{lbl}}</span></td>
      <td>${{scoreBar}}</td>
      <td style="font-family:monospace;font-size:11px">${{r.id}}</td>
      <td><em>${{r.organism||'—'}}</em></td>
      <td>${{r.st ? 'ST'+r.st : '—'}}</td>
      <td>${{r.mdr_status||'—'}}</td>
      <td style="text-align:center">${{r.num_amr_classes}}</td>
      <td style="text-align:center">${{r.num_prophages}}</td>
      <td>${{lrBadge}}</td>
      <td>${{topGenes}}</td>
    </tr>`;
  }}).join('');

  document.getElementById('cand-count').textContent =
    `Showing ${{rows.length}} of ${{RECORDS.length}} isolates`;
}}

function populateOrganismFilter() {{
  const orgs = [...new Set(RECORDS.map(r=>r.organism).filter(Boolean))].sort();
  const sel = document.getElementById('f-organism');
  sel.innerHTML = '<option value="">All organisms</option>' +
    orgs.map(o=>`<option value="${{o}}">${{o}}</option>`).join('');
}}

// ── AMR profile ───────────────────────────────────────────────────────────
function renderAMR() {{
  const cf = STATS.class_freq;
  const labels = Object.keys(cf);
  const vals   = labels.map(k=>cf[k]);
  const colors = labels.map(l =>
    ['carbapenem','colistin','polymyxin','tigecycline','cefiderocol','fosfomycin']
      .includes(l.toLowerCase()) ? '#c0392b' : '#3498db');

  new Chart(document.getElementById('chart-amr-classes'), {{
    type: 'bar',
    data: {{
      labels, datasets: [{{ label:'Isolates', data:vals, backgroundColor:colors }}]
    }},
    options: {{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>`${{c.raw}} isolates (${{pct(c.raw,RECORDS.length)}}%)`}}}}
      }},
      scales:{{ x:{{title:{{display:true,text:'Isolate count'}}}} }}
    }}
  }});

  const mdr = STATS.mdr_counts;
  const mdrKeys = Object.keys(mdr).sort();
  const mdrColors = mdrKeys.map(k=>({{'PDR':'#c0392b','XDR':'#e74c3c','MDR':'#e67e22',
    'Susceptible':'#27ae60','Non-MDR':'#2ecc71'}})[k]||'#bdc3c7');
  new Chart(document.getElementById('chart-amr-mdr'), {{
    type: 'doughnut',
    data: {{ labels:mdrKeys, datasets:[{{data:mdrKeys.map(k=>mdr[k]),
      backgroundColor:mdrColors, borderWidth:2}}] }},
    options: {{ responsive:true, maintainAspectRatio:false,
      plugins:{{legend:{{position:'right'}}}} }}
  }});

  // Last-resort genes table
  const lrRows = RECORDS.filter(r=>r.last_resort);
  const geneCounts = {{}};
  lrRows.forEach(r => {{
    r.top_amr_genes.split(',').forEach(g => {{
      g = g.trim();
      if (/KPC|NDM|OXA-48|VIM|IMP|mcr-/i.test(g)) geneCounts[g] = (geneCounts[g]||0)+1;
    }});
  }});
  const lrDiv = document.getElementById('lr-genes-table');
  if (Object.keys(geneCounts).length === 0) {{
    lrDiv.innerHTML = '<p style="color:var(--muted);font-size:12px">No last-resort resistance genes detected in top_amr_genes.</p>';
  }} else {{
    const sorted = Object.entries(geneCounts).sort((a,b)=>b[1]-a[1]);
    lrDiv.innerHTML = `<table><thead><tr><th>Gene</th><th>Isolates</th><th>% of collection</th></tr></thead>
      <tbody>${{sorted.map(([g,c])=>`<tr><td><span class="tag lr">${{g}}</span></td>
        <td>${{c}}</td><td>${{pct(c,RECORDS.length)}}%</td></tr>`).join('')}}</tbody></table>`;
  }}
}}

// ── prophage landscape ────────────────────────────────────────────────────
function renderProphage() {{
  // Histogram
  const hist = STATS.prophage_hist;
  const hLabels = Object.keys(hist).map(k => +k === 24 ? '24+' : k);
  new Chart(document.getElementById('chart-phg-hist'), {{
    type: 'bar',
    data: {{
      labels: hLabels,
      datasets: [{{ label:'Isolates', data:Object.values(hist),
        backgroundColor:'#3498db88', borderColor:'#2980b9', borderWidth:1 }}]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}}},
      scales:{{
        x:{{title:{{display:true,text:'Prophage count'}}}},
        y:{{title:{{display:true,text:'Isolates'}}}}
      }}
    }}
  }});

  // Lytic vs lysogenic — group into bins
  const bins = [0,1,2,3,4,5,6,7,8,9,'10+'];
  const lyticBins = {{}}, lysoBins = {{}};
  bins.forEach(b=>{{ lyticBins[b]=0; lysoBins[b]=0; }});
  RECORDS.forEach(r=>{{
    const k = r.num_prophages >= 10 ? '10+' : r.num_prophages;
    lyticBins[k]  = (lyticBins[k]||0) + r.num_lytic;
    lysoBins[k]   = (lysoBins[k]||0) + r.num_lysogenic;
  }});
  new Chart(document.getElementById('chart-phg-lifestyle'), {{
    type: 'bar',
    data: {{
      labels: bins.map(String),
      datasets: [
        {{ label:'Lytic', data:bins.map(b=>lyticBins[b]),
           backgroundColor:'#e74c3c88', borderColor:'#c0392b', borderWidth:1 }},
        {{ label:'Lysogenic', data:bins.map(b=>lysoBins[b]),
           backgroundColor:'#8e44ad88', borderColor:'#7d3c98', borderWidth:1 }}
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      scales:{{
        x:{{stacked:true, title:{{display:true,text:'Prophages per isolate'}}}},
        y:{{stacked:true, title:{{display:true,text:'Total phage count'}}}}
      }}
    }}
  }});

  // Top families
  const ff = STATS.family_freq;
  const ffLabels = Object.keys(ff).slice(0,15);
  new Chart(document.getElementById('chart-phg-families'), {{
    type: 'bar',
    data: {{
      labels: ffLabels,
      datasets:[{{ label:'Hits', data:ffLabels.map(k=>ff[k]),
        backgroundColor:'#9b59b688', borderColor:'#8e44ad', borderWidth:1 }}]
    }},
    options: {{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}}},
      scales:{{x:{{title:{{display:true,text:'Total hits'}}}}}}
    }}
  }});

  // Superinfection risk
  const risk = [
    [0, 1, 'Low', '#27ae60', 'Minimal prophage content — highly receptive to new phage infection'],
    [2, 5, 'Moderate', '#f1c40f', 'Some prophage present — partial immunity possible for related phages'],
    [6, 12, 'Elevated', '#e67e22', 'High prophage burden — superinfection immunity likely for some phage families'],
    [13, 999, 'High', '#c0392b', 'Very high prophage burden — strong superinfection immunity; cocktail approach recommended'],
  ];
  const riskCounts = risk.map(([lo,hi,lbl,col,desc]) => {{
    const n = RECORDS.filter(r => r.num_prophages >= lo && r.num_prophages <= hi).length;
    return {{lo,hi,lbl,col,desc,n}};
  }});
  document.getElementById('si-risk-content').innerHTML =
    riskCounts.map(r => `
      <div style="margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">
          <span class="badge" style="background:${{r.col}};color:#fff">${{r.lbl}}</span>
          <strong style="font-size:13px">${{r.n}} isolates (${{pct(r.n,RECORDS.length)}}%)</strong>
          <span style="font-size:11px;color:var(--muted)">${{r.lo}}–${{r.hi == 999 ? '∞' : r.hi}} prophages</span>
        </div>
        <div style="font-size:12px;color:var(--muted)">${{r.desc}}</div>
      </div>`).join('');
}}

// ── strain diversity ──────────────────────────────────────────────────────
function renderStrains() {{
  const sf = STATS.st_freq;
  const stLabels = Object.keys(sf).map(k => 'ST' + k);
  const stVals   = Object.values(sf);
  const total    = RECORDS.length;

  new Chart(document.getElementById('chart-st'), {{
    type: 'bar',
    data: {{
      labels: stLabels,
      datasets:[{{ label:'Isolates', data:stVals,
        backgroundColor:'#2980b988', borderColor:'#2980b9', borderWidth:1 }}]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>`${{c.raw}} isolates (${{pct(c.raw,total)}}%)`}}}}
      }},
      scales:{{ x:{{title:{{display:true,text:'Sequence Type'}}}},
                y:{{title:{{display:true,text:'Isolate count'}}}} }}
    }}
  }});

  // Coverage estimate
  const stArr = Object.entries(sf).sort((a,b)=>b[1]-a[1]);
  let cumulative = 0, coverageHTML = '<table><thead><tr><th>Top N STs</th><th>Isolates covered</th><th>% of collection</th></tr></thead><tbody>';
  [1,2,5,10].forEach(topN => {{
    const cov = stArr.slice(0,topN).reduce((s,[,c])=>s+c,0);
    coverageHTML += `<tr><td>Top ${{topN}} ST${{topN>1?'s':''}}</td><td>${{cov}}</td><td>${{pct(cov,total)}}%</td></tr>`;
  }});
  coverageHTML += `<tr><td>All ${{stArr.length}} STs</td><td>${{total}}</td><td>100%</td></tr>`;
  coverageHTML += '</tbody></table>';
  coverageHTML += `<p style="margin-top:12px;font-size:12px;color:var(--muted)">
    A phage targeting the top ST may cover ${{pct(stArr[0]?.[1]||0, total)}}% of isolates.
    A 5-phage cocktail targeting the top 5 STs could cover ~${{pct(stArr.slice(0,5).reduce((s,[,c])=>s+c,0),total)}}% of the collection.
    (Note: phage host range extends by receptor, not strictly by ST — empirical validation required.)</p>`;
  document.getElementById('coverage-content').innerHTML = coverageHTML;
}}

// ── phage matching ────────────────────────────────────────────────────────
function renderMatching() {{
  if (!HAS_PHINDER) return;
  document.getElementById('phinder-tab-btn').style.display = '';

  // Group PHINDER phages by host organism
  const phagesByHost = {{}};
  PHINDER.forEach(p => {{
    const h = p.host || 'Unknown';
    (phagesByHost[h] = phagesByHost[h]||[]).push(p);
  }});

  // Group COMPASS isolates by organism
  const isolatesByOrg = {{}};
  RECORDS.forEach(r => {{
    const o = r.organism || 'Unknown';
    (isolatesByOrg[o] = isolatesByOrg[o]||[]).push(r);
  }});

  let html = '';
  Object.entries(isolatesByOrg).sort((a,b)=>b[1].length-a[1].length).forEach(([org, isos]) => {{
    // Find matching phages (case-insensitive genus match)
    const genus = org.split(' ')[0].toLowerCase();
    const matching = PHINDER.filter(p => p.host.toLowerCase().includes(genus));

    const p1 = isos.filter(i=>i.priority===1).length;
    const lr = isos.filter(i=>i.last_resort).length;

    html += `<div class="card" style="margin-bottom:14px">
      <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:10px">
        <h3 style="text-transform:none;font-size:14px"><em>${{org}}</em></h3>
        <span style="font-size:12px;color:var(--muted)">${{isos.length}} isolates</span>
        ${{p1?`<span class="badge" style="background:#c0392b;color:#fff">${{p1}} Priority 1</span>`:''}}
        ${{lr?`<span class="badge" style="background:#fde8e8;color:#c0392b">${{lr}} last-resort</span>`:''}}

      </div>`;

    if (matching.length === 0) {{
      html += `<p style="font-size:12px;color:var(--muted)">No matching phages in PHINDER library for this organism.</p>`;
    }} else {{
      html += `<table><thead><tr><th>Phage ID</th><th>Lifestyle</th><th>Taxonomy</th><th>CheckV Quality</th><th>Genome (bp)</th></tr></thead><tbody>`;
      matching.forEach(p => {{
        html += `<tr><td style="font-family:monospace;font-size:11px">${{p.id}}</td>
          <td>${{p.lifestyle||'—'}}</td><td>${{p.taxonomy||'—'}}</td>
          <td>${{p.checkv||'—'}}</td><td>${{p.length?p.length.toLocaleString():'—'}}</td></tr>`;
      }});
      html += `</tbody></table>`;
    }}
    html += `</div>`;
  }});
  document.getElementById('matching-content').innerHTML = html;
}}

// ── init ──────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {{
  renderStatsBar();
  renderOverview();
  populateOrganismFilter();
  renderCandidates();
  renderAMR();
  renderProphage();
  renderStrains();
  if (HAS_PHINDER) {{
    document.getElementById('phinder-tab-btn').style.display = '';
    renderMatching();
  }}
}});
</script>
</body>
</html>
"""
    with open(out_path, 'w') as f:
        f.write(html)
    print(f'Wrote: {out_path}')

# ── main ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='Build phage therapy viewer from COMPASS output')
    p.add_argument('--compass',  default=os.environ.get('COMPASS_TSV', 'compass_summary.tsv'),
                   help='Path to compass_summary.tsv')
    p.add_argument('--phinder', default=None,
                   help='Path to PHINDER summary TSV (optional, enables Phage Matching tab)')
    p.add_argument('--out', default='phage_therapy_viewer.html',
                   help='Output HTML path (default: phage_therapy_viewer.html)')
    return p.parse_args()

def main():
    args = parse_args()
    if not os.path.exists(args.compass):
        sys.exit(f'ERROR: COMPASS summary not found: {args.compass}')
    records  = load_compass(args.compass)
    phinder  = load_phinder(args.phinder) if args.phinder else []
    stats    = summarize(records)
    build_html(records, phinder, stats, args.out)
    p1 = sum(1 for r in records if r['priority'] == 1)
    lr = sum(1 for r in records if r['last_resort'])
    print(f'Priority 1 candidates: {p1}')
    print(f'Last-resort resistance: {lr} ({100*lr/max(len(records),1):.1f}%)')
    print(f'Unique STs: {stats["unique_sts"]}')

if __name__ == '__main__':
    main()
