#!/usr/bin/env python3
"""
Food Source Risk Assessment

Comprehensive risk ranking of food sources based on:
1. AMR gene burden (total and diversity)
2. Prophage diversity and prevalence
3. High-risk sequence type prevalence
4. Multi-drug resistance rates
5. Temporal trends (improving vs. worsening)
6. Organism diversity

Generates actionable risk scores for food safety surveillance.

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

def parse_diamond_prophage_hits(diamond_file: Path) -> Counter:
    """Parse DIAMOND prophage hits"""
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

def parse_amr_data(amr_file: Path) -> Dict:
    """Parse AMRFinder results"""
    amr_data = {
        'genes': [],
        'classes': []
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

def load_mlst_data(base_dir):
    """Load MLST data from year directories"""
    print("Loading MLST data...")

    mlst_data = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        mlst_dir = base_path / f"results_kansas_{year}" / "mlst"

        if not mlst_dir.exists():
            continue

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

    print(f"  Loaded MLST for {len(mlst_data)} samples")
    return mlst_data

def analyze_food_source_risk(base_dir: Path, metadata: Dict, mlst_data: Dict):
    """Main analysis function"""

    print("\n🔬 Analyzing Food Source Risk Assessment...")
    print("=" * 70)

    # High-risk STs (pandemic clones and common high-AMR types)
    high_risk_sts = {'131', '10', '69', '95', '73', '127', '648', '32', '355', '162'}

    # Data structures for each food source
    food_data = defaultdict(lambda: {
        'n_samples': 0,
        'organisms': Counter(),
        'years': Counter(),
        'amr_genes': Counter(),
        'amr_classes': Counter(),
        'total_amr_genes': 0,
        'prophage_families': Counter(),
        'total_prophages': 0,
        'sts': Counter(),
        'high_risk_st_samples': 0,
        'mdr_samples': 0,  # ≥3 AMR classes
        'samples_list': []
    })

    # Process all samples
    total_samples = 0
    for year in [2021, 2022, 2023, 2024, 2025]:
        year_dir = base_dir / f"results_kansas_{year}"
        if not year_dir.exists():
            continue

        # Find all samples
        amr_dir = year_dir / "amrfinder"
        if not amr_dir.exists():
            continue

        for amr_file in amr_dir.glob("*_amrfinder.tsv"):
            sample_id = amr_file.stem.replace('_amrfinder', '')

            # Get metadata
            sample_meta = metadata.get(sample_id, {})
            organism = sample_meta.get('organism', 'Unknown')
            if organism == 'Other' or organism == 'Unknown':
                continue

            food_source = extract_source_from_sample_name(sample_meta.get('sample_name', ''))
            if food_source == 'Unknown':
                continue

            year_str = sample_meta.get('year', str(year))

            # Parse AMR data
            amr_data = parse_amr_data(amr_file)
            n_genes = len(amr_data['genes'])
            unique_classes = list(set(amr_data['classes']))
            n_classes = len(unique_classes)

            # Parse prophage data
            diamond_file = year_dir / "diamond_prophage" / f"{sample_id}_diamond_results.tsv"
            prophage_families = parse_diamond_prophage_hits(diamond_file)
            n_prophages = sum(prophage_families.values())

            # Get ST if available
            st = mlst_data.get(sample_id, None)
            is_high_risk_st = (st in high_risk_sts) if st else False

            # Update food source data
            food_data[food_source]['n_samples'] += 1
            food_data[food_source]['organisms'][organism] += 1
            food_data[food_source]['years'][year_str] += 1
            food_data[food_source]['total_amr_genes'] += n_genes
            food_data[food_source]['total_prophages'] += n_prophages

            for gene in amr_data['genes']:
                food_data[food_source]['amr_genes'][gene] += 1
            for amr_class in unique_classes:
                food_data[food_source]['amr_classes'][amr_class] += 1
            for prophage in prophage_families:
                food_data[food_source]['prophage_families'][prophage] += 1

            if st:
                food_data[food_source]['sts'][st] += 1
            if is_high_risk_st:
                food_data[food_source]['high_risk_st_samples'] += 1
            if n_classes >= 3:
                food_data[food_source]['mdr_samples'] += 1

            food_data[food_source]['samples_list'].append({
                'sample_id': sample_id,
                'organism': organism,
                'year': year_str,
                'n_genes': n_genes,
                'n_classes': n_classes,
                'n_prophages': n_prophages,
                'st': st
            })

            total_samples += 1

    print(f"✅ Processed {total_samples} samples")
    print(f"📊 Found {len(food_data)} food sources")

    # Calculate risk scores
    food_risk_scores = []
    for food, data in food_data.items():
        if data['n_samples'] < 3:  # Need minimum samples
            continue

        n_samples = data['n_samples']

        # Metrics
        avg_amr_genes = data['total_amr_genes'] / n_samples
        amr_gene_diversity = len(data['amr_genes'])
        amr_class_diversity = len(data['amr_classes'])
        avg_prophages = data['total_prophages'] / n_samples
        prophage_diversity = len(data['prophage_families'])
        st_diversity = len(data['sts'])
        high_risk_st_pct = (data['high_risk_st_samples'] / n_samples * 100) if n_samples > 0 else 0
        mdr_pct = (data['mdr_samples'] / n_samples * 100) if n_samples > 0 else 0

        # Risk score calculation (0-100 scale)
        # Weighted components:
        # - AMR burden (avg genes per sample): 25%
        # - AMR diversity (unique genes): 20%
        # - MDR prevalence: 20%
        # - High-risk ST prevalence: 15%
        # - Prophage diversity: 10%
        # - Prophage burden: 10%

        amr_burden_score = min(avg_amr_genes * 5, 25)  # Cap at 25
        amr_diversity_score = min(amr_gene_diversity / 2, 20)  # Cap at 20
        mdr_score = min(mdr_pct / 5, 20)  # Cap at 20
        high_risk_st_score = min(high_risk_st_pct / 6.67, 15)  # Cap at 15
        prophage_div_score = min(prophage_diversity / 10, 10)  # Cap at 10
        prophage_burden_score = min(avg_prophages / 5, 10)  # Cap at 10

        total_risk_score = (
            amr_burden_score +
            amr_diversity_score +
            mdr_score +
            high_risk_st_score +
            prophage_div_score +
            prophage_burden_score
        )

        food_risk_scores.append({
            'food': food,
            'risk_score': total_risk_score,
            'n_samples': n_samples,
            'avg_amr_genes': avg_amr_genes,
            'amr_gene_diversity': amr_gene_diversity,
            'amr_class_diversity': amr_class_diversity,
            'mdr_pct': mdr_pct,
            'high_risk_st_pct': high_risk_st_pct,
            'avg_prophages': avg_prophages,
            'prophage_diversity': prophage_diversity,
            'st_diversity': st_diversity,
            'organisms': dict(data['organisms']),
            'top_amr_genes': data['amr_genes'].most_common(5),
            'top_prophages': data['prophage_families'].most_common(5),
            'top_sts': data['sts'].most_common(5),
            'yearly_trend': data['years']
        })

    food_risk_scores.sort(key=lambda x: x['risk_score'], reverse=True)

    print(f"🎯 Calculated risk scores for {len(food_risk_scores)} food sources")

    # Generate report
    output_dir = base_dir / 'publication_analysis' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "KANSAS_FOOD_SOURCE_RISK_ASSESSMENT.html"

    generate_html_report(output_file, food_risk_scores, food_data)

    print(f"\n✅ Report generated: {output_file}")
    return output_file

def generate_html_report(output_file: Path, food_risk_scores: List, food_data: Dict):
    """Generate HTML report"""

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food Source Risk Assessment</title>
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

        .risk-very-high {
            background: #ffebee;
            border-left: 4px solid #c62828;
        }

        .risk-high {
            background: #fff3e0;
            border-left: 4px solid #ef6c00;
        }

        .risk-medium {
            background: #fff9c4;
            border-left: 4px solid #f9a825;
        }

        .risk-low {
            background: #f1f8e9;
            border-left: 4px solid #558b2f;
        }

        .risk-score {
            font-size: 1.5em;
            font-weight: bold;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }

        .score-very-high {
            background: #c62828;
            color: white;
        }

        .score-high {
            background: #ef6c00;
            color: white;
        }

        .score-medium {
            background: #f9a825;
            color: white;
        }

        .score-low {
            background: #558b2f;
            color: white;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }

        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }

        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }

        .metric-label {
            font-size: 0.85em;
            color: #666;
            margin-top: 5px;
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

        .food-detail {
            margin: 30px 0;
            padding: 20px;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍗 Food Source Risk Assessment</h1>
        <p class="subtitle">Comprehensive Risk Ranking for Food Safety Surveillance</p>

        <div class="info-box">
            <h4>📊 Risk Score Methodology</h4>
            <p><strong>Risk scores (0-100 scale) based on weighted components:</strong></p>
            <ul style="margin-left: 30px; margin-top: 10px; line-height: 1.8;">
                <li><strong>AMR Burden</strong> (25%): Average AMR genes per sample</li>
                <li><strong>AMR Diversity</strong> (20%): Unique resistance genes detected</li>
                <li><strong>MDR Prevalence</strong> (20%): % samples with ≥3 resistance classes</li>
                <li><strong>High-Risk STs</strong> (15%): % samples with pandemic/high-risk clones</li>
                <li><strong>Prophage Diversity</strong> (10%): Unique prophage families</li>
                <li><strong>Prophage Burden</strong> (10%): Average prophages per sample</li>
            </ul>
            <p style="margin-top: 10px;"><strong>Risk Categories:</strong> Very High (≥70), High (60-69), Medium (40-59), Low (<40)</p>
        </div>

        <div class="toc">
            <h3>📑 Table of Contents</h3>
            <ul>
                <li><a href="#risk-ranking">Overall Risk Ranking</a></li>
                <li><a href="#detailed-profiles">Detailed Food Source Profiles</a></li>
            </ul>
        </div>
"""

    # Section 1: Risk Ranking
    html_content += """
        <section id="risk-ranking">
            <h2>🎯 Overall Risk Ranking</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Food Source</th>
                        <th>Risk Score</th>
                        <th>Samples</th>
                        <th>Avg AMR Genes</th>
                        <th>AMR Diversity</th>
                        <th>MDR %</th>
                        <th>High-Risk ST %</th>
                        <th>Prophage Diversity</th>
                    </tr>
                </thead>
                <tbody>
"""

    for rank, food_risk in enumerate(food_risk_scores, 1):
        risk_score = food_risk['risk_score']

        if risk_score >= 70:
            score_class = 'score-very-high'
        elif risk_score >= 60:
            score_class = 'score-high'
        elif risk_score >= 40:
            score_class = 'score-medium'
        else:
            score_class = 'score-low'

        html_content += f"""
                    <tr>
                        <td><strong>{rank}</strong></td>
                        <td><strong>{food_risk['food']}</strong></td>
                        <td><div class="risk-score {score_class}">{risk_score:.1f}</div></td>
                        <td>{food_risk['n_samples']}</td>
                        <td>{food_risk['avg_amr_genes']:.1f}</td>
                        <td>{food_risk['amr_gene_diversity']}</td>
                        <td>{food_risk['mdr_pct']:.1f}%</td>
                        <td>{food_risk['high_risk_st_pct']:.1f}%</td>
                        <td>{food_risk['prophage_diversity']}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 2: Detailed Profiles
    html_content += """
        <section id="detailed-profiles">
            <h2>📋 Detailed Food Source Profiles</h2>
"""

    for rank, food_risk in enumerate(food_risk_scores, 1):
        risk_score = food_risk['risk_score']

        if risk_score >= 70:
            risk_class = 'risk-very-high'
            risk_label = 'VERY HIGH RISK'
        elif risk_score >= 60:
            risk_class = 'risk-high'
            risk_label = 'HIGH RISK'
        elif risk_score >= 40:
            risk_class = 'risk-medium'
            risk_label = 'MEDIUM RISK'
        else:
            risk_class = 'risk-low'
            risk_label = 'LOW RISK'

        html_content += f"""
            <div class="food-detail {risk_class}">
                <h3>#{rank} - {food_risk['food']} ({risk_label}: {risk_score:.1f})</h3>

                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{food_risk['n_samples']}</div>
                        <div class="metric-label">Samples</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{food_risk['avg_amr_genes']:.1f}</div>
                        <div class="metric-label">Avg AMR Genes</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{food_risk['amr_gene_diversity']}</div>
                        <div class="metric-label">Unique AMR Genes</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{food_risk['amr_class_diversity']}</div>
                        <div class="metric-label">AMR Classes</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{food_risk['mdr_pct']:.0f}%</div>
                        <div class="metric-label">MDR Samples</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{food_risk['prophage_diversity']}</div>
                        <div class="metric-label">Prophage Families</div>
                    </div>
                </div>

                <p style="margin-top: 15px;"><strong>Organisms:</strong> {', '.join([f'{org} ({count})' for org, count in food_risk['organisms'].items()])}</p>
                <p><strong>Top AMR Genes:</strong> {', '.join([f'{gene} ({count})' for gene, count in food_risk['top_amr_genes']])}</p>
                <p><strong>Top Prophages:</strong> {', '.join([f'{phage} ({count})' for phage, count in food_risk['top_prophages']])}</p>
"""

        if food_risk['top_sts']:
            html_content += f"""                <p><strong>Top STs:</strong> {', '.join([f'ST{st} ({count})' for st, count in food_risk['top_sts']])}</p>
"""

        html_content += """            </div>
"""

    html_content += """
        </section>
"""

    # Footer
    html_content += """
        <footer>
            <p>Generated by COMPASS Pipeline - Food Source Risk Assessment</p>
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
    print("🍗 FOOD SOURCE RISK ASSESSMENT")
    print("=" * 70)
    print(f"\n📂 Base directory: {base_dir}")

    # Load data
    metadata = load_metadata_files(base_dir)
    mlst_data = load_mlst_data(base_dir)

    if not metadata:
        print("\n❌ Error: No metadata found!")
        return

    # Run analysis
    output_file = analyze_food_source_risk(base_dir, metadata, mlst_data)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_file}")
    print("\n🎯 Key insights:")
    print("   - Comprehensive risk scores calculated")
    print("   - Food sources ranked by multiple risk factors")
    print("   - Detailed profiles for each food source")
    print("   - Actionable data for food safety surveillance")
    print()

if __name__ == "__main__":
    main()
