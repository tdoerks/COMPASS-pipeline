#!/usr/bin/env python3
"""
True AMR-Prophage Co-location Analysis (Distance-Based)

This script performs accurate physical co-location analysis by:
1. Parsing exact prophage coordinates from VIBRANT outputs
2. Parsing exact AMR gene coordinates from AMRFinder
3. Calculating physical distances between AMR genes and prophage regions
4. Categorizing co-location based on distance thresholds

Co-location Categories:
- within_prophage: AMR gene inside prophage region boundaries
- proximal_10kb: Within 10kb of prophage boundaries
- proximal_50kb: Within 50kb of prophage boundaries
- same_contig_distant: On same contig but >50kb away
- different_contig: AMR and prophage on different contigs
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

    Categories:
    - within_prophage: Distance = 0 (inside prophage)
    - proximal_10kb: Distance 1-10,000 bp
    - proximal_50kb: Distance 10,001-50,000 bp
    - same_contig_distant: Distance >50,000 bp
    - different_contig: On different contigs
    """
    if distance == 'different_contig':
        return 'different_contig'

    if distance == 0:
        return 'within_prophage'
    elif distance <= 10000:
        return 'proximal_10kb'
    elif distance <= 50000:
        return 'proximal_50kb'
    else:
        return 'same_contig_distant'


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

    print(f"\n🎯 Co-location Categories:")
    print(f"  {'Category':<25} {'Count':<10} {'Percentage'}")
    print("  " + "-"*60)

    total = sum(stats['colocation_categories'].values())

    category_order = [
        'within_prophage',
        'proximal_10kb',
        'proximal_50kb',
        'same_contig_distant',
        'different_contig',
        'no_prophage'
    ]

    category_labels = {
        'within_prophage': '🔴 Inside Prophage',
        'proximal_10kb': '🟠 Within 10kb',
        'proximal_50kb': '🟡 Within 50kb',
        'same_contig_distant': '🔵 Same Contig (>50kb)',
        'different_contig': '⚪ Different Contig',
        'no_prophage': '⚫ No Prophage Found'
    }

    for category in category_order:
        count = stats['colocation_categories'].get(category, 0)
        pct = (count / total * 100) if total > 0 else 0
        label = category_labels.get(category, category)
        print(f"  {label:<25} {count:<10} {pct:>6.2f}%")

    # True co-location (within prophage)
    true_coloc = stats['colocation_categories'].get('within_prophage', 0)
    print(f"\n✨ TRUE CO-LOCATION (inside prophage): {true_coloc} / {total} ({true_coloc/total*100:.2f}%)")

    # Proximal (within 50kb)
    proximal = (stats['colocation_categories'].get('proximal_10kb', 0) +
                stats['colocation_categories'].get('proximal_50kb', 0))
    print(f"   Proximal co-location (within 50kb): {proximal} / {total} ({proximal/total*100:.2f}%)")

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

    print(f"\n🦠 Co-location by Organism:")
    print(f"  {'Organism':<20} {'Inside':<10} {'Proximal':<12} {'Total AMR'}")
    print("  " + "-"*60)
    for organism in sorted(stats['organism_colocation'].keys()):
        org_stats = stats['organism_colocation'][organism]
        inside = org_stats.get('within_prophage', 0)
        proximal = org_stats.get('proximal_10kb', 0) + org_stats.get('proximal_50kb', 0)
        total_org = sum(org_stats.values())
        print(f"  {organism:<20} {inside:<10} {proximal:<12} {total_org}")

    print(f"\n📅 Co-location by Year:")
    print(f"  {'Year':<8} {'Inside':<10} {'Proximal':<12} {'Total AMR'}")
    print("  " + "-"*50)
    for year in sorted(stats['year_colocation'].keys()):
        year_stats = stats['year_colocation'][year]
        inside = year_stats.get('within_prophage', 0)
        proximal = year_stats.get('proximal_10kb', 0) + year_stats.get('proximal_50kb', 0)
        total_year = sum(year_stats.values())
        print(f"  {year:<8} {inside:<10} {proximal:<12} {total_year}")

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
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_true_amr_prophage_colocation.py <results_dir> [output_csv]")
        print("\nExample:")
        print("  python3 analyze_true_amr_prophage_colocation.py /fastscratch/tylerdoe/results_kansas_2021_2025 kansas_true_colocation.csv")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    output_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "true_amr_prophage_colocation.csv"

    if not results_dir.exists():
        print(f"❌ Error: Results directory not found: {results_dir}")
        sys.exit(1)

    # Run analysis
    stats, detailed_results = run_true_colocation_analysis(results_dir)

    # Print report
    print_colocation_report(stats, detailed_results)

    # Export CSV
    export_detailed_csv(detailed_results, output_csv)

    print(f"✅ Analysis complete!\n")


if __name__ == "__main__":
    main()
