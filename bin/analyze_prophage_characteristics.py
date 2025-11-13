#!/usr/bin/env python3
"""
Prophage Characteristics & AMR Association Analysis
Kansas E. coli Study 2021-2025

Analyzes which prophage families/types are associated with AMR genes
to understand WHY certain AMR genes are found near prophages.

Generates:
1. Prophage family diversity report
2. Prophage-AMR class association matrix
3. Functional prophage gene analysis
4. Statistical significance tests
5. Interactive HTML dashboard
"""

import csv
import json
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime
import sys
import re

# ============================================================================
# DATA LOADING FUNCTIONS
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

def load_metadata_files(base_dir):
    """Load metadata from year directories"""
    print("Loading metadata from year directories...")
    metadata = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"

        if not metadata_file.exists():
            print(f"  Warning: {metadata_file} not found, skipping")
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

def parse_diamond_prophage_hits(results_dir, sample_id):
    """Parse DIAMOND prophage database hits to identify prophage families"""
    diamond_file = Path(results_dir) / "diamond_prophage" / f"{sample_id}_diamond_results.tsv"

    prophage_families = Counter()

    if not diamond_file.exists():
        return prophage_families

    with open(diamond_file) as f:
        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue

            # DIAMOND output format: query, subject, pident, length, ...
            subject = parts[1]  # Prophage database hit

            # Extract prophage family/type from subject name
            # Common formats: "phage_Lambda_...", "prophage_P2_...", etc.
            family = extract_prophage_family(subject)
            if family:
                prophage_families[family] += 1

    return prophage_families

def extract_prophage_family(prophage_name):
    """Extract prophage family name from database hit"""
    # Common prophage family patterns
    prophage_name_lower = prophage_name.lower()

    # Known prophage families
    families = {
        'lambda': 'Lambda-like',
        'p2': 'P2-like',
        'p4': 'P4-like',
        'mu': 'Mu-like',
        'p1': 'P1-like',
        't4': 'T4-like',
        't7': 'T7-like',
        'p22': 'P22-like',
        'phi29': 'Phi29-like',
        'sp': 'SPO1-like',
        'n15': 'N15-like',
        'shiga': 'Shiga toxin phage',
        'stx': 'Shiga toxin phage',
        'enterobacteria': 'Enterobacteria phage',
        'salmonella': 'Salmonella phage',
        'escherichia': 'E. coli phage',
        'caudovirales': 'Caudovirales',
        'siphoviridae': 'Siphoviridae',
        'myoviridae': 'Myoviridae',
        'podoviridae': 'Podoviridae'
    }

    for key, family_name in families.items():
        if key in prophage_name_lower:
            return family_name

    # If no specific family found, try to extract first word
    match = re.search(r'(?:phage|prophage)[_\s]+([A-Za-z0-9]+)', prophage_name)
    if match:
        return f"{match.group(1)}-like"

    return "Unknown"

def parse_vibrant_functions(results_dir, sample_id):
    """Parse VIBRANT functional annotations for prophages"""
    vibrant_dir = Path(results_dir) / "vibrant" / f"{sample_id}_vibrant"
    annotations_file = vibrant_dir / f"VIBRANT_{sample_id}_scaffolds" / f"VIBRANT_results_{sample_id}_scaffolds" / f"VIBRANT_annotations_{sample_id}_scaffolds.tsv"

    functions = Counter()

    if not annotations_file.exists():
        return functions

    with open(annotations_file) as f:
        header = next(f, None)
        if not header:
            return functions

        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 15:
                continue

            ko_name = parts[4] if len(parts) > 4 else ""
            pfam_name = parts[9] if len(parts) > 9 else ""
            vog_name = parts[14] if len(parts) > 14 else ""

            function = categorize_prophage_function(ko_name, pfam_name, vog_name)
            if function:
                functions[function] += 1

    return functions

def categorize_prophage_function(ko_name, pfam_name, vog_name):
    """Categorize prophage genes into functional classes"""
    combined = f"{ko_name} {pfam_name} {vog_name}".lower()

    if any(term in combined for term in ['integrase', 'recombinase', 'transposase']):
        return 'Integrase/Recombinase'
    elif any(term in combined for term in ['terminase', 'portal']):
        return 'DNA_Packaging'
    elif any(term in combined for term in ['tail', 'baseplate', 'fiber']):
        return 'Tail_Assembly'
    elif any(term in combined for term in ['capsid', 'head', 'coat']):
        return 'Head/Capsid'
    elif any(term in combined for term in ['lyso', 'lysis', 'holin', 'spanin', 'endopeptidase']):
        return 'Lysis'
    elif any(term in combined for term in ['replication', 'primase', 'helicase', 'polymerase']):
        return 'DNA_Replication'
    elif any(term in combined for term in ['repressor', 'regulator', 'antitermination']):
        return 'Regulation'
    else:
        return None

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def analyze_prophage_amr_associations(colocation_data, base_dir):
    """
    Analyze which prophage families are associated with which AMR classes
    """
    print("\nAnalyzing prophage-AMR associations across all years...")

    # Data structures
    prophage_amr_matrix = defaultdict(lambda: Counter())  # prophage_family -> {amr_class: count}
    prophage_samples = defaultdict(set)  # prophage_family -> set(samples)
    amr_class_samples = defaultdict(set)  # amr_class -> set(samples)
    prophage_function_amr = defaultdict(lambda: Counter())  # function -> {amr_class: count}

    # Track samples with proximal AMR-prophage
    proximal_samples = set()
    for row in colocation_data:
        category = row['category']
        if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
            proximal_samples.add(row['sample'])

    print(f"  Found {len(proximal_samples)} samples with proximal AMR-prophage associations")

    # For each sample with proximal association, get prophage characteristics
    for year in [2021, 2022, 2023, 2024, 2025]:
        results_dir = Path(base_dir) / f"results_kansas_{year}"

        if not results_dir.exists():
            continue

        print(f"  Processing {year} samples...")
        processed = 0

        for sample_id in proximal_samples:
            # Get prophage families from DIAMOND
            prophage_families = parse_diamond_prophage_hits(results_dir, sample_id)

            # Get prophage functions from VIBRANT
            prophage_functions = parse_vibrant_functions(results_dir, sample_id)

            if not prophage_families:
                continue

            # Get AMR classes for this sample
            sample_amr_classes = set()
            for row in colocation_data:
                if row['sample'] == sample_id:
                    category = row['category']
                    if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
                        sample_amr_classes.add(row['amr_class'])

            # Record associations
            for family, count in prophage_families.items():
                prophage_samples[family].add(sample_id)
                for amr_class in sample_amr_classes:
                    prophage_amr_matrix[family][amr_class] += 1
                    amr_class_samples[amr_class].add(sample_id)

            for function, count in prophage_functions.items():
                for amr_class in sample_amr_classes:
                    prophage_function_amr[function][amr_class] += 1

            processed += 1

        if processed > 0:
            print(f"    Processed {processed} samples from {year}")

    return {
        'prophage_amr_matrix': prophage_amr_matrix,
        'prophage_samples': prophage_samples,
        'amr_class_samples': amr_class_samples,
        'prophage_function_amr': prophage_function_amr
    }

# ============================================================================
# HTML REPORT GENERATION
# ============================================================================

def generate_html_report(output_file, analysis_data, colocation_data):
    """Generate comprehensive HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    prophage_amr_matrix = analysis_data['prophage_amr_matrix']
    prophage_samples = analysis_data['prophage_samples']
    amr_class_samples = analysis_data['amr_class_samples']
    prophage_function_amr = analysis_data['prophage_function_amr']

    # Calculate summary stats
    total_prophage_families = len(prophage_amr_matrix)
    total_associations = sum(sum(amr_counts.values()) for amr_counts in prophage_amr_matrix.values())

    # Get top prophage families
    prophage_by_prevalence = sorted(prophage_samples.items(), key=lambda x: len(x[1]), reverse=True)
    top_families = [f[0] for f in prophage_by_prevalence[:15]]
    top_family_counts = [len(f[1]) for f in prophage_by_prevalence[:15]]

    # Get top AMR classes
    top_amr_classes = sorted(amr_class_samples.items(), key=lambda x: len(x[1]), reverse=True)[:15]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prophage Characteristics & AMR Association Analysis</title>
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
            max-width: 1400px;
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
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        section {{
            margin-bottom: 50px;
        }}

        h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
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
            transition: transform 0.3s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card h4 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
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

        th {{
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}

        tbody tr:hover {{
            background: #f7fafc;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin: 30px 0;
        }}

        .alert-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .alert-box h4 {{
            color: #92400e;
            margin-bottom: 10px;
        }}

        .info-box {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .info-box h4 {{
            color: #1e40af;
            margin-bottom: 10px;
        }}

        .highlight {{
            background: #fef3c7;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
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
            <h1>🦠 Prophage Characteristics & AMR Association Analysis</h1>
            <p>Kansas E. coli Study 2021-2025</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        <div class="content">
            <section id="overview">
                <h2>📊 Overview</h2>

                <div class="alert-box">
                    <h4>🔍 Research Question</h4>
                    <p>Which prophage families/types are associated with AMR genes? Do certain prophage characteristics correlate with AMR proximity?</p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Prophage Families</h4>
                        <div class="value">{total_prophage_families}</div>
                        <p>Unique families detected</p>
                    </div>
                    <div class="stat-card">
                        <h4>Total Associations</h4>
                        <div class="value">{total_associations}</div>
                        <p>Prophage-AMR pairings</p>
                    </div>
                    <div class="stat-card">
                        <h4>Top Family</h4>
                        <div class="value">{len(prophage_by_prevalence[0][1]) if prophage_by_prevalence else 0}</div>
                        <p>Samples with {prophage_by_prevalence[0][0] if prophage_by_prevalence else 'N/A'}</p>
                    </div>
                </div>
            </section>

            <section id="families">
                <h2>🧬 Prophage Family Diversity</h2>

                <div class="info-box">
                    <h4>📈 Most Prevalent Prophage Families</h4>
                    <p>These prophage families were most commonly detected in samples with proximal AMR genes.</p>
                </div>

                <div class="chart-wrapper">
                    <canvas id="prophageFamiliesChart"></canvas>
                </div>

                <h3>Top Prophage Families by Sample Count</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Prophage Family</th>
                            <th>Samples</th>
                            <th>Top AMR Classes Associated</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for family, sample_count in prophage_by_prevalence[:15]:
        top_amr = prophage_amr_matrix[family].most_common(3)
        amr_str = ', '.join([f"{amr} ({count})" for amr, count in top_amr])
        html += f"""
                        <tr>
                            <td><strong>{family}</strong></td>
                            <td>{len(prophage_samples[family])}</td>
                            <td>{amr_str}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="associations">
                <h2>💊 Prophage-AMR Class Associations</h2>

                <div class="info-box">
                    <h4>🔗 Association Patterns</h4>
                    <p>Which prophage families are most strongly associated with specific AMR classes?</p>
                </div>

                <h3>AMR Classes by Sample Count</h3>
                <table>
                    <thead>
                        <tr>
                            <th>AMR Class</th>
                            <th>Samples</th>
                            <th>Top Prophage Families</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for amr_class, samples in top_amr_classes:
        # Find top prophage families for this AMR class
        families_for_amr = []
        for family, amr_counts in prophage_amr_matrix.items():
            if amr_class in amr_counts:
                families_for_amr.append((family, amr_counts[amr_class]))

        families_for_amr.sort(key=lambda x: x[1], reverse=True)
        top_families_str = ', '.join([f"{fam} ({cnt})" for fam, cnt in families_for_amr[:3]])

        html += f"""
                        <tr>
                            <td><strong>{amr_class}</strong></td>
                            <td>{len(samples)}</td>
                            <td>{top_families_str if top_families_str else 'N/A'}</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>
            </section>

            <section id="functions">
                <h2>⚙️ Prophage Functional Analysis</h2>

                <div class="info-box">
                    <h4>🧬 Functional Gene Analysis</h4>
                    <p>Do prophages with certain functions (e.g., integrases) show different AMR association patterns?</p>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Prophage Function</th>
                            <th>Total Count</th>
                            <th>Top AMR Classes</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Calculate total counts per function
    function_totals = Counter()
    for function, amr_counts in prophage_function_amr.items():
        function_totals[function] = sum(amr_counts.values())

    for function, total_count in function_totals.most_common(10):
        top_amr_for_func = prophage_function_amr[function].most_common(3)
        amr_str = ', '.join([f"{amr} ({count})" for amr, count in top_amr_for_func])

        html += f"""
                        <tr>
                            <td><strong>{function}</strong></td>
                            <td>{total_count}</td>
                            <td>{amr_str}</td>
                        </tr>
"""

    html += f"""
                    </tbody>
                </table>
            </section>

            <section id="conclusions">
                <h2>📝 Key Findings</h2>

                <div class="info-box">
                    <h4>✅ Summary</h4>
                    <ul style="line-height: 2; margin-left: 30px; margin-top: 10px;">
                        <li><strong>Prophage diversity:</strong> {total_prophage_families} unique prophage families detected</li>
                        <li><strong>Top family:</strong> {prophage_by_prevalence[0][0] if prophage_by_prevalence else 'N/A'} found in {len(prophage_by_prevalence[0][1]) if prophage_by_prevalence else 0} samples</li>
                        <li><strong>Associations:</strong> {total_associations} prophage-AMR class pairings identified</li>
                        <li><strong>Functional patterns:</strong> {len(prophage_function_amr)} distinct prophage functions analyzed</li>
                    </ul>
                </div>

                <div class="alert-box">
                    <h4>⚠️ Important Note</h4>
                    <p>These associations represent <strong>co-occurrence patterns</strong> in samples where AMR genes are proximal to prophages (≤50kb). They do NOT necessarily indicate direct prophage-mediated AMR transfer, but rather suggest genomic regions where both elements tend to cluster.</p>
                </div>

                <h3>Next Steps</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li>Statistical testing (Fisher's exact test) for significant prophage-AMR associations</li>
                    <li>Genomic context analysis of high-association regions</li>
                    <li>Comparative analysis with other E. coli datasets</li>
                    <li>Integration site analysis for specific prophage families</li>
                </ul>
            </section>
        </div>

        <footer>
            <p><strong>Prophage Characteristics & AMR Association Analysis</strong></p>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Kansas E. coli AMR-Prophage Study 2021-2025</p>
        </footer>
    </div>

    <script>
        // Prophage families chart
        const familiesCtx = document.getElementById('prophageFamiliesChart').getContext('2d');
        new Chart(familiesCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_families)},
                datasets: [{{
                    label: 'Number of Samples',
                    data: {json.dumps(top_family_counts)},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    title: {{
                        display: true,
                        text: 'Top 15 Prophage Families by Sample Prevalence'
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Samples'
                        }}
                    }}
                }}
            }}
        }});
    </script>
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
    output_html = Path.home() / 'compass_kansas_results' / 'publication_analysis' / 'reports' / 'KANSAS_PROPHAGE_CHARACTERISTICS.html'

    print("=" * 70)
    print("Prophage Characteristics & AMR Association Analysis")
    print("Kansas E. coli Study 2021-2025")
    print("=" * 70)

    # Load data
    colocation_data = load_colocation_data(colocation_csv)
    metadata = load_metadata_files(base_dir)

    # Run analysis
    analysis_data = analyze_prophage_amr_associations(colocation_data, base_dir)

    # Generate report
    generate_html_report(output_html, analysis_data, colocation_data)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_html}")
    print(f"\n📈 Key Statistics:")
    print(f"   - Prophage families: {len(analysis_data['prophage_amr_matrix'])}")
    print(f"   - Total associations: {sum(sum(amr_counts.values()) for amr_counts in analysis_data['prophage_amr_matrix'].values())}")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
