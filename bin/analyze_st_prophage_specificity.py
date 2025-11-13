#!/usr/bin/env python3
"""
Analyze ST-Prophage Specificity

Connects MLST sequence types to specific prophage families to answer:
1. Which prophage families are associated with which STs?
2. Do high-risk clones carry specific prophages?
3. Are certain ST-prophage combinations more prevalent in specific foods?
4. Do prophage profiles differ between high-risk and low-risk STs?

Author: Claude Code
Date: 2025-01-13
"""

import re
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set

def extract_source_from_sample_name(sample_name: str) -> str:
    """Extract food source from NARMS sample naming convention"""
    if not sample_name:
        return 'Unknown'

    # Extract product code pattern (second occurrence)
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


def extract_prophage_family(subject_name: str) -> str:
    """Extract prophage family from DIAMOND subject name"""
    if not subject_name or subject_name == 'N/A':
        return None

    # Common patterns in prophage names
    patterns = [
        (r'(?:phage|prophage)[_\s]+(\w+)', 1),
        (r'^(\w+)[_\s]+(?:phage|prophage)', 1),
        (r'(\w+phage)', 0),
        (r'^([A-Z][a-z]+virus)', 0),
    ]

    for pattern, group in patterns:
        match = re.search(pattern, subject_name, re.IGNORECASE)
        if match:
            family = match.group(group) if group > 0 else match.group(1)
            return family.capitalize()

    # If no pattern matches, try to get first word
    first_word = subject_name.split('_')[0].split()[0]
    if len(first_word) > 3:
        return first_word.capitalize()

    return 'Unknown'

def parse_diamond_prophage_hits(diamond_file: Path) -> Counter:
    """Parse DIAMOND prophage hits to identify prophage families"""
    prophage_families = Counter()
    try:
        with open(diamond_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    subject = parts[1]
                    family = extract_prophage_family(subject)
                    if family:
                        prophage_families[family] += 1
    except FileNotFoundError:
        pass
    return prophage_families

def parse_vibrant_results(vibrant_dir: Path, sample_id: str) -> Set[str]:
    """Parse VIBRANT results to get prophage annotations"""
    prophages = set()

    # Check for VIBRANT summary files
    phages_file = vibrant_dir / f"{sample_id}_phages_combined.txt"
    if phages_file.exists():
        try:
            with open(phages_file, 'r') as f:
                for line in f:
                    if not line.startswith('#') and line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) > 0:
                            prophages.add(parts[0])
        except Exception:
            pass

    return prophages

def parse_amr_data(amr_file: Path) -> Dict[str, List[str]]:
    """Parse AMRFinder results to get AMR genes and classes"""
    amr_data = {'genes': [], 'classes': []}
    try:
        with open(amr_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 11:
                    gene = parts[5]
                    amr_class = parts[10]
                    amr_data['genes'].append(gene)
                    if amr_class and amr_class != 'N/A':
                        amr_data['classes'].append(amr_class)
    except FileNotFoundError:
        pass
    return amr_data


def identify_high_risk_sts(st_data: Dict[str, Dict]) -> Set[str]:
    """Identify high-risk STs based on sample count and AMR profile"""
    high_risk = set()

    pandemic_clones = {'131', '10', '69', '95', '73', '127', '648'}

    for st, data in st_data.items():
        # Pandemic clones are automatically high-risk
        if st in pandemic_clones:
            high_risk.add(st)
            continue

        # High-risk if: ≥5 samples AND ≥3 AMR classes
        if data['n_samples'] >= 5 and len(data['amr_classes']) >= 3:
            high_risk.add(st)

    return high_risk

def analyze_st_prophage_specificity_from_dirs(base_dir: Path, all_sts: Dict, metadata: Dict):
    """Main analysis function - processes data from year-based directories"""

    print("\n🔬 Analyzing ST-Prophage Specificity...")
    print("=" * 70)

    # Data structures
    st_prophage_matrix = defaultdict(lambda: Counter())  # st -> {prophage: count}
    st_sample_prophages = defaultdict(lambda: defaultdict(list))  # st -> sample -> [prophages]
    st_data = defaultdict(lambda: {
        'n_samples': 0,
        'prophage_families': Counter(),
        'amr_classes': Counter(),
        'amr_genes': Counter(),
        'food_sources': Counter(),
        'years': Counter(),
        'vibrant_prophages': set()
    })
    prophage_st_matrix = defaultdict(lambda: Counter())  # prophage -> {st: count}
    st_prophage_food = defaultdict(lambda: defaultdict(lambda: Counter()))  # st -> prophage -> {food: count}

    print(f"📊 Processing {len(all_sts)} samples with MLST data")

    # Process each sample with ST data
    samples_processed = 0
    for sample_id, st in all_sts.items():
        # Get metadata
        sample_meta = metadata.get(sample_id, {})
        food_source = extract_source_from_sample_name(sample_meta.get('sample_name', ''))
        year = sample_meta.get('year', 'Unknown')

        # Find which year directory this sample is in
        year_dir = None
        for yr in [2021, 2022, 2023, 2024, 2025]:
            test_dir = base_dir / f"results_kansas_{yr}"
            if (test_dir / "mlst" / f"{sample_id}_mlst.tsv").exists():
                year_dir = test_dir
                break

        if not year_dir:
            continue

        # Get prophage data from DIAMOND
        diamond_file = year_dir / "diamond_prophage" / f"{sample_id}_diamond_results.tsv"
        prophage_families = parse_diamond_prophage_hits(diamond_file)

        # Get VIBRANT prophages
        vibrant_dir = year_dir / "vibrant" / f"VIBRANT_{sample_id}"
        vibrant_prophages = parse_vibrant_results(vibrant_dir, sample_id)

        # Get AMR data
        amr_file = year_dir / "amrfinder" / f"{sample_id}_amrfinder.tsv"
        amr_data = parse_amr_data(amr_file)

        # Update ST data
        st_data[st]['n_samples'] += 1
        st_data[st]['food_sources'][food_source] += 1
        st_data[st]['years'][year] += 1
        st_data[st]['vibrant_prophages'].update(vibrant_prophages)

        for gene in amr_data['genes']:
            st_data[st]['amr_genes'][gene] += 1
        for amr_class in amr_data['classes']:
            st_data[st]['amr_classes'][amr_class] += 1

        # Update prophage associations
        for prophage, count in prophage_families.items():
            st_prophage_matrix[st][prophage] += count
            st_data[st]['prophage_families'][prophage] += count
            prophage_st_matrix[prophage][st] += count
            st_prophage_food[st][prophage][food_source] += count
            st_sample_prophages[st][sample_id].append(prophage)

        samples_processed += 1

    print(f"✅ Processed {samples_processed} samples with ST and prophage data")
    print(f"📊 Found {len(st_data)} unique STs")
    print(f"🦠 Found {len(prophage_st_matrix)} unique prophage families")

    # Identify high-risk STs
    high_risk_sts = identify_high_risk_sts(st_data)
    print(f"⚠️  Identified {len(high_risk_sts)} high-risk STs")

    # Generate HTML report
    output_dir = base_dir / 'publication_analysis' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "KANSAS_ST_PROPHAGE_SPECIFICITY.html"

    generate_html_report(
        output_file,
        st_prophage_matrix,
        st_data,
        prophage_st_matrix,
        st_prophage_food,
        high_risk_sts,
        st_sample_prophages
    )

    print(f"\n✅ Report generated: {output_file}")
    return output_file

def generate_html_report(
    output_file: Path,
    st_prophage_matrix: Dict,
    st_data: Dict,
    prophage_st_matrix: Dict,
    st_prophage_food: Dict,
    high_risk_sts: Set[str],
    st_sample_prophages: Dict
):
    """Generate HTML report"""

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ST-Prophage Specificity Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            padding: 40px;
        }

        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
        }

        h2 {
            color: #764ba2;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }

        h3 {
            color: #667eea;
            margin-top: 25px;
            margin-bottom: 15px;
        }

        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .info-box h4 {
            color: #764ba2;
            margin-bottom: 10px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }

        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }

        tr:hover {
            background-color: #f5f5f5;
        }

        .high-risk {
            background-color: #fff3cd;
            font-weight: bold;
        }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }

        .stat-label {
            font-size: 1em;
            opacity: 0.9;
        }

        .prophage-badge {
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.9em;
        }

        .st-badge {
            display: inline-block;
            background: #f3e5f5;
            color: #7b1fa2;
            padding: 4px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.9em;
            font-weight: bold;
        }

        .risk-high {
            background: #ffebee;
            color: #c62828;
        }

        .heatmap-cell {
            text-align: center;
            font-weight: bold;
        }

        .heatmap-high { background-color: #d32f2f; color: white; }
        .heatmap-med-high { background-color: #f57c00; color: white; }
        .heatmap-med { background-color: #fbc02d; color: black; }
        .heatmap-low { background-color: #fff9c4; color: black; }
        .heatmap-none { background-color: #f5f5f5; color: #999; }

        .section {
            margin: 40px 0;
        }

        .toc {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }

        .toc ul {
            list-style-position: inside;
            padding-left: 20px;
        }

        .toc li {
            margin: 8px 0;
        }

        .toc a {
            color: #667eea;
            text-decoration: none;
        }

        .toc a:hover {
            text-decoration: underline;
        }

        footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 ST-Prophage Specificity Analysis</h1>
        <p class="subtitle">Connecting E. coli Sequence Types to Prophage Families</p>

        <div class="info-box">
            <h4>📊 Analysis Overview</h4>
            <p>This report identifies which prophage families are specifically associated with E. coli sequence types (STs),
            revealing potential mechanisms of horizontal gene transfer and clonal evolution. High-risk clones are highlighted
            to understand their prophage profiles.</p>
        </div>
"""

    # Statistics
    total_sts = len(st_data)
    total_prophages = len(prophage_st_matrix)
    high_risk_count = len(high_risk_sts)
    total_samples = sum(data['n_samples'] for data in st_data.values())

    html_content += f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Sequence Types</div>
                <div class="stat-value">{total_sts}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Prophage Families</div>
                <div class="stat-value">{total_prophages}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">High-Risk STs</div>
                <div class="stat-value">{high_risk_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Samples Analyzed</div>
                <div class="stat-value">{total_samples}</div>
            </div>
        </div>

        <div class="toc">
            <h3>📑 Table of Contents</h3>
            <ul>
                <li><a href="#high-risk">High-Risk STs and Their Prophages</a></li>
                <li><a href="#st-prophage-matrix">ST-Prophage Association Matrix</a></li>
                <li><a href="#prophage-st-distribution">Prophage Distribution Across STs</a></li>
                <li><a href="#st-prophage-food">ST-Prophage-Food Connections</a></li>
                <li><a href="#specific-associations">Specific ST-Prophage Pairs</a></li>
            </ul>
        </div>
"""

    # Section 1: High-Risk STs
    html_content += """
        <section id="high-risk" class="section">
            <h2>⚠️ High-Risk STs and Their Prophages</h2>
            <div class="info-box">
                <h4>Identifying High-Risk Clones</h4>
                <p>High-risk STs are defined as: pandemic clones (ST131, ST10, etc.) OR STs with ≥5 samples and ≥3 AMR classes</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ST</th>
                        <th>Samples</th>
                        <th>AMR Classes</th>
                        <th>Top Prophages</th>
                        <th>Food Sources</th>
                        <th>Prophage Count</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Sort high-risk STs by sample count
    high_risk_sorted = sorted(
        [(st, st_data[st]) for st in high_risk_sts],
        key=lambda x: x[1]['n_samples'],
        reverse=True
    )

    for st, data in high_risk_sorted:
        top_prophages = data['prophage_families'].most_common(5)
        prophage_str = ', '.join([f"{p} ({c})" for p, c in top_prophages])

        top_foods = data['food_sources'].most_common(3)
        food_str = ', '.join([f"{f} ({c})" for f, c in top_foods])

        n_prophages = len(data['prophage_families'])
        n_amr = len(data['amr_classes'])

        html_content += f"""
                    <tr class="high-risk">
                        <td><span class="st-badge risk-high">ST{st}</span></td>
                        <td>{data['n_samples']}</td>
                        <td>{n_amr}</td>
                        <td>{prophage_str if prophage_str else 'None'}</td>
                        <td>{food_str}</td>
                        <td>{n_prophages}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 2: ST-Prophage Matrix (top STs only)
    html_content += """
        <section id="st-prophage-matrix" class="section">
            <h2>🔬 ST-Prophage Association Matrix</h2>
            <div class="info-box">
                <h4>Top 30 STs by Sample Count</h4>
                <p>Heat map showing prophage family associations. Color intensity indicates frequency of association.</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ST</th>
                        <th>Samples</th>
"""

    # Get top prophages for columns
    all_prophages = Counter()
    for st in st_prophage_matrix:
        all_prophages.update(st_prophage_matrix[st])
    top_prophages_list = [p for p, _ in all_prophages.most_common(15)]

    for prophage in top_prophages_list:
        html_content += f"                        <th>{prophage}</th>\n"

    html_content += """
                    </tr>
                </thead>
                <tbody>
"""

    # Get top 30 STs
    top_sts = sorted(st_data.items(), key=lambda x: x[1]['n_samples'], reverse=True)[:30]

    for st, data in top_sts:
        is_high_risk = st in high_risk_sts
        row_class = 'high-risk' if is_high_risk else ''
        st_badge = 'risk-high' if is_high_risk else ''

        html_content += f"""
                    <tr class="{row_class}">
                        <td><span class="st-badge {st_badge}">ST{st}</span></td>
                        <td>{data['n_samples']}</td>
"""

        for prophage in top_prophages_list:
            count = st_prophage_matrix[st].get(prophage, 0)
            if count == 0:
                cell_class = 'heatmap-none'
                display = '-'
            elif count >= 10:
                cell_class = 'heatmap-high'
                display = str(count)
            elif count >= 5:
                cell_class = 'heatmap-med-high'
                display = str(count)
            elif count >= 2:
                cell_class = 'heatmap-med'
                display = str(count)
            else:
                cell_class = 'heatmap-low'
                display = str(count)

            html_content += f'                        <td class="heatmap-cell {cell_class}">{display}</td>\n'

        html_content += "                    </tr>\n"

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 3: Prophage Distribution
    html_content += """
        <section id="prophage-st-distribution" class="section">
            <h2>🦠 Prophage Distribution Across STs</h2>
            <div class="info-box">
                <h4>Which Prophages Are ST-Specific?</h4>
                <p>Shows how broadly each prophage family is distributed across sequence types.</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Prophage Family</th>
                        <th>Total Hits</th>
                        <th>STs Found In</th>
                        <th>Top 5 STs</th>
                        <th>Specificity</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Sort prophages by total hits
    prophage_sorted = sorted(
        prophage_st_matrix.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True
    )[:50]  # Top 50 prophages

    for prophage, st_counts in prophage_sorted:
        total_hits = sum(st_counts.values())
        n_sts = len(st_counts)
        top_sts = st_counts.most_common(5)
        top_sts_str = ', '.join([f"ST{st} ({c})" for st, c in top_sts])

        # Calculate specificity (0-100): 100 = found in only 1 ST
        if n_sts == 1:
            specificity = 100.0
        else:
            # Gini coefficient-like measure
            max_count = max(st_counts.values())
            specificity = (max_count / total_hits) * 100

        html_content += f"""
                    <tr>
                        <td><span class="prophage-badge">{prophage}</span></td>
                        <td>{total_hits}</td>
                        <td>{n_sts}</td>
                        <td>{top_sts_str}</td>
                        <td>{specificity:.1f}%</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 4: ST-Prophage-Food Connections
    html_content += """
        <section id="st-prophage-food" class="section">
            <h2>🍗 ST-Prophage-Food Connections</h2>
            <div class="info-box">
                <h4>Food Source Context</h4>
                <p>Which food sources harbor specific ST-prophage combinations?</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ST</th>
                        <th>Prophage</th>
                        <th>Total</th>
                        <th>Food Source Distribution</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Get top ST-prophage pairs
    st_prophage_pairs = []
    for st in st_prophage_matrix:
        for prophage, count in st_prophage_matrix[st].most_common(3):
            if count >= 2:  # At least 2 occurrences
                st_prophage_pairs.append((st, prophage, count))

    # Sort by count
    st_prophage_pairs.sort(key=lambda x: x[2], reverse=True)

    for st, prophage, total in st_prophage_pairs[:100]:  # Top 100 pairs
        food_dist = st_prophage_food[st][prophage]
        food_str = ', '.join([f"{f} ({c})" for f, c in food_dist.most_common()])

        is_high_risk = st in high_risk_sts
        row_class = 'high-risk' if is_high_risk else ''

        html_content += f"""
                    <tr class="{row_class}">
                        <td><span class="st-badge">ST{st}</span></td>
                        <td><span class="prophage-badge">{prophage}</span></td>
                        <td>{total}</td>
                        <td>{food_str}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 5: Specific Associations
    html_content += """
        <section id="specific-associations" class="section">
            <h2>🎯 Highly Specific ST-Prophage Associations</h2>
            <div class="info-box">
                <h4>Strong Associations</h4>
                <p>ST-prophage pairs that show strong co-occurrence (prophage found in ≥50% of ST samples)</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ST</th>
                        <th>Prophage</th>
                        <th>Samples with Prophage</th>
                        <th>Total ST Samples</th>
                        <th>Prevalence</th>
                        <th>AMR Classes in ST</th>
                    </tr>
                </thead>
                <tbody>
"""

    specific_associations = []
    for st, data in st_data.items():
        if data['n_samples'] < 3:  # Need at least 3 samples
            continue
        for prophage, count in data['prophage_families'].items():
            prevalence = (count / data['n_samples']) * 100
            if prevalence >= 50:  # Found in ≥50% of samples
                specific_associations.append((
                    st, prophage, count, data['n_samples'],
                    prevalence, len(data['amr_classes'])
                ))

    # Sort by prevalence
    specific_associations.sort(key=lambda x: x[4], reverse=True)

    for st, prophage, with_prophage, total, prevalence, n_amr in specific_associations:
        is_high_risk = st in high_risk_sts
        row_class = 'high-risk' if is_high_risk else ''

        html_content += f"""
                    <tr class="{row_class}">
                        <td><span class="st-badge">ST{st}</span></td>
                        <td><span class="prophage-badge">{prophage}</span></td>
                        <td>{with_prophage}</td>
                        <td>{total}</td>
                        <td>{prevalence:.1f}%</td>
                        <td>{n_amr}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Footer
    html_content += """
        <footer>
            <p>Generated by COMPASS Pipeline - ST-Prophage Specificity Analysis</p>
            <p>🤖 Analysis performed with Claude Code</p>
        </footer>
    </div>
</body>
</html>
"""

    # Write report
    with open(output_file, 'w') as f:
        f.write(html_content)

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

def load_mlst_data_from_dirs(base_dir):
    """Load MLST data from year directories"""
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

def main():
    """Main entry point"""
    # Define paths - update to match actual Beocat structure
    base_dir = Path.home() / 'compass_kansas_results'
    output_dir = base_dir / 'publication_analysis' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("🧬 ST-PROPHAGE SPECIFICITY ANALYSIS")
    print("=" * 70)
    print(f"\n📂 Base directory: {base_dir}")

    # Load metadata from year directories
    metadata = load_metadata_files(base_dir)

    # Load MLST data from year directories
    all_sts = load_mlst_data_from_dirs(base_dir)

    if not all_sts:
        print("\n❌ Error: No MLST data found!")
        print("   Check that MLST files exist in results_kansas_YYYY/mlst/")
        return

    # Run analysis with year-based directory structure
    output_file = analyze_st_prophage_specificity_from_dirs(base_dir, all_sts, metadata)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_file}")
    print("\n🔬 Key insights:")
    print("   - High-risk ST prophage profiles identified")
    print("   - ST-prophage association matrix generated")
    print("   - Food source connections revealed")
    print("   - Specific ST-prophage pairs highlighted")
    print()

if __name__ == "__main__":
    main()
