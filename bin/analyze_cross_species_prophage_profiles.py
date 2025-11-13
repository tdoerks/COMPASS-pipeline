#!/usr/bin/env python3
"""
Cross-Species Prophage Profile Analysis

Compares prophage carriage across E. coli, Salmonella, and Campylobacter to identify:
1. Species-specific prophages vs. shared prophages
2. Prophage-AMR associations by species
3. Food source patterns for prophage carriage by species
4. Species-specific prophage diversity

Does NOT require MLST - focuses on organism-level differences.

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
                    if family and family != 'Unknown':
                        prophage_families[family] += 1
    except FileNotFoundError:
        pass
    return prophage_families

def parse_vibrant_results(vibrant_dir: Path, sample_id: str) -> Set[str]:
    """Parse VIBRANT results to get prophage counts"""
    prophages = set()
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

def analyze_cross_species_prophages(base_dir: Path, metadata: Dict):
    """Main analysis function"""

    print("\n🔬 Analyzing Cross-Species Prophage Profiles...")
    print("=" * 70)

    # Data structures
    organism_prophage_matrix = defaultdict(lambda: Counter())  # organism -> {prophage: count}
    organism_data = defaultdict(lambda: {
        'n_samples': 0,
        'n_prophages_total': 0,
        'prophage_families': Counter(),
        'amr_classes': Counter(),
        'amr_genes': Counter(),
        'food_sources': Counter(),
        'years': Counter(),
        'prophage_diversity': set()
    })
    prophage_organism_matrix = defaultdict(lambda: Counter())  # prophage -> {organism: count}
    organism_food_prophage = defaultdict(lambda: defaultdict(lambda: Counter()))  # organism -> food -> {prophage: count}
    organism_prophage_amr = defaultdict(lambda: defaultdict(lambda: Counter()))  # organism -> prophage -> {amr: count}
    prophage_food_organism = defaultdict(lambda: defaultdict(lambda: Counter()))  # prophage -> food -> {organism: count}

    # Process all samples from all years
    total_samples = 0
    for year in [2021, 2022, 2023, 2024, 2025]:
        year_dir = base_dir / f"results_kansas_{year}"
        if not year_dir.exists():
            continue

        # Find all samples in this year
        diamond_dir = year_dir / "diamond_prophage"
        if not diamond_dir.exists():
            continue

        for diamond_file in diamond_dir.glob("*_diamond_results.tsv"):
            sample_id = diamond_file.stem.replace('_diamond_results', '')

            # Get metadata
            sample_meta = metadata.get(sample_id, {})
            organism = sample_meta.get('organism', 'Unknown')
            if organism == 'Other' or organism == 'Unknown':
                continue

            food_source = extract_source_from_sample_name(sample_meta.get('sample_name', ''))
            year_str = sample_meta.get('year', str(year))

            # Get prophage data
            prophage_families = parse_diamond_prophage_hits(diamond_file)

            # Get VIBRANT data
            vibrant_dir = year_dir / "vibrant" / f"VIBRANT_{sample_id}"
            vibrant_prophages = parse_vibrant_results(vibrant_dir, sample_id)

            # Get AMR data
            amr_file = year_dir / "amrfinder" / f"{sample_id}_amrfinder.tsv"
            amr_data = parse_amr_data(amr_file)

            # Update organism data
            organism_data[organism]['n_samples'] += 1
            organism_data[organism]['n_prophages_total'] += sum(prophage_families.values())
            organism_data[organism]['food_sources'][food_source] += 1
            organism_data[organism]['years'][year_str] += 1
            organism_data[organism]['prophage_diversity'].update(prophage_families.keys())

            for gene in amr_data['genes']:
                organism_data[organism]['amr_genes'][gene] += 1
            for amr_class in amr_data['classes']:
                organism_data[organism]['amr_classes'][amr_class] += 1

            # Update prophage associations
            for prophage, count in prophage_families.items():
                organism_prophage_matrix[organism][prophage] += count
                organism_data[organism]['prophage_families'][prophage] += count
                prophage_organism_matrix[prophage][organism] += count
                organism_food_prophage[organism][food_source][prophage] += count
                prophage_food_organism[prophage][food_source][organism] += count

                # Link to AMR
                for amr_class in amr_data['classes']:
                    organism_prophage_amr[organism][prophage][amr_class] += 1

            total_samples += 1

    print(f"✅ Processed {total_samples} samples with prophage data")
    print(f"📊 Found {len(organism_data)} organisms:")
    for org, data in organism_data.items():
        print(f"   - {org}: {data['n_samples']} samples, {len(data['prophage_diversity'])} unique prophages")

    # Generate report
    output_dir = base_dir / 'publication_analysis' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "KANSAS_CROSS_SPECIES_PROPHAGE_PROFILES.html"

    generate_html_report(
        output_file,
        organism_prophage_matrix,
        organism_data,
        prophage_organism_matrix,
        organism_food_prophage,
        organism_prophage_amr,
        prophage_food_organism
    )

    print(f"\n✅ Report generated: {output_file}")
    return output_file

def generate_html_report(
    output_file: Path,
    organism_prophage_matrix: Dict,
    organism_data: Dict,
    prophage_organism_matrix: Dict,
    organism_food_prophage: Dict,
    organism_prophage_amr: Dict,
    prophage_food_organism: Dict
):
    """Generate HTML report"""

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cross-Species Prophage Profile Analysis</title>
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

        .organism-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: 600;
            margin: 2px;
        }

        .ecoli {
            background: #dbeafe;
            color: #1e40af;
        }

        .salmonella {
            background: #fef3c7;
            color: #92400e;
        }

        .campylobacter {
            background: #d1fae5;
            color: #065f46;
        }

        .prophage-badge {
            display: inline-block;
            background: #f3e5f5;
            color: #7b1fa2;
            padding: 4px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.9em;
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
        <h1>🦠 Cross-Species Prophage Profile Analysis</h1>
        <p class="subtitle">Comparing Prophage Carriage Across E. coli, Salmonella, and Campylobacter</p>

        <div class="info-box">
            <h4>📊 Analysis Overview</h4>
            <p>This report compares prophage profiles across three major foodborne pathogens to identify species-specific
            vs. shared prophages, and their associations with AMR genes and food sources.</p>
        </div>
"""

    # Statistics
    total_samples = sum(data['n_samples'] for data in organism_data.values())
    total_prophages = len(prophage_organism_matrix)

    # Count species-specific prophages
    species_specific = sum(1 for p_counts in prophage_organism_matrix.values() if len(p_counts) == 1)
    shared_prophages = total_prophages - species_specific

    html_content += f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Total Samples</div>
                <div class="stat-value">{total_samples}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Prophage Families</div>
                <div class="stat-value">{total_prophages}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Species-Specific</div>
                <div class="stat-value">{species_specific}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Shared Prophages</div>
                <div class="stat-value">{shared_prophages}</div>
            </div>
        </div>

        <div class="toc">
            <h3>📑 Table of Contents</h3>
            <ul>
                <li><a href="#organism-overview">Organism Overview</a></li>
                <li><a href="#organism-prophage-matrix">Organism-Prophage Matrix</a></li>
                <li><a href="#species-specific">Species-Specific Prophages</a></li>
                <li><a href="#shared-prophages">Shared Prophages</a></li>
                <li><a href="#food-patterns">Food Source Patterns</a></li>
                <li><a href="#amr-associations">AMR Associations by Species</a></li>
            </ul>
        </div>
"""

    # Section 1: Organism Overview
    html_content += """
        <section id="organism-overview">
            <h2>🧬 Organism Overview</h2>
            <div class="info-box">
                <h4>Species-Level Statistics</h4>
                <p>Prophage diversity and AMR profiles by organism</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Organism</th>
                        <th>Samples</th>
                        <th>Unique Prophages</th>
                        <th>Total Prophage Hits</th>
                        <th>Avg per Sample</th>
                        <th>AMR Classes</th>
                        <th>Top Food Sources</th>
                    </tr>
                </thead>
                <tbody>
"""

    organism_order = ['E. coli', 'Salmonella', 'Campylobacter']
    for organism in organism_order:
        if organism not in organism_data:
            continue

        data = organism_data[organism]
        n_samples = data['n_samples']
        n_unique = len(data['prophage_diversity'])
        n_total = data['n_prophages_total']
        avg_per_sample = n_total / n_samples if n_samples > 0 else 0
        n_amr_classes = len(data['amr_classes'])

        top_foods = data['food_sources'].most_common(3)
        food_str = ', '.join([f"{f} ({c})" for f, c in top_foods])

        org_class = organism.lower().replace(' ', '').replace('.', '')

        html_content += f"""
                    <tr>
                        <td><span class="organism-badge {org_class}">{organism}</span></td>
                        <td>{n_samples}</td>
                        <td>{n_unique}</td>
                        <td>{n_total}</td>
                        <td>{avg_per_sample:.1f}</td>
                        <td>{n_amr_classes}</td>
                        <td>{food_str}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 2: Organism-Prophage Matrix
    html_content += """
        <section id="organism-prophage-matrix">
            <h2>🔬 Organism-Prophage Association Matrix</h2>
            <div class="info-box">
                <h4>Top 30 Prophages Across All Species</h4>
                <p>Heat map showing distribution of prophage families across organisms</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Prophage Family</th>
                        <th>Total Hits</th>
                        <th>E. coli</th>
                        <th>Salmonella</th>
                        <th>Campylobacter</th>
                        <th>Specificity</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Get top prophages
    all_prophages_total = Counter()
    for p, orgs in prophage_organism_matrix.items():
        all_prophages_total[p] = sum(orgs.values())

    top_prophages = [p for p, _ in all_prophages_total.most_common(30)]

    for prophage in top_prophages:
        org_counts = prophage_organism_matrix[prophage]
        total = sum(org_counts.values())

        ecoli_count = org_counts.get('E. coli', 0)
        sal_count = org_counts.get('Salmonella', 0)
        campy_count = org_counts.get('Campylobacter', 0)

        # Determine specificity
        if len(org_counts) == 1:
            specificity = "Species-specific"
        else:
            max_pct = max(ecoli_count, sal_count, campy_count) / total * 100
            if max_pct >= 80:
                specificity = f"{max_pct:.0f}% dominant"
            else:
                specificity = "Shared"

        html_content += f"""
                    <tr>
                        <td><span class="prophage-badge">{prophage}</span></td>
                        <td>{total}</td>
                        <td class="heatmap-cell {'heatmap-high' if ecoli_count >= 50 else 'heatmap-med-high' if ecoli_count >= 20 else 'heatmap-med' if ecoli_count >= 5 else 'heatmap-low' if ecoli_count > 0 else 'heatmap-none'}">{ecoli_count if ecoli_count > 0 else '-'}</td>
                        <td class="heatmap-cell {'heatmap-high' if sal_count >= 50 else 'heatmap-med-high' if sal_count >= 20 else 'heatmap-med' if sal_count >= 5 else 'heatmap-low' if sal_count > 0 else 'heatmap-none'}">{sal_count if sal_count > 0 else '-'}</td>
                        <td class="heatmap-cell {'heatmap-high' if campy_count >= 50 else 'heatmap-med-high' if campy_count >= 20 else 'heatmap-med' if campy_count >= 5 else 'heatmap-low' if campy_count > 0 else 'heatmap-none'}">{campy_count if campy_count > 0 else '-'}</td>
                        <td>{specificity}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 3: Species-Specific Prophages
    html_content += """
        <section id="species-specific">
            <h2>🎯 Species-Specific Prophages</h2>
            <div class="info-box">
                <h4>Prophages Found in Only One Organism</h4>
                <p>These may represent species-specific mobile elements</p>
            </div>
"""

    for organism in organism_order:
        if organism not in organism_data:
            continue

        org_class = organism.lower().replace(' ', '').replace('.', '')

        # Find prophages only in this organism
        specific_prophages = []
        for prophage, org_counts in prophage_organism_matrix.items():
            if len(org_counts) == 1 and organism in org_counts:
                count = org_counts[organism]
                specific_prophages.append((prophage, count))

        specific_prophages.sort(key=lambda x: x[1], reverse=True)

        html_content += f"""
            <h3><span class="organism-badge {org_class}">{organism}</span> - {len(specific_prophages)} Specific Prophages</h3>
            <table>
                <thead>
                    <tr>
                        <th>Prophage Family</th>
                        <th>Hits</th>
                        <th>% of {organism} Samples</th>
                    </tr>
                </thead>
                <tbody>
"""

        n_samples = organism_data[organism]['n_samples']
        for prophage, count in specific_prophages[:20]:  # Top 20
            pct = (count / n_samples) * 100 if n_samples > 0 else 0
            html_content += f"""
                    <tr>
                        <td><span class="prophage-badge">{prophage}</span></td>
                        <td>{count}</td>
                        <td>{pct:.1f}%</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
"""

    html_content += """
        </section>
"""

    # Section 4: Shared Prophages
    html_content += """
        <section id="shared-prophages">
            <h2>🔄 Shared Prophages Across Species</h2>
            <div class="info-box">
                <h4>Prophages Found in Multiple Organisms</h4>
                <p>May represent broadly distributed mobile elements</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Prophage Family</th>
                        <th>Species Count</th>
                        <th>Total Hits</th>
                        <th>E. coli</th>
                        <th>Salmonella</th>
                        <th>Campylobacter</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Find shared prophages
    shared = []
    for prophage, org_counts in prophage_organism_matrix.items():
        if len(org_counts) >= 2:
            total = sum(org_counts.values())
            shared.append((prophage, len(org_counts), total, org_counts))

    shared.sort(key=lambda x: x[2], reverse=True)  # Sort by total hits

    for prophage, n_species, total, org_counts in shared[:30]:
        ecoli = org_counts.get('E. coli', 0)
        sal = org_counts.get('Salmonella', 0)
        campy = org_counts.get('Campylobacter', 0)

        html_content += f"""
                    <tr>
                        <td><span class="prophage-badge">{prophage}</span></td>
                        <td>{n_species}</td>
                        <td>{total}</td>
                        <td>{ecoli if ecoli > 0 else '-'}</td>
                        <td>{sal if sal > 0 else '-'}</td>
                        <td>{campy if campy > 0 else '-'}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 5: Food Patterns
    html_content += """
        <section id="food-patterns">
            <h2>🍗 Food Source Patterns by Species</h2>
            <div class="info-box">
                <h4>Organism-Food-Prophage Connections</h4>
                <p>Top prophages in each food source, by organism</p>
            </div>
"""

    for organism in organism_order:
        if organism not in organism_data:
            continue

        org_class = organism.lower().replace(' ', '').replace('.', '')

        html_content += f"""
            <h3><span class="organism-badge {org_class}">{organism}</span></h3>
            <table>
                <thead>
                    <tr>
                        <th>Food Source</th>
                        <th>Samples</th>
                        <th>Top Prophages</th>
                    </tr>
                </thead>
                <tbody>
"""

        food_data = organism_food_prophage[organism]
        for food, prophages in sorted(food_data.items(), key=lambda x: sum(x[1].values()), reverse=True)[:10]:
            n_samples = organism_data[organism]['food_sources'][food]
            top_prophages = prophages.most_common(5)
            prophage_str = ', '.join([f"{p} ({c})" for p, c in top_prophages])

            html_content += f"""
                    <tr>
                        <td>{food}</td>
                        <td>{n_samples}</td>
                        <td>{prophage_str}</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
"""

    html_content += """
        </section>
"""

    # Section 6: AMR Associations
    html_content += """
        <section id="amr-associations">
            <h2>💊 AMR-Prophage Associations by Species</h2>
            <div class="info-box">
                <h4>Which Prophages Co-occur with AMR Genes?</h4>
                <p>Top 10 prophage-AMR associations per species</p>
            </div>
"""

    for organism in organism_order:
        if organism not in organism_data:
            continue

        org_class = organism.lower().replace(' ', '').replace('.', '')

        html_content += f"""
            <h3><span class="organism-badge {org_class}">{organism}</span></h3>
            <table>
                <thead>
                    <tr>
                        <th>Prophage</th>
                        <th>AMR Class</th>
                        <th>Co-occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Get top prophage-AMR pairs for this organism
        pairs = []
        for prophage, amr_counts in organism_prophage_amr[organism].items():
            for amr_class, count in amr_counts.items():
                pairs.append((prophage, amr_class, count))

        pairs.sort(key=lambda x: x[2], reverse=True)

        for prophage, amr_class, count in pairs[:15]:
            html_content += f"""
                    <tr>
                        <td><span class="prophage-badge">{prophage}</span></td>
                        <td>{amr_class}</td>
                        <td>{count}</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
"""

    html_content += """
        </section>
"""

    # Footer
    html_content += """
        <footer>
            <p>Generated by COMPASS Pipeline - Cross-Species Prophage Profile Analysis</p>
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
    print("🦠 CROSS-SPECIES PROPHAGE PROFILE ANALYSIS")
    print("=" * 70)
    print(f"\n📂 Base directory: {base_dir}")

    # Load metadata
    metadata = load_metadata_files(base_dir)

    if not metadata:
        print("\n❌ Error: No metadata found!")
        return

    # Run analysis
    output_file = analyze_cross_species_prophages(base_dir, metadata)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_file}")
    print("\n🔬 Key insights:")
    print("   - Species-specific prophages identified")
    print("   - Shared prophages across organisms revealed")
    print("   - Food source patterns by species analyzed")
    print("   - AMR-prophage associations compared")
    print()

if __name__ == "__main__":
    main()
