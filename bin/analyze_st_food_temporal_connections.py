#!/usr/bin/env python3
"""
ST-Food-Temporal Connection Analysis
Kansas E. coli Study 2021-2025

Deep dive into sequence type distributions across:
- Food sources (which foods carry which STs?)
- Temporal patterns (ST emergence/persistence over years)
- AMR profiles by ST and food source
- Sample-level ST tracking

Answers:
- Are certain STs specific to certain food sources?
- Which STs are emerging vs declining?
- Do food-specific STs have different AMR profiles?
- Can we track ST spread through the food supply?

Generates:
- ST × Food source matrix
- Temporal ST trends
- Food-specific ST profiles
- Sample tracking table
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

                st = parts[2]

                if st and st != '-' and st != 'ST':
                    mlst_data[sample_id] = st
                    count += 1

        print(f"    Found {count} samples with MLST data")

    print(f"  Total samples with MLST: {len(mlst_data)}")
    return mlst_data

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

# ============================================================================
# ANALYSIS
# ============================================================================

def analyze_st_food_temporal_connections(mlst_data, metadata, colocation_data):
    """
    Comprehensive ST-Food-Temporal connection analysis
    """
    print("\nAnalyzing ST-Food-Temporal connections...")

    # Data structures

    # ST × Food matrix
    st_food_matrix = defaultdict(lambda: Counter())  # st -> {food: count}

    # ST × Year matrix
    st_year_matrix = defaultdict(lambda: Counter())  # st -> {year: count}

    # ST × Food × Year (3-way)
    st_food_year = defaultdict(lambda: defaultdict(lambda: Counter()))  # st -> food -> {year: count}

    # Sample-level tracking
    sample_tracking = []  # List of sample details

    # AMR profiles by ST and food
    st_food_amr = defaultdict(lambda: defaultdict(lambda: Counter()))  # st -> food -> {amr_class: count}

    # Process all samples with MLST
    for sample_id, st in mlst_data.items():
        if sample_id not in metadata:
            continue

        meta = metadata[sample_id]
        food_source = meta['food_source']
        year = meta['year']
        sample_name = meta['sample_name']

        # Populate matrices
        st_food_matrix[st][food_source] += 1
        st_year_matrix[st][year] += 1
        st_food_year[st][food_source][year] += 1

        # Get AMR data for this sample
        sample_amr_classes = Counter()
        sample_amr_genes = []
        proximal_count = 0

        for row in colocation_data:
            if row['sample'] == sample_id:
                amr_class = row['amr_class']
                amr_gene = row['amr_gene']
                category = row['category']

                sample_amr_classes[amr_class] += 1
                sample_amr_genes.append(amr_gene)

                if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
                    proximal_count += 1

                # Record ST-food-AMR association
                st_food_amr[st][food_source][amr_class] += 1

        # Sample tracking
        sample_tracking.append({
            'sample_id': sample_id,
            'sample_name': sample_name,
            'st': st,
            'food_source': food_source,
            'year': year,
            'total_amr': len(sample_amr_genes),
            'unique_amr_classes': len(sample_amr_classes),
            'proximal_amr': proximal_count,
            'top_amr_classes': ', '.join([f"{c} ({n})" for c, n in sample_amr_classes.most_common(3)])
        })

    return {
        'st_food_matrix': st_food_matrix,
        'st_year_matrix': st_year_matrix,
        'st_food_year': st_food_year,
        'sample_tracking': sample_tracking,
        'st_food_amr': st_food_amr
    }

def identify_food_specific_sts(st_food_matrix):
    """Identify STs that are specific to certain food sources"""

    food_specific = []

    for st, food_counts in st_food_matrix.items():
        total_samples = sum(food_counts.values())

        if total_samples < 3:  # Minimum threshold
            continue

        # Find dominant food source
        top_food, top_count = food_counts.most_common(1)[0]
        dominance_pct = (top_count / total_samples * 100)

        # Food-specific if >80% from one source
        if dominance_pct >= 80:
            food_specific.append({
                'st': st,
                'food_source': top_food,
                'samples_in_food': top_count,
                'total_samples': total_samples,
                'dominance_pct': dominance_pct
            })

    food_specific.sort(key=lambda x: x['dominance_pct'], reverse=True)

    return food_specific

def identify_emerging_declining_sts(st_year_matrix):
    """Identify STs that are emerging or declining over time"""

    emerging = []
    declining = []

    for st, year_counts in st_year_matrix.items():
        years = sorted(year_counts.keys())

        if len(years) < 2:  # Need at least 2 years
            continue

        # Get first and last year counts
        first_year = years[0]
        last_year = years[-1]

        first_count = year_counts[first_year]
        last_count = year_counts[last_year]

        # Calculate trend
        if last_count > first_count * 2:  # Doubling
            emerging.append({
                'st': st,
                'first_year': first_year,
                'last_year': last_year,
                'first_count': first_count,
                'last_count': last_count,
                'fold_change': last_count / first_count if first_count > 0 else 0
            })
        elif first_count > last_count * 2:  # Halving
            declining.append({
                'st': st,
                'first_year': first_year,
                'last_year': last_year,
                'first_count': first_count,
                'last_count': last_count,
                'fold_change': first_count / last_count if last_count > 0 else 0
            })

    emerging.sort(key=lambda x: x['fold_change'], reverse=True)
    declining.sort(key=lambda x: x['fold_change'], reverse=True)

    return emerging, declining

# ============================================================================
# HTML REPORT GENERATION
# ============================================================================

def generate_html_report(output_file, analysis_data, food_specific, emerging, declining):
    """Generate comprehensive HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    st_food_matrix = analysis_data['st_food_matrix']
    st_year_matrix = analysis_data['st_year_matrix']
    sample_tracking = analysis_data['sample_tracking']
    st_food_amr = analysis_data['st_food_amr']

    # Get top STs
    st_totals = [(st, sum(foods.values())) for st, foods in st_food_matrix.items()]
    st_totals.sort(key=lambda x: x[1], reverse=True)
    top_sts = st_totals[:15]

    # Get all food sources
    all_foods = set()
    for foods in st_food_matrix.values():
        all_foods.update(foods.keys())
    all_foods = sorted(all_foods)

    # Get all years
    all_years = sorted(set(year for years in st_year_matrix.values() for year in years.keys()))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ST-Food-Temporal Connection Analysis</title>
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
            font-size: 0.85em;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th, td {{
            padding: 10px;
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
            <h1>🔗 ST-Food-Temporal Connection Analysis</h1>
            <p>Tracking Sequence Types Across Food Sources and Time</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Kansas E. coli Study 2021-2025</p>
            <p style="font-size: 0.85em;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        <div class="content">
            <section id="overview">
                <h2>📊 Overview</h2>

                <div class="alert-box">
                    <h4>🔬 Key Questions</h4>
                    <ul style="margin-left: 20px; margin-top: 10px; line-height: 1.8;">
                        <li>Which STs are specific to certain food sources?</li>
                        <li>Are STs emerging or declining over time?</li>
                        <li>Which samples carry which STs?</li>
                        <li>Do food-specific STs have different AMR profiles?</li>
                    </ul>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Total Samples Tracked</h4>
                        <div class="value">{len(sample_tracking)}</div>
                        <p>With MLST data</p>
                    </div>
                    <div class="stat-card">
                        <h4>Food-Specific STs</h4>
                        <div class="value">{len(food_specific)}</div>
                        <p>≥80% in one food source</p>
                    </div>
                    <div class="stat-card">
                        <h4>Emerging STs</h4>
                        <div class="value">{len(emerging)}</div>
                        <p>Increasing over time</p>
                    </div>
                    <div class="stat-card">
                        <h4>Declining STs</h4>
                        <div class="value">{len(declining)}</div>
                        <p>Decreasing over time</p>
                    </div>
                </div>
            </section>

            <section id="st-food-matrix">
                <h2>🍗 ST × Food Source Matrix</h2>

                <div class="info-box">
                    <h4>📈 Top 15 STs by Food Source</h4>
                    <p>Distribution of sequence types across different food products</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>ST</th>
                            <th>Total</th>
"""

    for food in all_foods:
        html += f"                            <th>{food}</th>\n"

    html += """
                        </tr>
                    </thead>
                    <tbody>
"""

    for st, total in top_sts:
        html += f"                        <tr>\n"
        html += f"                            <td><strong>ST{st}</strong></td>\n"
        html += f"                            <td><span class='highlight'>{total}</span></td>\n"

        for food in all_foods:
            count = st_food_matrix[st].get(food, 0)
            if count > 0:
                html += f"                            <td>{count}</td>\n"
            else:
                html += f"                            <td>-</td>\n"

        html += f"                        </tr>\n"

    html += """
                    </tbody>
                </table>
            </section>

            <section id="food-specific">
                <h2>🎯 Food-Specific Sequence Types</h2>

                <div class="success-box">
                    <h4>✨ STs Predominantly Found in Single Food Sources</h4>
                    <p>STs where ≥80% of samples come from one food source</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>ST</th>
                            <th>Food Source</th>
                            <th>Samples in This Food</th>
                            <th>Total Samples</th>
                            <th>Dominance %</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for fs in food_specific[:20]:
        html += f"""
                        <tr>
                            <td><strong>ST{fs['st']}</strong></td>
                            <td><span class="highlight">{fs['food_source']}</span></td>
                            <td>{fs['samples_in_food']}</td>
                            <td>{fs['total_samples']}</td>
                            <td><span class="badge badge-success">{fs['dominance_pct']:.1f}%</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="temporal">
                <h2>📅 Temporal Trends</h2>

                <div class="info-box">
                    <h4>⏱️ Emerging and Declining Sequence Types</h4>
                </div>

                <h3>Emerging STs (Increasing Over Time)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ST</th>
                            <th>First Year</th>
                            <th>Last Year</th>
                            <th>Initial Count</th>
                            <th>Final Count</th>
                            <th>Fold Change</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for emg in emerging[:10]:
        html += f"""
                        <tr>
                            <td><strong>ST{emg['st']}</strong></td>
                            <td>{emg['first_year']}</td>
                            <td>{emg['last_year']}</td>
                            <td>{emg['first_count']}</td>
                            <td><span class="highlight">{emg['last_count']}</span></td>
                            <td><span class="badge badge-danger">{emg['fold_change']:.1f}x</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>

                <h3>Declining STs (Decreasing Over Time)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ST</th>
                            <th>First Year</th>
                            <th>Last Year</th>
                            <th>Initial Count</th>
                            <th>Final Count</th>
                            <th>Fold Change</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for dec in declining[:10]:
        html += f"""
                        <tr>
                            <td><strong>ST{dec['st']}</strong></td>
                            <td>{dec['first_year']}</td>
                            <td>{dec['last_year']}</td>
                            <td><span class="highlight">{dec['first_count']}</span></td>
                            <td>{dec['last_count']}</td>
                            <td><span class="badge badge-info">{dec['fold_change']:.1f}x</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="samples">
                <h2>🔬 Sample-Level Tracking</h2>

                <div class="info-box">
                    <h4>📋 Individual Samples with ST Assignments</h4>
                    <p>Showing first 50 samples (sorted by AMR burden)</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Sample ID</th>
                            <th>Sample Name</th>
                            <th>ST</th>
                            <th>Food Source</th>
                            <th>Year</th>
                            <th>Total AMR</th>
                            <th>AMR Classes</th>
                            <th>Proximal AMR</th>
                            <th>Top AMR Classes</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Sort samples by total AMR
    sample_tracking_sorted = sorted(sample_tracking, key=lambda x: x['total_amr'], reverse=True)

    for sample in sample_tracking_sorted[:50]:
        html += f"""
                        <tr>
                            <td>{sample['sample_id']}</td>
                            <td>{sample['sample_name']}</td>
                            <td><strong>ST{sample['st']}</strong></td>
                            <td>{sample['food_source']}</td>
                            <td>{sample['year']}</td>
                            <td><span class="highlight">{sample['total_amr']}</span></td>
                            <td>{sample['unique_amr_classes']}</td>
                            <td>{sample['proximal_amr']}</td>
                            <td>{sample['top_amr_classes']}</td>
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
                        <li><strong>Samples tracked:</strong> {len(sample_tracking)} with complete ST/food/temporal data</li>
                        <li><strong>Food-specific STs:</strong> {len(food_specific)} STs show ≥80% dominance in one food source</li>
                        <li><strong>Emerging STs:</strong> {len(emerging)} STs increasing over time</li>
                        <li><strong>Declining STs:</strong> {len(declining)} STs decreasing over time</li>
                    </ul>
                </div>

                <h3>Public Health Implications</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li><strong>Food-specific STs:</strong> Target interventions at specific food-ST combinations</li>
                    <li><strong>Emerging STs:</strong> Monitor for potential outbreaks or resistance spread</li>
                    <li><strong>Declining STs:</strong> May indicate successful interventions or natural shifts</li>
                    <li><strong>Sample tracking:</strong> Enables trace-back during outbreak investigations</li>
                </ul>
            </section>
        </div>

        <footer>
            <p><strong>ST-Food-Temporal Connection Analysis</strong></p>
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
    output_html = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'reports' / 'KANSAS_ST_FOOD_TEMPORAL_CONNECTIONS.html'

    print("=" * 70)
    print("ST-Food-Temporal Connection Analysis")
    print("Tracking Sequence Types Across Food Sources and Time")
    print("=" * 70)

    # Load data
    metadata = load_metadata_files(base_dir)
    mlst_data = load_mlst_data(base_dir)
    colocation_data = load_colocation_data(colocation_csv)

    if not mlst_data:
        print("\n❌ Error: No MLST data found!")
        sys.exit(1)

    # Run analysis
    analysis_data = analyze_st_food_temporal_connections(mlst_data, metadata, colocation_data)

    # Identify patterns
    food_specific = identify_food_specific_sts(analysis_data['st_food_matrix'])
    emerging, declining = identify_emerging_declining_sts(analysis_data['st_year_matrix'])

    # Generate report
    generate_html_report(output_html, analysis_data, food_specific, emerging, declining)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_html}")
    print(f"\n📈 Key Statistics:")
    print(f"   - Samples tracked: {len(analysis_data['sample_tracking'])}")
    print(f"   - Food-specific STs: {len(food_specific)}")
    print(f"   - Emerging STs: {len(emerging)}")
    print(f"   - Declining STs: {len(declining)}")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
