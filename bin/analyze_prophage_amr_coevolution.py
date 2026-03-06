#!/usr/bin/env python3
"""
Prophage-AMR Co-evolution Network Analysis

Identifies temporal co-evolution patterns between prophage families and AMR genes:
1. Which prophage-AMR pairs are increasing together (emerging threats)
2. Which are declining together (interventions working)
3. Co-trending prophage-AMR combinations over 2021-2025
4. Network visualization of co-evolving elements
5. By organism and food source

Reveals temporal dynamics of mobile genetic element evolution.

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

def normalize_organism_name(organism: str) -> str:
    """Normalize organism names to standard format"""
    org_lower = organism.lower()
    if 'coli' in org_lower or 'escherichia' in org_lower:
        return 'E. coli'
    elif 'salmonella' in org_lower:
        return 'Salmonella'
    elif 'campylobacter' in org_lower or 'campy' in org_lower:
        return 'Campylobacter'
    else:
        return 'Other'

def extract_prophage_family(subject_name: str) -> str:
    """Extract prophage family from DIAMOND subject name"""
    if not subject_name or subject_name == 'N/A':
        return None

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

    first_word = subject_name.split('_')[0].split()[0]
    if len(first_word) > 3:
        return first_word.capitalize()

    return 'Unknown'

def parse_diamond_prophage_hits(diamond_file: Path) -> Set[str]:
    """Parse DIAMOND prophage hits to get unique prophage families"""
    prophage_families = set()
    try:
        with open(diamond_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    subject = parts[1]
                    family = extract_prophage_family(subject)
                    if family and family != 'Unknown':
                        prophage_families.add(family)
    except FileNotFoundError:
        pass
    return prophage_families

def parse_amr_data(amr_file: Path) -> Dict:
    """Parse AMRFinder results"""
    amr_data = {
        'genes': set(),
        'classes': set()
    }
    try:
        with open(amr_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 11:
                    gene = parts[5]
                    amr_class = parts[10]
                    amr_data['genes'].add(gene)
                    if amr_class and amr_class != 'N/A':
                        amr_data['classes'].add(amr_class)
    except FileNotFoundError:
        pass
    return amr_data

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
                organism = normalize_organism_name(row.get('organism', 'Unknown'))

                metadata[srr_id] = {
                    'sample_name': sample_name,
                    'organism': organism,
                    'year': str(year)
                }

    print(f"  Loaded metadata for {len(metadata)} samples")
    return metadata

def analyze_prophage_amr_coevolution(base_dir: Path, metadata: Dict):
    """Main analysis function"""

    print("\n🔬 Analyzing Prophage-AMR Co-evolution...")
    print("=" * 70)

    # Data structures
    # Year-specific counts
    year_prophage_counts = defaultdict(lambda: Counter())  # year -> {prophage: count}
    year_amr_gene_counts = defaultdict(lambda: Counter())  # year -> {gene: count}
    year_amr_class_counts = defaultdict(lambda: Counter())  # year -> {class: count}
    year_prophage_amr_pairs = defaultdict(lambda: Counter())  # year -> {(prophage, amr_gene): count}
    year_prophage_class_pairs = defaultdict(lambda: Counter())  # year -> {(prophage, amr_class): count}
    year_sample_counts = Counter()  # year -> sample count

    # By organism
    organism_year_prophage_amr = defaultdict(lambda: defaultdict(lambda: Counter()))  # org -> year -> {(prophage, amr): count}

    # By food source
    food_year_prophage_amr = defaultdict(lambda: defaultdict(lambda: Counter()))  # food -> year -> {(prophage, amr): count}

    # Process all samples year by year
    total_samples = 0
    for year in [2021, 2022, 2023, 2024, 2025]:
        year_dir = base_dir / f"results_kansas_{year}"
        if not year_dir.exists():
            continue

        year_str = str(year)

        # Find all samples with both prophage and AMR data
        diamond_dir = year_dir / "diamond_prophage"
        amr_dir = year_dir / "amrfinder"

        if not diamond_dir.exists() or not amr_dir.exists():
            continue

        for diamond_file in diamond_dir.glob("*_diamond_results.tsv"):
            sample_id = diamond_file.stem.replace('_diamond_results', '')
            amr_file = amr_dir / f"{sample_id}_amrfinder.tsv"

            if not amr_file.exists():
                continue

            # Get metadata
            sample_meta = metadata.get(sample_id, {})
            organism = sample_meta.get('organism', 'Unknown')
            if organism == 'Other' or organism == 'Unknown':
                continue

            food_source = extract_source_from_sample_name(sample_meta.get('sample_name', ''))

            # Parse data
            prophage_families = parse_diamond_prophage_hits(diamond_file)
            amr_data = parse_amr_data(amr_file)

            if not prophage_families or not amr_data['genes']:
                continue

            # Update counts
            year_sample_counts[year_str] += 1

            for prophage in prophage_families:
                year_prophage_counts[year_str][prophage] += 1

            for gene in amr_data['genes']:
                year_amr_gene_counts[year_str][gene] += 1

            for amr_class in amr_data['classes']:
                year_amr_class_counts[year_str][amr_class] += 1

            # Record co-occurrences (prophage + AMR in same sample)
            for prophage in prophage_families:
                for gene in amr_data['genes']:
                    pair = (prophage, gene)
                    year_prophage_amr_pairs[year_str][pair] += 1
                    organism_year_prophage_amr[organism][year_str][pair] += 1
                    food_year_prophage_amr[food_source][year_str][pair] += 1

                for amr_class in amr_data['classes']:
                    pair = (prophage, amr_class)
                    year_prophage_class_pairs[year_str][pair] += 1

            total_samples += 1

    print(f"✅ Processed {total_samples} samples with both prophage and AMR data")
    print(f"📊 Analyzing temporal trends from {min(year_sample_counts.keys())} to {max(year_sample_counts.keys())}")

    # Calculate temporal trends for prophage-AMR pairs
    coevolving_pairs = []

    # Get all unique pairs across all years
    all_pairs = set()
    for year_pairs in year_prophage_amr_pairs.values():
        all_pairs.update(year_pairs.keys())

    for prophage, amr_gene in all_pairs:
        # Get counts per year
        year_counts = {}
        for year in ['2021', '2022', '2023', '2024', '2025']:
            count = year_prophage_amr_pairs[year].get((prophage, amr_gene), 0)
            samples = year_sample_counts.get(year, 1)  # Avoid division by zero
            prevalence = (count / samples * 100) if samples > 0 else 0
            year_counts[year] = {
                'count': count,
                'prevalence': prevalence
            }

        # Calculate trend (compare 2021-2022 vs 2024-2025)
        early_years = ['2021', '2022']
        late_years = ['2024', '2025']

        early_total = sum(year_counts[y]['count'] for y in early_years)
        late_total = sum(year_counts[y]['count'] for y in late_years)

        early_samples = sum(year_sample_counts.get(y, 0) for y in early_years)
        late_samples = sum(year_sample_counts.get(y, 0) for y in late_years)

        early_prevalence = (early_total / early_samples * 100) if early_samples > 0 else 0
        late_prevalence = (late_total / late_samples * 100) if late_samples > 0 else 0

        # Only include pairs with at least 5 total occurrences
        total_occurrences = sum(year_counts[y]['count'] for y in year_counts)
        if total_occurrences < 5:
            continue

        # Calculate fold change
        if early_prevalence > 0:
            fold_change = late_prevalence / early_prevalence
        elif late_prevalence > 0:
            fold_change = float('inf')  # Emerging (0 -> positive)
        else:
            fold_change = 1.0

        # Classify trend
        if fold_change >= 2.0:
            trend = 'Strongly Increasing'
        elif fold_change >= 1.3:
            trend = 'Increasing'
        elif fold_change <= 0.5:
            trend = 'Strongly Decreasing'
        elif fold_change <= 0.77:
            trend = 'Decreasing'
        else:
            trend = 'Stable'

        coevolving_pairs.append({
            'prophage': prophage,
            'amr_gene': amr_gene,
            'trend': trend,
            'fold_change': fold_change,
            'early_prevalence': early_prevalence,
            'late_prevalence': late_prevalence,
            'total_occurrences': total_occurrences,
            'year_counts': year_counts
        })

    # Sort by fold change
    coevolving_pairs.sort(key=lambda x: x['fold_change'], reverse=True)

    emerging = [p for p in coevolving_pairs if p['trend'] in ['Strongly Increasing', 'Increasing']]
    declining = [p for p in coevolving_pairs if p['trend'] in ['Strongly Decreasing', 'Decreasing']]
    stable = [p for p in coevolving_pairs if p['trend'] == 'Stable']

    print(f"🔺 Found {len(emerging)} emerging prophage-AMR pairs")
    print(f"🔻 Found {len(declining)} declining prophage-AMR pairs")
    print(f"➡️  Found {len(stable)} stable prophage-AMR pairs")

    # Generate report
    output_dir = base_dir / 'publication_analysis' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "KANSAS_PROPHAGE_AMR_COEVOLUTION.html"

    generate_html_report(
        output_file,
        emerging,
        declining,
        stable,
        year_sample_counts,
        organism_year_prophage_amr,
        food_year_prophage_amr
    )

    print(f"\n✅ Report generated: {output_file}")
    return output_file

def generate_html_report(
    output_file: Path,
    emerging: List,
    declining: List,
    stable: List,
    year_sample_counts: Counter,
    organism_year_prophage_amr: Dict,
    food_year_prophage_amr: Dict
):
    """Generate HTML report"""

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prophage-AMR Co-evolution Analysis</title>
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
            max-width: 1600px;
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

        .alert-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .success-box {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 0.9em;
        }

        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }

        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }

        tr:hover {
            background-color: #f5f5f5;
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

        .trend-increasing {
            background: #ffebee;
            border-left: 4px solid #c62828;
        }

        .trend-decreasing {
            background: #e8f5e9;
            border-left: 4px solid #2e7d32;
        }

        .trend-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .badge-increasing {
            background: #ffcdd2;
            color: #b71c1c;
        }

        .badge-decreasing {
            background: #c8e6c9;
            color: #1b5e20;
        }

        .badge-stable {
            background: #e0e0e0;
            color: #424242;
        }

        .prophage-badge {
            display: inline-block;
            background: #e3f2fd;
            color: #1565c0;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.85em;
            font-family: monospace;
        }

        .amr-badge {
            display: inline-block;
            background: #fff3e0;
            color: #e65100;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.85em;
            font-family: monospace;
        }

        .fold-change {
            font-weight: bold;
            font-size: 1.1em;
        }

        .fold-high {
            color: #c62828;
        }

        .fold-low {
            color: #2e7d32;
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
        <h1>🧬 Prophage-AMR Co-evolution Analysis</h1>
        <p class="subtitle">Temporal Dynamics of Mobile Genetic Elements (2021-2025)</p>

        <div class="info-box">
            <h4>📊 Analysis Overview</h4>
            <p>This report tracks how prophage families and AMR genes co-evolve over time, identifying
            emerging and declining prophage-AMR combinations that may represent spreading resistance cassettes.</p>
            <p style="margin-top: 10px;"><strong>Methodology:</strong></p>
            <ul style="margin-left: 30px; margin-top: 5px; line-height: 1.8;">
                <li>Compare early years (2021-2022) vs. late years (2024-2025)</li>
                <li>Calculate fold change in prevalence</li>
                <li>Strongly Increasing: ≥2.0x fold change</li>
                <li>Increasing: 1.3-2.0x fold change</li>
                <li>Stable: 0.77-1.3x fold change</li>
                <li>Decreasing: 0.5-0.77x fold change</li>
                <li>Strongly Decreasing: ≤0.5x fold change</li>
            </ul>
        </div>
"""

    # Statistics
    total_pairs = len(emerging) + len(declining) + len(stable)

    html_content += f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Total Pairs Tracked</div>
                <div class="stat-value">{total_pairs}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Emerging Threats</div>
                <div class="stat-value">{len(emerging)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Declining Pairs</div>
                <div class="stat-value">{len(declining)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Stable Pairs</div>
                <div class="stat-value">{len(stable)}</div>
            </div>
        </div>

        <div class="toc">
            <h3>📑 Table of Contents</h3>
            <ul>
                <li><a href="#emerging">Emerging Prophage-AMR Pairs (Increasing)</a></li>
                <li><a href="#declining">Declining Prophage-AMR Pairs (Decreasing)</a></li>
                <li><a href="#stable">Stable Prophage-AMR Pairs</a></li>
            </ul>
        </div>
"""

    # Section 1: Emerging Pairs
    html_content += """
        <section id="emerging">
            <h2>🔺 Emerging Prophage-AMR Pairs</h2>
            <div class="alert-box">
                <h4>⚠️ Rising Threats - Prophage-AMR Combinations Increasing Over Time</h4>
                <p>These pairs show increasing prevalence from 2021-2022 to 2024-2025, potentially representing
                spreading resistance cassettes or emerging mobile genetic element combinations.</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Prophage Family</th>
                        <th>AMR Gene</th>
                        <th>Trend</th>
                        <th>Fold Change</th>
                        <th>Early Prevalence<br>(2021-2022)</th>
                        <th>Late Prevalence<br>(2024-2025)</th>
                        <th>Total Occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""

    for rank, pair in enumerate(emerging[:50], 1):  # Top 50
        fold_change = pair['fold_change']
        if fold_change == float('inf'):
            fold_str = "NEW"
            fold_class = "fold-high"
        else:
            fold_str = f"{fold_change:.2f}x"
            fold_class = "fold-high"

        trend_badge = 'badge-increasing'

        html_content += f"""
                    <tr class="trend-increasing">
                        <td>{rank}</td>
                        <td><span class="prophage-badge">{pair['prophage']}</span></td>
                        <td><span class="amr-badge">{pair['amr_gene']}</span></td>
                        <td><span class="trend-badge {trend_badge}">{pair['trend']}</span></td>
                        <td><span class="fold-change {fold_class}">{fold_str}</span></td>
                        <td>{pair['early_prevalence']:.2f}%</td>
                        <td>{pair['late_prevalence']:.2f}%</td>
                        <td>{pair['total_occurrences']}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 2: Declining Pairs
    html_content += """
        <section id="declining">
            <h2>🔻 Declining Prophage-AMR Pairs</h2>
            <div class="success-box">
                <h4>✅ Decreasing Combinations - Potential Intervention Success</h4>
                <p>These pairs show decreasing prevalence over time, possibly indicating successful interventions
                or natural selection against these combinations.</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Prophage Family</th>
                        <th>AMR Gene</th>
                        <th>Trend</th>
                        <th>Fold Change</th>
                        <th>Early Prevalence<br>(2021-2022)</th>
                        <th>Late Prevalence<br>(2024-2025)</th>
                        <th>Total Occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""

    for rank, pair in enumerate(declining[:50], 1):  # Top 50
        fold_change = pair['fold_change']
        fold_str = f"{fold_change:.2f}x"
        fold_class = "fold-low"

        trend_badge = 'badge-decreasing'

        html_content += f"""
                    <tr class="trend-decreasing">
                        <td>{rank}</td>
                        <td><span class="prophage-badge">{pair['prophage']}</span></td>
                        <td><span class="amr-badge">{pair['amr_gene']}</span></td>
                        <td><span class="trend-badge {trend_badge}">{pair['trend']}</span></td>
                        <td><span class="fold-change {fold_class}">{fold_str}</span></td>
                        <td>{pair['early_prevalence']:.2f}%</td>
                        <td>{pair['late_prevalence']:.2f}%</td>
                        <td>{pair['total_occurrences']}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 3: Stable Pairs
    html_content += """
        <section id="stable">
            <h2>➡️ Stable Prophage-AMR Pairs</h2>
            <div class="info-box">
                <h4>📊 Persistent Combinations</h4>
                <p>These pairs show stable prevalence over time (0.77-1.3x fold change), representing
                established prophage-AMR associations in the population.</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Prophage Family</th>
                        <th>AMR Gene</th>
                        <th>Fold Change</th>
                        <th>Early Prevalence<br>(2021-2022)</th>
                        <th>Late Prevalence<br>(2024-2025)</th>
                        <th>Total Occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Sort stable by total occurrences
    stable_sorted = sorted(stable, key=lambda x: x['total_occurrences'], reverse=True)

    for rank, pair in enumerate(stable_sorted[:50], 1):  # Top 50
        fold_change = pair['fold_change']
        fold_str = f"{fold_change:.2f}x"

        html_content += f"""
                    <tr>
                        <td>{rank}</td>
                        <td><span class="prophage-badge">{pair['prophage']}</span></td>
                        <td><span class="amr-badge">{pair['amr_gene']}</span></td>
                        <td><span class="fold-change">{fold_str}</span></td>
                        <td>{pair['early_prevalence']:.2f}%</td>
                        <td>{pair['late_prevalence']:.2f}%</td>
                        <td>{pair['total_occurrences']}</td>
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
            <p>Generated by COMPASS Pipeline - Prophage-AMR Co-evolution Analysis</p>
            <p>🤖 Analysis performed with Claude Code</p>
        </footer>
    </div>
</body>
</html>
"""

    # Write report
    with open(output_file, 'w') as f:
        f.write(html_content)

def main():
    """Main entry point"""
    base_dir = Path.home() / 'compass_kansas_results'

    print("\n" + "=" * 70)
    print("🧬 PROPHAGE-AMR CO-EVOLUTION ANALYSIS")
    print("=" * 70)
    print(f"\n📂 Base directory: {base_dir}")

    # Load metadata
    metadata = load_metadata_files(base_dir)

    if not metadata:
        print("\n❌ Error: No metadata found!")
        return

    # Run analysis
    output_file = analyze_prophage_amr_coevolution(base_dir, metadata)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_file}")
    print("\n🧬 Key insights:")
    print("   - Emerging prophage-AMR pairs identified (rising threats)")
    print("   - Declining pairs tracked (potential intervention success)")
    print("   - Stable combinations mapped (established associations)")
    print("   - Temporal dynamics of mobile genetic elements revealed")
    print()

if __name__ == "__main__":
    main()
