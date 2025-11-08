#!/usr/bin/env python3
"""
Analyze associations between specific AMR genes and prophages in bacterial samples.
Identifies co-occurrence patterns and correlations.
"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd

def parse_amr_genes(amr_file):
    """Extract AMR gene names from AMRFinder results"""
    genes = []
    if not Path(amr_file).exists():
        return genes

    with open(amr_file) as f:
        header = next(f, None)  # Skip header
        if not header:
            return genes

        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 9:
                element_type = parts[8]  # Element type column (0-indexed, so column 9)
                gene_symbol = parts[5]   # Gene symbol column (0-indexed, so column 6)

                # Only include AMR genes, not virulence or stress
                if element_type == 'AMR' and gene_symbol != 'NA':
                    genes.append(gene_symbol)
    return genes

def parse_prophage_hits(diamond_file):
    """Extract prophage IDs from DIAMOND prophage results"""
    prophages = []
    if not Path(diamond_file).exists():
        return prophages

    with open(diamond_file) as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                prophage_id = parts[1]  # Subject/target ID
                # Extract meaningful prophage name (remove accession numbers)
                if '|' in prophage_id:
                    prophage_name = prophage_id.split('|')[0]
                else:
                    prophage_name = prophage_id.split('_')[0] if '_' in prophage_id else prophage_id
                prophages.append(prophage_name)

    return list(set(prophages))  # Unique prophages per sample

def analyze_associations(results_dir):
    """Analyze AMR-prophage associations across all samples"""
    results_dir = Path(results_dir)
    amr_dir = results_dir / "amrfinder"
    prophage_dir = results_dir / "diamond_prophage"

    if not amr_dir.exists():
        print(f"❌ Error: AMR directory not found: {amr_dir}")
        sys.exit(1)
    if not prophage_dir.exists():
        print(f"❌ Error: Prophage directory not found: {prophage_dir}")
        sys.exit(1)

    # Data structures for analysis
    sample_data = []  # List of dicts: {sample, amr_genes, prophages}
    amr_prophage_cooccur = defaultdict(lambda: defaultdict(int))  # amr_gene -> prophage -> count
    all_amr_genes = Counter()
    all_prophages = Counter()

    # Parse all samples
    for amr_file in amr_dir.glob("*_amr.tsv"):
        sample_id = amr_file.stem.replace('_amr', '')
        prophage_file = prophage_dir / f"{sample_id}_diamond_results.tsv"

        amr_genes = parse_amr_genes(amr_file)
        prophages = parse_prophage_hits(prophage_file)

        if not amr_genes or not prophages:
            continue

        sample_data.append({
            'sample': sample_id,
            'amr_genes': amr_genes,
            'prophages': prophages,
            'amr_count': len(amr_genes),
            'prophage_count': len(prophages)
        })

        # Track overall frequencies
        all_amr_genes.update(amr_genes)
        all_prophages.update(prophages)

        # Track co-occurrences
        for amr in amr_genes:
            for prophage in prophages:
                amr_prophage_cooccur[amr][prophage] += 1

    return sample_data, amr_prophage_cooccur, all_amr_genes, all_prophages

def print_summary(sample_data, amr_prophage_cooccur, all_amr_genes, all_prophages, results_dir):
    """Print comprehensive analysis summary"""

    print("\n" + "="*70)
    print(f"AMR-Prophage Association Analysis")
    print(f"Results directory: {results_dir}")
    print("="*70)

    print(f"\n📊 Dataset Summary:")
    print(f"  Total samples analyzed: {len(sample_data)}")
    print(f"  Unique AMR genes found: {len(all_amr_genes)}")
    print(f"  Unique prophages found: {len(all_prophages)}")

    # Top AMR genes
    print(f"\n🦠 Top 15 AMR Genes (by frequency):")
    print(f"  {'Gene':<20} {'Samples':<10} {'% of samples'}")
    print("  " + "-"*50)
    for gene, count in all_amr_genes.most_common(15):
        pct = (count / len(sample_data)) * 100
        print(f"  {gene:<20} {count:<10} {pct:>6.1f}%")

    # Top prophages
    print(f"\n🧬 Top 15 Prophages (by frequency):")
    print(f"  {'Prophage':<25} {'Samples':<10} {'% of samples'}")
    print("  " + "-"*55)
    for prophage, count in all_prophages.most_common(15):
        pct = (count / len(sample_data)) * 100
        print(f"  {prophage:<25} {count:<10} {pct:>6.1f}%")

    # Strong associations (AMR gene appears in >20% of samples with that prophage)
    print(f"\n🔗 Strong AMR-Prophage Associations:")
    print(f"  (Pairs co-occurring in ≥10 samples)")
    print(f"  {'AMR Gene':<20} {'Prophage':<25} {'Co-occur':<10} {'AMR freq':<10} {'Prophage freq'}")
    print("  " + "-"*85)

    associations = []
    for amr, prophage_counts in amr_prophage_cooccur.items():
        for prophage, cooccur_count in prophage_counts.items():
            if cooccur_count >= 10:  # At least 10 co-occurrences
                amr_total = all_amr_genes[amr]
                prophage_total = all_prophages[prophage]
                associations.append((amr, prophage, cooccur_count, amr_total, prophage_total))

    # Sort by co-occurrence count
    associations.sort(key=lambda x: x[2], reverse=True)

    for amr, prophage, cooccur, amr_total, prophage_total in associations[:30]:
        print(f"  {amr:<20} {prophage:<25} {cooccur:<10} {amr_total:<10} {prophage_total}")

    # Samples with high AMR and prophage diversity
    print(f"\n🎯 Samples with High AMR-Prophage Diversity:")
    print(f"  {'Sample ID':<20} {'AMR genes':<12} {'Prophages':<12} {'Total elements'}")
    print("  " + "-"*60)

    sorted_samples = sorted(sample_data,
                          key=lambda x: x['amr_count'] + x['prophage_count'],
                          reverse=True)

    for sample in sorted_samples[:20]:
        total = sample['amr_count'] + sample['prophage_count']
        print(f"  {sample['sample']:<20} {sample['amr_count']:<12} {sample['prophage_count']:<12} {total}")

def main():
    # Get results directory from command line or use default
    if len(sys.argv) > 1:
        results_dir = Path(sys.argv[1])
    else:
        results_dir = Path("/homes/tylerdoe/compass_kansas_results/results_kansas_2024")

    sample_data, amr_prophage_cooccur, all_amr_genes, all_prophages = analyze_associations(results_dir)

    if not sample_data:
        print("❌ No samples with both AMR and prophage data found!")
        sys.exit(1)

    print_summary(sample_data, amr_prophage_cooccur, all_amr_genes, all_prophages, results_dir)

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
