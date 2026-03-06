#!/usr/bin/env python3
"""
MLST Strain-Level AMR-Prophage Analysis
Kansas E. coli Study 2021-2025

Investigates whether specific E. coli sequence types (STs) are
associated with AMR-prophage patterns.

Key Questions:
1. Which sequence types carry the most AMR genes?
2. Do certain STs show higher prophage proximity rates?
3. Are there high-risk clonal lineages?
4. How do STs spread temporally and across food sources?
5. Are pandemic clones (ST131, ST10, etc.) present?

Generates:
- ST-specific AMR profiles
- ST-prophage association rates
- Temporal ST distribution
- Food source-ST associations
- High-risk clone identification
- Interactive HTML dashboard
"""

import csv
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

def extract_food_source_from_sample_name(sample_name):
    """Extract food source from NARMS sample naming convention"""
    if not sample_name:
        return 'Unknown'

    matches = re.findall(r'\d([A-Z]{2})\d', sample_name)
    if len(matches) >= 2:
        product_code = matches[1]

        source_map = {
            'GB': 'Ground Beef',
            'CB': 'Chicken/Poultry',
            'GT': 'Ground Turkey',
            'PC': 'Pork Products',
            'CL': 'Chicken Liver',
            'CG': 'Chicken Gizzards',
            'CH': 'Chicken Hearts',
            'TK': 'Turkey',
            'BF': 'Beef',
        }

        return source_map.get(product_code, f'Other ({product_code})')

    return 'Unknown'

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

                food_source = extract_food_source_from_sample_name(sample_name)

                metadata[srr_id] = {
                    'sample_name': sample_name,
                    'food_source': food_source,
                    'organism': organism,
                    'year': str(year)
                }

    print(f"  Loaded metadata for {len(metadata)} samples")
    return metadata

def load_mlst_data(base_dir):
    """Load MLST sequence type data from all year directories"""
    print("Loading MLST data from year directories...")

    mlst_data = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        mlst_dir = base_path / f"results_kansas_{year}" / "mlst"

        if not mlst_dir.exists():
            print(f"  Warning: {mlst_dir} not found, skipping")
            continue

        print(f"  Loading {year} MLST data...")
        count = 0

        for mlst_file in mlst_dir.glob("*_mlst.tsv"):
            sample_id = mlst_file.stem.replace('_mlst', '')

            with open(mlst_file) as f:
                line = f.readline().strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) < 3:
                    continue

                # MLST format: filename, scheme, ST, allele1, allele2, ...
                st = parts[2]

                if st and st != '-' and st != 'ST':
                    mlst_data[sample_id] = st
                    count += 1

        print(f"    Found {count} samples with MLST data")

    print(f"  Total samples with MLST: {len(mlst_data)}")
    return mlst_data

# ============================================================================
# ANALYSIS
# ============================================================================

def analyze_st_patterns(colocation_data, mlst_data, metadata):
    """
    Comprehensive MLST strain-level analysis
    """
    print("\nAnalyzing MLST strain patterns...")

    # Data structures
    st_stats = defaultdict(lambda: {
        'samples': set(),
        'total_amr': 0,
        'proximal_amr': 0,
        'amr_genes': Counter(),
        'amr_classes': Counter(),
        'years': Counter(),
        'food_sources': Counter(),
        'prophages': 0
    })

    # Track samples
    samples_by_st = defaultdict(set)
    samples_without_st = set()

    # First, get all samples with AMR data
    all_amr_samples = set(row['sample'] for row in colocation_data)

    # Categorize samples by ST
    for sample_id in all_amr_samples:
        if sample_id in mlst_data:
            st = mlst_data[sample_id]
            samples_by_st[st].add(sample_id)
        else:
            samples_without_st.add(sample_id)

    print(f"  Samples with MLST data: {sum(len(s) for s in samples_by_st.values())}")
    print(f"  Samples without MLST data: {len(samples_without_st)}")
    print(f"  Unique sequence types: {len(samples_by_st)}")

    # Analyze each AMR-prophage association
    for row in colocation_data:
        sample_id = row['sample']
        amr_gene = row['amr_gene']
        amr_class = row['amr_class']
        category = row['category']

        # Skip if no MLST data
        if sample_id not in mlst_data:
            continue

        st = mlst_data[sample_id]

        # Get metadata
        meta = metadata.get(sample_id, {})
        year = meta.get('year', 'Unknown')
        food_source = meta.get('food_source', 'Unknown')

        # Determine proximity
        is_proximal = category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']

        # Record statistics
        st_stats[st]['samples'].add(sample_id)
        st_stats[st]['total_amr'] += 1
        st_stats[st]['amr_genes'][amr_gene] += 1
        st_stats[st]['amr_classes'][amr_class] += 1
        st_stats[st]['years'][year] += 1
        st_stats[st]['food_sources'][food_source] += 1

        if is_proximal:
            st_stats[st]['proximal_amr'] += 1

        if row.get('prophage_id', 'None') != 'None':
            st_stats[st]['prophages'] += 1

    # Calculate derived statistics
    st_summary = []
    for st, stats in st_stats.items():
        n_samples = len(stats['samples'])
        total_amr = stats['total_amr']
        proximal_amr = stats['proximal_amr']
        proximal_pct = (proximal_amr / total_amr * 100) if total_amr > 0 else 0

        # Get temporal spread
        years = sorted(stats['years'].keys())
        year_range = f"{years[0]}-{years[-1]}" if len(years) > 1 else years[0] if years else 'Unknown'

        # Get predominant food source
        top_food = stats['food_sources'].most_common(1)[0] if stats['food_sources'] else ('Unknown', 0)

        # Unique AMR genes and classes
        unique_genes = len(stats['amr_genes'])
        unique_classes = len(stats['amr_classes'])

        st_summary.append({
            'st': st,
            'n_samples': n_samples,
            'total_amr': total_amr,
            'proximal_amr': proximal_amr,
            'proximal_pct': proximal_pct,
            'unique_genes': unique_genes,
            'unique_classes': unique_classes,
            'year_range': year_range,
            'top_food': top_food[0],
            'top_food_count': top_food[1],
            'top_amr_genes': stats['amr_genes'].most_common(5),
            'top_amr_classes': stats['amr_classes'].most_common(5),
            'years': dict(stats['years']),
            'food_sources': dict(stats['food_sources'])
        })

    # Sort by number of samples
    st_summary.sort(key=lambda x: x['n_samples'], reverse=True)

    return {
        'st_summary': st_summary,
        'st_stats': st_stats,
        'samples_by_st': samples_by_st,
        'samples_without_st': samples_without_st
    }

def identify_high_risk_clones(analysis_data):
    """Identify high-risk sequence types"""

    st_summary = analysis_data['st_summary']

    high_risk = []

    for st_data in st_summary:
        # Criteria for high-risk:
        # 1. Multiple samples (≥5)
        # 2. High AMR burden (≥3 unique classes)
        # 3. Elevated proximal rate OR high absolute proximal count

        if (st_data['n_samples'] >= 5 and
            st_data['unique_classes'] >= 3 and
            (st_data['proximal_pct'] > 2.0 or st_data['proximal_amr'] >= 3)):

            risk_score = (st_data['n_samples'] * 0.3 +
                         st_data['unique_classes'] * 5 +
                         st_data['proximal_pct'] * 2)

            high_risk.append({
                'st': st_data['st'],
                'risk_score': risk_score,
                'n_samples': st_data['n_samples'],
                'unique_classes': st_data['unique_classes'],
                'proximal_pct': st_data['proximal_pct'],
                'year_range': st_data['year_range']
            })

    high_risk.sort(key=lambda x: x['risk_score'], reverse=True)

    return high_risk

def identify_pandemic_clones(st_summary):
    """Identify known pandemic E. coli clones"""

    # Known pandemic/important E. coli STs
    pandemic_sts = {
        'ST131': 'ExPEC pandemic clone (fluoroquinolone-resistant)',
        'ST10': 'Widespread commensal/ExPEC clone',
        'ST95': 'ExPEC clone',
        'ST73': 'ExPEC clone',
        'ST69': 'ExPEC clone',
        'ST12': 'EHEC O157:H7 lineage',
        'ST11': 'EHEC O157:H7 lineage',
        'ST38': 'Widespread clone',
        'ST648': 'ESBL-producing clone',
    }

    found_pandemic = []

    for st_data in st_summary:
        st = st_data['st']
        if st in pandemic_sts:
            found_pandemic.append({
                'st': st,
                'description': pandemic_sts[st],
                'n_samples': st_data['n_samples'],
                'proximal_pct': st_data['proximal_pct'],
                'top_amr_classes': st_data['top_amr_classes']
            })

    return found_pandemic

# ============================================================================
# HTML REPORT GENERATION
# ============================================================================

def generate_html_report(output_file, analysis_data, high_risk_clones, pandemic_clones, metadata):
    """Generate comprehensive HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    st_summary = analysis_data['st_summary']
    samples_without_st = analysis_data['samples_without_st']

    # Get top STs
    top_sts = st_summary[:20]

    # Temporal distribution
    years = ['2021', '2022', '2023', '2024', '2025']

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLST Strain-Level AMR-Prophage Analysis</title>
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
            max-width: 1800px;
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
            font-size: 0.9em;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th, td {{
            padding: 12px;
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

        .danger-box {{
            background: #fee2e2;
            border-left: 4px solid #dc2626;
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

        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-info {{
            background: #dbeafe;
            color: #1e40af;
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
            <h1>🧬 MLST Strain-Level AMR-Prophage Analysis</h1>
            <p>Clonal Distribution and High-Risk Lineages</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Kansas E. coli Study 2021-2025</p>
            <p style="font-size: 0.85em;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        <div class="content">
            <section id="overview">
                <h2>📊 Overview</h2>

                <div class="alert-box">
                    <h4>🔬 Research Questions</h4>
                    <ul style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li>Which sequence types (STs) carry the most AMR genes?</li>
                        <li>Do certain STs show higher prophage-AMR proximity rates?</li>
                        <li>Are there high-risk clonal lineages spreading over time?</li>
                        <li>Are pandemic clones (ST131, ST10) present in the dataset?</li>
                    </ul>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Unique Sequence Types</h4>
                        <div class="value">{len(st_summary)}</div>
                        <p>STs identified</p>
                    </div>
                    <div class="stat-card">
                        <h4>Top ST</h4>
                        <div class="value">{st_summary[0]['st'] if st_summary else 'N/A'}</div>
                        <p>{st_summary[0]['n_samples'] if st_summary else 0} samples</p>
                    </div>
                    <div class="stat-card">
                        <h4>High-Risk Clones</h4>
                        <div class="value">{len(high_risk_clones)}</div>
                        <p>Identified</p>
                    </div>
                    <div class="stat-card">
                        <h4>Pandemic Clones</h4>
                        <div class="value">{len(pandemic_clones)}</div>
                        <p>Found in dataset</p>
                    </div>
                </div>
            </section>
"""

    # Pandemic clones section
    if pandemic_clones:
        html += """
            <section id="pandemic">
                <h2>⚠️ Pandemic/Important Clones Detected</h2>

                <div class="danger-box">
                    <h4>🚨 Known High-Risk E. coli Lineages Found</h4>
                    <p>These sequence types are clinically or epidemiologically important</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>ST</th>
                            <th>Description</th>
                            <th>Samples</th>
                            <th>Proximal %</th>
                            <th>Top AMR Classes</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        for clone in pandemic_clones:
            top_classes = ', '.join([f"{c[0]} ({c[1]})" for c in clone['top_amr_classes'][:3]])

            html += f"""
                        <tr>
                            <td><strong>{clone['st']}</strong></td>
                            <td>{clone['description']}</td>
                            <td><span class="highlight">{clone['n_samples']}</span></td>
                            <td>{clone['proximal_pct']:.2f}%</td>
                            <td>{top_classes}</td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </section>
"""

    # High-risk clones
    html += """
            <section id="high-risk">
                <h2>🔥 High-Risk Clones</h2>

                <div class="info-box">
                    <h4>📈 Clones with Elevated AMR Burden</h4>
                    <p>STs with ≥5 samples, ≥3 AMR classes, and elevated prophage proximity or counts</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>ST</th>
                            <th>Risk Score</th>
                            <th>Samples</th>
                            <th>AMR Classes</th>
                            <th>Proximal %</th>
                            <th>Year Range</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for clone in high_risk_clones[:15]:
        html += f"""
                        <tr>
                            <td><strong>{clone['st']}</strong></td>
                            <td><span class="badge badge-danger">{clone['risk_score']:.1f}</span></td>
                            <td>{clone['n_samples']}</td>
                            <td>{clone['unique_classes']}</td>
                            <td>{clone['proximal_pct']:.2f}%</td>
                            <td>{clone['year_range']}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="top-sts">
                <h2>🏆 Top 20 Sequence Types</h2>

                <div class="info-box">
                    <h4>📊 Most Prevalent STs</h4>
                    <p>Ranked by number of samples</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>ST</th>
                            <th>Samples</th>
                            <th>Total AMR</th>
                            <th>Proximal AMR</th>
                            <th>Proximal %</th>
                            <th>Unique Genes</th>
                            <th>Unique Classes</th>
                            <th>Years</th>
                            <th>Top Food Source</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for i, st_data in enumerate(top_sts, 1):
        badge_class = 'badge-danger' if st_data['proximal_pct'] > 2.0 else 'badge-info'

        html += f"""
                        <tr>
                            <td>{i}</td>
                            <td><strong>{st_data['st']}</strong></td>
                            <td>{st_data['n_samples']}</td>
                            <td>{st_data['total_amr']}</td>
                            <td><span class="highlight">{st_data['proximal_amr']}</span></td>
                            <td><span class="badge {badge_class}">{st_data['proximal_pct']:.2f}%</span></td>
                            <td>{st_data['unique_genes']}</td>
                            <td>{st_data['unique_classes']}</td>
                            <td>{st_data['year_range']}</td>
                            <td>{st_data['top_food']} ({st_data['top_food_count']})</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>
            </section>

            <section id="details">
                <h2>🔬 Detailed ST Profiles</h2>

                <div class="info-box">
                    <h4>💊 AMR Gene and Class Distributions for Top STs</h4>
                </div>
"""

    for st_data in top_sts[:10]:
        top_genes = ', '.join([f"{g[0]} ({g[1]})" for g in st_data['top_amr_genes'][:5]])
        top_classes = ', '.join([f"{c[0]} ({c[1]})" for c in st_data['top_amr_classes'][:5]])

        html += f"""
                <h3>ST{st_data['st']}</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li><strong>Samples:</strong> {st_data['n_samples']}</li>
                    <li><strong>Top AMR Genes:</strong> {top_genes}</li>
                    <li><strong>Top AMR Classes:</strong> {top_classes}</li>
                    <li><strong>Proximal Rate:</strong> {st_data['proximal_pct']:.2f}% ({st_data['proximal_amr']}/{st_data['total_amr']})</li>
                </ul>
"""

    html += f"""
            </section>

            <section id="conclusions">
                <h2>📝 Key Findings</h2>

                <div class="alert-box">
                    <h4>✅ Summary</h4>
                    <ul style="line-height: 2; margin-left: 30px; margin-top: 10px;">
                        <li><strong>Clonal diversity:</strong> {len(st_summary)} unique sequence types identified</li>
                        <li><strong>Top ST:</strong> ST{st_summary[0]['st'] if st_summary else 'N/A'} with {st_summary[0]['n_samples'] if st_summary else 0} samples</li>
                        <li><strong>High-risk clones:</strong> {len(high_risk_clones)} STs meet high-risk criteria</li>
                        <li><strong>Pandemic clones:</strong> {len(pandemic_clones)} known pandemic STs detected</li>
                        <li><strong>Samples with MLST:</strong> {sum(st['n_samples'] for st in st_summary)}</li>
                        <li><strong>Samples without MLST:</strong> {len(samples_without_st)}</li>
                    </ul>
                </div>

                <h3>Public Health Implications</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li>Monitor high-risk STs for temporal and geographic spread</li>
                    <li>Target surveillance on STs with elevated AMR-prophage associations</li>
                    <li>Track pandemic clones (ST131, ST10) for emerging resistance</li>
                    <li>Use ST data to inform outbreak investigations</li>
                </ul>

                <h3>Next Steps</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li>Phylogenetic analysis of high-risk STs</li>
                    <li>SNP-level analysis for microevolution within STs</li>
                    <li>Comparison with national/international ST distributions</li>
                    <li>Integration with virulence factor data</li>
                </ul>
            </section>
        </div>

        <footer>
            <p><strong>MLST Strain-Level AMR-Prophage Analysis</strong></p>
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
    base_dir = Path.home() / 'compass_kansas_results'
    output_html = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'reports' / 'KANSAS_MLST_STRAIN_ANALYSIS.html'

    print("=" * 70)
    print("MLST Strain-Level AMR-Prophage Analysis")
    print("Clonal Distribution and High-Risk Lineages")
    print("=" * 70)

    # Load data
    metadata = load_metadata_files(base_dir)
    mlst_data = load_mlst_data(base_dir)
    colocation_data = load_colocation_data(colocation_csv)

    if not mlst_data:
        print("\n❌ Error: No MLST data found!")
        print("   Check that MLST results exist in results directories.")
        sys.exit(1)

    # Run analysis
    analysis_data = analyze_st_patterns(colocation_data, mlst_data, metadata)

    # Identify patterns
    high_risk_clones = identify_high_risk_clones(analysis_data)
    pandemic_clones = identify_pandemic_clones(analysis_data['st_summary'])

    # Generate report
    generate_html_report(output_html, analysis_data, high_risk_clones, pandemic_clones, metadata)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_html}")
    print(f"\n📈 Key Statistics:")
    print(f"   - Unique STs: {len(analysis_data['st_summary'])}")
    print(f"   - High-risk clones: {len(high_risk_clones)}")
    print(f"   - Pandemic clones found: {len(pandemic_clones)}")
    if pandemic_clones:
        print(f"   - Detected pandemic STs: {', '.join([c['st'] for c in pandemic_clones])}")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
