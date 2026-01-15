#!/usr/bin/env python3
"""
True AMR-Prophage Co-location Analysis (Within Boundaries Only)

This script performs physical co-location analysis by:
1. Parsing exact prophage coordinates from VIBRANT outputs
2. Parsing exact AMR gene coordinates from AMRFinder
3. Identifying AMR genes physically located WITHIN prophage boundaries

Focus: Only reports AMR genes that are truly inside prophage regions.
This ensures we're only identifying resistance genes carried by mobile prophage elements.
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import json

# ============================================================================
# COORDINATE PARSING
# ============================================================================

def parse_vibrant_prophage_coordinates(vibrant_dir, sample_id):
    """
    Parse prophage coordinates from VIBRANT outputs

    VIBRANT creates multiple output files with coordinates:
    - VIBRANT_integrated_prophage_coordinates_*.tsv (integrated prophages)
    - VIBRANT_phages_*.fasta (contains coordinates in headers)

    Returns: list of dicts with {contig, start, end, prophage_id}
    """
    prophage_regions = []

    sample_vibrant_dir = vibrant_dir / f"{sample_id}_vibrant"
    if not sample_vibrant_dir.exists():
        return prophage_regions

    # Method 1: Parse coordinate file if it exists
    coord_files = list(sample_vibrant_dir.glob("**/VIBRANT_integrated_prophage_coordinates_*.tsv"))

    for coord_file in coord_files:
        try:
            with open(coord_file) as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    # VIBRANT format: scaffold, fragment, start, end, type
                    prophage_regions.append({
                        'contig': row.get('scaffold', row.get('contig', '')),
                        'start': int(row.get('start', row.get('protein start', 0))),
                        'end': int(row.get('end', row.get('protein end', 0))),
                        'prophage_id': f"{row.get('scaffold', '')}_{row.get('fragment', '')}",
                        'type': row.get('type', 'prophage')
                    })
        except Exception as e:
            print(f"  ⚠️  Could not parse {coord_file.name}: {e}")

    # Method 2: Parse from phages FASTA headers if coordinate file doesn't exist
    if not prophage_regions:
        phages_fasta = vibrant_dir / f"{sample_id}_phages.fna"
        if phages_fasta.exists():
            prophage_regions = parse_prophage_from_fasta(phages_fasta)

    return prophage_regions


def parse_prophage_from_fasta(fasta_file):
    """
    Parse prophage coordinates from VIBRANT phages.fna file

    VIBRANT FASTA headers contain coordinate information:
    >NODE_123_length_45678_cov_12.34_fragment_1 # 10000 # 35000 # ...

    Returns: list of dicts with {contig, start, end, prophage_id}
    """
    prophage_regions = []

    with open(fasta_file) as f:
        for line in f:
            if line.startswith('>'):
                # Parse header
                parts = line.strip().split()
                header = parts[0][1:]  # Remove '>'

                # Extract contig name (remove fragment suffix)
                contig_parts = header.split('_')
                # Find where 'fragment' appears and take everything before it
                try:
                    fragment_idx = contig_parts.index('fragment')
                    contig = '_'.join(contig_parts[:fragment_idx])
                except ValueError:
                    # No fragment in name, use whole thing
                    contig = header

                # Try to parse coordinates from header comment
                # Format: >header # start # end # strand
                start, end = None, None
                if len(parts) >= 4 and parts[1] == '#':
                    try:
                        start = int(parts[2])
                        end = int(parts[4])
                    except (ValueError, IndexError):
                        pass

                if start and end:
                    prophage_regions.append({
                        'contig': contig,
                        'start': start,
                        'end': end,
                        'prophage_id': header,
                        'type': 'prophage'
                    })

    return prophage_regions


def parse_amr_coordinates(amr_file):
    """
    Parse AMR gene coordinates from AMRFinder output

    AMRFinder TSV columns include:
    - Contig id (column 1)
    - Start (column 2)
    - End (column 3)
    - Gene symbol (column 5)
    - Element type (column 8)
    - Class (column 10)

    Returns: list of dicts with {contig, start, end, gene, class, strand}
    """
    amr_genes = []

    if not Path(amr_file).exists():
        return amr_genes

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return amr_genes

        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 11:
                continue

            contig = parts[1]
            element_type = parts[8]
            gene_symbol = parts[5]

            # Only process AMR genes
            if element_type != 'AMR' or gene_symbol == 'NA':
                continue

            try:
                start = int(parts[2])
                end = int(parts[3])
                strand = parts[4]
                gene_class = parts[10]

                amr_genes.append({
                    'contig': contig,
                    'start': start,
                    'end': end,
                    'gene': gene_symbol,
                    'class': gene_class,
                    'strand': strand
                })
            except (ValueError, IndexError) as e:
                print(f"  ⚠️  Could not parse AMR line: {e}")
                continue

    return amr_genes


# ============================================================================
# DISTANCE CALCULATION
# ============================================================================

def calculate_distance_to_prophage(amr_gene, prophage_region):
    """
    Calculate minimum distance between AMR gene and prophage region

    Returns:
    - 0 if AMR is inside prophage
    - Positive distance if AMR is outside prophage
    - 'different_contig' if on different contigs
    """
    if amr_gene['contig'] != prophage_region['contig']:
        return 'different_contig'

    amr_start = amr_gene['start']
    amr_end = amr_gene['end']
    prophage_start = prophage_region['start']
    prophage_end = prophage_region['end']

    # Check if AMR is inside prophage
    if amr_start >= prophage_start and amr_end <= prophage_end:
        return 0  # Inside prophage

    # AMR is before prophage
    if amr_end < prophage_start:
        return prophage_start - amr_end

    # AMR is after prophage
    if amr_start > prophage_end:
        return amr_start - prophage_end

    # Overlapping but not fully inside
    return 0


def categorize_colocation(distance):
    """
    Categorize co-location based on distance

    Simplified categories:
    - within_prophage: Distance = 0 (inside prophage) - TRUE CO-LOCATION
    - outside_prophage: Any distance > 0 - NOT CO-LOCATED
    """
    if distance == 'different_contig':
        return 'outside_prophage'

    if distance == 0:
        return 'within_prophage'
    else:
        return 'outside_prophage'


def find_nearest_prophage(amr_gene, prophage_regions):
    """
    Find the nearest prophage region to an AMR gene

    Returns: (nearest_prophage, distance, category)
    """
    if not prophage_regions:
        return None, None, 'no_prophage'

    # Filter to same contig first
    same_contig_prophages = [p for p in prophage_regions if p['contig'] == amr_gene['contig']]

    if not same_contig_prophages:
        return None, 'different_contig', 'different_contig'

    # Find nearest
    min_distance = float('inf')
    nearest_prophage = None

    for prophage in same_contig_prophages:
        dist = calculate_distance_to_prophage(amr_gene, prophage)
        if dist != 'different_contig' and dist < min_distance:
            min_distance = dist
            nearest_prophage = prophage

    category = categorize_colocation(min_distance)

    return nearest_prophage, min_distance, category


# ============================================================================
# METADATA PARSING
# ============================================================================

def parse_metadata(metadata_file):
    """Parse metadata from filtered_samples.csv"""
    metadata = {}

    if not Path(metadata_file).exists():
        return metadata

    with open(metadata_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['Run']

            organism = row.get('organism', row.get('Organism', 'Unknown'))
            year = row.get('Year', '')
            if not year and 'Collection_Date' in row:
                year = row['Collection_Date'][:4] if row['Collection_Date'] else 'Unknown'
            if not year:
                year = 'Unknown'

            source = row.get('Isolation_source', row.get('source', 'Unknown'))
            sample_name = row.get('SampleName', '')

            metadata[sample_id] = {
                'organism': organism,
                'year': year,
                'source': source,
                'sample_name': sample_name
            }

    return metadata


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def run_true_colocation_analysis(results_dir):
    """
    Run true co-location analysis with physical distances
    """
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"
    metadata_file = results_dir / "filtered_samples" / "filtered_samples.csv"

    # Load metadata
    sample_metadata = parse_metadata(metadata_file)

    # Statistics
    stats = {
        'total_samples': 0,
        'samples_with_amr': 0,
        'samples_with_prophage': 0,
        'total_amr_genes': 0,
        'total_prophage_regions': 0,
        'colocation_categories': Counter(),
        'genes_by_category': defaultdict(Counter),
        'classes_by_category': defaultdict(Counter),
        'organism_colocation': defaultdict(lambda: Counter()),
        'year_colocation': defaultdict(lambda: Counter())
    }

    # Detailed results
    detailed_results = []

    # Process each sample
    print("\n🔬 Analyzing true AMR-prophage co-location...")
    print("="*80)

    for amr_file in sorted(amr_dir.glob("*_amr.tsv")):
        sample_id = amr_file.stem.replace('_amr', '')
        stats['total_samples'] += 1

        if stats['total_samples'] % 100 == 0:
            print(f"  Processed {stats['total_samples']} samples...")

        # Get metadata
        meta = sample_metadata.get(sample_id, {})
        organism = meta.get('organism', 'Unknown')
        year = meta.get('year', 'Unknown')

        # Parse data
        amr_genes = parse_amr_coordinates(amr_file)
        prophage_regions = parse_vibrant_prophage_coordinates(vibrant_dir, sample_id)

        if amr_genes:
            stats['samples_with_amr'] += 1

        if prophage_regions:
            stats['samples_with_prophage'] += 1

        stats['total_amr_genes'] += len(amr_genes)
        stats['total_prophage_regions'] += len(prophage_regions)

        # Analyze each AMR gene
        for amr_gene in amr_genes:
            nearest_prophage, distance, category = find_nearest_prophage(amr_gene, prophage_regions)

            stats['colocation_categories'][category] += 1
            stats['genes_by_category'][category][amr_gene['gene']] += 1
            stats['classes_by_category'][category][amr_gene['class']] += 1

            if organism != 'Unknown':
                stats['organism_colocation'][organism][category] += 1

            if year != 'Unknown':
                stats['year_colocation'][year][category] += 1

            # Store detailed result
            detailed_results.append({
                'sample': sample_id,
                'organism': organism,
                'year': year,
                'amr_gene': amr_gene['gene'],
                'amr_class': amr_gene['class'],
                'contig': amr_gene['contig'],
                'amr_start': amr_gene['start'],
                'amr_end': amr_gene['end'],
                'prophage_id': nearest_prophage['prophage_id'] if nearest_prophage else 'None',
                'prophage_start': nearest_prophage['start'] if nearest_prophage else None,
                'prophage_end': nearest_prophage['end'] if nearest_prophage else None,
                'distance': distance if distance != 'different_contig' else 'N/A',
                'category': category
            })

    print(f"  ✅ Processed {stats['total_samples']} samples\n")

    return stats, detailed_results


# ============================================================================
# REPORTING
# ============================================================================

def print_colocation_report(stats, detailed_results):
    """Print comprehensive co-location report"""

    print("\n" + "="*80)
    print("TRUE AMR-PROPHAGE CO-LOCATION ANALYSIS (DISTANCE-BASED)")
    print("="*80)

    print(f"\n📊 Overall Statistics:")
    print(f"  Total samples analyzed: {stats['total_samples']}")
    print(f"  Samples with AMR genes: {stats['samples_with_amr']}")
    print(f"  Samples with prophages: {stats['samples_with_prophage']}")
    print(f"  Total AMR genes: {stats['total_amr_genes']}")
    print(f"  Total prophage regions: {stats['total_prophage_regions']}")

    print(f"\n🎯 Co-location Results:")
    print(f"  {'Category':<25} {'Count':<10} {'Percentage'}")
    print("  " + "-"*60)

    total = sum(stats['colocation_categories'].values())
    within = stats['colocation_categories'].get('within_prophage', 0)
    outside = stats['colocation_categories'].get('outside_prophage', 0) + stats['colocation_categories'].get('no_prophage', 0)

    print(f"  {'🔴 Inside Prophage':<25} {within:<10} {(within/total*100 if total > 0 else 0):>6.2f}%")
    print(f"  {'⚪ Outside Prophage':<25} {outside:<10} {(outside/total*100 if total > 0 else 0):>6.2f}%")

    print(f"\n✨ AMR GENES CARRIED BY PROPHAGES:")
    print(f"   {within} out of {total} AMR genes ({within/total*100:.2f}%) are physically located")
    print(f"   inside prophage regions - potentially mobile with the prophage!")

    print(f"\n🧬 Top AMR Genes Inside Prophages:")
    print(f"  {'Gene':<25} {'Count'}")
    print("  " + "-"*40)
    for gene, count in stats['genes_by_category']['within_prophage'].most_common(15):
        print(f"  {gene:<25} {count}")

    print(f"\n💊 Top Drug Classes Inside Prophages:")
    print(f"  {'Drug Class':<40} {'Count'}")
    print("  " + "-"*50)
    for drug_class, count in stats['classes_by_category']['within_prophage'].most_common(10):
        print(f"  {drug_class:<40} {count}")

    print(f"\n🦠 Prophage-Carried AMR by Organism:")
    print(f"  {'Organism':<20} {'Inside Prophage':<15} {'Total AMR':<12} {'% Prophage-Carried'}")
    print("  " + "-"*70)
    for organism in sorted(stats['organism_colocation'].keys()):
        org_stats = stats['organism_colocation'][organism]
        inside = org_stats.get('within_prophage', 0)
        total_org = sum(org_stats.values())
        pct = (inside / total_org * 100) if total_org > 0 else 0
        print(f"  {organism:<20} {inside:<15} {total_org:<12} {pct:>6.2f}%")

    print(f"\n📅 Prophage-Carried AMR by Year:")
    print(f"  {'Year':<8} {'Inside Prophage':<15} {'Total AMR':<12} {'% Prophage-Carried'}")
    print("  " + "-"*50)
    for year in sorted(stats['year_colocation'].keys()):
        year_stats = stats['year_colocation'][year]
        inside = year_stats.get('within_prophage', 0)
        total_year = sum(year_stats.values())
        pct = (inside / total_year * 100) if total_year > 0 else 0
        print(f"  {year:<8} {inside:<15} {total_year:<12} {pct:>6.2f}%")

    print("\n" + "="*80 + "\n")


def export_detailed_csv(detailed_results, output_file):
    """Export detailed results to CSV"""
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['sample', 'organism', 'year', 'amr_gene', 'amr_class',
                     'contig', 'amr_start', 'amr_end', 'prophage_id',
                     'prophage_start', 'prophage_end', 'distance', 'category']

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_results)

    print(f"✅ Detailed results exported to: {output_file}\n")


# ============================================================================
# HTML REPORT GENERATION
# ============================================================================

def generate_html_report(detailed_results, stats, output_file):
    """Generate interactive HTML report from analysis results"""
    import pandas as pd
    from collections import Counter

    # Convert to DataFrame
    df = pd.DataFrame(detailed_results)

    # Filter to only within-prophage hits
    df_within = df[df['category'] == 'within_prophage'].copy()

    # Calculate statistics
    total_amr = len(df)
    total_within = len(df_within)
    pct_within = (total_within / total_amr * 100) if total_amr > 0 else 0

    # Top genes
    top_genes = df_within['amr_gene'].value_counts().head(15)

    # Top drug classes
    top_classes = df_within['amr_class'].value_counts().head(10)

    # By organism
    organism_stats_list = []
    for organism in df['organism'].unique():
        org_df = df[df['organism'] == organism]
        org_within = len(org_df[org_df['category'] == 'within_prophage'])
        org_total = len(org_df)
        org_pct = (org_within / org_total * 100) if org_total > 0 else 0
        organism_stats_list.append({
            'organism': organism,
            'within': org_within,
            'total': org_total,
            'percentage': org_pct
        })
    organism_stats_list = sorted(organism_stats_list, key=lambda x: x['within'], reverse=True)

    # By year
    year_stats_list = []
    for year in sorted(df['year'].unique()):
        year_df = df[df['year'] == year]
        year_within = len(year_df[year_df['category'] == 'within_prophage'])
        year_total = len(year_df)
        year_pct = (year_within / year_total * 100) if year_total > 0 else 0
        year_stats_list.append({
            'year': year,
            'within': year_within,
            'total': year_total,
            'percentage': year_pct
        })

    # Unique samples
    samples_with_coloc = df_within['sample'].nunique()
    total_samples = stats['total_samples']

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMR-Prophage Co-location Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }}
        .header p {{ font-size: 1.2em; opacity: 0.95; }}
        .nav-tabs {{
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
            padding: 0 20px;
            overflow-x: auto;
        }}
        .nav-tab {{
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1em;
            font-weight: 600;
            color: #6c757d;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            white-space: nowrap;
        }}
        .nav-tab:hover {{ color: #495057; background: rgba(0, 0, 0, 0.02); }}
        .nav-tab.active {{ color: #667eea; border-bottom-color: #667eea; }}
        .content {{ padding: 40px; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; animation: fadeIn 0.3s; }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .section h3 {{ color: #34495e; font-size: 1.4em; margin: 30px 0 15px 0; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        .stat-card .number {{ font-size: 2.5em; font-weight: 700; margin-bottom: 5px; }}
        .stat-card .label {{ font-size: 1em; opacity: 0.95; }}
        .highlight-box {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin: 30px 0;
            text-align: center;
            box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
        }}
        .highlight-box h2 {{ color: white; border: none; margin: 0 0 10px 0; font-size: 2em; }}
        .highlight-box p {{ font-size: 1.2em; opacity: 0.95; }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border-radius: 5px;
            overflow: hidden;
        }}
        .data-table thead tr {{ background: #667eea; color: white; text-align: left; }}
        .data-table th, .data-table td {{ padding: 12px 15px; }}
        .data-table tbody tr {{ border-bottom: 1px solid #dee2e6; }}
        .data-table tbody tr:hover {{ background: #f8f9fa; }}
        .data-table tbody tr:nth-of-type(even) {{ background: #f8f9fa; }}
        .bar-chart {{ margin: 20px 0; }}
        .bar-row {{ display: flex; align-items: center; margin: 10px 0; }}
        .bar-label {{
            width: 150px;
            font-weight: 600;
            color: #34495e;
            font-size: 0.9em;
        }}
        .bar-container {{
            flex: 1;
            background: #e9ecef;
            border-radius: 5px;
            overflow: hidden;
            height: 30px;
            position: relative;
        }}
        .bar-fill {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
            transition: width 0.5s ease;
        }}
        .alert {{
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .alert-info {{ background: #d1ecf1; border-color: #17a2b8; color: #0c5460; }}
        .alert-success {{ background: #d4edda; border-color: #28a745; color: #155724; }}
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }}
        .percentage-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: 600;
            font-size: 0.9em;
        }}
        .badge-low {{ background: #d4edda; color: #155724; }}
        .badge-medium {{ background: #fff3cd; color: #856404; }}
        .badge-high {{ background: #f8d7da; color: #721c24; }}
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8em; }}
            .content {{ padding: 20px; }}
            .stats-grid {{ grid-template-columns: 1fr; }}
            .bar-label {{ width: 100px; font-size: 0.8em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦠 AMR-Prophage Co-location Analysis</h1>
            <p>Resistance Genes Carried by Mobile Prophage Elements</p>
        </div>
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showTab('genes')">🧬 Genes</button>
            <button class="nav-tab" onclick="showTab('organisms')">🦠 Organisms</button>
            <button class="nav-tab" onclick="showTab('temporal')">📅 Temporal</button>
            <button class="nav-tab" onclick="showTab('data')">📁 Data</button>
        </div>
        <div class="content">
            <div id="overview" class="tab-content active">
                <div class="section">
                    <h2>Analysis Summary</h2>
                    <div class="highlight-box">
                        <h2>{total_within:,}</h2>
                        <p>AMR genes physically located inside prophage regions</p>
                        <p style="margin-top: 10px; font-size: 1.1em;">
                            {pct_within:.2f}% of all {total_amr:,} AMR genes detected
                        </p>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="number">{total_samples:,}</div>
                            <div class="label">Total Samples</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{samples_with_coloc:,}</div>
                            <div class="label">Samples with Prophage-Carried AMR</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{len(top_genes)}</div>
                            <div class="label">Unique AMR Genes in Prophages</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{len(top_classes)}</div>
                            <div class="label">Drug Classes Affected</div>
                        </div>
                    </div>
                    <div class="alert alert-info">
                        <strong>ℹ️ About This Analysis</strong><br>
                        This report identifies AMR genes that are physically located <strong>within</strong> prophage
                        region boundaries based on genomic coordinates. These genes are potentially mobile.
                    </div>
                </div>
            </div>
            <div id="genes" class="tab-content">
                <div class="section">
                    <h2>AMR Genes Inside Prophages</h2>
                    <h3>Top AMR Genes</h3>
                    <div class="bar-chart">
"""

    max_count = top_genes.max() if len(top_genes) > 0 else 1
    for gene, count in top_genes.items():
        width_pct = (count / max_count * 100)
        html_content += f"""
                        <div class="bar-row">
                            <div class="bar-label">{gene}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {width_pct}%">{count}</div>
                            </div>
                        </div>
"""

    html_content += """
                    </div>
                    <h3>Drug Resistance Classes</h3>
                    <div class="bar-chart">
"""

    max_class_count = top_classes.max() if len(top_classes) > 0 else 1
    for drug_class, count in top_classes.items():
        width_pct = (count / max_class_count * 100)
        html_content += f"""
                        <div class="bar-row">
                            <div class="bar-label" style="width: 250px;">{drug_class}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {width_pct}%">{count}</div>
                            </div>
                        </div>
"""

    html_content += """
                    </div>
                </div>
            </div>
            <div id="organisms" class="tab-content">
                <div class="section">
                    <h2>Prophage-Carried AMR by Organism</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Organism</th>
                                <th>AMR in Prophages</th>
                                <th>Total AMR Genes</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
"""

    for org in organism_stats_list:
        badge_class = 'badge-low' if org['percentage'] < 5 else 'badge-medium' if org['percentage'] < 15 else 'badge-high'
        html_content += f"""
                            <tr>
                                <td><strong>{org['organism']}</strong></td>
                                <td>{org['within']:,}</td>
                                <td>{org['total']:,}</td>
                                <td><span class="percentage-badge {badge_class}">{org['percentage']:.2f}%</span></td>
                            </tr>
"""

    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            <div id="temporal" class="tab-content">
                <div class="section">
                    <h2>Temporal Trends</h2>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Year</th>
                                <th>AMR in Prophages</th>
                                <th>Total AMR Genes</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
"""

    for year_data in year_stats_list:
        badge_class = 'badge-low' if year_data['percentage'] < 5 else 'badge-medium' if year_data['percentage'] < 15 else 'badge-high'
        html_content += f"""
                            <tr>
                                <td><strong>{year_data['year']}</strong></td>
                                <td>{year_data['within']:,}</td>
                                <td>{year_data['total']:,}</td>
                                <td><span class="percentage-badge {badge_class}">{year_data['percentage']:.2f}%</span></td>
                            </tr>
"""

    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            <div id="data" class="tab-content">
                <div class="section">
                    <h2>Detailed Data</h2>
                    <h3>Prophage-Associated AMR Genes (Preview)</h3>
"""

    preview_df = df_within[['sample', 'organism', 'year', 'amr_gene', 'amr_class', 'contig']].head(50)
    html_content += preview_df.to_html(classes='data-table', index=False, border=0)

    html_content += f"""
                    <div class="alert alert-info" style="margin-top: 30px;">
                        <strong>📊 Full Dataset</strong><br>
                        Showing first 50 of {len(df_within):,} prophage-associated AMR genes.
                        Download the complete CSV file for full analysis.
                    </div>
                </div>
            </div>
        </div>
        <div class="footer">
            <p><strong>AMR-Prophage Co-location Analysis Report</strong></p>
            <p>Generated from COMPASS pipeline results</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                🤖 Generated with <a href="https://claude.com/claude-code" style="color: #667eea;">Claude Code</a>
            </p>
        </div>
    </div>
    <script>
        function showTab(tabName) {{
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"✅ Generated HTML report: {output_file}\n")


# ============================================================================
# MULTI-YEAR SUPPORT
# ============================================================================

def find_year_directories(parent_dir):
    """
    Find all subdirectories that look like year-based results directories

    Looks for directories with 'amrfinder' and 'vibrant' subdirectories
    Returns list of Path objects
    """
    parent_dir = Path(parent_dir)
    year_dirs = []

    if not parent_dir.is_dir():
        return []

    for item in sorted(parent_dir.iterdir()):
        if item.is_dir():
            # Check if this directory has the expected structure
            if (item / "amrfinder").exists() and (item / "vibrant").exists():
                year_dirs.append(item)

    return year_dirs


def merge_stats(all_stats):
    """Merge statistics from multiple directories"""
    merged = {
        'total_samples': 0,
        'samples_with_amr': 0,
        'samples_with_prophage': 0,
        'total_amr_genes': 0,
        'total_prophage_regions': 0,
        'colocation_categories': Counter(),
        'genes_by_category': defaultdict(Counter),
        'classes_by_category': defaultdict(Counter),
        'organism_colocation': defaultdict(lambda: Counter()),
        'year_colocation': defaultdict(lambda: Counter())
    }

    for stats in all_stats:
        # Merge simple counts
        for key in ['total_samples', 'samples_with_amr', 'samples_with_prophage',
                    'total_amr_genes', 'total_prophage_regions']:
            merged[key] += stats[key]

        # Merge counters
        merged['colocation_categories'].update(stats['colocation_categories'])

        # Merge nested counters
        for category in stats['genes_by_category']:
            merged['genes_by_category'][category].update(stats['genes_by_category'][category])

        for category in stats['classes_by_category']:
            merged['classes_by_category'][category].update(stats['classes_by_category'][category])

        for organism in stats['organism_colocation']:
            merged['organism_colocation'][organism].update(stats['organism_colocation'][organism])

        for year in stats['year_colocation']:
            merged['year_colocation'][year].update(stats['year_colocation'][year])

    return merged


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_true_amr_prophage_colocation.py <results_dir_or_parent> [output_csv]")
        print("\nExamples:")
        print("  # Single year:")
        print("  python3 analyze_true_amr_prophage_colocation.py results_kansas_2021 kansas_2021_colocation.csv")
        print()
        print("  # All years (auto-detect subdirectories with results):")
        print("  python3 analyze_true_amr_prophage_colocation.py ~/compass_kansas_results kansas_all_years_colocation.csv")
        sys.exit(1)

    results_path = Path(sys.argv[1])
    output_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "true_amr_prophage_colocation.csv"

    if not results_path.exists():
        print(f"❌ Error: Path not found: {results_path}")
        sys.exit(1)

    # Check if this is a single results directory or parent with multiple subdirectories
    is_single_dir = (results_path / "amrfinder").exists() and (results_path / "vibrant").exists()

    if is_single_dir:
        # Single directory mode
        print(f"\n🔬 Running true co-location analysis on single directory...")
        print(f"   Directory: {results_path}")

        stats, detailed_results = run_true_colocation_analysis(results_path)

        if stats['total_samples'] == 0:
            print("❌ No samples found!")
            sys.exit(1)

        print_colocation_report(stats, detailed_results)
        export_detailed_csv(detailed_results, output_csv)

        # Generate HTML report
        html_file = output_csv.with_suffix('.html')
        generate_html_report(detailed_results, stats, html_file)

        print(f"✅ Analysis complete!\n")

    else:
        # Multi-directory mode - search for year directories
        print(f"\n🔍 Searching for results directories in: {results_path}")
        year_dirs = find_year_directories(results_path)

        if not year_dirs:
            print("❌ No results directories found and not a valid single results directory!")
            print("   Looking for subdirectories with 'amrfinder' and 'vibrant' folders")
            sys.exit(1)

        print(f"\n✅ Found {len(year_dirs)} results directories:")
        for d in year_dirs:
            print(f"   - {d.name}")

        print(f"\n🔬 Processing all directories...")

        all_stats = []
        all_detailed_results = []

        for directory in year_dirs:
            print(f"\n   📁 Processing {directory.name}...")
            try:
                stats, detailed_results = run_true_colocation_analysis(directory)
                if stats['total_samples'] > 0:
                    all_stats.append(stats)
                    all_detailed_results.extend(detailed_results)
                    print(f"   ✅ {directory.name}: {stats['total_samples']} samples, "
                          f"{stats['total_amr_genes']} AMR genes, "
                          f"{stats['total_prophage_regions']} prophage regions")
                else:
                    print(f"   ⚠️  {directory.name}: No samples found")
            except Exception as e:
                print(f"   ❌ {directory.name}: Error - {e}")

        if not all_stats:
            print("\n❌ No data collected from any directory!")
            sys.exit(1)

        # Merge all statistics
        print(f"\n🔄 Merging data from {len(all_stats)} directories...")
        merged_stats = merge_stats(all_stats)

        # Print combined report
        print_colocation_report(merged_stats, all_detailed_results)

        # Export combined CSV
        export_detailed_csv(all_detailed_results, output_csv)

        # Generate HTML report
        html_file = output_csv.with_suffix('.html')
        generate_html_report(all_detailed_results, merged_stats, html_file)

        print(f"✅ Multi-year analysis complete!\n")


if __name__ == "__main__":
    main()
