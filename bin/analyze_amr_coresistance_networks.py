#!/usr/bin/env python3
"""
AMR Co-resistance Network Analysis

Identifies patterns of antimicrobial resistance gene co-occurrence to reveal:
1. Which AMR genes appear together in the same samples
2. Resistance gene clusters (genes that travel together)
3. Core vs. accessory resistance profiles
4. Co-resistance patterns by food source and organism
5. Temporal trends in multi-drug resistance

Author: Claude Code
Date: 2025-01-13
"""

import re
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set
from itertools import combinations

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

def parse_amr_data(amr_file: Path) -> Dict:
    """Parse AMRFinder results"""
    amr_data = {
        'genes': [],
        'classes': [],
        'gene_class_map': {}
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
                        amr_data['gene_class_map'][gene] = amr_class
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

def analyze_amr_coresistance(base_dir: Path, metadata: Dict):
    """Main analysis function"""

    print("\n🔬 Analyzing AMR Co-resistance Networks...")
    print("=" * 70)

    # Data structures
    gene_cooccurrence = defaultdict(lambda: Counter())  # gene1 -> {gene2: count}
    class_cooccurrence = defaultdict(lambda: Counter())  # class1 -> {class2: count}
    sample_resistance_profiles = []  # List of sample AMR profiles
    gene_frequency = Counter()  # How often each gene appears
    class_frequency = Counter()  # How often each class appears
    organism_gene_cooccur = defaultdict(lambda: defaultdict(lambda: Counter()))  # org -> gene1 -> {gene2: count}
    food_gene_cooccur = defaultdict(lambda: defaultdict(lambda: Counter()))  # food -> gene1 -> {gene2: count}
    year_gene_cooccur = defaultdict(lambda: defaultdict(lambda: Counter()))  # year -> gene1 -> {gene2: count}
    mdr_samples = []  # Multi-drug resistant samples (≥3 classes)

    # Process all samples
    total_samples = 0
    for year in [2021, 2022, 2023, 2024, 2025]:
        year_dir = base_dir / f"results_kansas_{year}"
        if not year_dir.exists():
            continue

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
            year_str = sample_meta.get('year', str(year))

            # Parse AMR data
            amr_data = parse_amr_data(amr_file)
            genes = list(set(amr_data['genes']))  # Unique genes
            classes = list(set(amr_data['classes']))  # Unique classes

            if len(genes) == 0:
                continue

            # Record sample profile
            sample_resistance_profiles.append({
                'sample_id': sample_id,
                'organism': organism,
                'food_source': food_source,
                'year': year_str,
                'n_genes': len(genes),
                'n_classes': len(classes),
                'genes': genes,
                'classes': classes
            })

            # Track MDR
            if len(classes) >= 3:
                mdr_samples.append({
                    'sample_id': sample_id,
                    'organism': organism,
                    'food_source': food_source,
                    'year': year_str,
                    'n_classes': len(classes),
                    'classes': ', '.join(sorted(classes))
                })

            # Update gene/class frequencies
            for gene in genes:
                gene_frequency[gene] += 1
            for amr_class in classes:
                class_frequency[amr_class] += 1

            # Gene co-occurrence (all pairs)
            for gene1, gene2 in combinations(sorted(genes), 2):
                gene_cooccurrence[gene1][gene2] += 1
                gene_cooccurrence[gene2][gene1] += 1  # Symmetric

                # By organism
                organism_gene_cooccur[organism][gene1][gene2] += 1
                organism_gene_cooccur[organism][gene2][gene1] += 1

                # By food
                food_gene_cooccur[food_source][gene1][gene2] += 1
                food_gene_cooccur[food_source][gene2][gene1] += 1

                # By year
                year_gene_cooccur[year_str][gene1][gene2] += 1
                year_gene_cooccur[year_str][gene2][gene1] += 1

            # Class co-occurrence
            for class1, class2 in combinations(sorted(classes), 2):
                class_cooccurrence[class1][class2] += 1
                class_cooccurrence[class2][class1] += 1

            total_samples += 1

    print(f"✅ Processed {total_samples} samples with AMR data")
    print(f"📊 Found {len(gene_frequency)} unique AMR genes")
    print(f"📊 Found {len(class_frequency)} unique AMR classes")
    print(f"⚠️  Identified {len(mdr_samples)} MDR samples (≥3 classes)")

    # Identify strong co-resistance pairs
    strong_pairs_genes = []
    for gene1, gene2_counts in gene_cooccurrence.items():
        gene1_freq = gene_frequency[gene1]
        for gene2, cooccur_count in gene2_counts.items():
            if gene1 < gene2:  # Avoid duplicates
                gene2_freq = gene_frequency[gene2]
                # Jaccard index: intersection / union
                union = gene1_freq + gene2_freq - cooccur_count
                jaccard = cooccur_count / union if union > 0 else 0

                if cooccur_count >= 5:  # At least 5 co-occurrences
                    strong_pairs_genes.append({
                        'gene1': gene1,
                        'gene2': gene2,
                        'cooccur': cooccur_count,
                        'gene1_freq': gene1_freq,
                        'gene2_freq': gene2_freq,
                        'jaccard': jaccard
                    })

    strong_pairs_genes.sort(key=lambda x: x['jaccard'], reverse=True)

    print(f"🔗 Found {len(strong_pairs_genes)} strong gene co-resistance pairs")

    # Generate report
    output_dir = base_dir / 'publication_analysis' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "KANSAS_AMR_CORESISTANCE_NETWORKS.html"

    generate_html_report(
        output_file,
        gene_cooccurrence,
        class_cooccurrence,
        gene_frequency,
        class_frequency,
        strong_pairs_genes,
        sample_resistance_profiles,
        mdr_samples,
        organism_gene_cooccur,
        food_gene_cooccur,
        year_gene_cooccur
    )

    print(f"\n✅ Report generated: {output_file}")
    return output_file

def generate_html_report(
    output_file: Path,
    gene_cooccurrence: Dict,
    class_cooccurrence: Dict,
    gene_frequency: Counter,
    class_frequency: Counter,
    strong_pairs_genes: List,
    sample_resistance_profiles: List,
    mdr_samples: List,
    organism_gene_cooccur: Dict,
    food_gene_cooccur: Dict,
    year_gene_cooccur: Dict
):
    """Generate HTML report"""

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMR Co-resistance Network Analysis</title>
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

        .gene-badge {
            display: inline-block;
            background: #e3f2fd;
            color: #1565c0;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.85em;
            font-family: monospace;
        }

        .class-badge {
            display: inline-block;
            background: #fff3e0;
            color: #e65100;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .jaccard-high {
            background: #c8e6c9;
            font-weight: bold;
        }

        .jaccard-med {
            background: #fff9c4;
        }

        .jaccard-low {
            background: #ffecb3;
        }

        .mdr-warning {
            background: #ffebee;
            color: #c62828;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
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
        <h1>🔗 AMR Co-resistance Network Analysis</h1>
        <p class="subtitle">Identifying Patterns of Multi-Drug Resistance Gene Co-occurrence</p>

        <div class="info-box">
            <h4>📊 Analysis Overview</h4>
            <p>This report analyzes which antimicrobial resistance genes appear together in the same samples,
            revealing resistance gene clusters, co-resistance patterns, and the architecture of multi-drug resistance.</p>
        </div>
"""

    # Statistics
    total_samples = len(sample_resistance_profiles)
    total_genes = len(gene_frequency)
    total_classes = len(class_frequency)
    n_mdr = len(mdr_samples)
    mdr_pct = (n_mdr / total_samples * 100) if total_samples > 0 else 0

    html_content += f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Samples Analyzed</div>
                <div class="stat-value">{total_samples}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Unique AMR Genes</div>
                <div class="stat-value">{total_genes}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">MDR Samples</div>
                <div class="stat-value">{n_mdr}</div>
                <div class="stat-label">{mdr_pct:.1f}% of samples</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Strong Gene Pairs</div>
                <div class="stat-value">{len(strong_pairs_genes)}</div>
            </div>
        </div>

        <div class="toc">
            <h3>📑 Table of Contents</h3>
            <ul>
                <li><a href="#gene-frequency">AMR Gene Frequency</a></li>
                <li><a href="#strong-pairs">Strong Co-resistance Pairs</a></li>
                <li><a href="#class-cooccurrence">AMR Class Co-occurrence</a></li>
                <li><a href="#mdr-samples">Multi-Drug Resistant Samples</a></li>
                <li><a href="#organism-patterns">Co-resistance by Organism</a></li>
                <li><a href="#food-patterns">Co-resistance by Food Source</a></li>
            </ul>
        </div>
"""

    # Section 1: Gene Frequency
    html_content += """
        <section id="gene-frequency">
            <h2>📊 AMR Gene Frequency</h2>
            <div class="info-box">
                <h4>Most Common Resistance Genes</h4>
                <p>Core vs. accessory resistance - genes found frequently vs. rarely</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Gene</th>
                        <th>Samples</th>
                        <th>Prevalence</th>
                    </tr>
                </thead>
                <tbody>
"""

    for rank, (gene, count) in enumerate(gene_frequency.most_common(30), 1):
        prevalence = (count / total_samples * 100) if total_samples > 0 else 0
        html_content += f"""
                    <tr>
                        <td>{rank}</td>
                        <td><span class="gene-badge">{gene}</span></td>
                        <td>{count}</td>
                        <td>{prevalence:.1f}%</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 2: Strong Co-resistance Pairs
    html_content += """
        <section id="strong-pairs">
            <h2>🔗 Strong Co-resistance Gene Pairs</h2>
            <div class="alert-box">
                <h4>⚠️ Genes That Travel Together</h4>
                <p>High Jaccard index (>0.5) indicates genes frequently found together, likely on same mobile element.
                These represent resistance cassettes spreading as units.</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Gene 1</th>
                        <th>Gene 2</th>
                        <th>Co-occurrences</th>
                        <th>Gene 1 Freq</th>
                        <th>Gene 2 Freq</th>
                        <th>Jaccard Index</th>
                    </tr>
                </thead>
                <tbody>
"""

    for pair in strong_pairs_genes[:50]:  # Top 50 pairs
        jaccard = pair['jaccard']
        if jaccard >= 0.5:
            row_class = 'jaccard-high'
        elif jaccard >= 0.3:
            row_class = 'jaccard-med'
        else:
            row_class = 'jaccard-low'

        html_content += f"""
                    <tr class="{row_class}">
                        <td><span class="gene-badge">{pair['gene1']}</span></td>
                        <td><span class="gene-badge">{pair['gene2']}</span></td>
                        <td>{pair['cooccur']}</td>
                        <td>{pair['gene1_freq']}</td>
                        <td>{pair['gene2_freq']}</td>
                        <td>{jaccard:.3f}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 3: Class Co-occurrence
    html_content += """
        <section id="class-cooccurrence">
            <h2>💊 AMR Class Co-occurrence</h2>
            <div class="info-box">
                <h4>Multi-Class Resistance Patterns</h4>
                <p>Which resistance classes appear together?</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Class 1</th>
                        <th>Class 2</th>
                        <th>Co-occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Get top class pairs
    class_pairs = []
    for class1, class2_counts in class_cooccurrence.items():
        for class2, count in class2_counts.items():
            if class1 < class2:  # Avoid duplicates
                class_pairs.append((class1, class2, count))

    class_pairs.sort(key=lambda x: x[2], reverse=True)

    for class1, class2, count in class_pairs[:30]:
        html_content += f"""
                    <tr>
                        <td><span class="class-badge">{class1}</span></td>
                        <td><span class="class-badge">{class2}</span></td>
                        <td>{count}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 4: MDR Samples
    html_content += """
        <section id="mdr-samples">
            <h2>⚠️ Multi-Drug Resistant Samples</h2>
            <div class="alert-box">
                <h4>Samples with ≥3 Resistance Classes</h4>
                <p>High-priority samples for public health surveillance</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Sample ID</th>
                        <th>Organism</th>
                        <th>Food Source</th>
                        <th>Year</th>
                        <th>Classes</th>
                        <th>Resistance Profile</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Sort by number of classes
    mdr_sorted = sorted(mdr_samples, key=lambda x: x['n_classes'], reverse=True)

    for sample in mdr_sorted[:100]:  # Top 100 MDR samples
        html_content += f"""
                    <tr>
                        <td>{sample['sample_id']}</td>
                        <td>{sample['organism']}</td>
                        <td>{sample['food_source']}</td>
                        <td>{sample['year']}</td>
                        <td><span class="mdr-warning">{sample['n_classes']} classes</span></td>
                        <td>{sample['classes']}</td>
                    </tr>
"""

    html_content += """
                </tbody>
            </table>
        </section>
"""

    # Section 5: Organism Patterns
    html_content += """
        <section id="organism-patterns">
            <h2>🦠 Co-resistance Patterns by Organism</h2>
            <div class="info-box">
                <h4>Species-Specific Co-resistance</h4>
                <p>Top gene pairs for each organism</p>
            </div>
"""

    for organism in ['E. coli', 'Salmonella', 'Campylobacter']:
        if organism not in organism_gene_cooccur:
            continue

        html_content += f"""
            <h3>{organism}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Gene 1</th>
                        <th>Gene 2</th>
                        <th>Co-occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Get top pairs for this organism
        org_pairs = []
        for gene1, gene2_counts in organism_gene_cooccur[organism].items():
            for gene2, count in gene2_counts.items():
                if gene1 < gene2 and count >= 3:
                    org_pairs.append((gene1, gene2, count))

        org_pairs.sort(key=lambda x: x[2], reverse=True)

        for gene1, gene2, count in org_pairs[:20]:
            html_content += f"""
                    <tr>
                        <td><span class="gene-badge">{gene1}</span></td>
                        <td><span class="gene-badge">{gene2}</span></td>
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

    # Section 6: Food Patterns
    html_content += """
        <section id="food-patterns">
            <h2>🍗 Co-resistance Patterns by Food Source</h2>
            <div class="info-box">
                <h4>Food-Specific Resistance Cassettes</h4>
                <p>Top gene pairs in major food sources</p>
            </div>
"""

    # Get top food sources
    food_counts = Counter()
    for profile in sample_resistance_profiles:
        food_counts[profile['food_source']] += 1

    top_foods = [f for f, _ in food_counts.most_common(5)]

    for food in top_foods:
        if food not in food_gene_cooccur:
            continue

        html_content += f"""
            <h3>{food}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Gene 1</th>
                        <th>Gene 2</th>
                        <th>Co-occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Get top pairs for this food
        food_pairs = []
        for gene1, gene2_counts in food_gene_cooccur[food].items():
            for gene2, count in gene2_counts.items():
                if gene1 < gene2 and count >= 3:
                    food_pairs.append((gene1, gene2, count))

        food_pairs.sort(key=lambda x: x[2], reverse=True)

        for gene1, gene2, count in food_pairs[:15]:
            html_content += f"""
                    <tr>
                        <td><span class="gene-badge">{gene1}</span></td>
                        <td><span class="gene-badge">{gene2}</span></td>
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
            <p>Generated by COMPASS Pipeline - AMR Co-resistance Network Analysis</p>
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
    print("🔗 AMR CO-RESISTANCE NETWORK ANALYSIS")
    print("=" * 70)
    print(f"\n📂 Base directory: {base_dir}")

    # Load metadata
    metadata = load_metadata_files(base_dir)

    if not metadata:
        print("\n❌ Error: No metadata found!")
        return

    # Run analysis
    output_file = analyze_amr_coresistance(base_dir, metadata)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_file}")
    print("\n🔗 Key insights:")
    print("   - Resistance gene co-occurrence patterns identified")
    print("   - Strong gene pairs (likely on same element) highlighted")
    print("   - Multi-drug resistant samples flagged")
    print("   - Organism and food-specific patterns revealed")
    print()

if __name__ == "__main__":
    main()
