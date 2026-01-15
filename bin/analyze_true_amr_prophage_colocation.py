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

        print(f"✅ Multi-year analysis complete!\n")


if __name__ == "__main__":
    main()
