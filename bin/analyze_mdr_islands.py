#!/usr/bin/env python3
"""
Identify Multi-Drug Resistance (MDR) Islands:
Contigs carrying AMR genes from multiple drug classes + prophage sequences.

These "super-prophages" represent mobile genetic elements with high clinical importance.
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter

def parse_amr_by_contig(amr_file):
    """Extract AMR genes grouped by contig and drug class"""
    contig_amr = defaultdict(list)

    if not Path(amr_file).exists():
        return contig_amr

    with open(amr_file) as f:
        header = next(f, None)
        if not header:
            return contig_amr

        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 11:
                contig = parts[1]
                element_type = parts[8]
                gene_symbol = parts[5]
                gene_class = parts[10]

                if element_type == 'AMR' and gene_symbol != 'NA':
                    contig_amr[contig].append({
                        'gene': gene_symbol,
                        'class': gene_class,
                        'start': int(parts[2]),
                        'end': int(parts[3])
                    })

    return contig_amr

def parse_prophage_contigs(vibrant_phages_file):
    """Extract prophage-containing contigs"""
    prophage_contigs = set()

    if not Path(vibrant_phages_file).exists():
        return prophage_contigs

    with open(vibrant_phages_file) as f:
        for line in f:
            if line.startswith('>'):
                # Extract base contig name (remove fragment suffix)
                contig = '_'.join(line.strip()[1:].split('_')[:-2])
                prophage_contigs.add(contig)

    return prophage_contigs

def get_contig_length(contig_name):
    """Extract contig length from name (format: NODE_X_length_12345_cov_Y)"""
    try:
        parts = contig_name.split('_')
        for i, part in enumerate(parts):
            if part == 'length' and i + 1 < len(parts):
                return int(parts[i + 1])
    except (ValueError, IndexError):
        pass
    return None

def parse_metadata(metadata_file, sample_id):
    """Parse organism from filtered_samples.csv"""
    if not Path(metadata_file).exists():
        return None

    with open(metadata_file) as f:
        header = next(f, None)
        if not header:
            return None

        for line in f:
            parts = line.strip().split(',')
            if len(parts) > 0 and sample_id in parts[0]:  # SRR ID in first column
                # Get organism from last column
                if len(parts) > 46:  # organism is at index 46
                    return parts[46]
    return None

def analyze_mdr_islands(results_dir):
    """Identify MDR islands across all samples"""
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    vibrant_dir = results_dir / "vibrant"
    metadata_file = results_dir / "filtered_samples" / "filtered_samples.csv"

    # Collect all MDR islands
    mdr_islands = []

    # Statistics
    total_samples = 0
    samples_with_mdr_islands = 0
    drug_class_combinations = Counter()

    for amr_file in sorted(amr_dir.glob("*_amr.tsv")):
        sample_id = amr_file.stem.replace('_amr', '')
        total_samples += 1

        # Parse data
        contig_amr = parse_amr_by_contig(amr_file)
        vibrant_phages_file = vibrant_dir / f"{sample_id}_phages.fna"
        prophage_contigs = parse_prophage_contigs(vibrant_phages_file)
        organism = parse_metadata(metadata_file, sample_id)

        # Find MDR islands (contigs with prophage + AMR from ≥2 drug classes)
        sample_has_mdr = False

        for contig, amr_genes in contig_amr.items():
            # Check if this contig has a prophage
            is_prophage = any(contig.startswith(pc) for pc in prophage_contigs)

            if not is_prophage:
                continue

            # Count unique drug classes on this contig
            drug_classes = set(gene['class'] for gene in amr_genes)

            # MDR island = ≥2 different drug classes
            if len(drug_classes) >= 2:
                sample_has_mdr = True
                contig_length = get_contig_length(contig)

                # Record drug class combination
                combo = tuple(sorted(drug_classes))
                drug_class_combinations[combo] += 1

                mdr_islands.append({
                    'sample': sample_id,
                    'organism': organism or 'Unknown',
                    'contig': contig,
                    'length': contig_length,
                    'num_amr_genes': len(amr_genes),
                    'num_drug_classes': len(drug_classes),
                    'drug_classes': drug_classes,
                    'amr_genes': amr_genes
                })

        if sample_has_mdr:
            samples_with_mdr_islands += 1

    return {
        'total_samples': total_samples,
        'samples_with_mdr_islands': samples_with_mdr_islands,
        'mdr_islands': mdr_islands,
        'drug_class_combinations': drug_class_combinations
    }

def print_analysis(data, results_dir):
    """Print comprehensive MDR island analysis"""

    print("\n" + "="*85)
    print("Multi-Drug Resistance (MDR) Island Analysis")
    print("Prophage-Associated Mobile Genetic Elements with Multi-Class AMR")
    print(f"Results: {results_dir}")
    print("="*85)

    print(f"\n📊 Overall Statistics:")
    print(f"  Total samples analyzed: {data['total_samples']}")
    print(f"  Samples with MDR islands: {data['samples_with_mdr_islands']} "
          f"({data['samples_with_mdr_islands']/data['total_samples']*100:.1f}%)")
    print(f"  Total MDR islands found: {len(data['mdr_islands'])}")

    if not data['mdr_islands']:
        print("\n❌ No MDR islands found (prophages with ≥2 drug classes)")
        return

    # Group by organism
    islands_by_organism = defaultdict(list)
    for island in data['mdr_islands']:
        islands_by_organism[island['organism']].append(island)

    print(f"\n🦠 MDR Islands by Organism:")
    for organism, islands in sorted(islands_by_organism.items()):
        print(f"  {organism:<20} {len(islands)} MDR islands")

    # Top drug class combinations
    print(f"\n💊 Most Common Drug Class Combinations:")
    print(f"  {'Drug Classes':<60} {'Count'}")
    print("  " + "-"*75)
    for combo, count in data['drug_class_combinations'].most_common(15):
        classes_str = ', '.join(sorted(combo))
        print(f"  {classes_str:<60} {count}")

    # Top MDR islands by diversity
    print(f"\n🔥 Top 20 MDR Islands (by drug class diversity):")
    print(f"  {'Sample':<20} {'Organism':<15} {'Contig Length':<15} "
          f"{'AMR Genes':<12} {'Drug Classes'}")
    print("  " + "-"*85)

    sorted_islands = sorted(data['mdr_islands'],
                          key=lambda x: (x['num_drug_classes'], x['num_amr_genes']),
                          reverse=True)

    for island in sorted_islands[:20]:
        length_str = f"{island['length']/1000:.1f}kb" if island['length'] else "Unknown"
        classes_str = ', '.join(sorted(island['drug_classes'])[:3])
        if len(island['drug_classes']) > 3:
            classes_str += f", +{len(island['drug_classes'])-3} more"

        print(f"  {island['sample']:<20} {island['organism']:<15} {length_str:<15} "
              f"{island['num_amr_genes']:<12} {classes_str}")

    # Detailed examples
    print(f"\n🔍 Detailed Examples of High-Impact MDR Islands:")

    # Show top 3 most diverse islands
    for i, island in enumerate(sorted_islands[:3], 1):
        print(f"\n  Example {i}: {island['sample']} ({island['organism']})")
        print(f"  Contig: {island['contig']}")
        length_str = f"{island['length']/1000:.1f}kb" if island['length'] else "Unknown"
        print(f"  Length: {length_str}")
        print(f"  Drug classes ({len(island['drug_classes'])}): {', '.join(sorted(island['drug_classes']))}")
        print(f"  AMR genes ({len(island['amr_genes'])}):")

        # Group genes by class
        by_class = defaultdict(list)
        for gene in island['amr_genes']:
            by_class[gene['class']].append(gene['gene'])

        for drug_class in sorted(by_class.keys()):
            genes_str = ', '.join(by_class[drug_class])
            print(f"    • {drug_class}: {genes_str}")

    # Large MDR islands (>100kb)
    large_islands = [i for i in data['mdr_islands'] if i['length'] and i['length'] > 100000]
    if large_islands:
        print(f"\n⚠️  Large MDR Islands (>100kb):")
        print(f"  Found {len(large_islands)} large prophage-MDR islands")
        print(f"  These likely represent complete prophage genomes with integrated AMR cassettes")

        for island in sorted(large_islands, key=lambda x: x['length'], reverse=True)[:5]:
            print(f"  • {island['sample']}: {island['length']/1000:.1f}kb, "
                  f"{island['num_drug_classes']} drug classes, "
                  f"{island['num_amr_genes']} AMR genes")

def main():
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    else:
        results_dir = Path("/homes/tylerdoe/compass_kansas_results/results_kansas_2024")

    data = analyze_mdr_islands(results_dir)

    print_analysis(data, results_dir)

    print("\n" + "="*85)
    print("✅ Analysis complete!")
    print("="*85 + "\n")

if __name__ == "__main__":
    main()
