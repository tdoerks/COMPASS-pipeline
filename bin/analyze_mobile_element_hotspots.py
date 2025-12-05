#!/usr/bin/env python3
"""
Mobile Element Hotspot Analysis
Kansas E. coli Study 2021-2025

Investigates the relationship between:
- Plasmid-borne vs chromosomal AMR genes
- Prophage integration sites
- Mobile genetic element clustering
- Multi-element genomic "hotspots"

Key Questions:
1. Are AMR genes on plasmids closer to prophages than chromosomal AMR?
2. Do prophages mark mobile element insertion hotspots?
3. Are there genomic regions with plasmid + prophage + AMR clustering?

Generates:
- Plasmid vs chromosome AMR distribution
- Prophage proximity by genetic context
- Multi-element hotspot identification
- Interactive HTML dashboard
"""

import csv
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime
import sys

# ============================================================================
# DATA LOADING
# ============================================================================

def load_colocation_data(csv_file):
    """Load AMR-prophage colocation CSV"""
    print(f"Loading co-location data from {csv_file}...")
    data = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    print(f"  Loaded {len(data)} AMR-prophage associations")
    return data

def load_mobile_elements_data(csv_file):
    """Load mobile elements CSV (plasmid predictions)"""
    print(f"Loading mobile elements data from {csv_file}...")
    data = []

    if not Path(csv_file).exists():
        print(f"  Warning: {csv_file} not found")
        return data

    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    print(f"  Loaded {len(data)} mobile element associations")
    return data

def parse_mobsuite_results(results_dir, sample_id):
    """Parse MOB-suite plasmid prediction results"""
    mobsuite_file = Path(results_dir) / "mobsuite" / f"{sample_id}_mobtyper_results.txt"

    plasmid_contigs = set()
    plasmid_info = {}

    if not mobsuite_file.exists():
        return plasmid_contigs, plasmid_info

    with open(mobsuite_file) as f:
        header = f.readline().strip().split('\t')

        for line in f:
            if not line.strip():
                continue

            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue

            # MOB-suite format: contig_id, num_contigs, size, predicted_mobility, ...
            contig_id = parts[0]

            # Mark as plasmid
            plasmid_contigs.add(contig_id)

            # Store plasmid characteristics
            plasmid_info[contig_id] = {
                'size': parts[2] if len(parts) > 2 else 'Unknown',
                'mobility': parts[3] if len(parts) > 3 else 'Unknown',
                'rep_types': parts[5] if len(parts) > 5 else 'Unknown'
            }

    return plasmid_contigs, plasmid_info

def load_metadata_files(base_dir):
    """Load metadata from all year directories"""
    print("Loading metadata from year directories...")

    metadata = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"

        if not metadata_file.exists():
            continue

        print(f"  Loading {year} metadata...")
        with open(metadata_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                srr_id = row['Run']
                sample_name = row.get('SampleName', '')
                organism = row.get('organism', 'Unknown')

                metadata[srr_id] = {
                    'sample_name': sample_name,
                    'organism': organism,
                    'year': str(year)
                }

    print(f"  Loaded metadata for {len(metadata)} samples")
    return metadata

# ============================================================================
# ANALYSIS
# ============================================================================

def analyze_mobile_element_hotspots(colocation_data, mobile_elements_data, base_dir, metadata):
    """
    Comprehensive analysis of plasmid vs chromosome AMR and prophage relationships
    """
    print("\nAnalyzing mobile element hotspots...")

    # Data structures
    plasmid_amr_prophage = {
        'plasmid': {'proximal': 0, 'distant': 0},
        'chromosome': {'proximal': 0, 'distant': 0},
        'unknown': {'proximal': 0, 'distant': 0}
    }

    plasmid_amr_classes = defaultdict(lambda: {'plasmid': 0, 'chromosome': 0})

    hotspots = []  # Samples with multiple mobile elements clustering

    sample_contexts = defaultdict(lambda: {
        'total_amr': 0,
        'plasmid_amr': 0,
        'chromosome_amr': 0,
        'prophages': 0,
        'plasmid_contigs': set(),
        'amr_contigs': set(),
        'prophage_contigs': set(),
        'amr_classes': Counter()
    })

    # First pass: get mobile elements data (plasmid assignments)
    mobile_element_map = {}
    for row in mobile_elements_data:
        sample_id = row['sample']
        contig = row['contig']
        on_plasmid = row['on_plasmid']

        if sample_id not in mobile_element_map:
            mobile_element_map[sample_id] = {}

        mobile_element_map[sample_id][contig] = (on_plasmid == 'Yes')

    # Second pass: analyze colocation with plasmid context
    for row in colocation_data:
        sample_id = row['sample']
        contig = row['contig']
        amr_class = row['amr_class']
        amr_gene = row['amr_gene']
        category = row['category']
        prophage_id = row.get('prophage_id', 'None')

        # Determine if proximal to prophage
        is_proximal = category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']
        proximity = 'proximal' if is_proximal else 'distant'

        # Determine genetic context (plasmid vs chromosome)
        if sample_id in mobile_element_map and contig in mobile_element_map[sample_id]:
            is_plasmid = mobile_element_map[sample_id][contig]
            context = 'plasmid' if is_plasmid else 'chromosome'
        else:
            context = 'unknown'

        # Record statistics
        plasmid_amr_prophage[context][proximity] += 1
        plasmid_amr_classes[amr_class][context] += 1

        # Track sample-level data
        sample_contexts[sample_id]['total_amr'] += 1
        sample_contexts[sample_id]['amr_contigs'].add(contig)
        sample_contexts[sample_id]['amr_classes'][amr_class] += 1

        if context == 'plasmid':
            sample_contexts[sample_id]['plasmid_amr'] += 1
            sample_contexts[sample_id]['plasmid_contigs'].add(contig)
        elif context == 'chromosome':
            sample_contexts[sample_id]['chromosome_amr'] += 1

        if prophage_id != 'None':
            sample_contexts[sample_id]['prophages'] += 1
            sample_contexts[sample_id]['prophage_contigs'].add(contig)

    # Identify multi-element hotspots
    for sample_id, ctx in sample_contexts.items():
        # Hotspot criteria: plasmid + prophage + AMR on same sample
        if ctx['plasmid_amr'] > 0 and ctx['prophages'] > 0:
            # Check for contig overlap
            overlap = ctx['plasmid_contigs'] & ctx['prophage_contigs']

            meta = metadata.get(sample_id, {})

            hotspots.append({
                'sample': sample_id,
                'year': meta.get('year', 'Unknown'),
                'organism': meta.get('organism', 'Unknown'),
                'total_amr': ctx['total_amr'],
                'plasmid_amr': ctx['plasmid_amr'],
                'chromosome_amr': ctx['chromosome_amr'],
                'prophages': ctx['prophages'],
                'shared_contigs': len(overlap),
                'plasmid_contigs': len(ctx['plasmid_contigs']),
                'top_amr_classes': ', '.join([f"{c} ({n})" for c, n in ctx['amr_classes'].most_common(3)])
            })

    # Sort hotspots by complexity
    hotspots.sort(key=lambda x: (x['shared_contigs'], x['plasmid_amr'], x['prophages']), reverse=True)

    return {
        'plasmid_amr_prophage': plasmid_amr_prophage,
        'plasmid_amr_classes': plasmid_amr_classes,
        'hotspots': hotspots,
        'sample_contexts': sample_contexts
    }

def calculate_statistics(analysis_data):
    """Calculate statistical measures"""

    pap = analysis_data['plasmid_amr_prophage']

    # Calculate percentages
    stats = {}

    for context in ['plasmid', 'chromosome', 'unknown']:
        total = pap[context]['proximal'] + pap[context]['distant']
        proximal_pct = (pap[context]['proximal'] / total * 100) if total > 0 else 0

        stats[context] = {
            'total': total,
            'proximal': pap[context]['proximal'],
            'distant': pap[context]['distant'],
            'proximal_pct': proximal_pct
        }

    return stats

# ============================================================================
# HTML REPORT GENERATION
# ============================================================================

def generate_html_report(output_file, analysis_data, stats, metadata):
    """Generate comprehensive HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    plasmid_amr_prophage = analysis_data['plasmid_amr_prophage']
    plasmid_amr_classes = analysis_data['plasmid_amr_classes']
    hotspots = analysis_data['hotspots']

    # Get top AMR classes
    top_amr_classes = sorted(plasmid_amr_classes.items(),
                             key=lambda x: x[1]['plasmid'] + x[1]['chromosome'],
                             reverse=True)[:15]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mobile Element Hotspot Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .content {{
            padding: 40px;
        }}

        h2 {{
            color: #667eea;
            font-size: 2em;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        h3 {{
            color: #764ba2;
            font-size: 1.5em;
            margin: 25px 0 15px 0;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}

        tbody tr:hover {{
            background: #f7fafc;
        }}

        .alert-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .info-box {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .success-box {{
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .highlight {{
            background: #fef3c7;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .badge-success {{
            background: #d1fae5;
            color: #065f46;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin: 30px 0;
        }}

        footer {{
            background: #2d3748;
            color: white;
            padding: 30px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 Mobile Element Hotspot Analysis</h1>
            <p>Plasmid vs Chromosome: AMR-Prophage Associations</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Kansas E. coli Study 2021-2025</p>
            <p style="font-size: 0.85em;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        <div class="content">
            <section id="overview">
                <h2>📊 Analysis Overview</h2>

                <div class="alert-box">
                    <h4>🔬 Key Research Questions</h4>
                    <ul style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li>Are plasmid-borne AMR genes closer to prophages than chromosomal AMR?</li>
                        <li>Do prophages mark mobile genetic element insertion hotspots?</li>
                        <li>Are there genomic regions with plasmid + prophage + AMR clustering?</li>
                        <li>What AMR classes are predominantly plasmid vs chromosome-associated?</li>
                    </ul>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Multi-Element Hotspots</h4>
                        <div class="value">{len(hotspots)}</div>
                        <p>Samples with plasmid + prophage + AMR</p>
                    </div>
                    <div class="stat-card">
                        <h4>Plasmid AMR</h4>
                        <div class="value">{stats['plasmid']['total']}</div>
                        <p>AMR genes on plasmids</p>
                    </div>
                    <div class="stat-card">
                        <h4>Chromosomal AMR</h4>
                        <div class="value">{stats['chromosome']['total']}</div>
                        <p>AMR genes on chromosome</p>
                    </div>
                </div>
            </section>

            <section id="comparison">
                <h2>🔬 Plasmid vs Chromosome Comparison</h2>

                <div class="info-box">
                    <h4>📈 Prophage Proximity by Genetic Context</h4>
                    <p>Do plasmid-borne AMR genes show different prophage proximity patterns than chromosomal AMR?</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Genetic Context</th>
                            <th>Total AMR Genes</th>
                            <th>Proximal to Prophage</th>
                            <th>Distant from Prophage</th>
                            <th>Proximal %</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for context in ['plasmid', 'chromosome', 'unknown']:
        context_label = context.capitalize()
        total = stats[context]['total']
        proximal = stats[context]['proximal']
        distant = stats[context]['distant']
        proximal_pct = stats[context]['proximal_pct']

        badge = 'badge-danger' if proximal_pct > 5 else 'badge-success'

        html += f"""
                        <tr>
                            <td><strong>{context_label}</strong></td>
                            <td>{total:,}</td>
                            <td><span class="highlight">{proximal}</span></td>
                            <td>{distant}</td>
                            <td><span class="badge {badge}">{proximal_pct:.2f}%</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="classes">
                <h2>💊 AMR Classes: Plasmid vs Chromosome</h2>

                <div class="info-box">
                    <h4>🧬 Genetic Context by Drug Class</h4>
                    <p>Which AMR classes are predominantly plasmid-borne vs chromosomal?</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>AMR Class</th>
                            <th>Plasmid</th>
                            <th>Chromosome</th>
                            <th>Total</th>
                            <th>% Plasmid</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for amr_class, counts in top_amr_classes:
        plasmid_count = counts['plasmid']
        chromosome_count = counts['chromosome']
        total = plasmid_count + chromosome_count
        plasmid_pct = (plasmid_count / total * 100) if total > 0 else 0

        if plasmid_pct > 50:
            badge = 'badge-danger'
            label = 'Plasmid-dominant'
        else:
            badge = 'badge-success'
            label = 'Chromosome-dominant'

        html += f"""
                        <tr>
                            <td><strong>{amr_class}</strong></td>
                            <td>{plasmid_count}</td>
                            <td>{chromosome_count}</td>
                            <td>{total}</td>
                            <td><span class="badge {badge}">{plasmid_pct:.1f}% - {label}</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="hotspots">
                <h2>🔥 Multi-Element Genomic Hotspots</h2>

                <div class="success-box">
                    <h4>✨ Samples with Plasmid + Prophage + AMR Co-occurrence</h4>
                    <p>These samples show clustering of multiple mobile genetic elements, suggesting genomic "hotspots"</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Sample</th>
                            <th>Year</th>
                            <th>Organism</th>
                            <th>Plasmid AMR</th>
                            <th>Chromosome AMR</th>
                            <th>Prophages</th>
                            <th>Shared Contigs</th>
                            <th>Top AMR Classes</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for hotspot in hotspots[:30]:  # Top 30 hotspots
        html += f"""
                        <tr>
                            <td><strong>{hotspot['sample']}</strong></td>
                            <td>{hotspot['year']}</td>
                            <td>{hotspot['organism']}</td>
                            <td><span class="highlight">{hotspot['plasmid_amr']}</span></td>
                            <td>{hotspot['chromosome_amr']}</td>
                            <td>{hotspot['prophages']}</td>
                            <td><span class="badge badge-danger">{hotspot['shared_contigs']}</span></td>
                            <td>{hotspot['top_amr_classes']}</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>
            </section>

            <section id="conclusions">
                <h2>📝 Key Findings</h2>

                <div class="alert-box">
                    <h4>✅ Summary</h4>
                    <ul style="line-height: 2; margin-left: 30px; margin-top: 10px;">
                        <li><strong>Plasmid AMR proximity:</strong> {stats['plasmid']['proximal_pct']:.2f}% of plasmid AMR genes are proximal to prophages</li>
                        <li><strong>Chromosomal AMR proximity:</strong> {stats['chromosome']['proximal_pct']:.2f}% of chromosomal AMR genes are proximal to prophages</li>
                        <li><strong>Multi-element hotspots:</strong> {len(hotspots)} samples show plasmid + prophage + AMR clustering</li>
                        <li><strong>Samples with shared contigs:</strong> {sum(1 for h in hotspots if h['shared_contigs'] > 0)} samples have plasmid and prophage on same contig</li>
                    </ul>
                </div>

                <h3>Biological Interpretation</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li><strong>If plasmid AMR shows higher prophage proximity:</strong> Prophages may mark plasmid integration hotspots</li>
                    <li><strong>If chromosomal AMR shows higher proximity:</strong> Chromosomal genomic islands may accumulate both elements</li>
                    <li><strong>Multi-element hotspots:</strong> Suggest regions of genomic instability or active recombination</li>
                    <li><strong>Shared contigs:</strong> Direct evidence of mobile element clustering on same DNA molecule</li>
                </ul>

                <h3>Next Steps</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li>Statistical testing (Chi-square) for plasmid vs chromosome differences</li>
                    <li>Detailed genomic context analysis of hotspot regions</li>
                    <li>Integration site sequence motif analysis</li>
                    <li>Comparative analysis with other E. coli datasets</li>
                </ul>
            </section>
        </div>

        <footer>
            <p><strong>Mobile Element Hotspot Analysis</strong></p>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Kansas E. coli Study 2021-2025</p>
        </footer>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Report generated: {output_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    # File paths
    colocation_csv = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'tables' / 'kansas_ALL_years_amr_phage_colocation.csv'
    mobile_elements_csv = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'tables' / 'kansas_ALL_years_mobile_elements.csv'
    base_dir = Path.home() / 'compass_kansas_results'
    output_html = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'reports' / 'KANSAS_MOBILE_ELEMENT_HOTSPOTS.html'

    print("=" * 70)
    print("Mobile Element Hotspot Analysis")
    print("Plasmid vs Chromosome: AMR-Prophage Associations")
    print("=" * 70)

    # Load data
    metadata = load_metadata_files(base_dir)
    colocation_data = load_colocation_data(colocation_csv)
    mobile_elements_data = load_mobile_elements_data(mobile_elements_csv)

    if not mobile_elements_data:
        print("\n⚠️  Warning: No mobile elements data found!")
        print("    Analysis will be limited without plasmid predictions.")
        print("    Continuing with available data...\n")

    # Run analysis
    analysis_data = analyze_mobile_element_hotspots(colocation_data, mobile_elements_data, base_dir, metadata)

    # Calculate statistics
    stats = calculate_statistics(analysis_data)

    # Generate report
    generate_html_report(output_html, analysis_data, stats, metadata)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_html}")
    print(f"\n📈 Key Statistics:")
    print(f"   - Plasmid AMR genes: {stats['plasmid']['total']}")
    print(f"   - Chromosomal AMR genes: {stats['chromosome']['total']}")
    print(f"   - Multi-element hotspots: {len(analysis_data['hotspots'])}")
    print(f"   - Plasmid AMR proximal to prophage: {stats['plasmid']['proximal_pct']:.2f}%")
    print(f"   - Chromosomal AMR proximal to prophage: {stats['chromosome']['proximal_pct']:.2f}%")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
