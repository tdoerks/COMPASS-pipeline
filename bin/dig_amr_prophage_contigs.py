#!/usr/bin/env python3
"""
Deep Dive: AMR Genes on Prophage-Containing Contigs

Analyzes the 7.77% of AMR genes that are on the same contigs as prophages.

Questions we'll answer:
1. Which specific AMR genes appear on prophage contigs?
2. Which drug classes are enriched on prophage contigs?
3. Which contigs carry both AMR and prophages most frequently?
4. Are certain organisms/sources more likely to have this pattern?
5. Do specific prophage-AMR combinations appear repeatedly?
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import json

# ============================================================================
# DATA LOADING
# ============================================================================

def extract_source_from_sample_name(sample_name):
    """Extract source type from NARMS sample name"""
    if not sample_name or len(sample_name) < 8:
        return 'Unknown'

    try:
        source_code = sample_name[6:8]
        source_map = {
            'GT': 'Ground Turkey',
            'CB': 'Chicken Breast',
            'GB': 'Ground Beef',
            'PK': 'Pork',
            'CC': 'Cecal Contents',
            'SW': 'Swine',
            'CT': 'Cattle',
            'CK': 'Chicken',
            'TK': 'Turkey',
            'PT': 'Poultry',
            'BF': 'Beef',
        }
        return source_map.get(source_code.upper(), f'Other ({source_code})')
    except:
        return 'Unknown'


def load_metadata(results_dir):
    """Load sample metadata"""
    metadata_file = Path(results_dir) / "filtered_samples" / "filtered_samples.csv"
    metadata = {}

    if not metadata_file.exists():
        return metadata

    with open(metadata_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row['Run']
            organism = row.get('organism', row.get('Organism', 'Unknown'))
            year = row.get('Year', '')
            if not year and 'Collection_Date' in row:
                year = row['Collection_Date'][:4] if row['Collection_Date'] else 'Unknown'

            sample_name = row.get('SampleName', row.get('Sample Name', ''))
            source = extract_source_from_sample_name(sample_name)

            metadata[sample_id] = {
                'organism': organism,
                'year': year,
                'source': source,
                'sample_name': sample_name
            }

    return metadata


def load_amr_by_contig(results_dir):
    """
    Load AMR data organized by contig

    Returns: dict[sample_id] -> dict[contig] -> list of AMR genes
    """
    amr_dir = Path(results_dir) / "amrfinder"
    amr_by_contig = {}

    for amr_file in amr_dir.glob("*_amr.tsv"):
        sample_id = amr_file.stem.replace('_amr', '')
        sample_data = defaultdict(list)

        with open(amr_file) as f:
            header = next(f, None)
            if not header:
                continue

            for line in f:
                if line.startswith('#'):
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 11:
                    continue

                if parts[8] != 'AMR':  # Only AMR genes
                    continue

                contig = parts[1]
                gene_data = {
                    'gene': parts[5],
                    'class': parts[10],
                    'subclass': parts[11] if len(parts) > 11 else '',
                    'start': int(parts[2]),
                    'end': int(parts[3])
                }

                sample_data[contig].append(gene_data)

        if sample_data:
            amr_by_contig[sample_id] = dict(sample_data)

    return amr_by_contig


def load_prophage_contigs(results_dir):
    """
    Load prophage data organized by contig

    Returns: dict[sample_id] -> set of contigs with prophages
    """
    vibrant_dir = Path(results_dir) / "vibrant"
    prophage_contigs = {}

    for sample_dir in vibrant_dir.glob("*_vibrant"):
        sample_id = sample_dir.name.replace('_vibrant', '')
        phage_fasta = vibrant_dir / f"{sample_id}_phages.fna"

        contigs = set()
        if phage_fasta.exists():
            with open(phage_fasta) as f:
                for line in f:
                    if line.startswith('>'):
                        header = line.strip()[1:].split()[0]
                        # Extract contig name (remove fragment suffix)
                        contig_parts = header.split('_')
                        try:
                            fragment_idx = contig_parts.index('fragment')
                            contig = '_'.join(contig_parts[:fragment_idx])
                        except ValueError:
                            contig = header
                        contigs.add(contig)

        if contigs:
            prophage_contigs[sample_id] = contigs

    return prophage_contigs


# ============================================================================
# ANALYSIS
# ============================================================================

def analyze_shared_contigs(amr_by_contig, prophage_contigs, metadata):
    """
    Deep analysis of contigs that have both AMR and prophages
    """
    print("\n" + "="*80)
    print("DEEP DIVE: AMR GENES ON PROPHAGE-CONTAINING CONTIGS")
    print("="*80)

    # Statistics
    stats = {
        'total_amr_genes': 0,
        'amr_on_prophage_contigs': 0,
        'samples_analyzed': set(),
        'samples_with_both': set(),
        'genes_on_prophage_contigs': Counter(),
        'classes_on_prophage_contigs': Counter(),
        'genes_not_on_prophage_contigs': Counter(),
        'classes_not_on_prophage_contigs': Counter(),
        'contig_frequency': Counter(),
        'by_organism': defaultdict(lambda: {'on_phage': 0, 'not_on_phage': 0}),
        'by_source': defaultdict(lambda: {'on_phage': 0, 'not_on_phage': 0}),
        'by_year': defaultdict(lambda: {'on_phage': 0, 'not_on_phage': 0}),
        'gene_pairs_on_phage_contigs': Counter(),
    }

    # Detailed records
    detailed_records = []

    # Analyze each sample
    for sample_id in set(amr_by_contig.keys()) | set(prophage_contigs.keys()):
        stats['samples_analyzed'].add(sample_id)

        if sample_id not in amr_by_contig or sample_id not in prophage_contigs:
            continue

        stats['samples_with_both'].add(sample_id)

        meta = metadata.get(sample_id, {})
        organism = meta.get('organism', 'Unknown')
        source = meta.get('source', 'Unknown')
        year = meta.get('year', 'Unknown')

        phage_contigs_set = prophage_contigs[sample_id]

        # Analyze each contig in this sample
        for contig, amr_genes in amr_by_contig[sample_id].items():
            is_on_phage_contig = contig in phage_contigs_set

            for gene_data in amr_genes:
                stats['total_amr_genes'] += 1

                if is_on_phage_contig:
                    stats['amr_on_prophage_contigs'] += 1
                    stats['genes_on_prophage_contigs'][gene_data['gene']] += 1
                    stats['classes_on_prophage_contigs'][gene_data['class']] += 1
                    stats['contig_frequency'][contig] += 1
                    stats['by_organism'][organism]['on_phage'] += 1
                    stats['by_source'][source]['on_phage'] += 1
                    stats['by_year'][year]['on_phage'] += 1

                    # Record detailed info
                    detailed_records.append({
                        'sample': sample_id,
                        'organism': organism,
                        'source': source,
                        'year': year,
                        'contig': contig,
                        'gene': gene_data['gene'],
                        'class': gene_data['class'],
                        'subclass': gene_data['subclass']
                    })
                else:
                    stats['genes_not_on_prophage_contigs'][gene_data['gene']] += 1
                    stats['classes_not_on_prophage_contigs'][gene_data['class']] += 1
                    stats['by_organism'][organism]['not_on_phage'] += 1
                    stats['by_source'][source]['not_on_phage'] += 1
                    stats['by_year'][year]['not_on_phage'] += 1

            # Find gene pairs on prophage contigs
            if is_on_phage_contig and len(amr_genes) > 1:
                genes_on_contig = sorted([g['gene'] for g in amr_genes])
                for i, g1 in enumerate(genes_on_contig):
                    for g2 in genes_on_contig[i+1:]:
                        stats['gene_pairs_on_phage_contigs'][(g1, g2)] += 1

    return stats, detailed_records


def print_analysis(stats, detailed_records):
    """Print comprehensive analysis"""

    print(f"\n📊 Overall Statistics:")
    print(f"  Total samples analyzed: {len(stats['samples_analyzed'])}")
    print(f"  Samples with both AMR and prophages: {len(stats['samples_with_both'])}")
    print(f"  Total AMR genes: {stats['total_amr_genes']}")
    print(f"  AMR genes on prophage contigs: {stats['amr_on_prophage_contigs']}")
    pct = stats['amr_on_prophage_contigs'] / stats['total_amr_genes'] * 100 if stats['total_amr_genes'] > 0 else 0
    print(f"  Percentage: {pct:.2f}%")

    print(f"\n🧬 Top AMR Genes on Prophage Contigs:")
    print(f"  {'Gene':<25} {'On Phage Ctg':<15} {'Not on Phage':<15} {'% On Phage'}")
    print("  " + "-"*80)

    for gene, count_on in stats['genes_on_prophage_contigs'].most_common(20):
        count_not = stats['genes_not_on_prophage_contigs'].get(gene, 0)
        total = count_on + count_not
        pct = count_on / total * 100 if total > 0 else 0
        print(f"  {gene:<25} {count_on:<15} {count_not:<15} {pct:>6.1f}%")

    print(f"\n💊 Top Drug Classes on Prophage Contigs:")
    print(f"  {'Drug Class':<40} {'On Phage Ctg':<15} {'Not on Phage':<15} {'% On Phage'}")
    print("  " + "-"*95)

    for drug_class, count_on in stats['classes_on_prophage_contigs'].most_common(15):
        count_not = stats['classes_not_on_prophage_contigs'].get(drug_class, 0)
        total = count_on + count_not
        pct = count_on / total * 100 if total > 0 else 0
        print(f"  {drug_class:<40} {count_on:<15} {count_not:<15} {pct:>6.1f}%")

    print(f"\n🔗 AMR Gene Pairs Co-occurring on Same Prophage Contig:")
    print(f"  {'Gene 1':<25} {'Gene 2':<25} {'Occurrences'}")
    print("  " + "-"*70)

    for (g1, g2), count in stats['gene_pairs_on_phage_contigs'].most_common(15):
        print(f"  {g1:<25} {g2:<25} {count}")

    print(f"\n🦠 By Organism:")
    print(f"  {'Organism':<20} {'On Phage Ctg':<15} {'Not on Phage':<15} {'% On Phage'}")
    print("  " + "-"*70)

    for organism in sorted(stats['by_organism'].keys()):
        data = stats['by_organism'][organism]
        on_phage = data['on_phage']
        not_on_phage = data['not_on_phage']
        total = on_phage + not_on_phage
        pct = on_phage / total * 100 if total > 0 else 0
        print(f"  {organism:<20} {on_phage:<15} {not_on_phage:<15} {pct:>6.1f}%")

    print(f"\n🔬 By Food Source:")
    print(f"  {'Source':<30} {'On Phage Ctg':<15} {'Not on Phage':<15} {'% On Phage'}")
    print("  " + "-"*80)

    # Sort by total count
    sorted_sources = sorted(stats['by_source'].items(),
                           key=lambda x: x[1]['on_phage'] + x[1]['not_on_phage'],
                           reverse=True)

    for source, data in sorted_sources[:15]:
        on_phage = data['on_phage']
        not_on_phage = data['not_on_phage']
        total = on_phage + not_on_phage
        if total < 5:  # Skip very small groups
            continue
        pct = on_phage / total * 100 if total > 0 else 0
        print(f"  {source:<30} {on_phage:<15} {not_on_phage:<15} {pct:>6.1f}%")

    print(f"\n📅 By Year:")
    print(f"  {'Year':<10} {'On Phage Ctg':<15} {'Not on Phage':<15} {'% On Phage'}")
    print("  " + "-"*60)

    for year in sorted(stats['by_year'].keys()):
        data = stats['by_year'][year]
        on_phage = data['on_phage']
        not_on_phage = data['not_on_phage']
        total = on_phage + not_on_phage
        pct = on_phage / total * 100 if total > 0 else 0
        print(f"  {year:<10} {on_phage:<15} {not_on_phage:<15} {pct:>6.1f}%")

    print(f"\n📍 Most Frequent Prophage-AMR Contigs:")
    print(f"  {'Contig Name':<50} {'AMR Genes'}")
    print("  " + "-"*70)

    for contig, count in stats['contig_frequency'].most_common(20):
        contig_display = contig[:50] if len(contig) <= 50 else contig[:47] + "..."
        print(f"  {contig_display:<50} {count}")


def export_csv(detailed_records, output_file):
    """Export detailed records to CSV"""
    if not detailed_records:
        print("⚠️  No records to export")
        return

    with open(output_file, 'w', newline='') as f:
        fieldnames = ['sample', 'organism', 'source', 'year', 'contig', 'gene', 'class', 'subclass']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_records)

    print(f"\n✅ Detailed records exported to: {output_file}")


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
            if (item / "amrfinder").exists() and (item / "vibrant").exists():
                year_dirs.append(item)

    return year_dirs


def merge_data(all_amr, all_prophage, all_metadata):
    """Merge data from multiple directories"""
    merged_amr = {}
    merged_prophage = {}
    merged_metadata = {}

    for amr_dict in all_amr:
        merged_amr.update(amr_dict)

    for prophage_dict in all_prophage:
        merged_prophage.update(prophage_dict)

    for metadata_dict in all_metadata:
        merged_metadata.update(metadata_dict)

    return merged_amr, merged_prophage, merged_metadata


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dig_amr_prophage_contigs.py <results_dir_or_parent> [output_csv]")
        print("\nExamples:")
        print("  # Single year:")
        print("  python3 dig_amr_prophage_contigs.py results_kansas_2022")
        print()
        print("  # All years:")
        print("  python3 dig_amr_prophage_contigs.py ~/compass_kansas_results amr_prophage_contigs.csv")
        sys.exit(1)

    results_path = Path(sys.argv[1])
    output_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "amr_prophage_contigs.csv"

    if not results_path.exists():
        print(f"❌ Error: Path not found: {results_path}")
        sys.exit(1)

    # Check if single directory or parent
    is_single_dir = (results_path / "amrfinder").exists() and (results_path / "vibrant").exists()

    if is_single_dir:
        print(f"\n🔬 Analyzing AMR-Prophage contig overlap...")
        print(f"   Directory: {results_path}")

        metadata = load_metadata(results_path)
        amr_by_contig = load_amr_by_contig(results_path)
        prophage_contigs = load_prophage_contigs(results_path)

        stats, detailed_records = analyze_shared_contigs(amr_by_contig, prophage_contigs, metadata)
        print_analysis(stats, detailed_records)
        export_csv(detailed_records, output_csv)

    else:
        # Multi-year mode
        print(f"\n🔍 Searching for results directories in: {results_path}")
        year_dirs = find_year_directories(results_path)

        if not year_dirs:
            print("❌ No results directories found!")
            sys.exit(1)

        print(f"\n✅ Found {len(year_dirs)} results directories:")
        for d in year_dirs:
            print(f"   - {d.name}")

        # Load data from all directories
        all_amr = []
        all_prophage = []
        all_metadata = []

        for directory in year_dirs:
            print(f"\n📁 Loading data from {directory.name}...")
            try:
                metadata = load_metadata(directory)
                amr_by_contig = load_amr_by_contig(directory)
                prophage_contigs = load_prophage_contigs(directory)

                all_metadata.append(metadata)
                all_amr.append(amr_by_contig)
                all_prophage.append(prophage_contigs)

                print(f"   ✅ {directory.name}: {len(amr_by_contig)} samples with AMR, "
                      f"{len(prophage_contigs)} with prophages")
            except Exception as e:
                print(f"   ❌ Error loading {directory.name}: {e}")

        # Merge all data
        print(f"\n🔄 Merging data from {len(year_dirs)} directories...")
        merged_amr, merged_prophage, merged_metadata = merge_data(all_amr, all_prophage, all_metadata)

        # Analyze
        stats, detailed_records = analyze_shared_contigs(merged_amr, merged_prophage, merged_metadata)
        print_analysis(stats, detailed_records)
        export_csv(detailed_records, output_csv)

    print("\n" + "="*80)
    print("✅ Deep dive analysis complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
