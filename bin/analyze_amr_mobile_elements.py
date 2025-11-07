#!/usr/bin/env python3
"""
AMR-Mobile Element Co-location Analysis

Analyzes the association between AMR genes and mobile genetic elements:
1. Integrons (integrase genes - intI1, intI2, intI3, etc.)
2. Transposons (transposase genes - IS elements, Tn elements)
3. Plasmids (identified by MOB-suite)
4. Insertion sequences and other mobile elements

This uses AMRFinder output which reports:
- AMR genes (Element type = "AMR")
- Stress/metal/biocide resistance genes
- Virulence factors
- Mobile element genes (integrases, transposases)

Co-location is determined by physical distance on contigs.
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

# Mobile element gene patterns
MOBILE_ELEMENT_PATTERNS = {
    'integrase': {
        'patterns': [r'^int[IATCG]\d*$', r'^intI', r'integrase'],
        'description': 'Integron integrases (intI1, intI2, intI3, etc.)'
    },
    'transposase': {
        'patterns': [r'^tnp', r'transposase', r'^IS\d+'],
        'description': 'Transposases and IS elements'
    },
    'recombinase': {
        'patterns': [r'recombinase', r'^xerC', r'^xerD'],
        'description': 'Site-specific recombinases'
    },
    'resolvase': {
        'patterns': [r'resolvase', r'^tnpR'],
        'description': 'Resolvases'
    }
}

# Distance thresholds for co-location
DISTANCE_THRESHOLDS = {
    'adjacent': 5000,      # Within 5kb - likely in same operon/cassette
    'proximal': 20000,     # Within 20kb - likely on same mobile element
    'nearby': 50000,       # Within 50kb - possibly related
}

# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def parse_amrfinder_full(amr_file):
    """
    Parse complete AMRFinder output including AMR genes AND mobile elements

    Returns:
        amr_genes: list of AMR gene dicts
        mobile_elements: list of mobile element gene dicts
    """
    amr_genes = []
    mobile_elements = []

    if not Path(amr_file).exists():
        return amr_genes, mobile_elements

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return amr_genes, mobile_elements

        for line in f:
            if line.startswith('#'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 11:
                continue

            contig = parts[1]
            start = int(parts[2])
            end = int(parts[3])
            strand = parts[4]
            gene_symbol = parts[5]
            element_type = parts[8]
            element_subtype = parts[9] if len(parts) > 9 else ''
            gene_class = parts[10] if len(parts) > 10 else ''
            gene_name = parts[6] if len(parts) > 6 else ''

            gene_data = {
                'contig': contig,
                'start': start,
                'end': end,
                'strand': strand,
                'gene': gene_symbol,
                'gene_name': gene_name,
                'class': gene_class,
                'element_type': element_type,
                'element_subtype': element_subtype
            }

            # Categorize as AMR or mobile element
            if element_type == 'AMR':
                amr_genes.append(gene_data)
            else:
                # Check if it's a mobile element we're interested in
                mobile_type = classify_mobile_element(gene_symbol, gene_name)
                if mobile_type:
                    gene_data['mobile_type'] = mobile_type
                    mobile_elements.append(gene_data)

    return amr_genes, mobile_elements


def classify_mobile_element(gene_symbol, gene_name):
    """
    Classify a gene as a specific type of mobile element

    Returns: mobile element type or None
    """
    # Combine gene symbol and name for pattern matching
    combined = f"{gene_symbol} {gene_name}".lower()

    for me_type, config in MOBILE_ELEMENT_PATTERNS.items():
        for pattern in config['patterns']:
            if re.search(pattern, combined, re.IGNORECASE):
                return me_type

    return None


def parse_mobsuite_results(mobsuite_dir, sample_id):
    """
    Parse MOB-suite results to identify plasmid contigs

    MOB-suite creates files like:
    - chromosome.fasta (chromosomal contigs)
    - plasmid_*.fasta (plasmid contigs)
    - mobtyper_results.txt (typing info)

    Returns: set of plasmid contig names
    """
    plasmid_contigs = set()

    sample_mobsuite_dir = mobsuite_dir / f"{sample_id}_mobsuite"
    if not sample_mobsuite_dir.exists():
        return plasmid_contigs

    # Parse plasmid FASTA files
    for plasmid_fasta in sample_mobsuite_dir.glob("plasmid_*.fasta"):
        try:
            with open(plasmid_fasta) as f:
                for line in f:
                    if line.startswith('>'):
                        # Extract contig name
                        contig_name = line.strip()[1:].split()[0]
                        plasmid_contigs.add(contig_name)
        except Exception as e:
            print(f"  ⚠️  Could not parse {plasmid_fasta.name}: {e}")

    return plasmid_contigs


# ============================================================================
# DISTANCE CALCULATION
# ============================================================================

def calculate_distance(amr_gene, mobile_element):
    """
    Calculate minimum distance between AMR gene and mobile element gene

    Returns:
        - 0 if overlapping
        - Positive distance if separated
        - 'different_contig' if on different contigs
    """
    if amr_gene['contig'] != mobile_element['contig']:
        return 'different_contig'

    amr_start = amr_gene['start']
    amr_end = amr_gene['end']
    me_start = mobile_element['start']
    me_end = mobile_element['end']

    # Check if overlapping
    if not (amr_end < me_start or amr_start > me_end):
        return 0

    # Calculate gap distance
    if amr_end < me_start:
        return me_start - amr_end
    else:
        return amr_start - me_end


def categorize_distance(distance):
    """Categorize co-location based on distance"""
    if distance == 'different_contig':
        return 'different_contig'

    if distance == 0:
        return 'overlapping'
    elif distance <= DISTANCE_THRESHOLDS['adjacent']:
        return 'adjacent_5kb'
    elif distance <= DISTANCE_THRESHOLDS['proximal']:
        return 'proximal_20kb'
    elif distance <= DISTANCE_THRESHOLDS['nearby']:
        return 'nearby_50kb'
    else:
        return 'same_contig_distant'


def find_nearest_mobile_elements(amr_gene, mobile_elements):
    """
    Find nearest mobile element of each type to an AMR gene

    Returns: dict with nearest element for each mobile type
    """
    nearest = {}

    # Group mobile elements by type
    by_type = defaultdict(list)
    for me in mobile_elements:
        by_type[me['mobile_type']].append(me)

    # Find nearest of each type
    for me_type, elements in by_type.items():
        # Filter to same contig
        same_contig = [e for e in elements if e['contig'] == amr_gene['contig']]

        if not same_contig:
            nearest[me_type] = {
                'distance': 'different_contig',
                'category': 'different_contig',
                'element': None
            }
            continue

        # Find nearest
        min_dist = float('inf')
        nearest_element = None

        for element in same_contig:
            dist = calculate_distance(amr_gene, element)
            if dist != 'different_contig' and dist < min_dist:
                min_dist = dist
                nearest_element = element

        nearest[me_type] = {
            'distance': min_dist,
            'category': categorize_distance(min_dist),
            'element': nearest_element
        }

    return nearest


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

            metadata[sample_id] = {
                'organism': organism,
                'year': year,
                'source': source
            }

    return metadata


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def run_mobile_element_analysis(results_dir):
    """
    Run AMR-mobile element co-location analysis
    """
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    mobsuite_dir = results_dir / "mobsuite"
    metadata_file = results_dir / "filtered_samples" / "filtered_samples.csv"

    # Load metadata
    sample_metadata = parse_metadata(metadata_file)

    # Statistics
    stats = {
        'total_samples': 0,
        'samples_with_amr': 0,
        'samples_with_mobile_elements': 0,
        'samples_with_plasmids': 0,
        'total_amr_genes': 0,
        'total_mobile_elements': Counter(),
        'total_plasmid_contigs': 0,
        'amr_on_plasmids': 0,
        'colocation_by_type': defaultdict(lambda: Counter()),
        'genes_near_mobile': defaultdict(lambda: Counter()),
        'classes_near_mobile': defaultdict(lambda: Counter()),
        'organism_stats': defaultdict(lambda: defaultdict(int)),
        'year_stats': defaultdict(lambda: defaultdict(int))
    }

    # Detailed results
    detailed_results = []

    print("\n🔬 Analyzing AMR-Mobile Element Co-location...")
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

        # Parse AMRFinder output
        amr_genes, mobile_elements = parse_amrfinder_full(amr_file)

        # Parse MOB-suite plasmid contigs
        plasmid_contigs = parse_mobsuite_results(mobsuite_dir, sample_id)

        # Update stats
        if amr_genes:
            stats['samples_with_amr'] += 1

        if mobile_elements:
            stats['samples_with_mobile_elements'] += 1

        if plasmid_contigs:
            stats['samples_with_plasmids'] += 1
            stats['total_plasmid_contigs'] += len(plasmid_contigs)

        stats['total_amr_genes'] += len(amr_genes)

        for me in mobile_elements:
            stats['total_mobile_elements'][me['mobile_type']] += 1

        # Analyze each AMR gene
        for amr_gene in amr_genes:
            # Check if on plasmid
            on_plasmid = amr_gene['contig'] in plasmid_contigs
            if on_plasmid:
                stats['amr_on_plasmids'] += 1

            # Find nearest mobile elements
            nearest_mes = find_nearest_mobile_elements(amr_gene, mobile_elements)

            # Update statistics for each mobile element type
            for me_type, info in nearest_mes.items():
                category = info['category']
                stats['colocation_by_type'][me_type][category] += 1

                # Track genes/classes near mobile elements (adjacent or proximal)
                if category in ['overlapping', 'adjacent_5kb', 'proximal_20kb']:
                    stats['genes_near_mobile'][me_type][amr_gene['gene']] += 1
                    stats['classes_near_mobile'][me_type][amr_gene['class']] += 1

            # Organism/year stats
            if organism != 'Unknown':
                stats['organism_stats'][organism]['total_amr'] += 1
                if on_plasmid:
                    stats['organism_stats'][organism]['on_plasmid'] += 1
                for me_type, info in nearest_mes.items():
                    if info['category'] in ['overlapping', 'adjacent_5kb', 'proximal_20kb']:
                        stats['organism_stats'][organism][f'near_{me_type}'] += 1

            if year != 'Unknown':
                stats['year_stats'][year]['total_amr'] += 1
                if on_plasmid:
                    stats['year_stats'][year]['on_plasmid'] += 1

            # Store detailed result
            result = {
                'sample': sample_id,
                'organism': organism,
                'year': year,
                'amr_gene': amr_gene['gene'],
                'amr_class': amr_gene['class'],
                'contig': amr_gene['contig'],
                'amr_start': amr_gene['start'],
                'amr_end': amr_gene['end'],
                'on_plasmid': 'Yes' if on_plasmid else 'No'
            }

            # Add nearest mobile element info for each type
            for me_type, info in nearest_mes.items():
                result[f'{me_type}_distance'] = info['distance'] if info['distance'] != 'different_contig' else 'N/A'
                result[f'{me_type}_category'] = info['category']
                if info['element']:
                    result[f'{me_type}_gene'] = info['element']['gene']
                else:
                    result[f'{me_type}_gene'] = 'None'

            detailed_results.append(result)

    print(f"  ✅ Processed {stats['total_samples']} samples\n")

    return stats, detailed_results


# ============================================================================
# REPORTING
# ============================================================================

def print_mobile_element_report(stats, detailed_results):
    """Print comprehensive mobile element co-location report"""

    print("\n" + "="*80)
    print("AMR-MOBILE ELEMENT CO-LOCATION ANALYSIS")
    print("="*80)

    print(f"\n📊 Overall Statistics:")
    print(f"  Total samples analyzed: {stats['total_samples']}")
    print(f"  Samples with AMR genes: {stats['samples_with_amr']}")
    print(f"  Samples with mobile element genes: {stats['samples_with_mobile_elements']}")
    print(f"  Samples with plasmids (MOB-suite): {stats['samples_with_plasmids']}")
    print(f"  Total AMR genes: {stats['total_amr_genes']}")
    print(f"  Total plasmid contigs: {stats['total_plasmid_contigs']}")

    print(f"\n🧬 Mobile Element Genes Found:")
    for me_type, count in sorted(stats['total_mobile_elements'].items()):
        desc = MOBILE_ELEMENT_PATTERNS.get(me_type, {}).get('description', me_type)
        print(f"  {me_type.capitalize():<20} {count:>6}  ({desc})")

    print(f"\n🎯 AMR Genes on Plasmids:")
    total_amr = stats['total_amr_genes']
    on_plasmid = stats['amr_on_plasmids']
    pct = (on_plasmid / total_amr * 100) if total_amr > 0 else 0
    print(f"  {on_plasmid} / {total_amr} ({pct:.2f}%)")

    # Report for each mobile element type
    for me_type in sorted(stats['colocation_by_type'].keys()):
        print(f"\n{'='*80}")
        print(f"🔍 Co-location with {me_type.upper()}")
        print(f"{'='*80}")

        coloc_stats = stats['colocation_by_type'][me_type]
        total = sum(coloc_stats.values())

        print(f"\n  Distance Categories:")
        print(f"  {'Category':<25} {'Count':<10} {'Percentage'}")
        print("  " + "-"*60)

        category_order = [
            'overlapping',
            'adjacent_5kb',
            'proximal_20kb',
            'nearby_50kb',
            'same_contig_distant',
            'different_contig'
        ]

        category_labels = {
            'overlapping': '🔴 Overlapping',
            'adjacent_5kb': '🟠 Adjacent (<5kb)',
            'proximal_20kb': '🟡 Proximal (<20kb)',
            'nearby_50kb': '🟢 Nearby (<50kb)',
            'same_contig_distant': '🔵 Same Contig (>50kb)',
            'different_contig': '⚪ Different Contig'
        }

        for category in category_order:
            count = coloc_stats.get(category, 0)
            pct = (count / total * 100) if total > 0 else 0
            label = category_labels.get(category, category)
            print(f"  {label:<25} {count:<10} {pct:>6.2f}%")

        # Close association (overlapping + adjacent + proximal)
        close_assoc = (coloc_stats.get('overlapping', 0) +
                      coloc_stats.get('adjacent_5kb', 0) +
                      coloc_stats.get('proximal_20kb', 0))
        close_pct = (close_assoc / total * 100) if total > 0 else 0

        print(f"\n  ✨ CLOSE ASSOCIATION (<20kb): {close_assoc} / {total} ({close_pct:.2f}%)")

        # Top genes near this mobile element type
        if stats['genes_near_mobile'][me_type]:
            print(f"\n  🧬 Top AMR Genes Near {me_type.capitalize()} (<20kb):")
            print(f"  {'Gene':<25} {'Count'}")
            print("  " + "-"*40)
            for gene, count in stats['genes_near_mobile'][me_type].most_common(15):
                print(f"  {gene:<25} {count}")

        # Top drug classes
        if stats['classes_near_mobile'][me_type]:
            print(f"\n  💊 Top Drug Classes Near {me_type.capitalize()} (<20kb):")
            print(f"  {'Drug Class':<40} {'Count'}")
            print("  " + "-"*50)
            for drug_class, count in stats['classes_near_mobile'][me_type].most_common(10):
                print(f"  {drug_class:<40} {count}")

    # Organism breakdown
    print(f"\n{'='*80}")
    print(f"🦠 Co-location by Organism")
    print(f"{'='*80}")
    print(f"\n  {'Organism':<20} {'Total AMR':<12} {'On Plasmid':<12} ", end="")
    for me_type in sorted(stats['colocation_by_type'].keys()):
        print(f"Near {me_type[:4]}", end="  ")
    print()
    print("  " + "-"*100)

    for organism in sorted(stats['organism_stats'].keys()):
        org_data = stats['organism_stats'][organism]
        print(f"  {organism:<20} {org_data['total_amr']:<12} {org_data['on_plasmid']:<12} ", end="")
        for me_type in sorted(stats['colocation_by_type'].keys()):
            count = org_data.get(f'near_{me_type}', 0)
            print(f"{count:<9} ", end="")
        print()

    # Year breakdown
    print(f"\n{'='*80}")
    print(f"📅 AMR on Plasmids by Year")
    print(f"{'='*80}")
    print(f"\n  {'Year':<10} {'Total AMR':<12} {'On Plasmid':<12} {'Percentage'}")
    print("  " + "-"*60)

    for year in sorted(stats['year_stats'].keys()):
        year_data = stats['year_stats'][year]
        total = year_data['total_amr']
        on_plas = year_data['on_plasmid']
        pct = (on_plas / total * 100) if total > 0 else 0
        print(f"  {year:<10} {total:<12} {on_plas:<12} {pct:>6.2f}%")

    print("\n" + "="*80 + "\n")


def export_detailed_csv(detailed_results, output_file):
    """Export detailed results to CSV"""
    if not detailed_results:
        print("⚠️  No results to export")
        return

    with open(output_file, 'w', newline='') as f:
        fieldnames = list(detailed_results[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_results)

    print(f"✅ Detailed results exported to: {output_file}\n")


# ============================================================================
# MULTI-YEAR SUPPORT
# ============================================================================

def find_year_directories(parent_dir):
    """Find all subdirectories with results"""
    parent_dir = Path(parent_dir)
    year_dirs = []

    if not parent_dir.is_dir():
        return []

    for item in sorted(parent_dir.iterdir()):
        if item.is_dir():
            if (item / "amrfinder").exists():
                year_dirs.append(item)

    return year_dirs


def merge_stats(all_stats):
    """Merge statistics from multiple directories"""
    merged = {
        'total_samples': 0,
        'samples_with_amr': 0,
        'samples_with_mobile_elements': 0,
        'samples_with_plasmids': 0,
        'total_amr_genes': 0,
        'total_mobile_elements': Counter(),
        'total_plasmid_contigs': 0,
        'amr_on_plasmids': 0,
        'colocation_by_type': defaultdict(lambda: Counter()),
        'genes_near_mobile': defaultdict(lambda: Counter()),
        'classes_near_mobile': defaultdict(lambda: Counter()),
        'organism_stats': defaultdict(lambda: defaultdict(int)),
        'year_stats': defaultdict(lambda: defaultdict(int))
    }

    for stats in all_stats:
        # Simple counts
        for key in ['total_samples', 'samples_with_amr', 'samples_with_mobile_elements',
                   'samples_with_plasmids', 'total_amr_genes', 'total_plasmid_contigs', 'amr_on_plasmids']:
            merged[key] += stats[key]

        # Counters
        merged['total_mobile_elements'].update(stats['total_mobile_elements'])

        # Nested counters
        for me_type in stats['colocation_by_type']:
            merged['colocation_by_type'][me_type].update(stats['colocation_by_type'][me_type])

        for me_type in stats['genes_near_mobile']:
            merged['genes_near_mobile'][me_type].update(stats['genes_near_mobile'][me_type])

        for me_type in stats['classes_near_mobile']:
            merged['classes_near_mobile'][me_type].update(stats['classes_near_mobile'][me_type])

        for organism in stats['organism_stats']:
            for key, val in stats['organism_stats'][organism].items():
                merged['organism_stats'][organism][key] += val

        for year in stats['year_stats']:
            for key, val in stats['year_stats'][year].items():
                merged['year_stats'][year][key] += val

    return merged


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_amr_mobile_elements.py <results_dir_or_parent> [output_csv]")
        print("\nExamples:")
        print("  # Single year:")
        print("  python3 analyze_amr_mobile_elements.py results_kansas_2021 kansas_2021_mobile.csv")
        print()
        print("  # All years:")
        print("  python3 analyze_amr_mobile_elements.py ~/compass_kansas_results kansas_all_mobile.csv")
        sys.exit(1)

    results_path = Path(sys.argv[1])
    output_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "amr_mobile_elements.csv"

    if not results_path.exists():
        print(f"❌ Error: Path not found: {results_path}")
        sys.exit(1)

    # Check if single directory or parent
    is_single_dir = (results_path / "amrfinder").exists()

    if is_single_dir:
        print(f"\n🔬 Running mobile element analysis on single directory...")
        print(f"   Directory: {results_path}")

        stats, detailed_results = run_mobile_element_analysis(results_path)

        if stats['total_samples'] == 0:
            print("❌ No samples found!")
            sys.exit(1)

        print_mobile_element_report(stats, detailed_results)
        export_detailed_csv(detailed_results, output_csv)
        print(f"✅ Analysis complete!\n")

    else:
        # Multi-directory mode
        print(f"\n🔍 Searching for results directories in: {results_path}")
        year_dirs = find_year_directories(results_path)

        if not year_dirs:
            print("❌ No results directories found!")
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
                stats, detailed_results = run_mobile_element_analysis(directory)
                if stats['total_samples'] > 0:
                    all_stats.append(stats)
                    all_detailed_results.extend(detailed_results)
                    print(f"   ✅ {directory.name}: {stats['total_samples']} samples, "
                          f"{stats['total_amr_genes']} AMR genes")
                else:
                    print(f"   ⚠️  {directory.name}: No samples found")
            except Exception as e:
                print(f"   ❌ {directory.name}: Error - {e}")

        if not all_stats:
            print("\n❌ No data collected!")
            sys.exit(1)

        # Merge and report
        print(f"\n🔄 Merging data from {len(all_stats)} directories...")
        merged_stats = merge_stats(all_stats)

        print_mobile_element_report(merged_stats, all_detailed_results)
        export_detailed_csv(all_detailed_results, output_csv)

        print(f"✅ Multi-year analysis complete!\n")


if __name__ == "__main__":
    main()
