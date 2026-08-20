#!/usr/bin/env python3
"""
build_compass_viewer.py

Join COMPASS genomic summary with NCBI MIC/SIR metadata and produce a
self-contained interactive HTML viewer.

USAGE (run from COMPASS-1.1.0/ on Beocat):
    python3 bin/build_compass_viewer.py

Inputs (defaults):
    results_mic_ecoli_6k/summary/compass_summary.tsv
    mic_ecoli_metadata/mic_metadata.csv

Output:
    compass_mic_viewer.html   (self-contained, open in browser)
"""

import csv
import json
import os
import re
import sys

COMPASS_TSV  = os.environ.get('COMPASS_TSV',  'results_mic_ecoli_6k/summary/compass_summary.tsv')
MIC_CSV      = os.environ.get('MIC_CSV',      'mic_ecoli_metadata/mic_metadata.csv')
OUT_HTML     = os.environ.get('OUT_HTML',     'compass_mic_viewer.html')

# ── helpers ──────────────────────────────────────────────────────────────────

def acc_key(acc):
    """GCA_000692755.1 → GCA_000692755_1  (match compass sample_id format)"""
    return acc.replace('.', '_', 1).replace('.', '_')

def num(v, default=None):
    try:
        return float(v) if v not in ('', '-', 'N/A', None) else default
    except (ValueError, TypeError):
        return default

# ── load compass ─────────────────────────────────────────────────────────────

def load_compass(path):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f, delimiter='\t'):
            rows[r['sample_id']] = r
    print(f'COMPASS: {len(rows)} samples')
    return rows

# ── load MIC ─────────────────────────────────────────────────────────────────

def load_mic(path):
    rows = {}
    sir_cols = []
    with open(path) as f:
        reader = csv.DictReader(f)
        sir_cols = [c for c in reader.fieldnames if c.startswith('sir_')]
        for r in reader:
            key = acc_key(r['assembly_accession'])
            rows[key] = r
    print(f'MIC: {len(rows)} samples, {len(sir_cols)} antibiotics')
    return rows, sir_cols

# ── merge ─────────────────────────────────────────────────────────────────────

def merge(compass, mic, sir_cols):
    records = []
    for sid, crow in compass.items():
        mrow = mic.get(sid, {})
        rec = {
            'id':              sid,
            'organism':        crow.get('organism', ''),
            'mlst_st':         crow.get('mlst_st', ''),
            'assembly_quality':crow.get('assembly_quality', ''),
            'n50':             num(crow.get('n50')),
            'assembly_length': num(crow.get('assembly_length')),
            'num_prophages':   num(crow.get('num_prophages'), 0),
            'num_lytic':       num(crow.get('num_lytic'), 0),
            'num_lysogenic':   num(crow.get('num_lysogenic'), 0),
            'num_amr_genes':   num(crow.get('num_amr_genes'), 0),
            'num_plasmids':    num(crow.get('num_plasmids'), 0),
            'mdr_status':      crow.get('mdr_status', ''),
            'amr_classes':     crow.get('amr_classes', ''),
            'inc_groups':      crow.get('inc_groups', ''),
            'num_virulence_genes': num(crow.get('num_virulence_genes'), 0),
            'strain':          mrow.get('strain', ''),
            'biosample':       mrow.get('biosample', ''),
        }
        for s in sir_cols:
            v = mrow.get(s, '').strip()
            rec[s] = v if v in ('S', 'I', 'R') else ''
        # Shiga toxin (stx) classification from top_virulence_genes
        _vf = crow.get('top_virulence_genes', '') or ''
        _has1 = bool(re.search(r'\bstx\w*1\b', _vf, re.IGNORECASE))
        _has2 = bool(re.search(r'\bstx\w*2\b', _vf, re.IGNORECASE))
        rec['stx_status'] = ('stx1+stx2' if _has1 and _has2 else
                             'stx1' if _has1 else 'stx2' if _has2 else 'negative')
        rec['stx_genes'] = ', '.join(g.strip() for g in _vf.split(',')
                                      if g.strip().lower().startswith('stx'))
        records.append(rec)
    print(f'Merged: {len(records)} records')
    return records

# ── statistics helpers ────────────────────────────────────────────────────────

def resistance_summary(records, sir_cols):
    """For each antibiotic: count S/I/R/missing and median prophage per group."""
    summary = []
    for col in sir_cols:
        drug = col[4:]  # strip sir_
        groups = {'S': [], 'I': [], 'R': []}
        for r in records:
            v = r.get(col, '')
            if v in groups:
                groups[v].append(r['num_prophages'] or 0)
        total = sum(len(v) for v in groups.values())
        if total == 0:
            continue
        def med(lst):
            if not lst: return None
            s = sorted(lst); n = len(s)
            return (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
        summary.append({
            'drug': drug,
            'n_S': len(groups['S']),
            'n_I': len(groups['I']),
            'n_R': len(groups['R']),
            'n_tested': total,
            'pct_R': round(100*len(groups['R'])/total, 1) if total else 0,
            'med_phage_S': med(groups['S']),
            'med_phage_I': med(groups['I']),
            'med_phage_R': med(groups['R']),
            'phage_S': groups['S'],
            'phage_I': groups['I'],
            'phage_R': groups['R'],
        })
    summary.sort(key=lambda x: -x['pct_R'])
    return summary

def mlst_summary(records, top_n=20):
    from collections import defaultdict
    sts = defaultdict(list)
    for r in records:
        st = r['mlst_st'] or 'Unknown'
        sts[st].append(r)
    result = []
    for st, recs in sorted(sts.items(), key=lambda x: -len(x[1]))[:top_n]:
        mdr = sum(1 for r in recs if r['mdr_status'] == 'Yes')
        phages = [r['num_prophages'] or 0 for r in recs]
        result.append({
            'st': st, 'n': len(recs),
            'pct_mdr': round(100*mdr/len(recs), 1),
            'med_phage': sorted(phages)[len(phages)//2],
        })
    return result

# ── build HTML ────────────────────────────────────────────────────────────────

def build_html(records, sir_cols, res_summary, mlst_sum, out_path):
    # Slim records for table (all fields)
    table_cols = ['id','organism','mlst_st','num_prophages','num_lytic','num_lysogenic',
                  'num_amr_genes','num_plasmids','mdr_status','assembly_quality','strain',
                  'stx_status','stx_genes']
    table_rows = [{c: r.get(c,'') for c in table_cols} for r in records]

    # For boxplot data per drug: send full lists
    boxplot_data = {s['drug']: {'S': s['phage_S'], 'I': s['phage_I'], 'R': s['phage_R']} for s in res_summary}

    # Scatter data: prophages vs amr_genes
    scatter = [{'x': r['num_amr_genes'], 'y': r['num_prophages'],
                'mdr': r['mdr_status'], 'id': r['id']} for r in records
               if r['num_amr_genes'] is not None and r['num_prophages'] is not None]

    # Scatter 2: plasmids vs prophages
    scatter2 = [{'x': r['num_plasmids'], 'y': r['num_prophages'],
                 'mdr': r['mdr_status'], 'id': r['id']} for r in records
                if r['num_plasmids'] is not None and r['num_prophages'] is not None]

    # Overview stats
    n_mdr = sum(1 for r in records if r['mdr_status'] == 'Yes')
    phage_vals = [r['num_prophages'] for r in records if r['num_prophages'] is not None]
    med_phage = sorted(phage_vals)[len(phage_vals)//2] if phage_vals else 0
    n_with_phage = sum(1 for v in phage_vals if v > 0)
    amr_vals = [r['num_amr_genes'] for r in records if r['num_amr_genes'] is not None]
    med_amr = sorted(amr_vals)[len(amr_vals)//2] if amr_vals else 0

    # Phage histogram bins
    from collections import Counter
    phage_hist = Counter(int(v) for v in phage_vals)
    phage_hist_data = [{'bin': k, 'count': v} for k, v in sorted(phage_hist.items()) if k <= 20]

    # Shiga toxin summary
    stx_counts = Counter(r.get('stx_status', 'negative') for r in records)
    stx_summary = {
        'stx1':     stx_counts.get('stx1', 0),
        'stx2':     stx_counts.get('stx2', 0),
        'stx1+stx2': stx_counts.get('stx1+stx2', 0),
        'negative': stx_counts.get('negative', 0),
        'n_positive': stx_counts.get('stx1', 0) + stx_counts.get('stx2', 0) + stx_counts.get('stx1+stx2', 0),
    }

    payload = {
        'records': records,
        'table_rows': table_rows,
        'res_summary': [{k:v for k,v in s.items() if k not in ('phage_S','phage_I','phage_R')} for s in res_summary],
        'boxplot_data': boxplot_data,
        'mlst_summary': mlst_sum,
        'scatter': scatter,
        'scatter2': scatter2,
        'phage_hist': phage_hist_data,
        'stats': {
            'n_total': len(records),
            'n_mdr': n_mdr,
            'pct_mdr': round(100*n_mdr/len(records), 1) if records else 0,
            'med_phage': med_phage,
            'n_with_phage': n_with_phage,
            'pct_with_phage': round(100*n_with_phage/len(phage_vals), 1) if phage_vals else 0,
            'med_amr': med_amr,
            'n_antibiotics': len(sir_cols),
        },
        'sir_cols': [c[4:] for c in sir_cols],
        'stx_summary': stx_summary,
    }

    html = HTML_TEMPLATE.replace('__DATA__', json.dumps(payload, separators=(',', ':')))
    with open(out_path, 'w') as f:
        f.write(html)
    size_mb = os.path.getsize(out_path) / 1e6
    print(f'Written: {out_path} ({size_mb:.1f} MB)')

# ── HTML template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>COMPASS — MIC & Genomics Explorer</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
:root{--bg:#0f1419;--panel:#161d26;--panel2:#1e2a38;--ink:#e8edf2;--muted:#6b7f94;
  --accent:#38bdf8;--warn:#f59e0b;--danger:#ef4444;--ok:#22c55e;--line:#2a3a4d;
  --S:#22c55e;--I:#f59e0b;--R:#ef4444;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font:14px/1.5 'Inter',system-ui,sans-serif;min-height:100vh}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:14px 24px;display:flex;align-items:center;gap:16px}
header h1{font-size:18px;font-weight:700}header span{color:var(--muted);font-size:13px}
nav{display:flex;gap:2px;padding:8px 16px;background:var(--panel);border-bottom:1px solid var(--line);flex-wrap:wrap}
nav button{background:none;border:none;color:var(--muted);padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:500}
nav button:hover{color:var(--ink);background:var(--panel2)}
nav button.active{color:var(--accent);background:var(--panel2)}
main{padding:20px;max-width:1400px;margin:0 auto}
.tab{display:none}.tab.active{display:block}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin-bottom:18px}
.card h3{font-size:15px;font-weight:600;margin-bottom:12px}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 22px;min-width:140px}
.kpi .n{font-size:28px;font-weight:700;color:var(--accent)}
.kpi .l{font-size:12px;color:var(--muted);margin-top:2px}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
.controls label{font-size:12px;color:var(--muted)}
select,input[type=text]{background:var(--panel2);border:1px solid var(--line);color:var(--ink);
  padding:5px 10px;border-radius:6px;font-size:13px}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:7px 10px;color:var(--muted);border-bottom:1px solid var(--line);white-space:nowrap;cursor:pointer}
th:hover{color:var(--ink)}
td{padding:6px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
tr:hover td{background:var(--panel2)}
.badge{display:inline-block;padding:1px 7px;border-radius:4px;font-size:11px;font-weight:600}
.S{background:#052e16;color:var(--S)}.I{background:#422006;color:var(--I)}.R{background:#450a0a;color:var(--R)}
.Yes{background:#450a0a;color:var(--danger)}.No{background:#052e16;color:var(--ok)}
.stx-chip{display:inline-block;padding:1px 7px;border-radius:4px;font-size:11px;font-weight:600}
.stx-pos1{background:#422006;color:#f59e0b}.stx-pos2{background:#450a0a;color:#ef4444}
.stx-both{background:#2d1b69;color:#a855f7}.stx-neg{background:#1e2a38;color:var(--muted)}
.axis text{fill:var(--muted);font-size:11px}.axis path,.axis line{stroke:var(--line)}
.grid line{stroke:var(--line);stroke-opacity:.5}
.empty{color:var(--muted);text-align:center;padding:40px}
.pagination{display:flex;gap:6px;align-items:center;margin-top:10px;font-size:12px;color:var(--muted)}
.pagination button{background:var(--panel2);border:1px solid var(--line);color:var(--ink);
  padding:3px 10px;border-radius:4px;cursor:pointer;font-size:12px}
.pagination button:disabled{opacity:.4;cursor:default}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:800px){.two-col{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>🧬 COMPASS — MIC &amp; Genomics Explorer</h1>
  <span id="hdr-stats"></span>
</header>
<nav>
  <button class="active" data-tab="overview">Overview</button>
  <button data-tab="mic-phage">MIC × Phage</button>
  <button data-tab="resistance">Resistance Profile</button>
  <button data-tab="correlations">Correlations</button>
  <button data-tab="mlst">MLST</button>
  <button data-tab="table">Data Table</button>
  <button data-tab="download">Download</button>
</nav>
<main>

<!-- OVERVIEW -->
<section id="overview" class="tab active">
  <div id="kpi-row" class="kpis"></div>
  <div class="two-col">
    <div class="card"><h3>Prophage burden distribution</h3><div id="phage-hist"></div></div>
    <div class="card"><h3>MDR status</h3><div id="mdr-pie"></div></div>
  </div>
  <div class="card">
    <h3>Shiga Toxin (stx) Status</h3>
    <div id="stx-kpis" class="kpis" style="margin-bottom:12px"></div>
    <div id="stx-bar"></div>
  </div>
</section>

<!-- MIC × PHAGE -->
<section id="mic-phage" class="tab">
  <div class="card">
    <div class="controls">
      <label>Antibiotic</label>
      <select id="drug-sel"></select>
      <label style="margin-left:16px">Color by</label>
      <select id="color-by">
        <option value="num_prophages">Total prophages</option>
        <option value="num_lytic">Lytic phages</option>
        <option value="num_lysogenic">Lysogenic phages</option>
      </select>
    </div>
    <div id="boxplot"></div>
    <div id="boxplot-stats" style="margin-top:10px;font-size:12px;color:var(--muted)"></div>
  </div>
</section>

<!-- RESISTANCE PROFILE -->
<section id="resistance" class="tab">
  <div class="card">
    <div class="controls">
      <label>Sort by</label>
      <select id="res-sort">
        <option value="pct_R">% Resistant</option>
        <option value="n_tested">N tested</option>
        <option value="drug">Drug name</option>
      </select>
      <label>Min tested</label>
      <input type="text" id="res-min" value="10" style="width:60px"/>
    </div>
    <div id="res-chart"></div>
  </div>
</section>

<!-- CORRELATIONS -->
<section id="correlations" class="tab">
  <div class="two-col">
    <div class="card">
      <h3>Prophages × AMR genes</h3>
      <div class="controls">
        <label>Color</label>
        <select id="sc1-color">
          <option value="mdr">MDR status</option>
          <option value="num_plasmids">Plasmid count</option>
        </select>
      </div>
      <div id="scatter1"></div>
    </div>
    <div class="card">
      <h3>Plasmids × Prophages</h3>
      <div id="scatter2"></div>
    </div>
  </div>
</section>

<!-- MLST -->
<section id="mlst" class="tab">
  <div class="card"><h3>Top sequence types</h3><div id="mlst-chart"></div></div>
</section>

<!-- DATA TABLE -->
<section id="table" class="tab">
  <div class="card">
    <div class="controls">
      <input type="text" id="tbl-search" placeholder="Search sample ID, ST, organism..." style="width:280px"/>
      <label>MDR</label>
      <select id="tbl-mdr"><option value="">All</option><option>Yes</option><option>No</option></select>
      <label>stx</label>
      <select id="tbl-stx"><option value="">All</option><option value="stx1">stx1</option><option value="stx2">stx2</option><option value="stx1+stx2">stx1+stx2</option><option value="negative">negative</option></select>
      <label>Min prophages</label>
      <input type="text" id="tbl-phage" value="0" style="width:50px"/>
    </div>
    <div class="scroll"><table id="main-table">
      <thead><tr>
        <th data-k="id">Sample</th>
        <th data-k="mlst_st">ST</th>
        <th data-k="num_prophages">Prophages</th>
        <th data-k="num_lytic">Lytic</th>
        <th data-k="num_lysogenic">Lysogenic</th>
        <th data-k="num_amr_genes">AMR genes</th>
        <th data-k="num_plasmids">Plasmids</th>
        <th data-k="mdr_status">MDR</th>
        <th data-k="assembly_quality">Quality</th>
        <th data-k="strain">Strain</th>
        <th data-k="stx_status">stx</th>
        <th data-k="stx_genes">stx genes</th>
      </tr></thead>
      <tbody id="tbl-body"></tbody>
    </table></div>
    <div class="pagination">
      <button id="pg-prev">◀</button>
      <span id="pg-info"></span>
      <button id="pg-next">▶</button>
    </div>
  </div>
</section>

<!-- DOWNLOAD -->
<section id="download" class="tab">
  <div class="card">
    <h3>Download merged dataset</h3>
    <p style="color:var(--muted);margin-bottom:16px">
      All COMPASS genomic features joined with NCBI MIC/SIR phenotypes.
      3,586 isolates × all columns.
    </p>
    <button onclick="downloadTSV()" style="background:var(--accent);color:#000;border:none;
      padding:10px 22px;border-radius:8px;font-weight:600;cursor:pointer;font-size:14px">
      ⬇ Download merged TSV
    </button>
  </div>
</section>

</main>
<script>
const D = __DATA__;

// ── tabs ──────────────────────────────────────────────────────────────────────
document.querySelectorAll('nav button').forEach(b => b.onclick = () => {
  document.querySelectorAll('nav button').forEach(x => x.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  document.getElementById(b.dataset.tab).classList.add('active');
  renders[b.dataset.tab] && renders[b.dataset.tab]();
});

// ── header stats ──────────────────────────────────────────────────────────────
document.getElementById('hdr-stats').textContent =
  `${D.stats.n_total.toLocaleString()} isolates · ${D.stats.n_antibiotics} antibiotics · ${D.stats.pct_mdr}% MDR`;

// ── KPIs ──────────────────────────────────────────────────────────────────────
const kpis = [
  {n: D.stats.n_total.toLocaleString(), l: 'Isolates'},
  {n: D.stats.pct_mdr+'%', l: 'MDR'},
  {n: D.stats.med_phage, l: 'Median prophages'},
  {n: D.stats.pct_with_phage+'%', l: 'Has ≥1 prophage'},
  {n: D.stats.med_amr, l: 'Median AMR genes'},
  {n: D.stats.n_antibiotics, l: 'Antibiotics tested'},
  {n: D.stx_summary.n_positive.toLocaleString(), l: 'stx-positive'},
];
document.getElementById('kpi-row').innerHTML = kpis.map(k =>
  `<div class="kpi"><div class="n">${k.n}</div><div class="l">${k.l}</div></div>`).join('');

// ── helpers ───────────────────────────────────────────────────────────────────
const pal = d3.schemeTableau10;
function downloadText(name, text) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], {type:'text/plain'}));
  a.download = name; a.click();
}

// ── phage histogram ───────────────────────────────────────────────────────────
function renderPhageHist() {
  const el = document.getElementById('phage-hist');
  el.innerHTML = '';
  const W = el.clientWidth||600, H = 220, m = {t:10,r:20,b:40,l:50};
  const svg = d3.select(el).append('svg').attr('width',W).attr('height',H);
  const x = d3.scaleBand().domain(D.phage_hist.map(d=>d.bin)).range([m.l,W-m.r]).padding(0.1);
  const y = d3.scaleLinear().domain([0, d3.max(D.phage_hist,d=>d.count)]).range([H-m.b,m.t]);
  svg.append('g').attr('class','axis').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).tickValues(x.domain().filter((_,i)=>i%2===0)));
  svg.append('g').attr('class','axis').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5));
  svg.selectAll('rect').data(D.phage_hist).join('rect')
    .attr('x',d=>x(d.bin)).attr('width',x.bandwidth())
    .attr('y',d=>y(d.count)).attr('height',d=>H-m.b-y(d.count))
    .attr('fill','var(--accent)').attr('opacity',.8)
    .append('title').text(d=>`${d.bin} prophages: ${d.count} isolates`);
  svg.append('text').attr('x',W/2).attr('y',H-4).attr('text-anchor','middle').attr('fill','var(--muted)').attr('font-size',11).text('Number of prophages');
}
renderPhageHist();

// ── MDR pie ───────────────────────────────────────────────────────────────────
function renderMdrPie() {
  const el = document.getElementById('mdr-pie'); el.innerHTML='';
  const n_mdr = D.stats.n_mdr, n_total = D.stats.n_total;
  const data = [{label:'MDR',val:n_mdr,color:'var(--danger)'},{label:'Non-MDR',val:n_total-n_mdr,color:'var(--ok)'}];
  const W=el.clientWidth||300, H=220, R=80;
  const svg=d3.select(el).append('svg').attr('width',W).attr('height',H);
  const g=svg.append('g').attr('transform',`translate(${W/2},${H/2})`);
  const pie=d3.pie().value(d=>d.val)(data);
  const arc=d3.arc().innerRadius(40).outerRadius(R);
  g.selectAll('path').data(pie).join('path').attr('d',arc).attr('fill',d=>d.data.color).attr('opacity',.85)
   .append('title').text(d=>`${d.data.label}: ${d.data.val} (${(100*d.data.val/n_total).toFixed(1)}%)`);
  g.selectAll('text').data(pie).join('text')
   .attr('transform',d=>`translate(${arc.centroid(d)})`)
   .attr('text-anchor','middle').attr('fill','#fff').attr('font-size',12).attr('font-weight',600)
   .text(d=>`${(100*d.data.val/n_total).toFixed(0)}%`);
  // legend
  const lg=svg.append('g').attr('transform',`translate(${W-100},${H/2-20})`);
  data.forEach((d,i)=>{
    lg.append('rect').attr('x',0).attr('y',i*22).attr('width',12).attr('height',12).attr('fill',d.color).attr('rx',2);
    lg.append('text').attr('x',16).attr('y',i*22+10).attr('fill','var(--muted)').attr('font-size',12).text(`${d.label} (${d.val.toLocaleString()})`);
  });
}
renderMdrPie();

// ── stx card ──────────────────────────────────────────────────────────────────
function renderStxCard() {
  const stx = D.stx_summary;
  const n_total = D.stats.n_total;
  const kpiData = [
    {n: stx.n_positive, l: 'stx-positive', color: 'var(--danger)'},
    {n: stx.stx1, l: 'stx1 only', color: '#f59e0b'},
    {n: stx['stx1+stx2'], l: 'stx1 + stx2', color: '#a855f7'},
    {n: stx.stx2, l: 'stx2 only', color: 'var(--danger)'},
  ];
  document.getElementById('stx-kpis').innerHTML = kpiData.map(k =>
    `<div class="kpi"><div class="n" style="color:${k.color}">${k.n}</div><div class="l">${k.l}</div></div>`
  ).join('');
  const segs = [
    {k: 'stx1', color: '#f59e0b', label: 'stx1 only'},
    {k: 'stx1+stx2', color: '#a855f7', label: 'stx1+stx2'},
    {k: 'stx2', color: '#ef4444', label: 'stx2 only'},
    {k: 'negative', color: '#1e2a38', label: 'negative'},
  ];
  const bars = segs.map(seg => {
    const pct = (100 * stx[seg.k] / n_total).toFixed(1);
    return `<div style="width:${pct}%;min-width:${stx[seg.k]?'2px':'0'};height:28px;background:${seg.color};display:inline-block;vertical-align:top" title="${seg.label}: ${stx[seg.k]} (${pct}%)"></div>`;
  }).join('');
  const legend = segs.filter(s => stx[s.k] > 0).map(s =>
    `<span style="margin-right:14px;color:${s.color}">■ ${s.label}: ${stx[s.k]}</span>`
  ).join('');
  document.getElementById('stx-bar').innerHTML =
    `<div style="display:flex;border-radius:4px;overflow:hidden;margin-bottom:8px">${bars}</div>
     <div style="font-size:11px;color:var(--muted)">${legend}</div>`;
}
renderStxCard();

// ── boxplot ───────────────────────────────────────────────────────────────────
const drugSel = document.getElementById('drug-sel');
D.sir_cols.forEach(d => drugSel.add(new Option(d,d)));
// default to ciprofloxacin if available
const cipIdx = D.sir_cols.indexOf('ciprofloxacin');
if(cipIdx>=0) drugSel.selectedIndex = cipIdx;

function boxStats(arr) {
  if(!arr||!arr.length) return null;
  const s=arr.slice().sort((a,b)=>a-b), n=s.length;
  const q=p=>{ const i=(p/100)*(n-1), lo=Math.floor(i), hi=Math.ceil(i); return s[lo]+(i-lo)*(s[hi]-s[lo]); };
  return {min:s[0],q1:q(25),med:q(50),q3:q(75),max:s[n-1],n,mean:arr.reduce((a,b)=>a+b,0)/n};
}

function renderBoxplot() {
  const drug = drugSel.value;
  const colorBy = document.getElementById('color-by').value;
  const bd = D.boxplot_data[drug];
  const el=document.getElementById('boxplot'); el.innerHTML='';
  if(!bd){el.innerHTML='<div class="empty">No data</div>';return;}

  // rebuild arrays using colorBy field from full records
  const groups = {S:[], I:[], R:[]};
  D.records.forEach(r => {
    const sir = r['sir_'+drug];
    if(sir in groups) groups[sir].push(r[colorBy]||0);
  });

  const cats=['S','I','R'];
  const colors={'S':'var(--S)','I':'var(--I)','R':'var(--R)'};
  const W=el.clientWidth||700, H=320, m={t:20,r:20,b:60,l:50};
  const svg=d3.select(el).append('svg').attr('width',W).attr('height',H);

  const allVals=[].concat(...Object.values(groups));
  const maxV=d3.max(allVals)||1;
  const y=d3.scaleLinear().domain([0,maxV*1.05]).range([H-m.b,m.t]);
  const x=d3.scaleBand().domain(cats).range([m.l,W-m.r]).padding(.4);
  const bw=x.bandwidth();

  svg.append('g').attr('class','axis').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).tickFormat(d=>({S:'Susceptible',I:'Intermediate',R:'Resistant'}[d])));
  svg.append('g').attr('class','axis').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6));
  svg.append('text').attr('x',-H/2).attr('y',12).attr('transform','rotate(-90)').attr('text-anchor','middle').attr('fill','var(--muted)').attr('font-size',11).text(colorBy.replace(/_/g,' '));

  cats.forEach(cat=>{
    const arr=groups[cat]; if(!arr.length) return;
    const st=boxStats(arr), xc=x(cat)+bw/2, col=colors[cat];
    // jitter points
    const pts=arr.slice(0,200);
    svg.selectAll(`.pt-${cat}`).data(pts).join('circle').attr('class',`pt-${cat}`)
      .attr('cx',d=>xc+(Math.random()-.5)*bw*.7).attr('cy',d=>y(d))
      .attr('r',2.5).attr('fill',col).attr('opacity',.35);
    // box
    svg.append('rect').attr('x',x(cat)).attr('y',y(st.q3)).attr('width',bw)
      .attr('height',y(st.q1)-y(st.q3)).attr('fill',col).attr('fill-opacity',.2)
      .attr('stroke',col).attr('stroke-width',1.5).attr('rx',3);
    // median line
    svg.append('line').attr('x1',x(cat)).attr('x2',x(cat)+bw).attr('y1',y(st.med)).attr('y2',y(st.med))
      .attr('stroke',col).attr('stroke-width',2.5);
    // whiskers
    [[st.min,st.q1],[st.q3,st.max]].forEach(([lo,hi])=>{
      svg.append('line').attr('x1',xc).attr('x2',xc).attr('y1',y(lo)).attr('y2',y(hi))
        .attr('stroke',col).attr('stroke-dasharray','4,2').attr('stroke-width',1);
    });
    // n label
    svg.append('text').attr('x',xc).attr('y',H-m.b+24).attr('text-anchor','middle')
      .attr('fill','var(--muted)').attr('font-size',11).text(`n=${st.n}`);
    // median label
    svg.append('text').attr('x',xc).attr('y',y(st.med)-5).attr('text-anchor','middle')
      .attr('fill',col).attr('font-size',11).attr('font-weight',600).text(st.med.toFixed(1));
  });

  // stats summary
  const s=cats.map(c=>{const st=boxStats(groups[c]);return st?`${({S:'Susceptible',I:'Intermediate',R:'Resistant'}[c])}: n=${st.n}, median=${st.med.toFixed(1)}, mean=${st.mean.toFixed(1)}`:''}).filter(Boolean);
  document.getElementById('boxplot-stats').textContent=s.join('  |  ');
}
drugSel.onchange=renderBoxplot;
document.getElementById('color-by').onchange=renderBoxplot;
const renders={'mic-phage':renderBoxplot};

// ── resistance profile ────────────────────────────────────────────────────────
function renderResistance() {
  const el=document.getElementById('res-chart'); el.innerHTML='';
  const sortBy=document.getElementById('res-sort').value;
  const minN=parseInt(document.getElementById('res-min').value)||0;
  let data=D.res_summary.filter(d=>d.n_tested>=minN);
  if(sortBy==='pct_R') data.sort((a,b)=>b.pct_R-a.pct_R);
  else if(sortBy==='n_tested') data.sort((a,b)=>b.n_tested-a.n_tested);
  else data.sort((a,b)=>a.drug.localeCompare(b.drug));
  const H=Math.max(400, data.length*18), W=el.clientWidth||800, m={t:10,r:120,b:30,l:200};
  const svg=d3.select(el).append('svg').attr('width',W).attr('height',H);
  const y=d3.scaleBand().domain(data.map(d=>d.drug)).range([m.t,H-m.b]).padding(.2);
  const x=d3.scaleLinear().domain([0,100]).range([m.l,W-m.r]);
  svg.append('g').attr('class','axis').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(5).tickFormat(d=>d+'%'));
  svg.append('g').attr('class','axis').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y));
  data.forEach(d=>{
    const yp=y(d.drug), bh=y.bandwidth();
    let cx=m.l;
    [['n_S','#052e16','var(--S)'],['n_I','#422006','var(--I)'],['n_R','#450a0a','var(--R)']].forEach(([k,bg,col])=>{
      const w=x(100*d[k]/d.n_tested)-x(0);
      svg.append('rect').attr('x',cx).attr('y',yp).attr('width',w).attr('height',bh)
        .attr('fill',bg).append('title').text(`${k.slice(2)}: ${d[k]} (${(100*d[k]/d.n_tested).toFixed(1)}%)`);
      svg.append('text').attr('x',cx+w/2).attr('y',yp+bh/2+4).attr('text-anchor','middle')
        .attr('fill',col).attr('font-size',9).attr('font-weight',600)
        .text(d[k]>0?d[k]:'');
      cx+=w;
    });
    svg.append('text').attr('x',cx+6).attr('y',yp+bh/2+4).attr('fill','var(--muted)').attr('font-size',10)
      .text(`${d.pct_R}% R (n=${d.n_tested})`);
  });
}
document.getElementById('res-sort').onchange=renderResistance;
document.getElementById('res-min').oninput=renderResistance;
renders['resistance']=renderResistance;

// ── scatter 1: prophages × AMR ────────────────────────────────────────────────
function renderScatter1() {
  const el=document.getElementById('scatter1'); el.innerHTML='';
  const colorBy=document.getElementById('sc1-color').value;
  const W=el.clientWidth||400, H=280, m={t:10,r:20,b:40,l:45};
  const svg=d3.select(el).append('svg').attr('width',W).attr('height',H);
  const data=D.scatter.slice(0,1000); // cap for perf
  const x=d3.scaleLinear().domain([0,d3.max(data,d=>d.x)||1]).range([m.l,W-m.r]);
  const y=d3.scaleLinear().domain([0,d3.max(data,d=>d.y)||1]).range([H-m.b,m.t]);
  svg.append('g').attr('class','axis').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(5));
  svg.append('g').attr('class','axis').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5));
  svg.append('text').attr('x',W/2).attr('y',H-4).attr('text-anchor','middle').attr('fill','var(--muted)').attr('font-size',11).text('AMR genes');
  svg.append('text').attr('x',-H/2).attr('y',10).attr('transform','rotate(-90)').attr('text-anchor','middle').attr('fill','var(--muted)').attr('font-size',11).text('Prophages');
  const colorFn = colorBy==='mdr'
    ? d=>d.mdr==='Yes'?'var(--danger)':'var(--ok)'
    : d=>d3.interpolateBlues(Math.min(1,(d.num_plasmids||0)/10));
  svg.selectAll('circle').data(data).join('circle')
    .attr('cx',d=>x(d.x)).attr('cy',d=>y(d.y)).attr('r',3)
    .attr('fill',d=>colorBy==='mdr'?(d.mdr==='Yes'?'var(--danger)':'var(--ok)'):'var(--accent)')
    .attr('opacity',.5)
    .append('title').text(d=>`${d.id}\nAMR: ${d.x}, Phage: ${d.y}, MDR: ${d.mdr}`);
}
document.getElementById('sc1-color').onchange=renderScatter1;

function renderScatter2() {
  const el=document.getElementById('scatter2'); el.innerHTML='';
  const W=el.clientWidth||400, H=280, m={t:10,r:20,b:40,l:45};
  const svg=d3.select(el).append('svg').attr('width',W).attr('height',H);
  const data=D.scatter2.slice(0,1000);
  const x=d3.scaleLinear().domain([0,d3.max(data,d=>d.x)||1]).range([m.l,W-m.r]);
  const y=d3.scaleLinear().domain([0,d3.max(data,d=>d.y)||1]).range([H-m.b,m.t]);
  svg.append('g').attr('class','axis').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(5));
  svg.append('g').attr('class','axis').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5));
  svg.append('text').attr('x',W/2).attr('y',H-4).attr('text-anchor','middle').attr('fill','var(--muted)').attr('font-size',11).text('Plasmids');
  svg.append('text').attr('x',-H/2).attr('y',10).attr('transform','rotate(-90)').attr('text-anchor','middle').attr('fill','var(--muted)').attr('font-size',11).text('Prophages');
  svg.selectAll('circle').data(data).join('circle')
    .attr('cx',d=>x(d.x)).attr('cy',d=>y(d.y)).attr('r',3)
    .attr('fill',d=>d.mdr==='Yes'?'var(--danger)':'var(--accent)').attr('opacity',.5)
    .append('title').text(d=>`${d.id}\nPlasmids: ${d.x}, Phage: ${d.y}, MDR: ${d.mdr}`);
}
renders['correlations']=()=>{renderScatter1();renderScatter2();};

// ── MLST ──────────────────────────────────────────────────────────────────────
function renderMlst() {
  const el=document.getElementById('mlst-chart'); el.innerHTML='';
  const data=D.mlst_summary;
  const W=el.clientWidth||700, H=Math.max(300,data.length*28), m={t:10,r:180,b:30,l:80};
  const svg=d3.select(el).append('svg').attr('width',W).attr('height',H);
  const y=d3.scaleBand().domain(data.map(d=>d.st==='Unknown'?'Unknown':('ST'+d.st))).range([m.t,H-m.b]).padding(.25);
  const x=d3.scaleLinear().domain([0,d3.max(data,d=>d.n)]).range([m.l,W-m.r]);
  svg.append('g').attr('class','axis').attr('transform',`translate(0,${H-m.b})`).call(d3.axisBottom(x).ticks(5));
  svg.append('g').attr('class','axis').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y));
  data.forEach(d=>{
    const lab=d.st==='Unknown'?'Unknown':('ST'+d.st);
    const yp=y(lab), bh=y.bandwidth();
    // main bar
    svg.append('rect').attr('x',m.l).attr('y',yp).attr('width',x(d.n)-m.l).attr('height',bh)
      .attr('fill','var(--accent)').attr('opacity',.7)
      .append('title').text(`ST${d.st}: n=${d.n}, ${d.pct_mdr}% MDR, median ${d.med_phage} phages`);
    // MDR overlay
    svg.append('rect').attr('x',m.l).attr('y',yp).attr('width',x(d.n*d.pct_mdr/100)-m.l).attr('height',bh)
      .attr('fill','var(--danger)').attr('opacity',.5);
    svg.append('text').attr('x',x(d.n)+6).attr('y',yp+bh/2+4).attr('fill','var(--muted)').attr('font-size',10)
      .text(`n=${d.n} | ${d.pct_mdr}% MDR | med phage=${d.med_phage}`);
  });
}
renders['mlst']=renderMlst;

// ── data table ────────────────────────────────────────────────────────────────
let tblSort={k:'num_prophages',dir:-1}, tblPage=0, tblPageSize=50, tblFiltered=[];

function filterTable() {
  const q=(document.getElementById('tbl-search').value||'').toLowerCase();
  const mdr=document.getElementById('tbl-mdr').value;
  const stxF=document.getElementById('tbl-stx').value;
  const minP=parseInt(document.getElementById('tbl-phage').value)||0;
  tblFiltered=D.table_rows.filter(r=>{
    if(q&&!Object.values(r).some(v=>String(v).toLowerCase().includes(q))) return false;
    if(mdr&&r.mdr_status!==mdr) return false;
    if(stxF&&r.stx_status!==stxF) return false;
    if((r.num_prophages||0)<minP) return false;
    return true;
  });
  tblFiltered.sort((a,b)=>tblSort.dir*(String(b[tblSort.k]||'').localeCompare(String(a[tblSort.k]||''),undefined,{numeric:true})));
  tblPage=0; renderTablePage();
}

function renderTablePage() {
  const start=tblPage*tblPageSize, end=start+tblPageSize;
  const page=tblFiltered.slice(start,end);
  const badge=(v,cls)=>v?`<span class="badge ${cls}">${v}</span>`:'-';
  const stxCls={'stx1':'stx-pos1','stx2':'stx-pos2','stx1+stx2':'stx-both','negative':'stx-neg'};
  const stxBadge=s=>s?`<span class="stx-chip ${stxCls[s]||''}">${s}</span>`:'-';
  document.getElementById('tbl-body').innerHTML=page.map(r=>`<tr>
    <td><b>${r.id}</b></td><td>${r.mlst_st||'-'}</td>
    <td>${r.num_prophages??'-'}</td><td>${r.num_lytic??'-'}</td><td>${r.num_lysogenic??'-'}</td>
    <td>${r.num_amr_genes??'-'}</td><td>${r.num_plasmids??'-'}</td>
    <td>${badge(r.mdr_status,r.mdr_status)}</td>
    <td>${r.assembly_quality||'-'}</td><td>${r.strain||'-'}</td>
    <td>${stxBadge(r.stx_status)}</td><td style="color:var(--muted);font-size:11px">${r.stx_genes||'-'}</td>
  </tr>`).join('');
  document.getElementById('pg-info').textContent=
    `${start+1}–${Math.min(end,tblFiltered.length)} of ${tblFiltered.length}`;
  document.getElementById('pg-prev').disabled=tblPage===0;
  document.getElementById('pg-next').disabled=end>=tblFiltered.length;
}

document.getElementById('tbl-search').oninput=filterTable;
document.getElementById('tbl-mdr').onchange=filterTable;
document.getElementById('tbl-stx').onchange=filterTable;
document.getElementById('tbl-phage').oninput=filterTable;
document.getElementById('pg-prev').onclick=()=>{tblPage--;renderTablePage();};
document.getElementById('pg-next').onclick=()=>{tblPage++;renderTablePage();};
document.querySelectorAll('#main-table th[data-k]').forEach(th=>{
  th.onclick=()=>{
    if(tblSort.k===th.dataset.k) tblSort.dir*=-1; else{tblSort.k=th.dataset.k;tblSort.dir=-1;}
    filterTable();
  };
});
renders['table']=filterTable;

// ── download TSV ──────────────────────────────────────────────────────────────
function downloadTSV() {
  const cols = Object.keys(D.records[0]);
  const tsv = [cols.join('\t'), ...D.records.map(r=>cols.map(c=>r[c]??'').join('\t'))].join('\n');
  downloadText('compass_mic_merged.tsv', tsv);
}
</script>
</body>
</html>
"""

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    compass = load_compass(COMPASS_TSV)
    mic, sir_cols = load_mic(MIC_CSV)
    records = merge(compass, mic, sir_cols)
    res_sum = resistance_summary(records, sir_cols)
    mlst_sum = mlst_summary(records)
    build_html(records, sir_cols, res_sum, mlst_sum, OUT_HTML)

if __name__ == '__main__':
    main()
